import axios from 'axios';
import type { AxiosInstance } from 'axios';

export interface ApiConfig {
  baseURL?: string;
  token?: string;
}

export interface ApiError {
  message: string;
  code?: string;
  status: number;
}

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;
  private baseURL: string;

  constructor(config: ApiConfig = {}) {
    this.baseURL = config.baseURL || import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (config.token) {
      this.setToken(config.token);
    }

    // Add request interceptor to inject token
    this.client.interceptors.request.use((config) => {
      if (this.token && !config.headers.Authorization) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          this.clearToken();
          // Redirect to login only if we're in browser and not already there
          if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string) {
    this.token = token;
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    localStorage.setItem('auth_token', token);
  }

  clearToken() {
    this.token = null;
    delete this.client.defaults.headers.common['Authorization'];
    localStorage.removeItem('auth_token');
  }

  getToken(): string | null {
    return this.token;
  }

  // ============ System Endpoints ============

  async getHealth() {
    const response = await this.client.get('/health');
    return response.data;
  }

  async getMetrics() {
    const response = await this.client.get('/metrics');
    return response.data;
  }

  async getDashboardHealth() {
    const response = await this.client.get('/system/health/dashboard');
    return response.data;
  }

  async getServicesHealth() {
    const response = await this.client.get('/system/health/services');
    return response.data;
  }

  // ============ User Endpoints ============

  async getUserProfile(userId: string) {
    const response = await this.client.get(`/users/${userId}/profile`);
    return response.data;
  }

  async updateUserProfile(userId: string, data: Record<string, any>) {
    const response = await this.client.put(`/users/${userId}/profile`, data);
    return response.data;
  }

  // ============ ARI Metrics Endpoints ============

  async getARIMetrics(userId: string) {
    const response = await this.client.get(`/users/${userId}/ari`);
    return response.data;
  }

  async getARIHistory(userId: string, days: number = 30) {
    const response = await this.client.get(`/users/${userId}/ari/history`, {
      params: { days },
    });
    return response.data;
  }

  // ============ FFE Goals Endpoints ============

  async getGoals(userId: string, status?: string) {
    const response = await this.client.get(`/users/${userId}/goals`, {
      params: status ? { status } : undefined,
    });
    return response.data;
  }

  async getGoal(userId: string, goalId: string) {
    const response = await this.client.get(`/users/${userId}/goals/${goalId}`);
    return response.data;
  }

  async createGoal(userId: string, goalData: Record<string, any>) {
    const response = await this.client.post(`/users/${userId}/goals`, goalData);
    return response.data;
  }

  async updateGoal(userId: string, goalId: string, goalData: Record<string, any>) {
    const response = await this.client.put(`/users/${userId}/goals/${goalId}`, goalData);
    return response.data;
  }

  async planGoal(userId: string, goalId: string) {
    const response = await this.client.post(`/users/${userId}/goals/${goalId}/plan`, {});
    return response.data;
  }

  async completeGoal(userId: string, goalId: string) {
    const response = await this.client.post(`/users/${userId}/goals/${goalId}/complete`, {});
    return response.data;
  }

  // ============ Personality Endpoints ============

  async getPersonality(userId: string) {
    const response = await this.client.get(`/users/${userId}/personality`);
    return response.data;
  }

  async startPersonalityDiscovery(userId: string) {
    const response = await this.client.post(`/users/${userId}/personality/discover`, {});
    return response.data;
  }

  async updateStrengths(userId: string, strengths: string[]) {
    const response = await this.client.post(`/users/${userId}/personality/strengths`, {
      strengths,
    });
    return response.data;
  }

  // ============ Teaching/Protégé Endpoints ============

  async getTeachingTopics(userId: string) {
    const response = await this.client.get(`/users/${userId}/teaching/topics`);
    return response.data;
  }

  async startTeachingSession(userId: string, topicId: string) {
    const response = await this.client.post(`/users/${userId}/teaching/start`, {
      topic_id: topicId,
    });
    return response.data;
  }

  async submitTeachingResponse(userId: string, sessionId: string, response: string) {
    const apiResponse = await this.client.post(
      `/users/${userId}/teaching/${sessionId}/submit`,
      { response }
    );
    return apiResponse.data;
  }

  async evaluateTeachingSession(userId: string, sessionId: string) {
    const response = await this.client.get(`/users/${userId}/teaching/${sessionId}/evaluate`);
    return response.data;
  }

  // ============ Social Endpoints ============

  async getSocialGroups(userId: string) {
    const response = await this.client.get(`/users/${userId}/groups`);
    return response.data;
  }

  async createGroup(userId: string, groupData: Record<string, any>) {
    const response = await this.client.post(`/users/${userId}/groups`, groupData);
    return response.data;
  }

  async shareWin(userId: string, winData: Record<string, any>) {
    const response = await this.client.post(`/users/${userId}/wins/share`, winData);
    return response.data;
  }

  async getGroupFeed(groupId: string) {
    const response = await this.client.get(`/groups/${groupId}/feed`);
    return response.data;
  }

  // ============ Audit & Security Endpoints ============

  async getAuditLogs(userId: string, limit: number = 100, offset: number = 0) {
    const response = await this.client.get(`/users/${userId}/audit-logs`, {
      params: { limit, offset },
    });
    return response.data;
  }

  async getSecurityAlerts(userId: string) {
    const response = await this.client.get(`/users/${userId}/security/alerts`);
    return response.data;
  }

  // ============ Patch & Appeals Endpoints ============

  async getPatchRequests(userId: string) {
    const response = await this.client.get(`/users/${userId}/patches`);
    return response.data;
  }

  async submitPatch(userId: string, patchData: Record<string, any>) {
    const response = await this.client.post(`/users/${userId}/patches`, patchData);
    return response.data;
  }

  async approvePatch(userId: string, patchId: string) {
    const response = await this.client.post(`/users/${userId}/patches/${patchId}/approve`, {});
    return response.data;
  }

  async getAppeals(userId: string) {
    const response = await this.client.get(`/users/${userId}/appeals`);
    return response.data;
  }

  async submitAppeal(userId: string, appealData: Record<string, any>) {
    const response = await this.client.post(`/users/${userId}/appeals`, appealData);
    return response.data;
  }

  // ============ Background Tasks Endpoints ============

  async listTasks(status?: string, userId?: string, limit: number = 20) {
    const response = await this.client.get('/tasks/list', {
      params: { status, user_id: userId, limit },
    });
    return response.data;
  }

  async getTaskStatus(taskId: string) {
    const response = await this.client.get(`/tasks/status/${taskId}`);
    return response.data;
  }

  async getPendingTasks(limit: number = 10) {
    const response = await this.client.get('/tasks/pending', {
      params: { limit },
    });
    return response.data;
  }

  async getFailedTasks(limit: number = 10) {
    const response = await this.client.get('/tasks/failed', {
      params: { limit },
    });
    return response.data;
  }

  async getTasksHealth() {
    const response = await this.client.get('/tasks/health');
    return response.data;
  }

  async submitARIAggregation(userId?: string, timeWindowHours: number = 24) {
    const response = await this.client.post('/tasks/ari/aggregate-snapshots', {
      task_type: 'ari_snapshot',
      user_id: userId,
      priority: 5,
      parameters: { time_window_hours: timeWindowHours },
    });
    return response.data;
  }

  async submitFFEPlanning(goalId: string, userId: string, goalDescription: string, complexityLevel: string = 'medium') {
    const response = await this.client.post('/tasks/ffe/plan-goal', {
      task_type: 'ffe_planning',
      user_id: userId,
      priority: 7,
      parameters: { goal_id: goalId, goal_description: goalDescription, complexity_level: complexityLevel },
    });
    return response.data;
  }

  async submitEDMAnalysis(userId?: string, timeWindowDays: number = 7, minSeverity: string = 'low') {
    const response = await this.client.post('/tasks/edm/batch-analysis', {
      task_type: 'edm_analysis',
      user_id: userId,
      priority: 5,
      parameters: { time_window_days: timeWindowDays, min_severity: minSeverity },
    });
    return response.data;
  }

  async cancelTask(taskId: string) {
    const response = await this.client.delete(`/tasks/${taskId}`);
    return response.data;
  }

  async retryTask(taskId: string) {
    const response = await this.client.post(`/tasks/${taskId}/retry`);
    return response.data;
  }

  // ============ Chat Endpoint ============

  async chat(message: string, context?: Record<string, any>) {
    const response = await this.client.post('/chat', {
      message,
      context,
    });
    return response.data;
  }

  // ============ WebSocket Support ============

  getWebSocketURL(endpoint: string): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = this.baseURL.replace(/^https?:\/\//, '').replace(/\/api\/?$/, '');
    const token = this.token ? `?token=${this.token}` : '';
    return `${protocol}//${host}${endpoint}${token}`;
  }
}

// Create a singleton instance
let apiClient: ApiClient | null = null;

export function initializeApiClient(config: ApiConfig) {
  apiClient = new ApiClient(config);
  return apiClient;
}

export function getApiClient(): ApiClient {
  if (!apiClient) {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
    const token = localStorage.getItem('auth_token') || undefined;
    apiClient = new ApiClient({ baseURL, token });
  }
  return apiClient;
}

export default ApiClient;
