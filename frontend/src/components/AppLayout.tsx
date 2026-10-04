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
    <div className="min-h-screen bg-surface-container-low font-sans text-on-surface antialiased flex flex-col">
      {/* Sidebar Rail (fixed w-64) */}
      <Sidebar />

      {/* Main Viewport Container offset by sidebar width */}
      <div className="pl-64 flex flex-col min-h-screen">
        {/* Fixed Top Header (left-64) */}
        <Navbar 
          onOpenCommand={() => setCommandOpen(true)}
          onOpenGlossary={() => setGlossaryOpen(true)}
        />

        {/* Content Body */}
        <main className="w-full pt-14 flex-1 bg-surface-container-low px-6 py-6 overflow-y-auto">
          <div className="max-w-[1520px] w-full mx-auto flex flex-col gap-6">
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
            background: '#ffffff',
            color: '#0a1d2e',
            border: '1px solid #D9E1EC',
            boxShadow: '0 4px 16px rgba(38, 74, 115, 0.08)',
            fontFamily: 'IBM Plex Sans, sans-serif',
            fontSize: '13px',
            borderRadius: '10px'
          }
        }}
      />
    </div>
  );
};
