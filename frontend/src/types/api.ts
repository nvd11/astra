/**
 * 统一 API 响应格式 (与后端 BaseResponse[T] 严格一致)
 */
export interface BaseResponse<T> {
  code: number;
  message: string;
  data: T;
}

/**
 * 分页数据容器 (与后端 PaginatedData[T] 严格一致)
 */
export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}
