import React, { useState, useEffect, useCallback } from 'react';
import {
  AlertOctagon,
  Cloud,
  Radio,
  Cpu,
  RefreshCw,
  Send,
  ExternalLink,
  Info,
  Clock,
  ShieldCheck,
  AlertTriangle
} from 'lucide-react';

import MetricCard from './components/MetricCard';
import TimelineChart from './components/TimelineChart';
import LogViewer from './components/LogViewer';
import AwsStatusModal from './components/AwsStatusModal';

export default function App() {
  const [totalErrors, setTotalErrors] = useState(0);
  const [recentLogs, setRecentLogs] = useState([]);
  const [timelineData, setTimelineData] = useState([]);
  const [awsStatus, setAwsStatus] = useState(null);
  const [mqttStatus, setMqttStatus] = useState(null);

  const [loading, setLoading] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [publishMessage, setPublishMessage] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [autoRefreshSecs, setAutoRefreshSecs] = useState(15); // default 15s
  const [isAwsModalOpen, setIsAwsModalOpen] = useState(false);

  // Fetch all dashboard data from FastAPI backend
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // Parallel requests to backend endpoints
      const [awsRes, errorsRes, recentRes, timelineRes, mqttRes] = await Promise.allSettled([
        fetch('/api/aws/status').then(r => r.json()),
        fetch('/api/logs/errors?hours=1').then(r => r.json()),
        fetch('/api/logs/recent?hours=1&limit=50').then(r => r.json()),
        fetch('/api/logs/timeline?hours=1&bucket_minutes=5').then(r => r.json()),
        fetch('/api/mqtt/status').then(r => r.json())
      ]);

      if (awsRes.status === 'fulfilled') setAwsStatus(awsRes.value);
      if (errorsRes.status === 'fulfilled') setTotalErrors(errorsRes.value?.error_count ?? 0);
      if (recentRes.status === 'fulfilled') setRecentLogs(recentRes.value?.events ?? []);
      if (timelineRes.status === 'fulfilled') setTimelineData(timelineRes.value?.timeline ?? []);
      if (mqttRes.status === 'fulfilled') setMqttStatus(mqttRes.value);

      setLastUpdated(new Date());
    } catch (err) {
      console.error("Dashboard refresh error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh interval
  useEffect(() => {
    if (!autoRefreshSecs || autoRefreshSecs === 0) return;
    const interval = setInterval(() => {
      fetchData();
    }, autoRefreshSecs * 1000);
    return () => clearInterval(interval);
  }, [autoRefreshSecs, fetchData]);

  // Manual MQTT publish
  const handlePublishMqtt = async () => {
    setPublishing(true);
    setPublishMessage(null);
    try {
      const res = await fetch('/api/mqtt/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error_count: totalErrors })
      });
      const data = await res.json();
      if (data.success) {
        setPublishMessage({ type: 'success', text: `Sent count (${data.error_count}) to MQTT topic!` });
        // Refresh MQTT status
        const mRes = await fetch('/api/mqtt/status');
        setMqttStatus(await mRes.json());
      } else {
        setPublishMessage({ type: 'error', text: data.error || 'Failed to publish to MQTT' });
      }
    } catch (err) {
      setPublishMessage({ type: 'error', text: err.message });
    } finally {
      setPublishing(false);
      setTimeout(() => setPublishMessage(null), 4000);
    }
  };

  const isAwsConnected = awsStatus?.connected;

  return (
    <div className="dashboard-root">
      {/* Top Navigation Bar */}
      <header className="navbar">
        <div className="nav-brand">
          <div className="brand-badge">
            <span className="live-indicator" />
            LIVE MONITOR
          </div>
          <h1 className="brand-title">Centralized Log Error Counter</h1>
          <span className="brand-subtitle">AWS CloudWatch • HiveMQ MQTT • ESP32</span>
        </div>

        <div className="nav-actions">
          {/* Last updated indicator */}
          <div className="last-updated-badge">
            <Clock size={13} />
            <span>
              {lastUpdated ? lastUpdated.toLocaleTimeString() : 'Updating...'}
            </span>
          </div>

          {/* Auto-refresh interval dropdown */}
          <div className="refresh-select-wrap">
            <label htmlFor="refresh-select" className="refresh-label">Auto-refresh:</label>
            <select
              id="refresh-select"
              className="refresh-select"
              value={autoRefreshSecs}
              onChange={(e) => setAutoRefreshSecs(Number(e.target.value))}
            >
              <option value={0}>Paused</option>
              <option value={10}>Every 10s</option>
              <option value={15}>Every 15s</option>
              <option value={30}>Every 30s</option>
              <option value={60}>Every 60s</option>
            </select>
          </div>

          {/* Manual Refresh Button */}
          <button
            className={`btn btn-refresh ${loading ? 'loading' : ''}`}
            onClick={fetchData}
            disabled={loading}
            title="Refresh dashboard metrics"
          >
            <RefreshCw size={15} className={loading ? "spin-icon" : ""} />
            <span>Refresh</span>
          </button>

          {/* Trigger MQTT Sync to ESP32 */}
          <button
            className="btn btn-primary"
            onClick={handlePublishMqtt}
            disabled={publishing}
            title="Publish current error count to ESP32 via MQTT"
          >
            <Send size={15} />
            <span>{publishing ? "Syncing..." : "Sync to ESP32"}</span>
          </button>
        </div>
      </header>

      {/* Publish Toast Feedback */}
      {publishMessage && (
        <div className={`toast-banner ${publishMessage.type === 'success' ? 'toast-success' : 'toast-error'}`}>
          {publishMessage.type === 'success' ? <ShieldCheck size={16} /> : <AlertTriangle size={16} />}
          <span>{publishMessage.text}</span>
        </div>
      )}

      {/* Main Container */}
      <main className="dashboard-content">
        {/* Metric Cards Grid */}
        <section className="metrics-grid">
          {/* Card 1: Total Errors */}
          <MetricCard
            title="Total Errors (Last 1h)"
            value={totalErrors}
            badge="Past 60 mins"
            status={totalErrors > 0 ? "Requires Attention" : "System Healthy"}
            statusType={totalErrors > 0 ? "danger" : "success"}
            icon={AlertOctagon}
            subvalue={`Log Group: ${awsStatus?.log_group || '/centralized-log-error-counter'}`}
          />

          {/* Card 2: AWS CloudWatch Status */}
          <MetricCard
            title="AWS CloudWatch Logs"
            value={isAwsConnected ? "Connected" : (awsStatus?.status || "Checking...")}
            badge={awsStatus?.region || "us-east-1"}
            status={isAwsConnected ? "Boto3 Session Active" : "Click to view diagnostics"}
            statusType={isAwsConnected ? "success" : "warning"}
            icon={Cloud}
            subvalue={`Stream: ${awsStatus?.log_stream || 'demo-stream'}`}
            clickable={true}
            onClick={() => setIsAwsModalOpen(true)}
          />

          {/* Card 3: HiveMQ MQTT Broker */}
          <MetricCard
            title="HiveMQ MQTT Broker"
            value={mqttStatus?.connected ? "Online" : "Connecting..."}
            badge="Port 1883"
            status={`Topic: ${mqttStatus?.topic || 'centralized/logs/error-count'}`}
            statusType={mqttStatus?.connected ? "success" : "info"}
            icon={Radio}
            subvalue={
              mqttStatus?.last_published_count !== null && mqttStatus?.last_published_count !== undefined
                ? `Last Dispatched: ${mqttStatus.last_published_count} error(s)`
                : `Host: ${mqttStatus?.broker || 'broker.hivemq.com'}`
            }
          />

          {/* Card 4: ESP32 Hardware Display */}
          <MetricCard
            title="ESP32 + TM1637 Display"
            value={totalErrors.toString().padStart(4, '0')}
            badge="Wokwi Simulated"
            status="Listening to MQTT topic"
            statusType="info"
            icon={Cpu}
            subvalue="4-Digit 7-Segment Display"
          />
        </section>

        {/* Informational banner when AWS needs credentials */}
        {!isAwsConnected && (
          <div className="callout-banner">
            <div className="callout-content">
              <Info size={20} className="callout-icon" />
              <div>
                <strong>AWS CloudWatch Credentials Required:</strong> The backend is ready to query CloudWatch. Update <code className="code-inline">backend/.env</code> with your AWS credentials to view live AWS metrics.
              </div>
            </div>
            <button className="btn btn-outline" onClick={() => setIsAwsModalOpen(true)}>
              Setup Instructions
            </button>
          </div>
        )}

        {/* Charts & Log Viewer Row */}
        <div className="dashboard-grid">
          {/* Error Timeline Chart */}
          <TimelineChart
            data={timelineData}
            loading={loading}
            totalErrors={totalErrors}
          />

          {/* Recent Error Logs Terminal */}
          <LogViewer
            logs={recentLogs}
            loading={loading}
            logGroup={awsStatus?.log_group}
            logStream={awsStatus?.log_stream}
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-left">
          <span>Project: Centralized Log Error Counter</span>
          <span className="dot-sep">•</span>
          <span>Target: AWS CloudWatch us-east-1</span>
          <span className="dot-sep">•</span>
          <span>Simulation: ESP32 (Wokwi)</span>
        </div>
        <div className="footer-right">
          <span>FastAPI + Boto3 + React + Vite + HiveMQ MQTT</span>
        </div>
      </footer>

      {/* AWS Connection Modal */}
      <AwsStatusModal
        isOpen={isAwsModalOpen}
        onClose={() => setIsAwsModalOpen(false)}
        awsStatus={awsStatus}
      />
    </div>
  );
}
