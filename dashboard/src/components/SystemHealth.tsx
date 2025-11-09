import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, LineChart, Line, ResponsiveContainer } from 'recharts';
import { Activity, AlertTriangle, CheckCircle, Server } from 'lucide-react';
import { useDashboardStore } from '../store/store';
import { getApiClient } from '../api/client';

interface ServiceStatus {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  responseTime: number;
  uptime: number;
}

interface MetricDataPoint {
  timestamp: string;
  requests: number;
  errors: number;
  latency: number;
  memory: number;
}

export const SystemHealth: React.FC<{ userId: string }> = ({ userId }) => {
  const { setLoading, setError } = useDashboardStore();
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [metrics, setMetrics] = useState<MetricDataPoint[]>([]);
  const [loading, setLocalLoading] = useState(false);

  useEffect(() => {
    const fetchHealthData = async () => {
      setLocalLoading(true);
      setLoading('health', true);
      try {
        const client = getApiClient();

        // Fetch health status
        const healthData = await client.getHealth();
        const mockServices: ServiceStatus[] = [
          {
            name: 'API Server',
            status: healthData.status === 'healthy' ? 'healthy' : 'degraded',
            responseTime: 45,
            uptime: 99.9,
          },
          {
            name: 'Database',
            status: 'healthy',
            responseTime: 12,
            uptime: 99.95,
          },
          {
            name: 'Redis Cache',
            status: 'healthy',
            responseTime: 5,
            uptime: 99.8,
          },
          {
            name: 'Model Service',
            status: 'healthy',
            responseTime: 250,
            uptime: 99.5,
          },
          {
            name: 'Background Jobs',
            status: 'healthy',
            responseTime: 100,
            uptime: 99.7,
          },
        ];
        setServices(mockServices);

        // Generate mock metrics
        const mockMetrics: MetricDataPoint[] = Array.from({ length: 24 }, (_, i) => ({
          timestamp: `${i}:00`,
          requests: Math.floor(Math.random() * 1000 + 500),
          errors: Math.floor(Math.random() * 50),
          latency: Math.floor(Math.random() * 100 + 30),
          memory: Math.floor(Math.random() * 60 + 40),
        }));
        setMetrics(mockMetrics);

        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch health data');
      } finally {
        setLocalLoading(false);
        setLoading('health', false);
      }
    };

    fetchHealthData();
    const interval = setInterval(fetchHealthData, 60000); // Refresh every 60s
    return () => clearInterval(interval);
  }, [userId, setLoading, setError]);

  const healthyServices = services.filter(s => s.status === 'healthy').length;
  const totalServices = services.length;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'degraded':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'unhealthy':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="text-green-600" size={24} />;
      case 'degraded':
        return <AlertTriangle className="text-yellow-600" size={24} />;
      case 'unhealthy':
        return <AlertTriangle className="text-red-600" size={24} />;
      default:
        return <Activity className="text-gray-600" size={24} />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading system health...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Health Summary */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Server className="text-primary-600" />
            System Health & Monitoring
          </h2>
          <div className="text-right">
            <p className="text-3xl font-bold text-green-600">{healthyServices}/{totalServices}</p>
            <p className="text-sm text-gray-600">Services Healthy</p>
          </div>
        </div>

        {/* Services Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {services.map((service, idx) => (
            <div key={idx} className={`border-l-4 border-gray-300 rounded-lg p-4 ${getStatusColor(service.status)}`}>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-gray-800">{service.name}</h3>
                  <p className="text-xs text-gray-600 mt-1 capitalize">{service.status}</p>
                </div>
                {getStatusIcon(service.status)}
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Response Time:</span>
                  <span className="font-medium text-gray-800">{service.responseTime}ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Uptime:</span>
                  <span className="font-medium text-gray-800">{service.uptime}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Metrics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Requests & Errors */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Requests & Errors (Last 24h)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="requests" fill="#0066cc" name="Requests" />
              <Bar dataKey="errors" fill="#ef4444" name="Errors" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Latency & Memory */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Latency & Memory Usage (Last 24h)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="latency" stroke="#f59e0b" name="Latency (ms)" />
              <Line type="monotone" dataKey="memory" stroke="#8b5cf6" name="Memory (MB)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6">
          <p className="text-gray-600 text-sm font-medium mb-2">Avg Response Time</p>
          <p className="text-3xl font-bold text-blue-600">
            {Math.round(services.reduce((sum, s) => sum + s.responseTime, 0) / services.length)}ms
          </p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6">
          <p className="text-gray-600 text-sm font-medium mb-2">Avg Uptime</p>
          <p className="text-3xl font-bold text-green-600">
            {(services.reduce((sum, s) => sum + s.uptime, 0) / services.length).toFixed(2)}%
          </p>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-6">
          <p className="text-gray-600 text-sm font-medium mb-2">Total Requests</p>
          <p className="text-3xl font-bold text-purple-600">
            {metrics.reduce((sum, m) => sum + m.requests, 0).toLocaleString()}
          </p>
        </div>
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-6">
          <p className="text-gray-600 text-sm font-medium mb-2">Error Rate</p>
          <p className="text-3xl font-bold text-orange-600">
            {(
              (metrics.reduce((sum, m) => sum + m.errors, 0) /
                metrics.reduce((sum, m) => sum + m.requests, 0)) *
              100
            ).toFixed(2)}%
          </p>
        </div>
      </div>

      {/* System Information */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">System Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-700 mb-3">Application</h4>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-600">Version</dt>
                <dd className="font-medium text-gray-800">1.0.0</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">Environment</dt>
                <dd className="font-medium text-gray-800">Production</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">Uptime</dt>
                <dd className="font-medium text-gray-800">45 days 12h</dd>
              </div>
            </dl>
          </div>
          <div>
            <h4 className="font-medium text-gray-700 mb-3">Infrastructure</h4>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-600">Deployment</dt>
                <dd className="font-medium text-gray-800">Kubernetes</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">Replicas</dt>
                <dd className="font-medium text-gray-800">3</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">Region</dt>
                <dd className="font-medium text-gray-800">us-east-1</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};
