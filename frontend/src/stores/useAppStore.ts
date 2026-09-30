import { create } from 'zustand';

interface User {
  id: number;
  email: string;
  name: string;
  role: 'Investigator' | 'Supervisor' | 'Admin';
}

interface AppState {
  user: User | null;
  mode: 'DEMO' | 'LIVE';
  wsConnected: boolean;
  unreadAlertsCount: number;
  explainMode: boolean;
  presentationMode: boolean;
  tourActive: boolean;
  currentTourStep: number;
  activeNarration: string | null;

  setUser: (user: User | null) => void;
  setMode: (mode: 'DEMO' | 'LIVE') => void;
  setWsConnected: (connected: boolean) => void;
  incrementUnreadAlerts: () => void;
  clearUnreadAlerts: () => void;
  toggleExplainMode: () => void;
  togglePresentationMode: () => void;
  startTour: () => void;
  endTour: () => void;
  setTourStep: (step: number) => void;
  setNarration: (text: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: {
    id: 1,
    email: 'investigator@demo',
    name: 'Vikram Rathore (IO Cyber Crime)',
    role: 'Investigator'
  },
  mode: 'DEMO',
  wsConnected: false,
  unreadAlertsCount: 3,
  explainMode: false,
  presentationMode: false,
  tourActive: false,
  currentTourStep: 0,
  activeNarration: null,

  setUser: (user) => set({ user }),
  setMode: (mode) => set({ mode }),
  setWsConnected: (wsConnected) => set({ wsConnected }),
  incrementUnreadAlerts: () => set((s) => ({ unreadAlertsCount: s.unreadAlertsCount + 1 })),
  clearUnreadAlerts: () => set({ unreadAlertsCount: 0 }),
  toggleExplainMode: () => set((s) => ({ explainMode: !s.explainMode })),
  togglePresentationMode: () => set((s) => ({ presentationMode: !s.presentationMode })),
  startTour: () => set({ tourActive: true, currentTourStep: 0 }),
  endTour: () => set({ tourActive: false, currentTourStep: 0 }),
  setTourStep: (currentTourStep) => set({ currentTourStep }),
  setNarration: (activeNarration) => set({ activeNarration })
}));
