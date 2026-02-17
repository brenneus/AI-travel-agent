import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Travel Agent",
  description: "Your personal AI travel assistant for seamless flight booking and itinerary planning.",
};

import { ChatProvider } from "./contexts/ChatContext";
import Sidebar from "./components/Sidebar";
import Image from "next/image";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ChatProvider>
          <div className="flex flex-col h-screen">
            <header className="bg-slate-800 shadow-md p-4 flex items-center">
              <Image src="/globe.svg" alt="Logo" width={40} height={40} />
              <h1 className="text-xl font-semibold ml-2 text-white">
                AI Travel Agent
              </h1>
            </header>
            <div className="flex flex-1 overflow-hidden">
              <Sidebar />
              <main className="flex-1 bg-slate-900 text-white overflow-y-auto">
                {children}
              </main>
            </div>
          </div>
        </ChatProvider>
      </body>
    </html>
  );
}
