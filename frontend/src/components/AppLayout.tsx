import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { GlossaryDrawer } from './GlossaryDrawer';
import { CommandPalette } from './CommandPalette';
import { GuidedTour } from './GuidedTour';
import { NarrationBar } from './NarrationBar';
import { useWebSocket } from '../hooks/useWebSocket';

export const AppLayout: React.FC = () => {
  const [glossaryOpen, setGlossaryOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);

  // Initialize global WebSocket listener
  useWebSocket('all');

  return (
    <div className="min-h-screen bg-ink text-text-primary flex flex-col font-sans selection:bg-amber/20 selection:text-amber">
      {/* Top Navbar */}
      <Navbar 
        onOpenCommand={() => setCommandOpen(true)}
        onOpenGlossary={() => setGlossaryOpen(true)}
      />

      {/* Main Container */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar Rail */}
        <Sidebar />

        {/* Content Body */}
        <main className="flex-1 overflow-y-auto flex flex-col relative forensic-noise">
          <div className="p-4 max-w-7xl w-full mx-auto flex-1 flex flex-col gap-4">
            <NarrationBar />
            <Outlet />
          </div>
        </main>
      </div>

      {/* Overlays */}
      <GlossaryDrawer isOpen={glossaryOpen} onClose={() => setGlossaryOpen(false)} />
      <CommandPalette isOpen={commandOpen} onClose={() => setCommandOpen(false)} />
      <GuidedTour />
      <Toaster 
        position="top-right" 
        toastOptions={{
          style: {
            background: '#0D1424',
            color: '#E6ECFF',
            border: '1px solid #1F2B47',
            fontFamily: 'Space Grotesk, sans-serif',
          }
        }}
      />
    </div>
  );
};
