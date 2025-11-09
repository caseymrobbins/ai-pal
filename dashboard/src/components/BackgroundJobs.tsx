import { useEffect, useState } from 'react';
import { getApiClient } from '../api/client';

interface Task {
  task_id: string;
  task_name: string;
  task_type: string;
  status: string;
  user_id?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  result?: Record<string, any>;
  error_message?: string;
  attempts: number;
  duration_seconds?: number;
}

interface TaskSubmissionForm {
  type: 'ari' | 'ffe' | 'edm';
  goalId?: string;
  goalDescription?: string;
  complexity?: string;
  timeWindow?: number;
  minSeverity?: string;
}

export function BackgroundJobs({ userId }: { userId: string }) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed' | 'failed'>('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [form, setForm] = useState<TaskSubmissionForm>({ type: 'ari', timeWindow: 24, complexity: 'medium', minSeverity: 'low' });
  const [submitting, setSubmitting] = useState(false);

  const client = getApiClient();

  // Fetch tasks
  const fetchTasks = async () => {
    try {
      setLoading(true);
      setError(null);

      let response;
      switch (filter) {
        case 'pending':
          response = await client.getPendingTasks(20);
          break;
        case 'failed':
          response = await client.getFailedTasks(20);
          break;
        default:
          response = await client.listTasks(undefined, userId, 50);
      }

      setTasks(response.tasks || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tasks');
      console.error('Error fetching tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh effect
  useEffect(() => {
    fetchTasks();

    let interval: ReturnType<typeof setInterval> | null = null;
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchTasks();
      }, 5000); // Refresh every 5 seconds
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [filter, autoRefresh]);

  // Submit task
  const handleSubmitTask = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setError(null);

      let response;
      switch (form.type) {
        case 'ari':
          response = await client.submitARIAggregation(userId, form.timeWindow || 24);
          break;
        case 'ffe':
          response = await client.submitFFEPlanning(
            form.goalId || 'goal-' + Date.now(),
            userId,
            form.goalDescription || 'Sample Goal',
            form.complexity || 'medium'
          );
          break;
        case 'edm':
          response = await client.submitEDMAnalysis(userId, form.timeWindow || 7, form.minSeverity || 'low');
          break;
      }

      console.log('Task submitted:', response);
      alert(`✓ ${form.type.toUpperCase()} task submitted (ID: ${response.task_id})`);

      // Refresh task list
      await fetchTasks();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to submit task';
      setError(msg);
      alert(`✗ Error: ${msg}`);
    } finally {
      setSubmitting(false);
    }
  };

  // Cancel task
  const handleCancelTask = async (taskId: string) => {
    if (!confirm('Cancel this task?')) return;

    try {
      await client.cancelTask(taskId);
      alert('✓ Task cancelled');
      await fetchTasks();
    } catch (err) {
      alert(`✗ Error: ${err instanceof Error ? err.message : 'Failed to cancel task'}`);
    }
  };

  // Retry task
  const handleRetryTask = async (taskId: string) => {
    try {
      await client.retryTask(taskId);
      alert('✓ Task retried');
      await fetchTasks();
    } catch (err) {
      alert(`✗ Error: ${err instanceof Error ? err.message : 'Failed to retry task'}`);
    }
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Get task type icon
  const getTaskIcon = (taskType: string) => {
    switch (taskType) {
      case 'ari_snapshot':
        return '📊';
      case 'ffe_planning':
        return '🎯';
      case 'edm_analysis':
        return '🔍';
      case 'model_training':
        return '🤖';
      case 'maintenance':
        return '🔧';
      default:
        return '⚙️';
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">⚙️ Background Jobs</h2>

      {/* Task Submission Form */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">📤 Submit a Task</h3>

        <form onSubmit={handleSubmitTask} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Task Type Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Task Type</label>
              <div className="space-y-2">
                {[
                  { id: 'ari', label: '📊 ARI Snapshot Aggregation', desc: 'Aggregate agency metrics' },
                  { id: 'ffe', label: '🎯 FFE Goal Planning', desc: 'Plan and decompose goals' },
                  { id: 'edm', label: '🔍 EDM Analysis', desc: 'Analyze epistemic debt' },
                ].map((t) => (
                  <label key={t.id} className="flex items-center">
                    <input
                      type="radio"
                      name="task_type"
                      value={t.id}
                      checked={form.type === t.id}
                      onChange={(e) => setForm({ ...form, type: e.target.value as any })}
                      className="mr-2"
                    />
                    <span className="text-sm">
                      {t.label}
                      <span className="text-gray-500 text-xs ml-2">({t.desc})</span>
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Task-specific Parameters */}
            <div className="space-y-3">
              {form.type === 'ari' && (
                <>
                  <label className="block text-sm font-medium text-gray-700">
                    Time Window (hours)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="720"
                    value={form.timeWindow}
                    onChange={(e) => setForm({ ...form, timeWindow: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </>
              )}

              {form.type === 'ffe' && (
                <>
                  <label className="block text-sm font-medium text-gray-700">
                    Goal Description
                  </label>
                  <input
                    type="text"
                    value={form.goalDescription}
                    onChange={(e) => setForm({ ...form, goalDescription: e.target.value })}
                    placeholder="e.g., Complete project"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <label className="block text-sm font-medium text-gray-700 mt-2">
                    Complexity Level
                  </label>
                  <select
                    value={form.complexity}
                    onChange={(e) => setForm({ ...form, complexity: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="simple">Simple</option>
                    <option value="medium">Medium</option>
                    <option value="complex">Complex</option>
                  </select>
                </>
              )}

              {form.type === 'edm' && (
                <>
                  <label className="block text-sm font-medium text-gray-700">
                    Time Window (days)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="365"
                    value={form.timeWindow}
                    onChange={(e) => setForm({ ...form, timeWindow: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <label className="block text-sm font-medium text-gray-700 mt-2">
                    Minimum Severity
                  </label>
                  <select
                    value={form.minSeverity}
                    onChange={(e) => setForm({ ...form, minSeverity: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </>
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition"
          >
            {submitting ? 'Submitting...' : '🚀 Submit Task'}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-3 bg-red-100 text-red-800 rounded-lg text-sm">
            {error}
          </div>
        )}
      </div>

      {/* Tasks List */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">📋 Tasks</h3>
          <div className="flex gap-2">
            <label className="flex items-center text-sm">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="mr-2"
              />
              Auto-refresh (5s)
            </label>
            <button
              onClick={fetchTasks}
              disabled={loading}
              className="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded-lg transition disabled:opacity-50"
            >
              🔄 Refresh
            </button>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-4 border-b">
          {(['all', 'pending', 'completed', 'failed'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-2 font-medium text-sm transition ${
                filter === f
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        {loading && !tasks.length ? (
          <div className="text-center py-8 text-gray-600">
            Loading tasks...
          </div>
        ) : tasks.length === 0 ? (
          <div className="text-center py-8 text-gray-600">
            No tasks found
          </div>
        ) : (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {tasks.map((task) => (
              <div
                key={task.task_id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">{getTaskIcon(task.task_type)}</span>
                      <h4 className="font-semibold text-sm">{task.task_name}</h4>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(task.status)}`}>
                        {task.status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 mb-2">
                      ID: <code className="bg-gray-100 px-1 rounded">{task.task_id.slice(0, 8)}...</code>
                    </p>
                    <div className="grid grid-cols-2 gap-2 text-xs text-gray-700">
                      <div>
                        <span className="font-medium">Created:</span>{' '}
                        {new Date(task.created_at).toLocaleString()}
                      </div>
                      {task.started_at && (
                        <div>
                          <span className="font-medium">Started:</span>{' '}
                          {new Date(task.started_at).toLocaleString()}
                        </div>
                      )}
                      {task.completed_at && (
                        <div>
                          <span className="font-medium">Completed:</span>{' '}
                          {new Date(task.completed_at).toLocaleString()}
                        </div>
                      )}
                      {task.duration_seconds && (
                        <div>
                          <span className="font-medium">Duration:</span> {task.duration_seconds.toFixed(2)}s
                        </div>
                      )}
                    </div>
                    {task.error_message && (
                      <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                        <span className="font-medium">Error:</span> {task.error_message}
                      </div>
                    )}
                    {task.result && (
                      <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-700">
                        <details>
                          <summary className="font-medium cursor-pointer">View Result</summary>
                          <pre className="mt-2 overflow-x-auto text-xs">
                            {JSON.stringify(task.result, null, 2).slice(0, 200)}...
                          </pre>
                        </details>
                      </div>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="ml-4 flex gap-2">
                    {task.status === 'pending' || task.status === 'running' ? (
                      <button
                        onClick={() => handleCancelTask(task.task_id)}
                        className="px-2 py-1 text-xs bg-red-500 hover:bg-red-600 text-white rounded transition"
                        title="Cancel task"
                      >
                        ✕
                      </button>
                    ) : task.status === 'failed' ? (
                      <button
                        onClick={() => handleRetryTask(task.task_id)}
                        className="px-2 py-1 text-xs bg-yellow-500 hover:bg-yellow-600 text-white rounded transition"
                        title="Retry task"
                      >
                        🔄
                      </button>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* System Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">🏥 System Status</h3>
        <p className="text-sm text-gray-600">
          Background job queue system status and Celery worker availability will be displayed here.
        </p>
        <button
          onClick={() => fetchTasks()}
          className="mt-4 px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
        >
          Check System Health
        </button>
      </div>
    </div>
  );
}
