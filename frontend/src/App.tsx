import React, { useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { ChatPage } from '@/pages/ChatPage';
import { KnowledgePage } from '@/pages/KnowledgePage';
import { SettingsPage } from '@/pages/SettingsPage';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'chat' | 'knowledge' | 'settings'>('chat');

  return (
    <MainLayout currentTab={currentTab} onSelectTab={setCurrentTab}>
      {currentTab === 'chat' && <ChatPage />}
      {currentTab === 'knowledge' && <KnowledgePage />}
      {currentTab === 'settings' && <SettingsPage />}
    </MainLayout>
  );
};

export default App;
