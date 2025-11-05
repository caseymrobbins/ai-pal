import React, { useState } from 'react';
import { Menu, X, LogOut, Settings } from 'lucide-react';
import { useDashboardStore } from '../store/store';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { user, logout } = useDashboardStore();

  const menuItems = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'ari', label: 'Agency Metrics', icon: '📈' },
    { id: 'goals', label: 'FFE Goals', icon: '🎯' },
    { id: 'health', label: 'System Health', icon: '🏥' },
    { id: 'personality', label: 'Personality', icon: '💡' },
    { id: 'teaching', label: 'Learn-by-Teaching', icon: '📚' },
    { id: 'audit', label: 'Audit Logs', icon: '📋' },
  ];

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? 'w-64' : 'w-20'
        } bg-white shadow-lg transition-all duration-300 flex flex-col`}
      >
        {/* Logo */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            {sidebarOpen && (
              <h1 className="text-xl font-bold text-primary-600">AI-Pal</h1>
            )}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-100 rounded-lg transition"
              aria-label="Toggle sidebar"
            >
              {sidebarOpen ? (
                <X size={20} />
              ) : (
                <Menu size={20} />
              )}
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-4 space-y-2 overflow-y-auto">
          {menuItems.map((item) => (
            <button
              key={item.id}
              className="w-full flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-100 transition text-gray-700 hover:text-primary-600"
              title={item.label}
            >
              <span className="text-xl flex-shrink-0">{item.icon}</span>
              {sidebarOpen && <span className="text-sm font-medium">{item.label}</span>}
            </button>
          ))}
        </nav>

        {/* Footer */}
        <div className="border-t border-gray-200 p-2 space-y-2">
          <button
            className="w-full flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-100 transition text-gray-700"
            title="Settings"
          >
            <Settings size={20} className="flex-shrink-0" />
            {sidebarOpen && <span className="text-sm font-medium">Settings</span>}
          </button>
          <button
            onClick={() => logout()}
            className="w-full flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-red-50 transition text-red-600"
            title="Logout"
          >
            <LogOut size={20} className="flex-shrink-0" />
            {sidebarOpen && <span className="text-sm font-medium">Logout</span>}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header */}
        <div className="bg-white shadow h-16 border-b border-gray-200 flex items-center justify-between px-8">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Dashboard</h2>
          </div>
          <div className="flex items-center gap-4">
            {user && (
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                  <span className="text-primary-600 font-bold">
                    {user.name?.charAt(0).toUpperCase() || '?'}
                  </span>
                </div>
                <div className="hidden sm:block">
                  <p className="text-sm font-medium text-gray-800">{user.name}</p>
                  <p className="text-xs text-gray-500">{user.email}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto p-8">
          {children}
        </div>
      </div>
    </div>
  );
};
