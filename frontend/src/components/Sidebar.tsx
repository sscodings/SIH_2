import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, Inbox, Eye, GitBranch, Network, 
  EyeOff, Building2, FileText, CheckCircle, BarChart3, 
  Webhook, Settings, Info, ChevronLeft, ChevronRight, PlayCircle,
  ShieldCheck
} from 'lucide-react';
import { useAppStore } from '../stores/useAppStore';

export const Sidebar: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const user = useAppStore((s) => s.user);

  const navItems = [
    { to: '/', label: 'Dashboard', icon: 'grid_view', LucideIcon: LayoutDashboard, tourId: 'tour-dashboard' },
    { to: '/inbox', label: 'Complaints', icon: 'inbox', LucideIcon: Inbox, badge: '37', tourId: 'tour-inbox' },
    { to: '/cases/1', label: 'Cases & Workspace', icon: 'folder_managed', LucideIcon: Eye, highlight: true, tourId: 'tour-case' },
    { to: '/cross-chain', label: 'Fund Flow Graph', icon: 'account_tree', LucideIcon: GitBranch, tourId: 'tour-crosschain' },
    { to: '/linking', label: 'Case Linking', icon: 'hub', LucideIcon: Network, tourId: 'tour-linking' },
    { to: '/watchlist', label: 'Watchlist & Alerts', icon: 'visibility', LucideIcon: EyeOff, badge: '4', tourId: 'tour-watchlist' },
    { to: '/vasps', label: 'VASP Directory', icon: 'account_balance', LucideIcon: Building2, tourId: 'tour-vasps' },
    { to: '/reports', label: 'Reports & Dossiers', icon: 'description', LucideIcon: FileText, tourId: 'tour-reports' },
    { to: '/verify', label: 'Evidence Verify', icon: 'verified_user', LucideIcon: CheckCircle, tourId: 'tour-verify' },
    { to: '/analytics', label: 'Analytics', icon: 'analytics', LucideIcon: BarChart3, tourId: 'tour-analytics' },
    { to: '/integrations', label: 'Integrations', icon: 'sync_alt', LucideIcon: Webhook, tourId: 'tour-integrations' },
    ...(user?.role === 'Admin' ? [{ to: '/admin', label: 'Admin & Labels', icon: 'admin_panel_settings', LucideIcon: Settings, tourId: 'tour-admin' }] : []),
    { to: '/about', label: 'System Overview', icon: 'info', LucideIcon: Info, tourId: 'tour-about' }
  ];

  return (
    <aside 
      className={`fixed left-0 top-0 h-full bg-tertiary text-on-tertiary z-50 flex flex-col justify-between select-none shadow-[0_1px_8px_rgba(0,0,0,0.08)] transition-all duration-200 ${
        collapsed ? 'w-18' : 'w-64'
      }`}
    >
      <div className="flex flex-col flex-1 overflow-y-auto">
        {/* Brand Header */}
        <div className="h-14 px-4 flex items-center gap-3 bg-tertiary-container/30 border-b border-tertiary-container/40">
          <img 
            alt="ChainNetra Logo" 
            className="h-8 w-auto object-contain rounded" 
            src="/chainnetra_logo.png"
            onError={(e) => {
              (e.currentTarget as HTMLImageElement).src = '/logo.svg';
            }}
          />
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-headline-sm text-[15px] font-semibold text-on-tertiary leading-none tracking-tight">ChainNetra</span>
              <span className="font-label-sm text-[10px] text-tertiary-fixed-dim uppercase tracking-wider mt-0.5">LE Forensics • CCTNS</span>
            </div>
          )}
        </div>

        {/* Section Header */}
        {!collapsed && (
          <div className="px-4 pt-3 pb-1">
            <span className="text-tertiary-fixed font-label-sm text-[10px] uppercase tracking-wider font-semibold">
              Operational Modules
            </span>
          </div>
        )}

        {/* Navigation Items */}
        <nav className="flex flex-col gap-0.5 px-2 py-1">
          {navItems.map((item) => {
            const Lucide = item.LucideIcon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                id={item.tourId}
                className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] font-medium transition-colors relative group ${
                  isActive 
                    ? 'bg-tertiary-container text-on-tertiary font-semibold before:content-[\'\'] before:absolute before:left-0 before:top-1 before:bottom-1 before:w-1 before:bg-on-tertiary before:rounded-r' 
                    : 'text-tertiary-fixed hover:bg-tertiary-container/50 hover:text-on-tertiary'
                }`}
                title={collapsed ? item.label : undefined}
              >
                <span className="material-symbols-outlined text-[18px] shrink-0">
                  {item.icon}
                </span>
                
                {!collapsed && (
                  <span className="truncate flex-1 tracking-tight">{item.label}</span>
                )}

                {!collapsed && item.badge && (
                  <span className="px-1.5 py-0.2 rounded-full bg-secondary-container/40 text-on-secondary-fixed text-[10px] font-mono font-bold">
                    {item.badge}
                  </span>
                )}

                {!collapsed && item.highlight && (
                  <span className="w-2 h-2 rounded-full bg-secondary-fixed animate-pulse" />
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer Info & Collapse Toggle */}
      <div className="p-3 bg-tertiary-container/20 border-t border-tertiary-container/30 flex flex-col gap-2">
        {!collapsed && (
          <div className="flex flex-col gap-1 text-xs">
            <div className="flex items-center gap-1.5 text-tertiary-fixed">
              <span className="material-symbols-outlined text-[16px] text-secondary-fixed">shield</span>
              <span className="font-label-sm text-[11px] font-semibold">CCTNS Certified Grid</span>
            </div>
            <div className="font-code-sm text-[10px] text-tertiary-fixed-dim">
              Node: IN-CYBER-DEL-04 • SHA-256
            </div>
          </div>
        )}

        <div className="flex items-center justify-between pt-1">
          <NavLink
            to="/cases/1"
            className="flex items-center gap-1.5 px-2 py-1 rounded bg-secondary-container/20 hover:bg-secondary-container/40 text-secondary-fixed text-[11px] font-medium transition-colors"
            title="Open Demo Case"
          >
            <PlayCircle className="w-3.5 h-3.5" />
            {!collapsed && <span>Guided Trace Demo</span>}
          </NavLink>

          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 rounded text-tertiary-fixed hover:text-on-tertiary hover:bg-tertiary-container/40 transition-colors"
            title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            type="button"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </aside>
  );
};
