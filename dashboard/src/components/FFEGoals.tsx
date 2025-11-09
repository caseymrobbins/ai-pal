import React, { useEffect, useState } from 'react';
import { CheckCircle2, Clock, Pause, Plus, TrendingUp } from 'lucide-react';
import { useDashboardStore } from '../store/store';
import { getApiClient } from '../api/client';

export const FFEGoals: React.FC<{ userId: string }> = ({ userId }) => {
  const { goals, setGoals, setLoading, setError } = useDashboardStore();
  const [showNewGoal, setShowNewGoal] = useState(false);

  useEffect(() => {
    const fetchGoals = async () => {
      setLoading('goals', true);
      try {
        const client = getApiClient();
        const data = await client.getGoals(userId);
        setGoals(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch goals');
      } finally {
        setLoading('goals', false);
      }
    };

    fetchGoals();
  }, [userId, setGoals, setLoading, setError]);

  const activeGoals = goals.filter(g => g.status === 'active');
  const completedGoals = goals.filter(g => g.status === 'completed');
  const totalValue = goals.reduce((sum, g) => sum + g.value, 0);

  const statusIcon = {
    active: <Clock className="text-blue-500" size={20} />,
    completed: <CheckCircle2 className="text-green-500" size={20} />,
    paused: <Pause className="text-yellow-500" size={20} />,
  };

  const statusColor = {
    active: 'bg-blue-50 border-blue-200',
    completed: 'bg-green-50 border-green-200',
    paused: 'bg-yellow-50 border-yellow-200',
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <TrendingUp className="text-primary-600" />
            FFE Goals & Progress
          </h2>
          <p className="text-gray-600 text-sm mt-2">
            Fractal Flow Engine goal tracking with 80/20 scoping
          </p>
        </div>
        <button
          onClick={() => setShowNewGoal(!showNewGoal)}
          className="flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg transition"
        >
          <Plus size={20} />
          New Goal
        </button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
          <p className="text-gray-600 text-sm font-medium mb-1">Active Goals</p>
          <p className="text-3xl font-bold text-blue-600">{activeGoals.length}</p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
          <p className="text-gray-600 text-sm font-medium mb-1">Completed</p>
          <p className="text-3xl font-bold text-green-600">{completedGoals.length}</p>
        </div>
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
          <p className="text-gray-600 text-sm font-medium mb-1">Total Value</p>
          <p className="text-3xl font-bold text-purple-600">{totalValue}</p>
        </div>
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4">
          <p className="text-gray-600 text-sm font-medium mb-1">Completion Rate</p>
          <p className="text-3xl font-bold text-orange-600">
            {goals.length > 0 ? Math.round((completedGoals.length / goals.length) * 100) : 0}%
          </p>
        </div>
      </div>

      {/* New Goal Form */}
      {showNewGoal && (
        <div className="bg-gray-50 rounded-lg p-6 mb-8 border-2 border-dashed border-primary-300">
          <h3 className="font-semibold text-gray-800 mb-4">Create New Goal</h3>
          <form className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Goal Title
              </label>
              <input
                type="text"
                placeholder="What do you want to achieve?"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                placeholder="Describe the goal and why it matters..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                rows={3}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Value (1-10)
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  placeholder="10"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Time Estimate (days)
                </label>
                <input
                  type="number"
                  min="1"
                  placeholder="7"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                className="flex-1 bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-lg transition"
              >
                Create Goal
              </button>
              <button
                type="button"
                onClick={() => setShowNewGoal(false)}
                className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-800 font-medium py-2 px-4 rounded-lg transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Goals List */}
      <div className="space-y-4">
        {goals.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">No goals yet. Create your first goal to get started!</p>
            <button
              onClick={() => setShowNewGoal(true)}
              className="inline-flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white px-6 py-2 rounded-lg transition"
            >
              <Plus size={20} />
              Create First Goal
            </button>
          </div>
        ) : (
          goals.map((goal) => (
            <div key={goal.id} className={`border-l-4 rounded-lg p-6 ${statusColor[goal.status]}`}>
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    {statusIcon[goal.status]}
                    <h3 className="text-lg font-semibold text-gray-800">{goal.title}</h3>
                  </div>
                  <p className="text-gray-600 text-sm">{goal.description}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-600">Value: <span className="text-lg font-bold text-primary-600">{goal.value}</span></p>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-medium text-gray-600">Progress</span>
                  <span className="text-xs font-bold text-gray-800">{goal.progress}%</span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 ${
                      goal.status === 'completed'
                        ? 'bg-green-500'
                        : goal.status === 'paused'
                        ? 'bg-yellow-500'
                        : 'bg-primary-500'
                    }`}
                    style={{ width: `${goal.progress}%` }}
                  ></div>
                </div>
              </div>

              {/* Metadata */}
              <div className="flex justify-between text-xs text-gray-500">
                <span>Created: {new Date(goal.created_at).toLocaleDateString()}</span>
                <span>Updated: {new Date(goal.updated_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* FFE Principles */}
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h4 className="font-semibold text-blue-900 mb-3">FFE Principles</h4>
        <ul className="space-y-2 text-sm text-blue-800">
          <li>✨ <strong>80/20 Scoping:</strong> Focus on the 20% of effort that yields 80% of results</li>
          <li>🎯 <strong>Atomic Blocks:</strong> Break goals into 5-block work sessions to maintain flow</li>
          <li>💪 <strong>Strength Amplifier:</strong> Leverage your unique strengths for each task</li>
          <li>🚀 <strong>Momentum Loop:</strong> Plan → Work → Review → Celebrate → Repeat</li>
        </ul>
      </div>
    </div>
  );
};
