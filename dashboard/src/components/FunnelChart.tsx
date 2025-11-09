import React from 'react';

export interface FunnelStage {
  name: string;
  value: number;
  description?: string;
}

export interface FunnelChartProps {
  data: FunnelStage[];
  title?: string;
  height?: number;
}

/**
 * Funnel chart for displaying conversion/progression metrics
 * Useful for goal pipeline: Created -> In Progress -> Completed
 */
export const FunnelChart: React.FC<FunnelChartProps> = ({
  data,
  title,
  height = 300,
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-500 text-center">No data available</p>
      </div>
    );
  }

  const maxValue = Math.max(...data.map((d) => d.value), 1);

  // Calculate conversion rates
  const conversionRates = data.map((stage, idx) => {
    if (idx === 0) return 100;
    return (stage.value / data[0].value) * 100;
  });

  // Colors for each stage
  const colors = [
    '#3b82f6', // blue
    '#10b981', // green
    '#f59e0b', // amber
    '#ef4444', // red
    '#8b5cf6', // purple
  ];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {title && <h3 className="text-lg font-semibold text-gray-800 mb-6">{title}</h3>}

      <div style={{ height }} className="flex flex-col justify-center">
        {data.map((stage, idx) => {
          const width = (stage.value / maxValue) * 100;
          const conversionRate = conversionRates[idx];
          const color = colors[idx % colors.length];

          return (
            <div key={idx} className="mb-6">
              {/* Stage label and count */}
              <div className="flex justify-between items-center mb-2">
                <h4 className="font-semibold text-gray-800">{stage.name}</h4>
                <div className="flex gap-4 items-center">
                  <span className="text-2xl font-bold text-gray-900">{stage.value}</span>
                  <span className="text-sm text-gray-600 w-12 text-right">
                    {conversionRate.toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* Funnel bar */}
              <div className="w-full bg-gray-200 rounded-lg overflow-hidden">
                <div
                  className="h-12 rounded-lg transition-all duration-300 flex items-center px-4"
                  style={{
                    width: `${width}%`,
                    backgroundColor: color,
                    opacity: 0.8,
                  }}
                >
                  <span className="text-white font-medium text-sm">
                    {((stage.value / maxValue) * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* Description if provided */}
              {stage.description && (
                <p className="text-sm text-gray-600 mt-2">{stage.description}</p>
              )}

              {/* Drop-off percentage for non-first stages */}
              {idx > 0 && (
                <p className="text-xs text-red-600 mt-1">
                  {(100 - conversionRate).toFixed(0)}% drop-off from {data[0].name}
                </p>
              )}
            </div>
          );
        })}
      </div>

      {/* Summary stats */}
      <div className="mt-8 pt-6 border-t border-gray-200 grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-600">Total entries</p>
          <p className="text-2xl font-bold text-gray-900">{data[0]?.value || 0}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Final conversion</p>
          <p className="text-2xl font-bold text-gray-900">
            {conversionRates[conversionRates.length - 1]?.toFixed(0) || 0}%
          </p>
        </div>
      </div>
    </div>
  );
};
