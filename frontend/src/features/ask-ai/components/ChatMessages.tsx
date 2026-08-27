import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import type { MessageResponse } from '../api/aiApi';
import { useAIStore } from '../stores/aiStore';

interface ChatMessagesProps {
  messages: MessageResponse[];
}

export default function ChatMessages({ messages }: ChatMessagesProps) {
  const { isStreaming } = useAIStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  return (
    <div
      style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px 0',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div style={{ maxWidth: '840px', width: '100%', margin: '0 auto', padding: '0 24px' }}>
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} style={{ height: '1px' }} />
      </div>
    </div>
  );
}
