import React, { useRef, useEffect, useState } from 'react';
import { Bot, User, Copy, Check, Sparkles, FileText } from 'lucide-react';

export default function ChatArea({ messages, onSelectStarter, isThinking }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isThinking]);

  const starterCards = [
    { title: "🎨 Image Generation", desc: "Type 'Generate image of a futuristic cyberpunk city'", action: "Generate image of a futuristic cyberpunk city" },
    { title: "📷 Vision & Analysis", desc: "Upload a screenshot, math question, or document", action: "Summarize this attached document." },
    { title: "⏰ Alarms & Timers", desc: "Type 'Remind me in 10 seconds to take a break'", action: "Remind me in 10 seconds to take a break" }
  ];

  return (
    <main className="chat-viewport" ref={scrollRef}>
      {messages.length === 0 ? (
        <div className="empty-state">
          <div className="jarvis-avatar-large">
            <Bot size={42} style={{ color: 'var(--accent-green)' }} />
          </div>
          <h1 className="welcome-title">I am JARVIS Ultra</h1>
          <p className="welcome-subtitle">Vision AI • Image Generation • Alarms • Live Weather • Document Reader</p>

          <div className="starters-grid">
            {starterCards.map((card, idx) => (
              <div key={idx} className="starter-card" onClick={() => onSelectStarter(card.action)}>
                <div className="starter-title">{card.title}</div>
                <div className="starter-desc">{card.desc}</div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="messages-container">
          {messages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} />
          ))}
          {isThinking && (
            <div className="message-row bot">
              <div className="avatar bot">
                <Bot size={20} />
              </div>
              <div className="bubble-content" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={16} className="pulse-dot" />
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>JARVIS is processing...</span>
              </div>
            </div>
          )}
        </div>
      )}
    </main>
  );
}

function MessageBubble({ message }) {
  const isUser = message.sender === 'user';

  return (
    <div className={`message-row ${isUser ? 'user' : 'bot'}`}>
      <div className={`avatar ${isUser ? 'user' : 'bot'}`}>
        {isUser ? <User size={20} /> : <Bot size={20} />}
      </div>
      <div className="bubble-content">
        {message.attachments && message.attachments.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
            {message.attachments.map((att, i) => (
              <div key={i}>
                {att.type === 'image' ? (
                  <img src={att.data} alt="uploaded" style={{ maxWidth: '220px', maxHeight: '220px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.2)' }} />
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(255,255,255,0.1)', padding: '6px 10px', borderRadius: '6px', fontSize: '0.8rem' }}>
                    <FileText size={16} /> <span>{att.name}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        <FormattedText content={message.text} />
      </div>
    </div>
  );
}

function FormattedText({ content }) {
  const [copiedIndex, setCopiedIndex] = useState(null);

  if (!content) return null;

  const parts = content.split(/(```[\s\S]*?```|!\[.*?\]\(.*?\))/g);

  const handleCopy = (codeText, idx) => {
    navigator.clipboard.writeText(codeText);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const renderInlineStyles = (textChunk) => {
    // Basic bold and inline code styling
    const tokens = textChunk.split(/(\*\*.*?\*\*|`.*?`)/g);
    return tokens.map((token, i) => {
      if (token.startsWith('**') && token.endsWith('**')) {
        return <strong key={i} style={{ color: '#fff', fontWeight: 600 }}>{token.slice(2, -2)}</strong>;
      }
      if (token.startsWith('`') && token.endsWith('`')) {
        return <code key={i} style={{ background: 'rgba(255,255,255,0.15)', padding: '2px 6px', borderRadius: '4px', fontSize: '0.88em', fontFamily: 'var(--font-mono)' }}>{token.slice(1, -1)}</code>;
      }
      return token;
    });
  };

  return (
    <div>
      {parts.map((part, idx) => {
        if (part.startsWith('```') && part.endsWith('```')) {
          const lines = part.slice(3, -3).trim().split('\n');
          const language = lines[0].match(/^[a-zA-Z0-9_-]+$/) ? lines[0] : '';
          const codeContent = language ? lines.slice(1).join('\n') : lines.join('\n');

          return (
            <pre key={idx}>
              <button 
                className="copy-code-btn" 
                onClick={() => handleCopy(codeContent, idx)}
              >
                {copiedIndex === idx ? <Check size={14} color="#25d366" /> : <Copy size={14} />}
                <span>{copiedIndex === idx ? 'Copied' : 'Copy'}</span>
              </button>
              <code>{codeContent}</code>
            </pre>
          );
        }

        const imgMatch = part.match(/^!\[(.*?)\]\((.*?)\)$/);
        if (imgMatch) {
          const altText = imgMatch[1];
          const imgUrl = imgMatch[2];
          return (
            <div key={idx} style={{ margin: '12px 0' }}>
              <img 
                src={imgUrl} 
                alt={altText} 
                style={{ width: '100%', maxWidth: '450px', borderRadius: '14px', border: '1px solid var(--border-active)', boxShadow: '0 8px 25px rgba(0,0,0,0.5)' }} 
              />
            </div>
          );
        }

        return (
          <p key={idx} style={{ whiteSpace: 'pre-wrap', marginBottom: idx < parts.length - 1 ? '8px' : '0' }}>
            {renderInlineStyles(part)}
          </p>
        );
      })}
    </div>
  );
}
