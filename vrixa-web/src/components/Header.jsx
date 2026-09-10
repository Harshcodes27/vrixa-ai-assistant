import React from 'react';
import { Menu, Bot, Settings, Volume2, VolumeX } from 'lucide-react';

export default function Header({ toggleSidebar, openSettings, ttsEnabled, setTtsEnabled }) {
  return (
    <header className="app-header">
      <div className="header-left">
        <button className="menu-toggle" onClick={toggleSidebar} title="Toggle Sidebar">
          <Menu size={22} />
        </button>
        <div className="brand-title">
          <Bot size={24} style={{ color: 'var(--accent-green)' }} />
          <span>JARVIS AI</span>
          <span className="pulse-dot"></span>
        </div>
      </div>

      <div className="header-actions">
        <button 
          className={`icon-btn ${ttsEnabled ? 'active' : ''}`} 
          onClick={() => setTtsEnabled(!ttsEnabled)}
          title={ttsEnabled ? "Voice Output Enabled (TTS)" : "Voice Output Muted"}
        >
          {ttsEnabled ? <Volume2 size={20} /> : <VolumeX size={20} />}
        </button>

        <button className="icon-btn" onClick={openSettings} title="Settings & API Keys">
          <Settings size={20} />
        </button>
      </div>
    </header>
  );
}
