import { create } from 'zustand';

export interface User {
  id: string;
  email: string;
  name: string;
}

export interface ARIMetrics {
  overall_score: number;
  dimensions: {
    decision_quality: number;
    skill_development: number;
    ai_reliance: number;
    bottleneck_resolution: number;
    user_confidence: number;
    engagement: number;
    autonomy_perception: number;
  };
  timestamp: string;
}

export interface Goal {
  id: string;
  title: string;
  description: string;
  value: number;
  status: 'active' | 'completed' | 'paused';
  progress: number;
  created_at: string;
  updated_at: string;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: Record<string, boolean>;
  timestamp: string;
}

interface DashboardStore {
  // Auth
  user: User | null;
  token: string | null;
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  logout: () => void;

  // Data
  ariMetrics: ARIMetrics | null;
  goals: Goal[];
  systemHealth: SystemHealth | null;
  loading: Record<string, boolean>;
  error: string | null;

  // Actions
  setARIMetrics: (metrics: ARIMetrics) => void;
  setGoals: (goals: Goal[]) => void;
  setSystemHealth: (health: SystemHealth) => void;
  setLoading: (key: string, loading: boolean) => void;
  setError: (error: string | null) => void;
  addGoal: (goal: Goal) => void;
  updateGoal: (goal: Goal) => void;
  removeGoal: (goalId: string) => void;
}

export const useDashboardStore = create<DashboardStore>((set) => ({
  // Initial state
  user: null,
  token: localStorage.getItem('auth_token') || null,
  ariMetrics: null,
  goals: [],
  systemHealth: null,
  loading: {},
  error: null,

  // Auth actions
  setUser: (user) => set({ user }),
  setToken: (token) => {
    localStorage.setItem('auth_token', token);
    set({ token });
  },
  logout: () => {
    localStorage.removeItem('auth_token');
    set({ user: null, token: null });
  },

  // Data actions
  setARIMetrics: (metrics) => set({ ariMetrics: metrics }),
  setGoals: (goals) => set({ goals }),
  setSystemHealth: (health) => set({ systemHealth: health }),
  setLoading: (key, loading) =>
    set((state) => ({
      loading: { ...state.loading, [key]: loading },
    })),
  setError: (error) => set({ error }),
  addGoal: (goal) =>
    set((state) => ({
      goals: [...state.goals, goal],
    })),
  updateGoal: (updatedGoal) =>
    set((state) => ({
      goals: state.goals.map((goal) =>
        goal.id === updatedGoal.id ? updatedGoal : goal
      ),
    })),
  removeGoal: (goalId) =>
    set((state) => ({
      goals: state.goals.filter((goal) => goal.id !== goalId),
    })),
}));
