import { useEffect, useState } from 'react';
import { LogOut, Search } from 'lucide-react';
import { useDashboardStore } from '../store/store';
import { getApiClient } from '../api/client';

interface AuditLog {
  timestamp: string;
  event_type: string;
  user_id?: string;
  component: string;
  action: string;
  details: Record<string, any>;
  severity: 'debug' | 'info' | 'warning' | 'error' | 'critical';
  result?: string;
  resource?: string;
}

export const AuditLogs: React.FC<{ userId: string }> = ({ userId }) => {
  const { setLoading, setError } = useDashboardStore();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<AuditLog[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [daysFilter, setDaysFilter] = useState<number>(30);
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('');

  useEffect(() => {
    const fetchLogs = async () => {
      setLoading('audit', true);
      try {
        const client = getApiClient();
        // Use new API parameters: days, severity, event_type, limit
        const data = await client.getAuditLogs(
          userId,
          daysFilter,
          eventTypeFilter || undefined,
          severityFilter !== 'all' ? severityFilter : undefined,
          100
        );

        // Handle both response formats: direct array or AuditLogsResponse object
        const logsArray = Array.isArray(data) ? data : (data.logs || []);
        setLogs(logsArray);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch audit logs');
      } finally {
        setLoading('audit', false);
      }
    };

    fetchLogs();
  }, [userId, daysFilter, eventTypeFilter, severityFilter, setLoading, setError]);

  // Filter logs based on search and severity
  useEffect(() => {
    let filtered = logs;

    if (severityFilter !== 'all') {
      filtered = filtered.filter(log => log.severity === severityFilter);
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        log =>
          log.event_type.toLowerCase().includes(term) ||
          log.details.toLowerCase().includes(term)
      );
    }

    setFilteredLogs(filtered);
  }, [logs, searchTerm, severityFilter]);


  const severityBadge = {
    debug: 'bg-gray-100 text-gray-800',
    info: 'bg-blue-100 text-blue-800',
    warning: 'bg-yellow-100 text-yellow-800',
    error: 'bg-red-100 text-red-800',
    critical: 'bg-purple-100 text-purple-800',
  };

  const severityCounts = {
    debug: logs.filter(l => l.severity === 'debug').length,
    info: logs.filter(l => l.severity === 'info').length,
    warning: logs.filter(l => l.severity === 'warning').length,
    error: logs.filter(l => l.severity === 'error').length,
    critical: logs.filter(l => l.severity === 'critical').length,
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <LogOut className="text-primary-600" />
          Audit Logs
        </h2>
        <p className="text-sm text-gray-600">Showing {filteredLogs.length} of {logs.length} events</p>
      </div>

      {/* Severity Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-gray-600 text-sm font-medium mb-1">Info Events</p>
          <p className="text-2xl font-bold text-blue-600">{severityCounts.info}</p>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-gray-600 text-sm font-medium mb-1">Warnings</p>
          <p className="text-2xl font-bold text-yellow-600">{severityCounts.warning}</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-gray-600 text-sm font-medium mb-1">Errors</p>
          <p className="text-2xl font-bold text-red-600">{severityCounts.error}</p>
        </div>
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <p className="text-gray-600 text-sm font-medium mb-1">Critical</p>
          <p className="text-2xl font-bold text-purple-600">{severityCounts.critical}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 space-y-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search events..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Days Filter */}
          <select
            value={daysFilter}
            onChange={(e) => setDaysFilter(parseInt(e.target.value))}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
            <option value="180">Last 180 days</option>
          </select>

          {/* Severity Filter */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="all">All Severities</option>
            <option value="debug">Debug</option>
            <option value="info">Info</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>

      {/* Logs Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b-2 border-gray-200">
              <th className="text-left py-3 px-4 font-semibold text-gray-700">Timestamp</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-700">Event Type</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-700">Component</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-700">Severity</th>
            </tr>
          </thead>
          <tbody>
            {filteredLogs.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-8 text-center text-gray-500">
                  No audit logs found
                </td>
              </tr>
            ) : (
              filteredLogs.map((log, idx) => (
                <tr key={`${log.timestamp}-${idx}`} className="border-b border-gray-200 hover:bg-gray-50 transition">
                  <td className="py-3 px-4">
                    <span className="text-gray-600 text-xs">
                      {new Date(log.timestamp).toLocaleString()}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <code className="bg-gray-100 px-2 py-1 rounded text-xs text-gray-700">
                      {log.event_type}
                    </code>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-gray-600 text-xs">{log.component}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${severityBadge[log.severity] || 'bg-gray-100 text-gray-800'}`}>
                      {log.severity.toUpperCase()}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Info */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          <strong>Audit Logs:</strong> These logs track system events including user actions, model invocations,
          privacy checks, and security alerts. Events are retained for 90 days and can be exported for compliance.
        </p>
      </div>
    </div>
  );
};
