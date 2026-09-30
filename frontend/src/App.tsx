import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/AppLayout';
import { Dashboard } from './pages/Dashboard';
import { Inbox } from './pages/Inbox';
import { CaseWorkspace } from './pages/CaseWorkspace';
import { CrossChain } from './pages/CrossChain';
import { WalletProfile } from './pages/WalletProfile';
import { CaseLinking } from './pages/CaseLinking';
import { Watchlist } from './pages/Watchlist';
import { Vasps } from './pages/Vasps';
import { Reports } from './pages/Reports';
import { Verify } from './pages/Verify';
import { Analytics } from './pages/Analytics';
import { Integrations } from './pages/Integrations';
import { Admin } from './pages/Admin';
import { About } from './pages/About';
import { Login } from './pages/Login';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="inbox" element={<Inbox />} />
          <Route path="cases/:id" element={<CaseWorkspace />} />
          <Route path="cross-chain" element={<CrossChain />} />
          <Route path="wallet/:chain/:address" element={<WalletProfile />} />
          <Route path="linking" element={<CaseLinking />} />
          <Route path="watchlist" element={<Watchlist />} />
          <Route path="vasps" element={<Vasps />} />
          <Route path="reports" element={<Reports />} />
          <Route path="verify" element={<Verify />} />
          <Route path="verify/:hash" element={<Verify />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="integrations" element={<Integrations />} />
          <Route path="admin" element={<Admin />} />
          <Route path="about" element={<About />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
