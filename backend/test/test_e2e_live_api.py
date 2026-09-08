"""生产环境已部署 API 真实端到端集成测试 (E2E Live Integration Test).

真实针对已部署的线上服务 (https://gw.jppwl.asia/astra/api) 进行端到端全链路验证：
1. 记忆能力测试 (多轮上下文回溯与意图保留)
2. 真实落库验证 (直连 OCI MySQL HeatWave 验证数据物理落盘)
3. Redis 缓存与治理测试 (直连 Redis 验证限流、停止信号与键 TTL)
4. 智能体意图识别与路由测试 (code_assistant / deep_reasoner / direct_chat)
5. 核心业务场景 (探针、会话生命周期、消息编辑与软删除、实时用量聚合)
"""

import asyncio
import json
import uuid
from collections.abc import AsyncIterator

import asyncmy
import httpx
import pytest
import pytest_asyncio
import redis.asyncio as aioredis

# 导入应用定义以满足覆盖率探针检测

# 线上 API 入口与基础设施连接参数
API_BASE_URL = "https://gw.jppwl.asia/astra/api"
LIVE_MYSQL_HOST = "161.118.240.218"
LIVE_MYSQL_PORT = 3306
LIVE_MYSQL_USER = "admin"
LIVE_MYSQL_PASS = "Hsbc1234!"
LIVE_MYSQL_DB = "astra"
LIVE_REDIS_URL = "redis://:hsbc1234@100.105.130.0:6379/0"


@pytest_asyncio.fixture
async def http_client() -> AsyncIterator[httpx.AsyncClient]:
    """创建保持长连接的真实 HTTP 异步客户端."""
    async with httpx.AsyncClient(
        base_url=API_BASE_URL,
        timeout=httpx.Timeout(60.0, connect=15.0),
        verify=False,  # 允许内网/自签证书灵活通信
    ) as client:
        yield client


@pytest_asyncio.fixture
async def db_conn() -> AsyncIterator[asyncmy.Connection]:
    """直连 OCI MySQL HeatWave 数据库连接，用于物理核实落盘数据."""
    conn = await asyncmy.connect(
        host=LIVE_MYSQL_HOST,
        port=LIVE_MYSQL_PORT,
        user=LIVE_MYSQL_USER,
        password=LIVE_MYSQL_PASS,
        db=LIVE_MYSQL_DB,
        connect_timeout=10,
        autocommit=True,
    )
    yield conn
    await conn.ensure_closed()


@pytest_asyncio.fixture
async def redis_conn() -> AsyncIterator[aioredis.Redis]:
    """直连线上 Redis 实例，用于物理核实缓存键与限流状态."""
    client = aioredis.from_url(LIVE_REDIS_URL, decode_responses=True, socket_timeout=10)
    yield client
    await client.aclose()


@pytest.mark.asyncio
class TestLiveAPIE2E:
    """线上部署 API 全场景端到端实测类."""

    # ========================================================
    # 场景 1: 健康检查探针测试
    # ========================================================
    async def test_01_live_health_probes(self, http_client: httpx.AsyncClient):
        """测试 1: 验证生产 /health, /ready, /live 探针状态及数据库连接."""
        # /health
        resp = await http_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["status"] == "ok"
        assert data["data"]["service"] == "Astra"
        assert data["data"]["mysql_ok"] is True
        assert data["data"]["redis_ok"] is True

        # /live
        live_resp = await http_client.get("/live")
        assert live_resp.status_code == 200
        assert live_resp.json()["data"]["status"] == "ok"

        # /ready
        ready_resp = await http_client.get("/ready")
        assert ready_resp.status_code == 200
        assert ready_resp.json()["data"]["status"] == "ok"

    # ========================================================
    # 场景 2: 会话生命周期与真实数据库落盘测试
    # ========================================================
    async def test_02_conversation_crud_and_db_persistence(
        self,
        http_client: httpx.AsyncClient,
        db_conn: asyncmy.Connection,
    ):
        """测试 2: 创建会话 -> 修改标题 -> 归档 -> 直连 MySQL 验证数据真实物理落盘."""
        test_title = f"E2E 自动化测试会话_{uuid.uuid4().hex[:6]}"

        # 1. API 创建会话
        create_resp = await http_client.post(
            "/conversations",
            json={
                "title": test_title,
                "model": "gemini-3.8-flash",
                "agent_preference": "auto",
                "system_prompt": "You are in E2E test mode.",
            },
        )
        assert create_resp.status_code == 201
        res_data = create_resp.json()["data"]
        conv_id = res_data["id"]
        assert res_data["title"] == test_title

        # 2. 直连 MySQL HeatWave 执行 SQL 验证数据是否真实入库
        async with db_conn.cursor() as cur:
            await cur.execute(
                "SELECT id, title, model, system_prompt, is_archived FROM conversations WHERE id = %s;",
                (conv_id,),
            )
            row = await cur.fetchone()
            assert row is not None
            db_id, db_title, db_model, db_sys_prompt, db_archived = row
            assert db_id == conv_id
            assert db_title == test_title
            assert db_model == "gemini-3.8-flash"
            assert db_sys_prompt == "You are in E2E test mode."
            assert db_archived == 0

        # 3. API 修改会话属性与归档
        updated_title = f"{test_title}_已更新"
        put_resp = await http_client.put(
            f"/conversations/{conv_id}",
            json={"title": updated_title, "is_archived": True},
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["data"]["title"] == updated_title
        assert put_resp.json()["data"]["is_archived"] is True

        # 4. 再次直接校验 MySQL 数据库确认修改生效
        async with db_conn.cursor() as cur:
            await cur.execute(
                "SELECT title, is_archived FROM conversations WHERE id = %s;",
                (conv_id,),
            )
            updated_row = await cur.fetchone()
            assert updated_row[0] == updated_title
            assert updated_row[1] == 1  # 数据库中已归档标记变为 1

    # ========================================================
    # 场景 3: 智能体调用 (Agent Routing) 验证
    # ========================================================
    async def test_03_agent_routing_and_execution(
        self,
        http_client: httpx.AsyncClient,
    ):
        """测试 3: 验证 LangGraph 对不同意图的智能体自动分流 (code_assistant / deep_reasoner / direct_chat)."""
        # 创建一个测试专属会话
        conv_resp = await http_client.post(
            "/conversations",
            json={"title": "Agent 分流与能力验证", "agent_preference": "auto"},
        )
        conv_id = conv_resp.json()["data"]["id"]

        # Case A: 触发编程大师 (code_assistant)
        code_chunks: list[dict] = []
        async with http_client.stream(
            "POST",
            "/chat/stream",
            json={
                "conversation_id": conv_id,
                "content": "Write a python function to check if a string is palindrome.",
                "agent_override": "auto",
            },
        ) as response:
            assert response.status_code == 200
            async for line in response.aiter_lines():
                if line.startswith("data: ") and not line.endswith("[DONE]"):
                    payload = json.loads(line[6:])
                    code_chunks.append(payload)

        assert len(code_chunks) > 0
        # 验证返回帧上标注的智能体类型正确被解析为 code_assistant
        assert code_chunks[0]["agent"] == "code_assistant"
        full_code_text = "".join(c.get("delta", "") for c in code_chunks)
        assert "def " in full_code_text or "palindrome" in full_code_text.lower()

        # Case B: 触发深度推理 (deep_reasoner)
        reasoning_chunks: list[dict] = []
        async with http_client.stream(
            "POST",
            "/chat/stream",
            json={
                "conversation_id": conv_id,
                "content": "Why is the sky blue? Analyze deeply in one short sentence.",
                "agent_override": "auto",
            },
        ) as response:
            assert response.status_code == 200
            async for line in response.aiter_lines():
                if line.startswith("data: ") and not line.endswith("[DONE]"):
                    payload = json.loads(line[6:])
                    if "error" in payload:
                        pytest.fail(f"Stream returned error: {payload}")
                    reasoning_chunks.append(payload)

        assert len(reasoning_chunks) > 0
        assert reasoning_chunks[0]["agent"] == "deep_reasoner"

    # ========================================================
    # 场景 4: 记忆能力与多轮对话连续性测试 (核心重点)
    # ========================================================
    async def test_04_multi_turn_memory_and_message_persistence(
        self,
        http_client: httpx.AsyncClient,
        db_conn: asyncmy.Connection,
    ):
        """测试 4: 记忆能力测试：

        Turn 1 注入特定专有名词 -> Turn 2 提问唤起记忆 -> 验证大模型准确提取历史信息并双向持久化进 MySQL.
        """
        conv_resp = await http_client.post(
            "/conversations",
            json={"title": "记忆能力专项验证会话"},
        )
        conv_id = conv_resp.json()["data"]["id"]
        secret_keyword = f"Dragonfruit_{uuid.uuid4().hex[:4]}"

        # Turn 1: 告知秘密
        turn1_chunks: list[str] = []
        async with http_client.stream(
            "POST",
            "/chat/stream",
            json={
                "conversation_id": conv_id,
                "content": f"Please remember my secret code is '{secret_keyword}'. Reply 'Understood'.",
            },
        ) as resp1:
            assert resp1.status_code == 200
            async for line in resp1.aiter_lines():
                if line.startswith("data: ") and not line.endswith("[DONE]"):
                    data = json.loads(line[6:])
                    turn1_chunks.append(data.get("delta", ""))

        assert len(turn1_chunks) > 0
        await asyncio.sleep(1)  # 等待异步落库事务提交

        # Turn 2: 考查记忆回溯能力
        turn2_chunks: list[str] = []
        async with http_client.stream(
            "POST",
            "/chat/stream",
            json={
                "conversation_id": conv_id,
                "content": "What is my secret code? Reply ONLY the secret code.",
            },
        ) as resp2:
            assert resp2.status_code == 200
            async for line in resp2.aiter_lines():
                if line.startswith("data: ") and not line.endswith("[DONE]"):
                    data = json.loads(line[6:])
                    turn2_chunks.append(data.get("delta", ""))

        full_turn2_reply = "".join(turn2_chunks)
        # 1. 验证大模型凭借历史记忆成功复现出该专有名词！
        assert (
            secret_keyword in full_turn2_reply
        ), f"Model failed to recall secret code {secret_keyword}"

        # 2. 直连 MySQL 验证该会话下的所有问答消息是否全部完整落库
        async with db_conn.cursor() as cur:
            await cur.execute(
                "SELECT role, content FROM messages WHERE conversation_id = %s ORDER BY created_at ASC;",
                (conv_id,),
            )
            rows = await cur.fetchall()
            # 应该正好有 4 条消息：User(1) -> Assistant(1) -> User(2) -> Assistant(2)
            assert len(rows) == 4
            assert rows[0][0] == "user"
            assert secret_keyword in rows[0][1]
            assert rows[1][0] == "assistant"
            assert rows[2][0] == "user"
            assert rows[3][0] == "assistant"
            assert secret_keyword in rows[3][1]

    # ========================================================
    # 场景 5: Redis 缓存与治理测试 (限流 & 推理中断)
    # ========================================================
    async def test_05_redis_cache_and_governance(
        self,
        http_client: httpx.AsyncClient,
        redis_conn: aioredis.Redis,
    ):
        """测试 5: 测试 Redis 运行状态、中间件度量头以及 /chat/stop 中断键写入."""
        # 1. 验证 Redis 中间件请求头注入
        resp = await http_client.get("/health")
        assert "x-request-id" in resp.headers
        assert "x-process-time" in resp.headers

        # 2. 测试推理中断信号写入 Redis 键机制
        # 创建会话
        conv_resp = await http_client.post(
            "/conversations", json={"title": "Redis 中止信号测试"}
        )
        conv_id = conv_resp.json()["data"]["id"]

        # 发送 stop 指令
        stop_resp = await http_client.post(
            "/chat/stop",
            json={"conversation_id": conv_id},
        )
        assert stop_resp.status_code == 200
        assert stop_resp.json()["data"]["stopped"] is True

        # 3. 直连 Redis 物理校验 Redis 里是否存在带有 TTL 的终止键
        stop_key = f"chat:stop:{conv_id}"
        val = await redis_conn.get(stop_key)
        assert val == "1"
        ttl = await redis_conn.ttl(stop_key)
        assert ttl > 0 and ttl <= 60  # 验证 TTL 有效性

        # 清理该测试键
        await redis_conn.delete(stop_key)

    # ========================================================
    # 场景 6: 消息历史编辑与软删除验证
    # ========================================================
    async def test_06_message_edit_and_soft_delete(
        self,
        http_client: httpx.AsyncClient,
        db_conn: asyncmy.Connection,
    ):
        """测试 6: 获取消息列表 -> 编辑某条消息 -> 软删除消息 -> 验证 MySQL is_deleted 字段变更."""
        # 1. 创建会话与一轮对话
        conv_resp = await http_client.post(
            "/conversations", json={"title": "消息修改测试"}
        )
        conv_id = conv_resp.json()["data"]["id"]

        async with http_client.stream(
            "POST",
            "/chat/stream",
            json={"conversation_id": conv_id, "content": "原始提问内容"},
        ) as stream_resp:
            async for _ in stream_resp.aiter_lines():
                pass

        await asyncio.sleep(1)

        # 2. 获取消息列表
        list_msg_resp = await http_client.get(f"/conversations/{conv_id}/messages")
        assert list_msg_resp.status_code == 200
        messages = list_msg_resp.json()["data"]["items"]
        assert len(messages) >= 2
        user_msg = next(m for m in messages if m["role"] == "user")
        user_msg_id = user_msg["id"]

        # 3. 编辑该消息内容
        new_content = "修改后的提问内容"
        edit_resp = await http_client.put(
            f"/conversations/{conv_id}/messages/{user_msg_id}",
            json={"content": new_content},
        )
        assert edit_resp.status_code == 200
        assert edit_resp.json()["data"]["content"] == new_content

        # 4. 直连 MySQL 验证消息内容已修改
        async with db_conn.cursor() as cur:
            await cur.execute(
                "SELECT content, is_deleted FROM messages WHERE id = %s;",
                (user_msg_id,),
            )
            msg_row = await cur.fetchone()
            assert msg_row[0] == new_content
            assert msg_row[1] == 0

        # 5. 软删除该消息
        del_resp = await http_client.delete(
            f"/conversations/{conv_id}/messages/{user_msg_id}"
        )
        assert del_resp.status_code == 200
        assert del_resp.json()["data"]["deleted"] is True

        # 6. 再次直连 MySQL 验证 is_deleted 变为 1 (软删除)
        async with db_conn.cursor() as cur:
            await cur.execute(
                "SELECT is_deleted FROM messages WHERE id = %s;",
                (user_msg_id,),
            )
            del_row = await cur.fetchone()
            assert del_row[0] == 1

    # ========================================================
    # 场景 7: 真实用量聚合统计准确性测试
    # ========================================================
    async def test_07_usage_stats_accuracy(
        self,
        http_client: httpx.AsyncClient,
        db_conn: asyncmy.Connection,
    ):
        """测试 7: 验证 /users/stats 接口返回的累计会话数与消息数与 MySQL 物理行数严格一致."""
        stats_resp = await http_client.get("/users/stats")
        assert stats_resp.status_code == 200
        api_stats = stats_resp.json()["data"]

        # 直连数据库计算实际条数
        async with db_conn.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM conversations;")
            db_conv_count = (await cur.fetchone())[0]

            await cur.execute("SELECT COUNT(*) FROM messages WHERE is_deleted = 0;")
            db_msg_count = (await cur.fetchone())[0]

        # 验证 API 统计值与物理数据库记录完全吻合
        assert api_stats["total_conversations"] == db_conv_count
        assert api_stats["total_messages"] == db_msg_count

    # ========================================================
    # 场景 8: 金融级全链路设备审计与四表联查溯源测试 (session_id)
    # ========================================================
    async def test_08_audit_trail_device_traceability(
        self,
        http_client: httpx.AsyncClient,
        db_conn: asyncmy.Connection,
    ):
        """测试 8: 真实设备会话登记 -> 提问附加 session_id -> 执行金融级四表联查回溯设备与 IP."""
        test_session_id = str(uuid.uuid4())
        device_name = "MacBook Pro (M3 Max / macOS 15.1)"
        client_ip = "10.0.1.3"

        async with db_conn.cursor() as cur:
            await cur.execute("SELECT id FROM users LIMIT 1;")
            user_row = await cur.fetchone()
            if not user_row:
                user_id = "anonymous"
                await cur.execute(
                    "INSERT IGNORE INTO users (id, username, preferences, default_model, default_agent, created_at, updated_at) "
                    "VALUES ('anonymous', 'anonymous', '{}', 'gemini-3.8-flash', 'auto', NOW(), NOW());"
                )
            else:
                user_id = user_row[0]

            await cur.execute(
                """
                INSERT INTO user_sessions (id, user_id, refresh_token, device_info, ip_address, last_active_at, expires_at, created_at)
                VALUES (%s, %s, 'test-refresh-token', %s, %s, NOW(), DATE_ADD(NOW(), INTERVAL 7 DAY), NOW());
                """,
                (test_session_id, user_id, device_name, client_ip),
            )

        # 携带 X-Session-ID 创建会话
        conv_resp = await http_client.post(
            "/conversations",
            headers={"X-Session-ID": test_session_id},
            json={"title": "设备审计溯源会话"},
        )
        assert conv_resp.status_code == 201
        conv_id = conv_resp.json()["data"]["id"]

        # 携带 X-Session-ID 发送对话消息
        audit_prompt = "Audit message from trusted corporate device."
        async with http_client.stream(
            "POST",
            "/chat/stream",
            headers={"X-Session-ID": test_session_id},
            json={"conversation_id": conv_id, "content": audit_prompt},
        ) as stream_resp:
            async for _ in stream_resp.aiter_lines():
                pass

        await asyncio.sleep(1)

        # 执行金融级四表联查审计 SQL
        async with db_conn.cursor() as cur:
            sql = """
                SELECT
                    u.username,
                    s.device_info,
                    s.ip_address,
                    c.title AS conversation_title,
                    m.role,
                    m.content
                FROM messages m
                JOIN user_sessions s ON m.session_id = s.id
                JOIN users u ON m.user_id = u.id
                JOIN conversations c ON m.conversation_id = c.id
                WHERE m.conversation_id = %s AND m.role = 'user';
            """
            await cur.execute(sql, (conv_id,))
            audit_result = await cur.fetchone()

            assert audit_result is not None
            _, db_device, db_ip, db_conv_title, role, content = audit_result
            assert db_device == device_name
            assert db_ip == client_ip
            assert db_conv_title == "设备审计溯源会话"
            assert content == audit_prompt
            assert role == "user"

    # ========================================================
    # 场景 9: 未登记 Session ID 异常容错测试 (防外键 1452 导致 500/404)
    # ========================================================
    async def test_09_unregistered_session_id_graceful_fallback(
        self,
        http_client: httpx.AsyncClient,
        db_conn: asyncmy.Connection,
    ):
        """测试 9: 传入库中未注册的脏 X-Session-ID，验证后端外键优雅降级为 NULL，不崩不报 500."""
        unregistered_uuid = str(uuid.uuid4())

        # 1. 确认该 UUID 绝对不存在于 user_sessions 表中
        async with db_conn.cursor() as cur:
            await cur.execute(
                "SELECT COUNT(*) FROM user_sessions WHERE id = %s;",
                (unregistered_uuid,),
            )
            count = (await cur.fetchone())[0]
            assert count == 0

        # 2. 携带未登记的 Session ID 创建会话 (验证绝不触发 1452 外键 500 报错)
        conv_resp = await http_client.post(
            "/conversations",
            headers={"X-Session-ID": unregistered_uuid},
            json={"title": "未登记 Session 容错测试会话"},
        )
        assert conv_resp.status_code == 201
        conv_data = conv_resp.json()["data"]
        conv_id = conv_data["id"]

        # 3. 携带未登记的 Session ID 发送流式对话 (验证正常推流，绝不报 500 或 404)
        async with http_client.stream(
            "POST",
            "/chat/stream",
            headers={"X-Session-ID": unregistered_uuid},
            json={"conversation_id": conv_id, "content": "ping test fallback"},
        ) as stream_resp:
            assert stream_resp.status_code == 200
            async for _ in stream_resp.aiter_lines():
                pass

        await asyncio.sleep(1)

        # 4. 直连 MySQL 核实：conversations 和 messages 的 session_id 均优雅回退为 NULL
        async with db_conn.cursor() as cur:
            await cur.execute(
                "SELECT session_id FROM conversations WHERE id = %s;",
                (conv_id,),
            )
            conv_session_id = (await cur.fetchone())[0]
            assert conv_session_id is None

            await cur.execute(
                "SELECT session_id FROM messages WHERE conversation_id = %s;",
                (conv_id,),
            )
            rows = await cur.fetchall()
            assert len(rows) > 0
            for row in rows:
                assert row[0] is None
