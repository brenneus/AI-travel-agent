"use client";

import { useState, useEffect, useRef } from 'react';
import { useChatContext } from './contexts/ChatContext';
import Image from 'next/image';


export default function Home() {
  const { activeChat, activeChatMessages, sendMessage } = useChatContext();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeChatMessages]);

  const handleSendMessage = async () => {
    if (input.trim() === '' || !activeChat) return;
    sendMessage(input);
    setInput('');
  };

  if (!activeChat) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center">
        <Image src="/window.svg" alt="AI Travel Agent" width={80} height={80} />
        <h1 className="text-2xl font-semibold mt-4">AI Travel Agent</h1>
        <p className="text-slate-400 mt-2">
          Start a new conversation to plan your next trip.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          {activeChatMessages.map((msg, index) => (
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
                    : 'bg-slate-700 text-white'
                } ${msg.type === 'tool' ? 'text-gray-400 italic' : ''}`}
              >
                {msg.content}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="bg-slate-900 border-t border-slate-700 p-4">
        <div className="flex items-center">
          <input
            type="text"
            className="flex-1 bg-slate-700 border-slate-600 rounded-full px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
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
      </div>
    </div>
  );
}

