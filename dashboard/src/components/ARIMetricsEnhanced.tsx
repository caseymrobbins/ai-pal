import React, { useEffect, useState } from 'react';
import { TrendingUp, AlertCircle } from 'lucide-react';
import { useDashboardStore } from '../store/store';
import { getApiClient } from '../api/client';
import { LineChart } from './LineChart';
import { HeatmapChart } from './HeatmapChart';
import { PredictionCard } from './PredictionCard';

export const ARIMetricsEnhanced: React.FC<{ userId: string }> = ({ userId }) => {
  const { setLoading, setError } = useDashboardStore();
  const [ariMetrics, setARIMetrics] = useState<any>(null);
  const [ariHistory, setARIHistory] = useState<any[]>([]);
  const [ariPrediction, setARIPrediction] = useState<any>(null);
  const [selectedDays, setSelectedDays] = useState(30);

  useEffect(() => {
    const fetchData = async () => {
      setLoading('ari', true);
      try {
        const client = getApiClient();

        // Fetch current metrics
        const metricsData = await client.getARIMetrics(userId);
        setARIMetrics(metricsData);

        // Fetch historical data
        const historyData = await client.getARIHistory(userId, selectedDays);
        setARIHistory(historyData.snapshots || historyData.history || []);

        // Fetch forecast
        const forecastData = await client.forecastARITrend(userId, 7);
        setARIPrediction(forecastData);

        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch ARI metrics');
      } finally {
        setLoading('ari', false);
      }
    };

    fetchData();
  }, [userId, selectedDays, setLoading, setError]);

  if (!ariMetrics) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading ARI metrics...</div>
      </div>
    );
  }

  const currentScore = ariMetrics.current_score || 50;
  const trend = ariMetrics.trend || 'stable';
  const status = ariMetrics.status || 'stable';

  // Prepare trend data for line chart
  const trendData = ariHistory.map((snapshot) => ({
    name: new Date(snapshot.created_at || snapshot.timestamp).toLocaleDateString(),
    score: snapshot.autonomy_retention || 50,
  }));

  // Prepare dimension data for heatmap
  const heatmapData = Array.isArray(ariMetrics.dimensions)
    ? ariMetrics.dimensions.map((dim: any) => ({
        dimension: dim.name || dim,
        current: typeof dim.value === 'number' ? dim.value / 100 : 0.5,
      }))
    : [];

  const statusColor =
    status === 'healthy'
      ? 'text-green-600'
      : status === 'warning'
        ? 'text-yellow-600'
        : 'text-red-600';

  const trendIcon = trend === 'improving' ? '📈' : trend === 'declining' ? '📉' : '➡️';

  return (
    <div className="space-y-6">
      {/* Header with Key Metrics */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">ARI Metrics</h2>
            <p className="text-gray-600 mt-1">Agency Retention Index & Autonomy Score</p>
          </div>
          {currentScore < 50 && (
            <AlertCircle className="w-8 h-8 text-red-600" />
          )}
        </div>

        {/* Main Score Card */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6">
            <p className="text-sm text-gray-600 mb-2">Current Score</p>
            <p className="text-5xl font-bold text-blue-600">{currentScore.toFixed(1)}</p>
            <p className="text-xs text-gray-600 mt-2">/100</p>
          </div>

          <div className={`bg-gradient-to-br rounded-lg p-6 ${
            status === 'healthy' ? 'from-green-50 to-green-100' :
            status === 'warning' ? 'from-yellow-50 to-yellow-100' :
            'from-red-50 to-red-100'
          }`}>
            <p className="text-sm text-gray-600 mb-2">Status</p>
            <p className={`text-2xl font-bold ${statusColor}`}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </p>
            <p className="text-xs text-gray-600 mt-2">System health indicator</p>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-6">
            <p className="text-sm text-gray-600 mb-2">Trend</p>
            <p className="text-3xl mb-2">{trendIcon}</p>
            <p className="text-sm font-semibold text-purple-700">
              {trend.charAt(0).toUpperCase() + trend.slice(1)}
            </p>
          </div>
        </div>
      </div>

      {/* Trend Chart */}
      {trendData.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">Trend</h3>
            <select
              value={selectedDays}
              onChange={(e) => setSelectedDays(parseInt(e.target.value))}
              className="px-3 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 90 days</option>
            </select>
          </div>
          <LineChart
            data={trendData}
            lines={[
              {
                dataKey: 'score',
                stroke: '#3b82f6',
                name: 'ARI Score',
                strokeWidth: 2,
              },
            ]}
            height={300}
            xAxisKey="name"
            showLegend={false}
          />
        </div>
      )}

      {/* 7-Day Forecast */}
      {ariPrediction && ariPrediction.can_forecast && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">7-Day Forecast</h3>
          <PredictionCard
            metric={{
              label: 'ARI Score Forecast',
              currentValue: currentScore,
              predictedValue: ariPrediction.predicted_score || currentScore,
              timeframe: '7 days',
              confidenceLevel: ariPrediction.confidence || 0.7,
              trend: ariPrediction.trend === 'improving' ? 'up' : ariPrediction.trend === 'declining' ? 'down' : 'stable',
              unit: '/100',
              warningThreshold: 50,
            }}
          />
        </div>
      )}

      {/* Dimensions Heatmap */}
      {heatmapData.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Dimension Scores</h3>
          <HeatmapChart
            data={heatmapData}
            title="ARI Dimensions"
            dimensions={["current"]}
          />
        </div>
      )}

      {/* Insight Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-2">📊 ARI Insights</h3>
        <p className="text-sm text-blue-800">
          {status === 'healthy'
            ? 'Your agency retention is strong. Continue maintaining your current decision-making patterns.'
            : status === 'warning'
              ? 'Your ARI score is declining. Consider reviewing your goals and decision-making patterns.'
              : 'Your ARI score needs attention. Take action to improve autonomy in decision-making.'}
        </p>
      </div>
    </div>
  );
};
