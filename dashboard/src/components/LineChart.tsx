import React from 'react';
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

export interface LineChartData {
  name: string;
  [key: string]: string | number;
}

export interface LineChartProps {
  data: LineChartData[];
  lines: Array<{
    dataKey: string;
    stroke: string;
    name: string;
    strokeWidth?: number;
  }>;
  title?: string;
  xAxisKey?: string;
  height?: number;
  showLegend?: boolean;
  showGrid?: boolean;
  showTooltip?: boolean;
}

/**
 * Reusable LineChart component for displaying time-series data
 * Supports multiple lines and customizable styling
 */
export const LineChart: React.FC<LineChartProps> = ({
  data,
  lines,
  title,
  xAxisKey = 'name',
  height = 300,
  showLegend = true,
  showGrid = true,
  showTooltip = true,
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6" style={{ height }}>
        <p className="text-gray-500 text-center">No data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {title && <h3 className="text-lg font-semibold text-gray-800 mb-4">{title}</h3>}
      <ResponsiveContainer width="100%" height={height}>
        <RechartsLineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" />}
          <XAxis
            dataKey={xAxisKey}
            tick={{ fill: '#666', fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis tick={{ fill: '#666', fontSize: 12 }} />
          {showTooltip && (
            <Tooltip
              contentStyle={{
                backgroundColor: '#f9fafb',
                border: '1px solid #e5e7eb',
                borderRadius: '0.5rem',
              }}
              formatter={(value) => {
                if (typeof value === 'number') {
                  return value.toFixed(2);
                }
                return value;
              }}
            />
          )}
          {showLegend && <Legend />}
          {lines.map((line) => (
            <Line
              key={line.dataKey}
              type="monotone"
              dataKey={line.dataKey}
              stroke={line.stroke}
              name={line.name}
              strokeWidth={line.strokeWidth || 2}
              dot={false}
              isAnimationActive={true}
            />
          ))}
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
};
