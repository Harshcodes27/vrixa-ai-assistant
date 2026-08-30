import React from 'react';
import { Plus, MessageSquare, Trash2, X } from 'lucide-react';

export default function Sidebar({ isOpen, closeSidebar, sessions, activeSessionId, onSelectSession, onNewChat, onDeleteSession }) {
  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <button className="new-chat-btn" onClick={onNewChat}>
          <Plus size={18} />
          <span>New Chat</span>
        </button>
        {isOpen && (
          <button className="menu-toggle" onClick={closeSidebar} style={{ marginLeft: '10px' }}>
            <X size={20} />
          </button>
        )}
      </div>

      <div className="history-list">
        <div style={{ padding: '8px 4px', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
          Chat History
        </div>
        {sessions.length === 0 ? (
          <div style={{ padding: '16px', color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center' }}>
            No previous chats
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              className={`history-item ${session.id === activeSessionId ? 'active' : ''}`}
              onClick={() => onSelectSession(session.id)}
            >
              <MessageSquare size={16} style={{ marginRight: '10px', flexShrink: 0 }} />
              <span className="history-title">{session.title || 'Untitled Chat'}</span>
              <button
                className="history-delete"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSession(session.id);
                }}
                title="Delete Chat"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}
