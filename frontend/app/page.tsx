"use client";

import { useState, useEffect, useRef } from 'react';
import Image from 'next/image';

type Message = {
  type: 'user' | 'agent' | 'tool';
  content: string;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (input.trim() === '') return;

    const userMessage: Message = { type: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input }),
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
              setMessages((prev) => [...prev, { type: 'agent', content: data.content }]);
            } else if (data.type === 'tool') {
                setMessages((prev) => [...prev, { type: 'tool', content: data.content }]);
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <header className="bg-white shadow-md p-4 flex items-center">
        <Image src="/globe.svg" alt="Logo" width={40} height={40} />
        <h1 className="text-xl font-semibold ml-2">AI Travel Agent</h1>
      </header>

      <main className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${
                msg.type === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-lg px-4 py-2 rounded-lg ${
                  msg.type === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-white'
                } ${msg.type === 'tool' ? 'text-gray-500 italic' : ''}`}
              >
                {msg.content}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </main>

      <footer className="bg-white border-t p-4">
        <div className="flex items-center">
          <input
            type="text"
            className="flex-1 border rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Ask about your travel plans..."
          />
          <button
            onClick={handleSendMessage}
            className="ml-2 bg-blue-500 text-white rounded-full px-4 py-2 hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Send
          </button>
        </div>
      </footer>
    </div>
  );
}
