import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, Inbox, Eye, GitBranch, Network, 
  EyeOff, Building2, FileText, CheckCircle, BarChart3, 
  Webhook, Settings, Info, ChevronLeft, ChevronRight, PlayCircle
} from 'lucide-react';
import { useAppStore } from '../stores/useAppStore';

export const Sidebar: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const user = useAppStore((s) => s.user);

  const navItems = [
    { to: '/', label: 'Command Center', icon: LayoutDashboard, tourId: 'tour-dashboard' },
    { to: '/inbox', label: 'Complaint Inbox', icon: Inbox, badge: '30', tourId: 'tour-inbox' },
    { to: '/cases/1', label: 'Case Workspace', icon: Eye, highlight: true, tourId: 'tour-case' },
    { to: '/cross-chain', label: 'Cross-Chain Flows', icon: GitBranch, tourId: 'tour-crosschain' },
    { to: '/linking', label: 'Case Linking', icon: Network, tourId: 'tour-linking' },
    { to: '/watchlist', label: 'Watchlist & Alerts', icon: EyeOff, tourId: 'tour-watchlist' },
    { to: '/vasps', label: 'VASP & Freeze', icon: Building2, tourId: 'tour-vasps' },
    { to: '/reports', label: 'Reports & Dossiers', icon: FileText, tourId: 'tour-reports' },
    { to: '/verify', label: 'Evidence Verify', icon: CheckCircle, tourId: 'tour-verify' },
    { to: '/analytics', label: 'Forensic Analytics', icon: BarChart3, tourId: 'tour-analytics' },
    { to: '/integrations', label: 'API & Connectors', icon: Webhook, tourId: 'tour-integrations' },
    ...(user?.role === 'Admin' ? [{ to: '/admin', label: 'Admin & Labels', icon: Settings, tourId: 'tour-admin' }] : []),
    { to: '/about', label: 'Architecture & Pitch', icon: Info, tourId: 'tour-about' }
  ];

  return (
    <aside className={`border-r border-hairline bg-panel transition-all duration-200 flex flex-col justify-between shrink-0 select-none z-20 ${
      collapsed ? 'w-16' : 'w-60'
    }`}>
      <div className="py-3 px-2 flex flex-col gap-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              id={item.tourId}
              className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all group relative ${
                isActive 
                  ? 'bg-amber/15 text-amber border border-amber/30 font-semibold shadow-sm' 
                  : 'text-text-muted hover:text-text-primary hover:bg-raised'
              }`}
              title={collapsed ? item.label : undefined}
            >
              <Icon className={`w-4 h-4 shrink-0 transition-transform group-hover:scale-110 ${item.highlight ? 'text-amber' : ''}`} />
              
              {!collapsed && (
                <span className="truncate flex-1 tracking-wide">{item.label}</span>
              )}

              {!collapsed && item.badge && (
                <span className="px-1.5 py-0.2 rounded bg-cyan/15 text-cyan border border-cyan/30 text-[10px] font-mono font-bold">
                  {item.badge}
                </span>
              )}

              {!collapsed && item.highlight && (
                <span className="w-1.5 h-1.5 rounded-full bg-amber animate-pulse" />
              )}
            </NavLink>
          );
        })}
      </div>

      {/* Guided Demo Shortcut & Collapse Trigger */}
      <div className="p-2 border-t border-hairline flex flex-col gap-2">
        <NavLink
          to="/cases/1"
          className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-amber/10 hover:bg-amber/20 border border-amber/30 text-amber text-xs font-semibold transition-all justify-center group"
          title="Load Case Zero Guided Demo"
        >
          <PlayCircle className="w-4 h-4 shrink-0 animate-spin-slow" />
          {!collapsed && <span>Case Zero Demo</span>}
        </NavLink>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center p-2 rounded hover:bg-raised text-text-muted hover:text-text-primary transition-colors text-xs"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>
    </aside>
  );
};
