import React, { useEffect, useState } from 'react';
import { Target, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';
import { useDashboardStore } from '../store/store';
import { getApiClient } from '../api/client';
import { FunnelChart } from './FunnelChart';
import { GoalTimeline } from './GoalTimeline';

interface FFEMetrics {
  total_goals: number;
  active_goals: number;
  completed_goals: number;
  completion_rate: number;
  average_clarity_score: number;
  average_difficulty: number;
  goals_by_complexity: {
    easy: number;
    medium: number;
    hard: number;
  };
  goals_by_status: {
    created: number;
    in_progress: number;
    completed: number;
  };
  average_time_to_completion: number;
  goal_success_rate_by_complexity: {
    easy: number;
    medium: number;
    hard: number;
  };
}

interface FFEDashboardProps {
  userId: string;
}

/**
 * Fractal Flow Engine Dashboard
 * Comprehensive view of goal management and FFE metrics
 */
export const FFEDashboard: React.FC<FFEDashboardProps> = ({ userId }) => {
  const { setLoading, setError } = useDashboardStore();
  const [metrics, setMetrics] = useState<FFEMetrics | null>(null);
  const [goals, setGoals] = useState<any[]>([]);

  useEffect(() => {
    const fetchMetrics = async () => {
      setLoading('ffe', true);
      try {
        const client = getApiClient();

        // Fetch FFE metrics (this endpoint will be created in Phase 2)
        // For now, we'll fetch goals and calculate metrics
        const goalsData = await client.getGoals(userId);
        const goalsArray = Array.isArray(goalsData) ? goalsData : goalsData.goals || [];

        // Calculate metrics from goals
        const completed = goalsArray.filter((g) => g.status === 'completed').length;
        const active = goalsArray.filter((g) => g.status === 'active').length;
        const total = goalsArray.length;

        const complexityBreakdown = {
          easy: goalsArray.filter((g) => g.complexity === 'easy').length,
          medium: goalsArray.filter((g) => g.complexity === 'medium').length,
          hard: goalsArray.filter((g) => g.complexity === 'hard').length,
        };

        const completedByComplexity = goalsArray
          .filter((g) => g.status === 'completed')
          .reduce(
            (acc, g) => {
              acc[g.complexity || 'medium'] = (acc[g.complexity || 'medium'] || 0) + 1;
              return acc;
            },
            { easy: 0, medium: 0, hard: 0 }
          );

        const successRateByComplexity = {
          easy: complexityBreakdown.easy > 0 ? (completedByComplexity.easy / complexityBreakdown.easy) * 100 : 0,
          medium: complexityBreakdown.medium > 0 ? (completedByComplexity.medium / complexityBreakdown.medium) * 100 : 0,
          hard: complexityBreakdown.hard > 0 ? (completedByComplexity.hard / complexityBreakdown.hard) * 100 : 0,
        };

        const calculatedMetrics: FFEMetrics = {
          total_goals: total,
          active_goals: active,
          completed_goals: completed,
          completion_rate: total > 0 ? (completed / total) * 100 : 0,
          average_clarity_score:
            goalsArray.length > 0
              ? goalsArray.reduce((sum, g) => sum + (g.clarity_score || 0), 0) /
                goalsArray.length
              : 0,
          average_difficulty:
            goalsArray.length > 0
              ? goalsArray.reduce((sum, g) => sum + (g.estimated_difficulty || 0), 0) /
                goalsArray.length
              : 0,
          goals_by_complexity: complexityBreakdown,
          goals_by_status: {
            created: goalsArray.filter((g) => g.status === 'created').length,
            in_progress: active,
            completed: completed,
          },
          average_time_to_completion: 7, // Placeholder - calculated from actual data
          goal_success_rate_by_complexity: successRateByComplexity,
        };

        setMetrics(calculatedMetrics);
        setGoals(goalsArray);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch FFE metrics');
      } finally {
        setLoading('ffe', false);
      }
    };

    fetchMetrics();
  }, [userId, setLoading, setError]);

  if (!metrics) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-500 text-center">Loading FFE metrics...</p>
      </div>
    );
  }

  // Prepare funnel data
  const funnelData = [
    {
      name: 'Created',
      value: metrics.goals_by_status.created,
      description: 'Newly created goals',
    },
    {
      name: 'In Progress',
      value: metrics.goals_by_status.in_progress,
      description: 'Goals actively being worked on',
    },
    {
      name: 'Completed',
      value: metrics.goals_by_status.completed,
      description: 'Successfully completed goals',
    },
  ];

  const timelineGoals = goals.map((goal) => ({
    id: goal.goal_id || goal.id,
    title: goal.description || goal.title,
    createdAt: goal.created_at,
    targetDate: goal.deadline,
    completedAt: goal.completed_at,
    status:
      goal.status === 'completed'
        ? 'completed'
        : goal.status === 'active'
          ? 'active'
          : 'at-risk',
    progress: goal.progress || 0,
    priority: goal.importance || 'medium',
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2 mb-2">
          <Target className="text-primary-600" />
          Fractal Flow Engine Dashboard
        </h1>
        <p className="text-gray-600">
          Comprehensive view of your goals and achievement metrics
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total Goals */}
        <div className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Goals</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {metrics.total_goals}
              </p>
            </div>
            <Target className="w-8 h-8 text-blue-600 opacity-20" />
          </div>
        </div>

        {/* Active Goals */}
        <div className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Active</p>
              <p className="text-3xl font-bold text-blue-600 mt-1">
                {metrics.active_goals}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-blue-600 opacity-20" />
          </div>
        </div>

        {/* Completion Rate */}
        <div className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Completion Rate</p>
              <p className="text-3xl font-bold text-green-600 mt-1">
                {metrics.completion_rate.toFixed(0)}%
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-600 opacity-20" />
          </div>
        </div>

        {/* Average Clarity */}
        <div className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Clarity</p>
              <p className="text-3xl font-bold text-purple-600 mt-1">
                {metrics.average_clarity_score.toFixed(1)}/10
              </p>
            </div>
            <AlertCircle className="w-8 h-8 text-purple-600 opacity-20" />
          </div>
        </div>
      </div>

      {/* Goal Pipeline Funnel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <FunnelChart data={funnelData} title="Goal Pipeline" height={250} />
        </div>

        {/* Success Rate by Complexity */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Success Rate by Complexity
          </h3>
          <div className="space-y-4">
            {/* Easy */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Easy</span>
                <span className="text-sm font-bold text-gray-900">
                  {metrics.goal_success_rate_by_complexity.easy.toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="h-full bg-green-500 rounded-full"
                  style={{
                    width: `${metrics.goal_success_rate_by_complexity.easy}%`,
                  }}
                />
              </div>
            </div>

            {/* Medium */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Medium</span>
                <span className="text-sm font-bold text-gray-900">
                  {metrics.goal_success_rate_by_complexity.medium.toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="h-full bg-yellow-500 rounded-full"
                  style={{
                    width: `${metrics.goal_success_rate_by_complexity.medium}%`,
                  }}
                />
              </div>
            </div>

            {/* Hard */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Hard</span>
                <span className="text-sm font-bold text-gray-900">
                  {metrics.goal_success_rate_by_complexity.hard.toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="h-full bg-red-500 rounded-full"
                  style={{
                    width: `${metrics.goal_success_rate_by_complexity.hard}%`,
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Goal Timeline */}
      <GoalTimeline goals={timelineGoals} title="Recent Goals" />

      {/* Complexity Breakdown */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          Goals by Complexity
        </h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <p className="text-sm text-gray-600">Easy</p>
            <p className="text-3xl font-bold text-green-600 mt-1">
              {metrics.goals_by_complexity.easy}
            </p>
            <p className="text-xs text-gray-600 mt-1">
              {((metrics.goals_by_complexity.easy / metrics.total_goals) * 100).toFixed(0)}%
            </p>
          </div>

          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <p className="text-sm text-gray-600">Medium</p>
            <p className="text-3xl font-bold text-yellow-600 mt-1">
              {metrics.goals_by_complexity.medium}
            </p>
            <p className="text-xs text-gray-600 mt-1">
              {((metrics.goals_by_complexity.medium / metrics.total_goals) * 100).toFixed(0)}%
            </p>
          </div>

          <div className="text-center p-4 bg-red-50 rounded-lg">
            <p className="text-sm text-gray-600">Hard</p>
            <p className="text-3xl font-bold text-red-600 mt-1">
              {metrics.goals_by_complexity.hard}
            </p>
            <p className="text-xs text-gray-600 mt-1">
              {((metrics.goals_by_complexity.hard / metrics.total_goals) * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
