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
    addMessage({ type: 'agent', content: 'Thinking...' });

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
            const messageType = data.type === 'tool' ? 'tool' : 'agent';
            const content = data.content;

            setChats((prev) =>
              prev.map((chat) => {
                if (chat.id === activeChatId) {
                  const newMessages = [...chat.messages];
                  const lastMessage = newMessages[newMessages.length - 1];
                  if (lastMessage && (lastMessage.content === 'Thinking...' || lastMessage.type === 'tool')) {
                    newMessages[newMessages.length - 1] = { type: messageType, content };
                  } else {
                    newMessages.push({ type: messageType, content });
                  }
                  return { ...chat, messages: newMessages };
                }
                return chat;
              })
            );
          }
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const deleteChat = (chatId: string) => {
    setChats((prev) => {
      const newChats = prev.filter((chat) => chat.id !== chatId);
      if (activeChatId === chatId) {
        const newActiveChatId = newChats.length > 0 ? newChats[0].id : null;
        setActiveChatId(newActiveChatId);
        if (newActiveChatId === null) {
          localStorage.removeItem("activeChatId");
        }
      }
      return newChats;
    });
  };

  const editChat = (chatId: string, newTitle: string) => {
    setChats((prev) =>
      prev.map((chat) =>
        chat.id === chatId ? { ...chat, title: newTitle } : chat
      )
    );
  };

  return {
    chats,
    activeChat,
    activeChatMessages: activeChat?.messages || [],
    createNewChat,
    setActiveChatId,
    sendMessage,
    deleteChat,
    editChat,
  };
};
