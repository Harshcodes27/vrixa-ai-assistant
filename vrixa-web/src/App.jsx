import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ChatArea from './components/ChatArea';
import MessageInput from './components/MessageInput';
import SettingsModal from './components/SettingsModal';
import { jarvisBrain } from './services/jarvisBrain';
import { speechService } from './services/speechService';

export default function App() {
  const [sessions, setSessions] = useState(() => {
    const saved = localStorage.getItem('JARVIS_CHAT_SESSIONS');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) { console.error(e); }
    }
    return [{ id: 'default-1', title: 'New Conversation', messages: [] }];
  });

  const [activeSessionId, setActiveSessionId] = useState(() => {
    return localStorage.getItem('JARVIS_ACTIVE_SESSION_ID') || 'default-1';
  });

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [isThinking, setIsThinking] = useState(false);

  useEffect(() => {
    localStorage.setItem('JARVIS_CHAT_SESSIONS', JSON.stringify(sessions));
  }, [sessions]);

  useEffect(() => {
    localStorage.setItem('JARVIS_ACTIVE_SESSION_ID', activeSessionId);
  }, [activeSessionId]);

  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0];

  const handleNewChat = () => {
    const newId = 'chat-' + Date.now();
    const newSession = { id: newId, title: 'New Conversation', messages: [] };
    setSessions(prev => [newSession, ...prev]);
    setActiveSessionId(newId);
    setSidebarOpen(false);
  };

  const handleSelectSession = (id) => {
    setActiveSessionId(id);
    setSidebarOpen(false);
  };

  const handleDeleteSession = (id) => {
    setSessions(prev => {
      const filtered = prev.filter(s => s.id !== id);
      if (filtered.length === 0) {
        const fallback = { id: 'chat-' + Date.now(), title: 'New Conversation', messages: [] };
        setActiveSessionId(fallback.id);
        return [fallback];
      }
      if (activeSessionId === id) {
        setActiveSessionId(filtered[0].id);
      }
      return filtered;
    });
  };

  const handleSendMessage = async (text, attachments = []) => {
    if (!text.trim() && attachments.length === 0) return;

    const userMsg = { sender: 'user', text, attachments, timestamp: new Date().toISOString() };

    setSessions(prev => prev.map(session => {
      if (session.id === activeSessionId) {
        const updatedMsgs = [...session.messages, userMsg];
        const updatedTitle = session.messages.length === 0 
          ? (text ? (text.length > 25 ? text.substring(0, 25) + '...' : text) : 'Attachment Analysis') 
          : session.title;
        return { ...session, title: updatedTitle, messages: updatedMsgs };
      }
      return session;
    }));

    setIsThinking(true);

    try {
      const replyText = await jarvisBrain.processInput(text, attachments);
      const botMsg = { sender: 'bot', text: replyText, timestamp: new Date().toISOString() };

      setSessions(prev => prev.map(session => {
        if (session.id === activeSessionId) {
          return { ...session, messages: [...session.messages, botMsg] };
        }
        return session;
      }));

      if (ttsEnabled) {
        speechService.speak(replyText);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsThinking(false);
    }
  };

  return (
    <div className="app-container">
      <Sidebar 
        isOpen={sidebarOpen} 
        closeSidebar={() => setSidebarOpen(false)}
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
      />

      <div className="main-wrapper">
        <Header 
          toggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          openSettings={() => setSettingsOpen(true)}
          ttsEnabled={ttsEnabled}
          setTtsEnabled={setTtsEnabled}
        />

        <ChatArea 
          messages={activeSession ? activeSession.messages : []}
          onSelectStarter={handleSendMessage}
          isThinking={isThinking}
        />

        <MessageInput 
          onSendMessage={handleSendMessage}
          disabled={isThinking}
        />
      </div>

      <SettingsModal 
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />
    </div>
  );
}
