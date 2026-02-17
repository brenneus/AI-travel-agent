"use client";

import { useState, useEffect } from "react";

type Message = {
  type: "user" | "agent" | "tool";
  content: string;
};

type Chat = {
  id: string;
  title: string;
  messages: Message[];
};

export const useChat = () => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);

  useEffect(() => {
    // Load state from local storage on mount (client-side only)
    const storedChats = localStorage.getItem("chats");
    if (storedChats) {
      setChats(JSON.parse(storedChats));
    }
    const storedActiveChatId = localStorage.getItem("activeChatId");
    if (storedActiveChatId) {
      setActiveChatId(JSON.parse(storedActiveChatId));
    }
  }, []);

  useEffect(() => {
    // Save state to local storage whenever it changes (client-side only)
    localStorage.setItem("chats", JSON.stringify(chats));
    if (activeChatId) {
      localStorage.setItem("activeChatId", JSON.stringify(activeChatId));
    }
  }, [chats, activeChatId]);

  const createNewChat = () => {
    const newChat: Chat = {
      id: crypto.randomUUID(),
      title: "New Chat",
      messages: [],
    };
    setChats((prev) => [...prev, newChat]);
    setActiveChatId(newChat.id);
  };

  const activeChat = chats.find((chat) => chat.id === activeChatId);

  const addMessage = (message: Message) => {
    if (!activeChatId) return;

    setChats((prev) =>
      prev.map((chat) =>
        chat.id === activeChatId
          ? { ...chat, messages: [...chat.messages, message] }
          : chat
      )
    );
  };

  const sendMessage = async (message: string) => {
    if (!activeChatId) return;

    if (activeChat && activeChat.messages.length === 0) {
      setChats((prev) =>
        prev.map((chat) =>
          chat.id === activeChatId ? { ...chat, title: message } : chat
        )
      );
    }

    const userMessage: Message = { type: 'user', content: message };
    addMessage(userMessage);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message, thread_id: activeChatId }),
      });

      if (!response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        const chunk = decoder.decode(value, { stream: true });
        
        const events = chunk.split('\n\n').filter(Boolean);
        for (const event of events) {
          if (event.startsWith('data:')) {
            const data = JSON.parse(event.substring(5));
            if (data.type === 'message') {
              addMessage({ type: 'agent', content: data.content });
            } else if (data.type === 'tool') {
                addMessage({ type: 'tool', content: data.content });
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  return {
    chats,
    activeChat,
    activeChatMessages: activeChat?.messages || [],
    createNewChat,
    setActiveChatId,
    sendMessage,
  };
};
