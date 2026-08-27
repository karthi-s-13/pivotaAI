import React, { useState, useRef, useEffect } from 'react';
import { Send, Square, Sparkles } from 'lucide-react';
import { useAIStore } from '../stores/aiStore';

interface ChatInputProps {
  onSend: (message: string) => void;
  onStop: () => void;
}

export default function ChatInput({ onSend, onStop }: ChatInputProps) {
  const { isStreaming, selectedContext } = useAIStore();
  const [text, setText] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!text.trim() || isStreaming) return;
    onSend(text.trim());
    setText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [text]);

  const isDisabled = !selectedContext || (!text.trim() && !isStreaming);

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        display: 'flex',
        alignItems: 'flex-end',
        gap: '12px',
        background: 'var(--bg-surface)',
        border: isFocused ? '1px solid #9b51e0' : '1px solid var(--border-default)',
        borderRadius: '28px',
        padding: '10px 20px',
        boxShadow: isFocused ? '0 0 12px rgba(155, 81, 224, 0.15)' : 'none',
        transition: 'all var(--transition-base)',
        position: 'relative',
      }}
    >
      {/* Decorative Gemini Sparkle status icon */}
      <div style={{ display: 'flex', alignItems: 'center', height: '32px', color: 'var(--text-muted)' }}>
        <Sparkles size={16} style={{ color: isFocused ? '#9b51e0' : 'inherit', transition: 'color var(--transition-fast)' }} />
      </div>

      <textarea
        ref={textareaRef}
        rows={1}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        placeholder={
          selectedContext
            ? "Ask Pivota AI about your tables, connections, schemas..."
            : "Select a connection database to begin..."
        }
        disabled={!selectedContext}
        style={{
          flex: 1,
          border: 'none',
          outline: 'none',
          resize: 'none',
          background: 'transparent',
          fontSize: '0.9rem',
          color: 'var(--text-primary)',
          fontFamily: 'inherit',
          padding: '6px 0',
          maxHeight: '180px',
          lineHeight: '1.4',
        }}
      />

      {isStreaming ? (
        <button
          type="button"
          onClick={onStop}
          style={{
            width: 34,
            height: 34,
            borderRadius: '50%',
            background: 'var(--status-error)',
            border: 'none',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            flexShrink: 0,
          }}
          title="Stop Generating"
        >
          <Square size={12} color="white" fill="white" />
        </button>
      ) : (
        <button
          type="submit"
          disabled={isDisabled}
          style={{
            width: 34,
            height: 34,
            borderRadius: '50%',
            background: isDisabled 
              ? 'var(--bg-elevated)' 
              : 'linear-gradient(135deg, #4285f4, #9b51e0, #e051a8)',
            border: 'none',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: isDisabled ? 'not-allowed' : 'pointer',
            transition: 'all var(--transition-base)',
            flexShrink: 0,
            boxShadow: isDisabled ? 'none' : '0 2px 8px rgba(155, 81, 224, 0.25)',
          }}
          onMouseEnter={e => {
            if (!isDisabled) e.currentTarget.style.transform = 'scale(1.05)';
          }}
          onMouseLeave={e => {
            if (!isDisabled) e.currentTarget.style.transform = 'none';
          }}
        >
          <Send size={13} color={isDisabled ? 'var(--text-muted)' : 'white'} />
        </button>
      )}
    </form>
  );
}
