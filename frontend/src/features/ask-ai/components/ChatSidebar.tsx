import { useState } from 'react';
import { MessageSquare, Plus, Trash2, Search } from 'lucide-react';
import { useAIStore } from '../stores/aiStore';
import type { ConversationResponse } from '../api/aiApi';

export default function ChatSidebar() {
  const {
    conversations,
    activeConversation,
    setActiveConversation,
    deleteConversation,
    startNewConversation,
    selectedContext,
    isStreaming
  } = useAIStore();
  const [searchTerm, setSearchTerm] = useState('');

  const handleNewChat = () => {
    if (!selectedContext || isStreaming) return;
    startNewConversation({
      dataSourceId: selectedContext.dataSourceId,
      database: selectedContext.database,
      schema: selectedContext.schema,
    });
  };

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this conversation?')) {
      deleteConversation(id);
    }
  };

  // Fuzzy filter search results
  const filteredConversations = conversations.filter(c => 
    c.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.database_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Group conversations by date
  const groupConversations = (items: ConversationResponse[]) => {
    const today: ConversationResponse[] = [];
    const yesterday: ConversationResponse[] = [];
    const older: ConversationResponse[] = [];

    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const yesterdayStart = todayStart - 24 * 60 * 60 * 1000;

    items.forEach(c => {
      const updateTime = new Date(c.updated_at).getTime();
      if (updateTime >= todayStart) {
        today.push(c);
      } else if (updateTime >= yesterdayStart) {
        yesterday.push(c);
      } else {
        older.push(c);
      }
    });

    return { today, yesterday, older };
  };

  const { today, yesterday, older } = groupConversations(filteredConversations);

  const renderSection = (title: string, list: ConversationResponse[]) => {
    if (list.length === 0) return null;
    return (
      <div style={{ marginBottom: '16px' }}>
        <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', padding: '0 8px 6px', letterSpacing: '0.05em' }}>
          {title}
        </div>
        {list.map(renderConvItem)}
      </div>
    );
  };

  const renderConvItem = (c: ConversationResponse) => {
    const isActive = activeConversation?.id === c.id;
    return (
      <div
        key={c.id}
        onClick={() => !isStreaming && setActiveConversation(c)}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 10px',
          borderRadius: '8px',
          cursor: isStreaming ? 'not-allowed' : 'pointer',
          marginBottom: '2px',
          background: isActive ? 'var(--bg-elevated)' : 'transparent',
          transition: 'all var(--transition-fast)',
        }}
        className="group hover:bg-[var(--bg-elevated)]"
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden', flex: 1 }}>
          <MessageSquare size={16} style={{ color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)', flexShrink: 0 }} />
          <div style={{ overflow: 'hidden' }}>
            <div
              style={{
                fontSize: '0.8rem',
                fontWeight: isActive ? 600 : 500,
                color: 'var(--text-primary)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {c.title}
            </div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {c.data_source_name || c.provider} • {c.database_name}
            </div>
          </div>
        </div>

        <button
          onClick={(e) => handleDelete(e, c.id)}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            padding: '2px',
            transition: 'opacity var(--transition-fast), color var(--transition-fast)',
          }}
          className="opacity-0 group-hover:opacity-100 hover:text-[var(--status-error)]"
          title="Delete Conversation"
        >
          <Trash2 size={13} />
        </button>
      </div>
    );
  };

  return (
    <aside
      style={{
        width: '260px',
        borderRight: '1px solid var(--border-default)',
        background: 'var(--bg-surface)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        flexShrink: 0,
      }}
    >
      {/* Action Header */}
      <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <button
          onClick={handleNewChat}
          disabled={!selectedContext || isStreaming}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: '9999px',
            border: '1px solid var(--border-default)',
            background: '#000000',
            color: '#ffffff',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: (!selectedContext || isStreaming) ? 'not-allowed' : 'pointer',
            opacity: (!selectedContext || isStreaming) ? 0.6 : 1,
            transition: 'background var(--transition-fast)',
          }}
          onMouseEnter={e => {
            if (selectedContext && !isStreaming) e.currentTarget.style.background = '#222';
          }}
          onMouseLeave={e => {
            if (selectedContext && !isStreaming) e.currentTarget.style.background = '#000';
          }}
        >
          <Plus size={16} />
          <span>New Chat</span>
        </button>

        {/* Search Input bar */}
        <div style={{ position: 'relative' }}>
          <Search size={14} style={{ position: 'absolute', left: 10, top: 9, color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '6px 12px 6px 30px',
              borderRadius: '9999px',
              border: '1px solid var(--border-default)',
              fontSize: '0.78rem',
              outline: 'none',
              background: 'var(--bg-elevated)',
            }}
          />
        </div>
      </div>

      {/* History scroll list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 12px 16px' }}>
        {filteredConversations.length === 0 ? (
          <div style={{ padding: '24px 8px', textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            No conversations found.
          </div>
        ) : (
          <>
            {renderSection('Today', today)}
            {renderSection('Yesterday', yesterday)}
            {renderSection('Recent Chats', older)}
          </>
        )}
      </div>
    </aside>
  );
}
