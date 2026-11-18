import React, { useState } from 'react';
import { Terminal, Search, Copy, Check, Filter } from 'lucide-react';

export default function LogViewer({ logs = [], loading = false, logGroup = "", logStream = "" }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [copiedId, setCopiedId] = useState(null);

  const filteredLogs = logs.filter(log => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      (log.message && log.message.toLowerCase().includes(term)) ||
      (log.log_stream && log.log_stream.toLowerCase().includes(term)) ||
      (log.timestamp_display && log.timestamp_display.toLowerCase().includes(term))
    );
  });

  const handleCopy = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="card log-viewer-card">
      <div className="card-header">
        <div className="card-title-group">
          <Terminal size={18} className="card-icon text-danger" />
          <div>
            <h3 className="card-title">Recent CloudWatch Error Logs</h3>
            <p className="card-subtitle">
              Live entries from <span className="highlight-code">{logGroup || '/centralized-log-error-counter'}</span> / <span className="highlight-code">{logStream || 'demo-stream'}</span>
            </p>
          </div>
        </div>

        <div className="log-search-wrap">
          <Search size={14} className="search-icon" />
          <input
            type="text"
            className="log-search-input"
            placeholder="Search error messages..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="terminal-container">
        {loading ? (
          <div className="terminal-placeholder">
            <div className="spinner" />
            <span>Fetching CloudWatch log events...</span>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="terminal-placeholder">
            <span>{searchTerm ? "No error logs match your search filter." : "No ERROR logs found in the last hour."}</span>
          </div>
        ) : (
          <div className="terminal-log-list">
            {filteredLogs.map((log, index) => (
              <div key={log.event_id || index} className="terminal-log-row">
                <div className="log-meta">
                  <span className="log-badge-error">ERROR</span>
                  <span className="log-timestamp">{log.timestamp_display || new Date(log.timestamp).toISOString()}</span>
                  <span className="log-stream-badge">{log.log_stream}</span>
                </div>
                <div className="log-message-row">
                  <pre className="log-message">{log.message}</pre>
                  <button
                    className="copy-btn"
                    title="Copy log entry"
                    onClick={() => handleCopy(log.event_id || index, log.message)}
                  >
                    {copiedId === (log.event_id || index) ? (
                      <Check size={14} className="text-success" />
                    ) : (
                      <Copy size={14} />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card-footer">
        <span>Showing {filteredLogs.length} of {logs.length} error entries</span>
      </div>
    </div>
  );
}
