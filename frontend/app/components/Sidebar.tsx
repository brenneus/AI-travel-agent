"use client";

import { useState } from "react";
import { Plus, MessageSquare, ChevronLeft, ChevronRight } from "lucide-react";
import { useChatContext } from "../contexts/ChatContext";

const Sidebar = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { chats, createNewChat, setActiveChatId, activeChat } = useChatContext();

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div
      className={`bg-slate-800 text-white flex flex-col transition-width duration-300 ${
        isCollapsed ? "w-20" : "w-64"
      }`}
    >
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        {!isCollapsed && (
          <h2 className="text-lg font-semibold">Chat History</h2>
        )}
        <button onClick={toggleSidebar} className="p-2 hover:bg-slate-700 rounded-md">
          {isCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        <div className="p-4">
          <button
            onClick={createNewChat}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-md flex items-center justify-center"
          >
            <Plus size={20} className={!isCollapsed ? "mr-2" : ""} />
            {!isCollapsed && "New Chat"}
          </button>
        </div>
        <nav className="mt-4">
          <ul>
            {chats.map((chat) => (
              <li
                key={chat.id}
                className={`flex items-center p-4 hover:bg-slate-700 cursor-pointer ${
                  activeChat?.id === chat.id ? "bg-slate-700" : ""
                }`}
                onClick={() => setActiveChatId(chat.id)}
              >
                <MessageSquare size={20} className={!isCollapsed ? "mr-3" : ""} />
                {!isCollapsed && (
                  <span className="truncate">
                    {chat.title || "New Chat"}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </div>
  );
};

export default Sidebar;
