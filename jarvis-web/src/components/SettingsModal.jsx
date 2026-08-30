import React, { useState, useEffect } from 'react';
import { X, Key, Info, Brain, Trash2 } from 'lucide-react';
import { jarvisBrain } from '../services/jarvisBrain';

export default function SettingsModal({ isOpen, onClose }) {
  const [apiKey, setApiKey] = useState('');
  const [memories, setMemories] = useState([]);
  const [savedStatus, setSavedStatus] = useState(false);

  useEffect(() => {
    if (isOpen) {
      const storedKey = localStorage.getItem('GEMINI_API_KEY') || '';
      setApiKey(storedKey);
      setMemories(jarvisBrain.getMemories());
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = () => {
    localStorage.setItem('GEMINI_API_KEY', apiKey.trim());
    setSavedStatus(true);
    setTimeout(() => {
      setSavedStatus(false);
      onClose();
    }, 1200);
  };

  const handleClearMemories = () => {
    localStorage.removeItem('JARVIS_LONG_TERM_MEMORY');
    setMemories([]);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Key size={20} style={{ color: 'var(--accent-green)' }} />
            <span>Jarvis Settings & Memory</span>
          </div>
          <button className="icon-btn" onClick={onClose} style={{ border: 'none' }}>
            <X size={18} />
          </button>
        </div>

        <div className="form-group">
          <label className="form-label">Google Gemini API Key</label>
          <input
            type="password"
            className="form-input"
            placeholder="AIzaSy..."
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
        </div>

        {/* Long-Term Memory Section */}
        <div style={{ margin: '20px 0 16px 0', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              <Brain size={18} style={{ color: 'var(--accent-cyan)' }} />
              <span>Cross-Session Long-Term Memory</span>
            </div>
            {memories.length > 0 && (
              <button 
                onClick={handleClearMemories} 
                style={{ background: 'none', border: 'none', color: '#ef4444', fontSize: '0.75rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
              >
                <Trash2 size={12} /> Clear Memory
              </button>
            )}
          </div>

          {memories.length === 0 ? (
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
             <p className="no-memories">No facts remembered yet. Tell Jarvis "Remember that I like AI & coding" in any chat!</p>
            </div>
          ) : (
            <div style={{ maxHeight: '100px', overflowY: 'auto', background: 'var(--bg-card)', padding: '8px 12px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              {memories.map((m, i) => (
                <div key={i} style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', padding: '3px 0' }}>
                  • {m}
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button 
            className="new-chat-btn" 
            onClick={handleSave} 
            style={{ width: 'auto', padding: '10px 24px' }}
          >
            {savedStatus ? 'Saved ✓' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}
