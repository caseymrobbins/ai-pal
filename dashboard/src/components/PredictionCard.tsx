import React from 'react';
import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';

export interface PredictionMetric {
  label: string;
  currentValue: number;
  predictedValue: number;
  timeframe: string;
  confidenceLevel: number; // 0-1
  trend: 'up' | 'down' | 'stable';
  unit?: string;
  warningThreshold?: number;
}

export interface PredictionCardProps {
  metric: PredictionMetric;
  compact?: boolean;
}

/**
 * Card component for displaying prediction data with confidence intervals
 * Shows current value, predicted value, and trend direction
 */
export const PredictionCard: React.FC<PredictionCardProps> = ({
  metric,
  compact = false,
}) => {
  const change = metric.predictedValue - metric.currentValue;
  const changePercent = (change / metric.currentValue) * 100;
  const isWarning =
    metric.warningThreshold !== undefined &&
    metric.predictedValue < metric.warningThreshold;

  const TrendIcon =
    metric.trend === 'up' ? TrendingUp : metric.trend === 'down' ? TrendingDown : null;

  const trendColor =
    metric.trend === 'up'
      ? 'text-green-600'
      : metric.trend === 'down'
        ? 'text-red-600'
        : 'text-gray-600';

  const confidencePercent = Math.round(metric.confidenceLevel * 100);
  const confidenceColor =
    confidencePercent >= 80 ? 'text-green-600' : 'text-yellow-600';

  if (compact) {
    return (
      <div className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-gray-600">{metric.label}</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {metric.currentValue.toFixed(1)}
              {metric.unit}
            </p>
            <p className="text-xs text-gray-500 mt-1">{metric.timeframe}</p>
          </div>

          <div className="text-right">
            {TrendIcon && <TrendIcon className={`${trendColor} w-5 h-5`} />}
            <p className={`text-sm font-semibold mt-1 ${trendColor}`}>
              {change > 0 ? '+' : ''}
              {change.toFixed(1)} ({changePercent.toFixed(0)}%)
            </p>
            <div className="text-xs text-gray-500 mt-1">
              Confidence: {confidencePercent}%
            </div>
          </div>
        </div>

        {isWarning && (
          <div className="mt-2 flex items-center gap-2 text-xs text-red-600 bg-red-50 p-2 rounded">
            <AlertCircle className="w-4 h-4" />
            <span>May fall below {metric.warningThreshold}</span>
          </div>
        )}
      </div>
    );
  }

  // Full card version
  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition">
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">{metric.label}</h3>
        {isWarning && (
          <AlertCircle className="w-6 h-6 text-red-600" />
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        {/* Current Value */}
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm text-gray-600 mb-1">Current</p>
          <p className="text-3xl font-bold text-gray-900">
            {metric.currentValue.toFixed(1)}
          </p>
          <p className="text-xs text-gray-500 mt-1">{metric.unit}</p>
        </div>

        {/* Predicted Value */}
        <div className="bg-blue-50 rounded-lg p-4">
          <p className="text-sm text-gray-600 mb-1">Predicted ({metric.timeframe})</p>
          <p className="text-3xl font-bold text-blue-600">
            {metric.predictedValue.toFixed(1)}
          </p>
          <p className="text-xs text-gray-500 mt-1">{metric.unit}</p>
        </div>
      </div>

      {/* Change indicator */}
      <div className="mb-4 p-4 bg-gray-50 rounded-lg flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">Expected change</p>
          <div className="flex items-center gap-2 mt-1">
            {TrendIcon && <TrendIcon className={`${trendColor} w-5 h-5`} />}
            <p className={`text-xl font-bold ${trendColor}`}>
              {change > 0 ? '+' : ''}
              {change.toFixed(1)} ({changePercent.toFixed(0)}%)
            </p>
          </div>
        </div>
      </div>

      {/* Confidence Level */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm text-gray-600">Confidence Level</p>
          <p className={`text-sm font-semibold ${confidenceColor}`}>
            {confidencePercent}%
          </p>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              confidencePercent >= 80 ? 'bg-green-500' : 'bg-yellow-500'
            }`}
            style={{ width: `${confidencePercent}%` }}
          />
        </div>
      </div>

      {/* Warning message */}
      {isWarning && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">
            <strong>Warning:</strong> Predicted value may fall below threshold of{' '}
            {metric.warningThreshold}. Consider taking action.
          </p>
        </div>
      )}

      {/* Interpretation */}
      <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-100">
        <p className="text-xs text-blue-800">
          {metric.trend === 'up'
            ? `Metric is expected to improve by ${Math.abs(changePercent).toFixed(0)}% over the next ${metric.timeframe}.`
            : metric.trend === 'down'
              ? `Metric is expected to decline by ${Math.abs(changePercent).toFixed(0)}% over the next ${metric.timeframe}.`
              : `Metric is expected to remain stable over the next ${metric.timeframe}.`}
        </p>
      </div>
    </div>
  );
};
