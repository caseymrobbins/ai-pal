import { useEffect } from 'react';
import { Chart as ChartJS, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend } from 'chart.js';
import { Radar } from 'react-chartjs-2';
import { useDashboardStore } from '../store/store';
import { getApiClient } from '../api/client';
import { AlertCircle, TrendingUp } from 'lucide-react';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

export const ARIMetrics: React.FC<{ userId: string }> = ({ userId }) => {
  const { ariMetrics, setARIMetrics, setLoading, setError } = useDashboardStore();

  useEffect(() => {
    const fetchARIMetrics = async () => {
      setLoading('ari', true);
      try {
        const client = getApiClient();
        const data = await client.getARIMetrics(userId);
        setARIMetrics(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch ARI metrics');
      } finally {
        setLoading('ari', false);
      }
    };

    fetchARIMetrics();
    const interval = setInterval(fetchARIMetrics, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [userId, setARIMetrics, setLoading, setError]);

  if (!ariMetrics) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading ARI metrics...</div>
      </div>
    );
  }

  // Handle both array and object formats for dimensions
  let dimensionData: Record<string, number> = {};
  let labels: string[] = [];

  if (Array.isArray(ariMetrics.dimensions)) {
    // New API format: array of {name, value} objects
    ariMetrics.dimensions.forEach((dim: any) => {
      dimensionData[dim.name] = dim.value / 100; // Normalize to 0-1
      labels.push(dim.name);
    });
  } else {
    // Legacy format: object with dimension names as keys
    dimensionData = ariMetrics.dimensions;
    labels = [
      'Decision Quality',
      'Skill Development',
      'AI Reliance',
      'Bottleneck Resolution',
      'User Confidence',
      'Engagement',
      'Autonomy Perception',
    ];
  }

  const values = Object.values(dimensionData);
  const currentScore = ariMetrics.current_score || ariMetrics.overall_score || 50;
  const isAlert = currentScore < 50;

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Agency Score',
        data: values,
        borderColor: '#0066cc',
        backgroundColor: 'rgba(0, 102, 204, 0.1)',
        borderWidth: 2,
        fill: true,
        pointRadius: 5,
        pointBackgroundColor: '#0066cc',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointHoverRadius: 7,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    scales: {
      r: {
        beginAtZero: true,
        max: 1,
        ticks: {
          stepSize: 0.25,
          font: { size: 12 },
        },
      },
    },
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Agency Retention Index (ARI)</h2>
        {isAlert && (
          <div className="flex items-center gap-2 px-4 py-2 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="text-red-600" size={20} />
            <span className="text-sm font-medium text-red-600">Alert: Agency below threshold</span>
          </div>
        )}
      </div>

      {/* Overall Score */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="col-span-3 sm:col-span-1">
          <div className="bg-gradient-to-br from-primary-50 to-primary-100 rounded-lg p-6 text-center">
            <p className="text-gray-600 text-sm font-medium mb-2">Overall Score</p>
            <p className="text-4xl font-bold text-primary-600">
              {currentScore.toFixed(1)}%
            </p>
            <p className="text-xs text-gray-500 mt-2">
              Last updated: {new Date(ariMetrics.update_timestamp || ariMetrics.timestamp).toLocaleTimeString()}
            </p>
          </div>
        </div>

        {/* Top 3 Strengths */}
        <div className="col-span-3 sm:col-span-2">
          <div className="grid grid-cols-3 gap-2">
            {Object.entries(dimensionData)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 3)
              .map(([key, value]) => (
                <div key={key} className="bg-green-50 rounded-lg p-4">
                  <p className="text-xs text-gray-600 font-medium capitalize mb-1">
                    {key}
                  </p>
                  <p className="text-2xl font-bold text-green-600">{(value * 100).toFixed(0)}%</p>
                  <div className="mt-2 h-1 bg-green-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-600"
                      style={{ width: `${value * 100}%` }}
                    ></div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Radar Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">7-Dimension Analysis</h3>
          <Radar data={chartData} options={chartOptions} />
        </div>

        {/* Metrics Breakdown */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Individual Metrics</h3>
          <div className="space-y-3">
            {labels.map((label, idx) => {
              const value = values[idx];
              const status = value >= 0.7 ? 'good' : value >= 0.5 ? 'fair' : 'poor';
              const statusColor = {
                good: 'text-green-600',
                fair: 'text-yellow-600',
                poor: 'text-red-600',
              }[status];

              return (
                <div key={label}>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-sm font-medium text-gray-700">{label}</label>
                    <span className={`text-sm font-bold ${statusColor}`}>
                      {(value * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 ${
                        status === 'good'
                          ? 'bg-green-500'
                          : status === 'fair'
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      }`}
                      style={{ width: `${value * 100}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex gap-2">
          <TrendingUp className="text-blue-600 flex-shrink-0" size={20} />
          <div>
            <p className="font-medium text-blue-900 mb-1">Recommendations</p>
            <p className="text-sm text-blue-800">
              {ariMetrics.overall_score >= 0.7
                ? "Your agency score is healthy. Continue leveraging AI for support while maintaining your autonomy."
                : ariMetrics.overall_score >= 0.5
                ? "Consider reducing AI dependency and focusing on skill development to improve your autonomy."
                : "Your agency is declining. Take a break from AI assistance and focus on independent problem-solving."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
