import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Paperclip, X, FileText } from 'lucide-react';
import { speechService } from '../services/speechService';

export default function MessageInput({ onSendMessage, disabled }) {
  const [text, setText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);

  // Dynamic Textarea Auto-Resize
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [text]);

  const handleSend = () => {
    if ((!text.trim() && attachments.length === 0) || disabled) return;
    onSendMessage(text, attachments);
    setText('');
    setAttachments([]);
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleVoiceInput = () => {
    if (isListening) {
      speechService.stopListening();
      setIsListening(false);
    } else {
      setIsListening(true);
      speechService.startListening(
        (transcript) => {
          setText(prev => (prev ? `${prev} ${transcript}` : transcript));
          setIsListening(false);
        },
        (error) => {
          console.warn('Speech error:', error);
          setIsListening(false);
        },
        () => {
          setIsListening(false);
        }
      );
    }
  };

  const processFiles = (files) => {
    Array.from(files).forEach(file => {
      const reader = new FileReader();
      if (file.type.startsWith('image/')) {
        reader.onload = (event) => {
          setAttachments(prev => [...prev, {
            id: Date.now() + Math.random(),
            name: file.name,
            type: 'image',
            mimeType: file.type,
            data: event.target.result
          }]);
        };
        reader.readAsDataURL(file);
      } else {
        reader.onload = (event) => {
          setAttachments(prev => [...prev, {
            id: Date.now() + Math.random(),
            name: file.name,
            type: 'document',
            mimeType: file.type || 'text/plain',
            data: event.target.result
          }]);
        };
        reader.readAsText(file);
      }
    });
  };

  const handleFileUpload = (e) => {
    if (e.target.files && e.target.files.length) {
      processFiles(e.target.files);
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length) {
      processFiles(e.dataTransfer.files);
    }
  };

  const removeAttachment = (id) => {
    setAttachments(prev => prev.filter(att => att.id !== id));
  };

  return (
    <div 
      className="input-section"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Attachment Previews */}
      {attachments.length > 0 && (
        <div style={{ display: 'flex', gap: '8px', padding: '8px 12px', background: 'var(--bg-card)', borderRadius: '12px 12px 0 0', border: '1px solid var(--border-color)', borderBottom: 'none', flexWrap: 'wrap' }}>
          {attachments.map(att => (
            <div key={att.id} style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: '6px', background: 'var(--bg-tertiary)', padding: '6px 10px', borderRadius: '8px', fontSize: '0.8rem', color: 'var(--text-primary)' }}>
              {att.type === 'image' ? (
                <img src={att.data} alt="thumb" style={{ width: '24px', height: '24px', borderRadius: '4px', objectFit: 'cover' }} />
              ) : (
                <FileText size={16} style={{ color: 'var(--accent-cyan)' }} />
              )}
              <span style={{ maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{att.name}</span>
              <button 
                onClick={() => removeAttachment(att.id)} 
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', marginLeft: '4px' }}
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      )}

      <div 
        className="input-box-wrapper" 
        style={{ 
          borderRadius: attachments.length > 0 ? '0 0 20px 20px' : '20px',
          borderColor: isDragging ? 'var(--accent-green)' : undefined,
          boxShadow: isDragging ? '0 0 25px var(--accent-glow)' : undefined
        }}
      >
        <button 
          className="mic-btn" 
          onClick={() => fileInputRef.current && fileInputRef.current.click()}
          title="Upload Image or Document (or drag & drop)"
        >
          <Paperclip size={20} />
        </button>

        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileUpload} 
          style={{ display: 'none' }} 
          accept="image/*,.txt,.md,.js,.py,.html,.css,.csv,.json,.pdf" 
          multiple
        />

        <button 
          className={`mic-btn ${isListening ? 'listening' : ''}`} 
          onClick={toggleVoiceInput}
          title={isListening ? "Listening... Click to stop" : "Speak to Jarvis"}
        >
          {isListening ? <MicOff size={20} /> : <Mic size={20} />}
        </button>

        <textarea
          ref={textareaRef}
          className="chat-input"
          placeholder={isListening ? "Listening..." : "Ask Jarvis, attach files, set timers..."}
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />

        <button 
          className="send-btn" 
          onClick={handleSend} 
          disabled={(!text.trim() && attachments.length === 0) || disabled}
          title="Send Command"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
