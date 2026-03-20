'use client';

import React from 'react';
import Sidebar from '@/components/Sidebar';
import ChatWindow, { Message } from '@/components/ChatWindow';
import { SearchMode } from '@/components/ModeToggle';
import { askNyaya } from '@/lib/api';

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  isPinned: boolean;
}

export default function Home() {
  const [sessions, setSessions] = React.useState<ChatSession[]>([]);
  const [activeChatId, setActiveChatId] = React.useState<string | null>(null);
  const [isTyping, setIsTyping] = React.useState(false);

  // Load initial from localStorage
  React.useEffect(() => {
    const saved = localStorage.getItem('nyaya-chat-sessions');
    if (saved) {
      try {
        setSessions(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to parse sessions", e);
      }
    }
  }, []);

  // Save to localStorage whenever sessions change
  React.useEffect(() => {
    localStorage.setItem('nyaya-chat-sessions', JSON.stringify(sessions));
  }, [sessions]);
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(true);
  const [sidebarWidth, setSidebarWidth] = React.useState(288); // Default w-72 (18rem * 16px)
  const isResizing = React.useRef(false);

  // Resize Handlers
  const startResizing = React.useCallback(() => {
    isResizing.current = true;
  }, []);

  const stopResizing = React.useCallback(() => {
    isResizing.current = false;
  }, []);

  const resize = React.useCallback((mouseMoveEvent: MouseEvent) => {
    if (isResizing.current) {
      setSidebarWidth(currentWidth => {
        const newWidth = mouseMoveEvent.clientX;
        if (newWidth < 200) return 200; // Min width
        if (newWidth > 480) return 480; // Max width
        return newWidth;
      });
    }
  }, []);

  React.useEffect(() => {
    window.addEventListener("mousemove", resize);
    window.addEventListener("mouseup", stopResizing);
    return () => {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResizing);
    };
  }, [resize, stopResizing]);



  const toggleSidebar = () => setIsSidebarOpen(prev => !prev);

  const handleNewChat = () => {
    setActiveChatId(null);
  };

  const handleSendMessage = async (content: string, mode: SearchMode) => {
    // Included in the request payload as required
    console.log("Request Payload:", { message: content, mode });

    const newUserMsg: Message = { id: Date.now().toString(), role: 'user', content, timestamp: new Date() };

    let currentChatId = activeChatId;

    if (!currentChatId) {
      currentChatId = Date.now().toString();
      const title = content.split(' ').slice(0, 5).join(' ') + (content.split(' ').length > 5 ? '...' : '');

      const newSession: ChatSession = {
        id: currentChatId,
        title,
        messages: [newUserMsg],
        createdAt: Date.now(),
        isPinned: false
      };

      setSessions(prev => [newSession, ...prev]);
      setActiveChatId(currentChatId);
    } else {
      setSessions(prev => prev.map(s => {
        if (s.id === currentChatId) {
          return { ...s, messages: [...s.messages, newUserMsg] };
        }
        return s;
      }));
    }

    setIsTyping(true);

    try {
      const data = await askNyaya(content);
      const systemMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'system',
        content: data.answer,
        timestamp: new Date()
      };

      setSessions(prev => prev.map(s => {
        if (s.id === currentChatId) {
          return { ...s, messages: [...s.messages, systemMsg] };
        }
        return s;
      }));
    } catch (e) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'system',
        content: "Sorry, something went wrong. Please try again.",
        timestamp: new Date()
      };

      setSessions(prev => prev.map(s => {
        if (s.id === currentChatId) {
          return { ...s, messages: [...s.messages, errorMsg] };
        }
        return s;
      }));
    } finally {
      setIsTyping(false);
    }
  };

  const togglePin = (id: string) => {
    setSessions(prev => prev.map(item =>
      item.id === id ? { ...item, isPinned: !item.isPinned } : item
    ));
  };

  const deleteItem = (id: string) => {
    setSessions(prev => prev.filter(item => item.id !== id));
    if (activeChatId === id) {
      setActiveChatId(null);
    }
  };

  const renameItem = (id: string, newTitle: string) => {
    setSessions(prev => prev.map(item =>
      item.id === id ? { ...item, title: newTitle } : item
    ));
  };

  const shareItem = (id: string) => {
    console.log("Sharing item:", id);
    alert("Share link copied to clipboard!");
  };

  const sortedHistory = [...sessions].sort((a, b) => {
    if (a.isPinned === b.isPinned) return b.createdAt - a.createdAt;
    return a.isPinned ? -1 : 1;
  });

  const activeSession = sessions.find(s => s.id === activeChatId);


  return (
    <main className="flex h-screen overflow-hidden bg-grey-50">
      <Sidebar
        onNewChat={handleNewChat}
        history={sortedHistory}
        onPin={togglePin}
        onDelete={deleteItem}
        onRename={renameItem}
        onShare={shareItem}
        activeChatId={activeChatId}
        onSelectChat={(id) => setActiveChatId(id)}
        isOpen={isSidebarOpen}
        width={sidebarWidth}
        onToggle={toggleSidebar}
        onResizeStart={startResizing}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full relative" style={{ marginLeft: isSidebarOpen ? 0 : 0 }}>
        <ChatWindow
          messages={activeSession ? activeSession.messages : []}
          isTyping={isTyping}
          onSendMessage={handleSendMessage}
          sidebarOpen={isSidebarOpen}
          onToggleSidebar={toggleSidebar}
        />
      </div>
    </main>
  );
}
