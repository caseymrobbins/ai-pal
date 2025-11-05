import { useEffect, useState } from 'react';
import './index.css';
import { Layout } from './components/Layout';
import { ARIMetrics } from './components/ARIMetrics';
import { FFEGoals } from './components/FFEGoals';
import { SystemHealth } from './components/SystemHealth';
import { AuditLogs } from './components/AuditLogs';
import { useDashboardStore } from './store/store';
import { initializeApiClient, getApiClient } from './api/client';

type ViewType = 'overview' | 'ari' | 'goals' | 'health' | 'personality' | 'teaching' | 'audit';

function App() {
  const [currentView, setCurrentView] = useState<ViewType>('overview');
  const [userId, setUserId] = useState<string>('');
  const [authenticated, setAuthenticated] = useState(false);
  const { setUser, setToken } = useDashboardStore();

  useEffect(() => {
    // Initialize API client
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
    const storedToken = localStorage.getItem('auth_token');

    if (storedToken) {
      setToken(storedToken);
      initializeApiClient({ baseURL, token: storedToken });
      setAuthenticated(true);
      // Use a placeholder userId - would typically come from JWT decode
      setUserId('user');
    }
  }, []);

  // Handle login with backend
  const handleLogin = async (email: string) => {
    try {
      const client = getApiClient();

      // In production, this would be a proper login endpoint that validates credentials
      // For now, we'll use a mock token but connect to real API
      // TODO: Implement proper authentication endpoint on backend

      const mockUser = {
        id: 'user-' + email.replace('@', '-'),
        email,
        name: email.split('@')[0],
      };

      // Generate a JWT-like token (in production, this comes from backend)
      const mockToken = btoa(JSON.stringify({
        user_id: mockUser.id,
        email: email,
        exp: Date.now() + (24 * 60 * 60 * 1000)
      }));

      setUser(mockUser);
      setToken(mockToken);
      setUserId(mockUser.id);
      setAuthenticated(true);

      // Try to verify token works by making a test API call
      try {
        await client.getHealth();
        console.log('✓ Connected to AI-Pal backend API');
      } catch (err) {
        console.warn('⚠ Backend API not available. Using mock data.', err);
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Login failed. Please try again.');
    }
  };

  // Render login screen
  if (!authenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-primary-50 to-primary-100">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-lg shadow-xl p-8">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-primary-600 mb-2">AI-Pal</h1>
              <p className="text-gray-600">Agency Retention Dashboard</p>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                const email = formData.get('email') as string;
                handleLogin(email);
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  name="email"
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="you@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  name="password"
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="••••••••"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-lg transition"
              >
                Sign In
              </button>
            </form>

            <p className="text-center text-sm text-gray-600 mt-4">
              Demo credentials: any email/password
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Render dashboard
  return (
    <Layout>
      <div className="space-y-6">
        {/* View Tabs */}
        <div className="flex gap-2 border-b border-gray-200 overflow-x-auto">
          {[
            { id: 'overview', label: '📊 Overview' },
            { id: 'ari', label: '📈 Agency Metrics' },
            { id: 'goals', label: '🎯 FFE Goals' },
            { id: 'health', label: '🏥 System Health' },
            { id: 'personality', label: '💡 Personality' },
            { id: 'teaching', label: '📚 Teaching' },
            { id: 'audit', label: '📋 Audit Logs' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setCurrentView(tab.id as ViewType)}
              className={`px-4 py-3 font-medium transition whitespace-nowrap ${
                currentView === tab.id
                  ? 'border-b-2 border-primary-600 text-primary-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        {currentView === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-gray-600 text-sm font-medium mb-2">System Status</p>
              <p className="text-3xl font-bold text-green-600">Healthy</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-gray-600 text-sm font-medium mb-2">Active Goals</p>
              <p className="text-3xl font-bold text-blue-600">5</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-gray-600 text-sm font-medium mb-2">Overall Agency</p>
              <p className="text-3xl font-bold text-primary-600">78%</p>
            </div>
          </div>
        )}

        {currentView === 'ari' && userId && <ARIMetrics userId={userId} />}

        {currentView === 'goals' && userId && <FFEGoals userId={userId} />}

        {currentView === 'health' && userId && <SystemHealth userId={userId} />}

        {currentView === 'personality' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold mb-4">💡 Personality Profile</h2>
            <div className="space-y-4">
              <p className="text-gray-600">
                Discover your unique strengths through interactive personality profiling.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
                  <h3 className="font-semibold text-purple-900 mb-3">Your Strengths</h3>
                  <ul className="space-y-2 text-sm text-purple-800">
                    <li>✓ Strategic Thinking</li>
                    <li>✓ Problem Solving</li>
                    <li>✓ Communication</li>
                  </ul>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                  <h3 className="font-semibold text-blue-900 mb-3">Development Areas</h3>
                  <ul className="space-y-2 text-sm text-blue-800">
                    <li>○ Time Management</li>
                    <li>○ Attention to Detail</li>
                    <li>○ Delegation</li>
                  </ul>
                </div>
              </div>
              <button className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-2 rounded-lg transition">
                Start Discovery Session
              </button>
            </div>
          </div>
        )}

        {currentView === 'teaching' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold mb-4">📚 Learn-by-Teaching</h2>
            <div className="space-y-4">
              <p className="text-gray-600">
                Deepen your understanding by explaining concepts to an AI student.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                  <h3 className="font-semibold text-green-900 mb-2">Available Topics</h3>
                  <p className="text-sm text-green-800">15+ subjects available</p>
                </div>
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6">
                  <h3 className="font-semibold text-indigo-900 mb-2">Learning Time</h3>
                  <p className="text-sm text-indigo-800">5-15 minutes per session</p>
                </div>
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
                  <h3 className="font-semibold text-orange-900 mb-2">Skill Growth</h3>
                  <p className="text-sm text-orange-800">Measurable progress tracking</p>
                </div>
              </div>
              <button className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-2 rounded-lg transition">
                Start Teaching Session
              </button>
            </div>
          </div>
        )}

        {currentView === 'audit' && userId && <AuditLogs userId={userId} />}
      </div>
    </Layout>
  );
}

export default App;
