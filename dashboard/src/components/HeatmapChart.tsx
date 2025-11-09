import React from 'react';

export interface HeatmapData {
  dimension: string;
  [key: string]: string | number;
}

export interface HeatmapChartProps {
  data: HeatmapData[];
  title?: string;
  dimensions?: string[];
  colorScale?: 'cool' | 'warm' | 'default';
}

/**
 * Heatmap component for displaying 2D data patterns
 * Useful for ARI dimension comparisons over time
 */
export const HeatmapChart: React.FC<HeatmapChartProps> = ({
  data,
  title,
  dimensions,
  colorScale = 'default',
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-500 text-center">No data available</p>
      </div>
    );
  }

  // Extract all keys except 'dimension'
  const allKeys = dimensions || Object.keys(data[0]).filter((key) => key !== 'dimension');

  // Get color based on value (0-1 range)
  const getColor = (value: number): string => {
    const normalized = Math.max(0, Math.min(1, value));

    if (colorScale === 'cool') {
      // Blue (cool) scale
      if (normalized < 0.5) {
        const intensity = normalized * 2;
        return `rgb(200, 230, 255, ${intensity})`;
      } else {
        const intensity = (normalized - 0.5) * 2;
        return `rgb(59, 130, 246, ${intensity})`;
      }
    } else if (colorScale === 'warm') {
      // Red (warm) scale
      if (normalized < 0.5) {
        const intensity = normalized * 2;
        return `rgb(255, 230, 200, ${intensity})`;
      } else {
        const intensity = (normalized - 0.5) * 2;
        return `rgb(239, 68, 68, ${intensity})`;
      }
    } else {
      // Default (green-to-red)
      if (normalized < 0.5) {
        const r = Math.round(255 * (normalized * 2));
        const g = 200;
        const b = 0;
        return `rgb(${r}, ${g}, ${b})`;
      } else {
        const r = 255;
        const g = Math.round(200 * (1 - (normalized - 0.5) * 2));
        const b = 0;
        return `rgb(${r}, ${g}, ${b})`;
      }
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {title && <h3 className="text-lg font-semibold text-gray-800 mb-4">{title}</h3>}

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr>
              <th className="border border-gray-200 bg-gray-50 px-3 py-2 text-left font-semibold text-gray-700">
                Dimension
              </th>
              {allKeys.map((key) => (
                <th
                  key={key}
                  className="border border-gray-200 bg-gray-50 px-3 py-2 text-center font-semibold text-gray-700 text-xs"
                >
                  {key}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr key={idx}>
                <td className="border border-gray-200 px-3 py-2 font-medium text-gray-800 bg-gray-50">
                  {row.dimension}
                </td>
                {allKeys.map((key) => {
                  const value = row[key];
                  const numValue = typeof value === 'number' ? value : 0;
                  const displayValue = (numValue * 100).toFixed(0);

                  return (
                    <td
                      key={`${row.dimension}-${key}`}
                      className="border border-gray-200 px-3 py-2 text-center relative"
                      title={`${numValue.toFixed(3)}`}
                    >
                      <div
                        className="absolute inset-0 opacity-70"
                        style={{ backgroundColor: getColor(numValue) }}
                      />
                      <span className="relative z-10 font-medium text-gray-900">
                        {displayValue}%
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center justify-center gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-6 h-4 bg-green-500" />
          <span>High</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-4 bg-yellow-500" />
          <span>Medium</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-4 bg-red-500" />
          <span>Low</span>
        </div>
      </div>
    </div>
  );
};
