import React from 'react';
import { CheckCircle, Clock, AlertCircle, Target } from 'lucide-react';

export interface TimelineGoal {
  id: string;
  title: string;
  createdAt: string;
  targetDate?: string;
  completedAt?: string;
  status: 'active' | 'completed' | 'at-risk';
  progress: number;
  priority: 'low' | 'medium' | 'high';
}

export interface GoalTimelineProps {
  goals: TimelineGoal[];
  title?: string;
}

/**
 * Timeline view of goals showing creation date, target date, and completion status
 */
export const GoalTimeline: React.FC<GoalTimelineProps> = ({
  goals,
  title = 'Goal Timeline',
}) => {
  if (!goals || goals.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-500 text-center">No goals to display</p>
      </div>
    );
  }

  // Sort goals by created date (newest first)
  const sortedGoals = [...goals].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );

  const getStatusIcon = (status: TimelineGoal['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'at-risk':
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      case 'active':
        return <Target className="w-5 h-5 text-blue-600" />;
    }
  };

  const getStatusColor = (status: TimelineGoal['status']): string => {
    switch (status) {
      case 'completed':
        return 'bg-green-50 border-l-4 border-green-600';
      case 'at-risk':
        return 'bg-red-50 border-l-4 border-red-600';
      case 'active':
        return 'bg-blue-50 border-l-4 border-blue-600';
    }
  };

  const getPriorityBadge = (priority: TimelineGoal['priority']): string => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTimelineLabel = (goal: TimelineGoal): string => {
    const now = new Date();
    const created = new Date(goal.createdAt);
    const daysAgo = Math.floor(
      (now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24)
    );

    if (daysAgo === 0) return 'Today';
    if (daysAgo === 1) return 'Yesterday';
    if (daysAgo < 7) return `${daysAgo} days ago`;
    if (daysAgo < 30) return `${Math.floor(daysAgo / 7)} weeks ago`;
    return `${Math.floor(daysAgo / 30)} months ago`;
  };

  const getDaysUntilDeadline = (targetDate?: string): string => {
    if (!targetDate) return 'No deadline';

    const now = new Date();
    const target = new Date(targetDate);
    const daysLeft = Math.ceil(
      (target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
    );

    if (daysLeft < 0) return 'Overdue';
    if (daysLeft === 0) return 'Due today';
    if (daysLeft === 1) return 'Due tomorrow';
    return `${daysLeft} days left`;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold text-gray-800 mb-6">{title}</h2>

      <div className="space-y-4">
        {sortedGoals.map((goal, idx) => (
          <div
            key={goal.id}
            className={`p-4 rounded-lg ${getStatusColor(goal.status)} transition hover:shadow-md`}
          >
            <div className="flex items-start gap-4">
              {/* Status icon */}
              <div className="flex-shrink-0 mt-1">
                {getStatusIcon(goal.status)}
              </div>

              {/* Goal content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-semibold text-gray-900 truncate">
                    {goal.title}
                  </h3>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${getPriorityBadge(
                      goal.priority
                    )}`}
                  >
                    {goal.priority.charAt(0).toUpperCase() + goal.priority.slice(1)}
                  </span>
                </div>

                {/* Progress bar */}
                <div className="mb-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-gray-600">Progress</span>
                    <span className="text-xs font-semibold text-gray-900">
                      {goal.progress}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        goal.status === 'completed'
                          ? 'bg-green-600'
                          : goal.status === 'at-risk'
                            ? 'bg-red-600'
                            : 'bg-blue-600'
                      }`}
                      style={{ width: `${goal.progress}%` }}
                    />
                  </div>
                </div>

                {/* Timeline info */}
                <div className="flex flex-wrap gap-4 text-xs text-gray-600">
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    <span>Created: {getTimelineLabel(goal)}</span>
                  </div>

                  {goal.targetDate && (
                    <div className="flex items-center gap-1">
                      <Target className="w-4 h-4" />
                      <span>{getDaysUntilDeadline(goal.targetDate)}</span>
                    </div>
                  )}

                  {goal.completedAt && (
                    <div className="flex items-center gap-1">
                      <CheckCircle className="w-4 h-4" />
                      <span>
                        Completed:{' '}
                        {new Date(goal.completedAt).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
