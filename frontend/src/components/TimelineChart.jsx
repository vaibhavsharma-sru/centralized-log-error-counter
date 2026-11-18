import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { Activity, Clock } from 'lucide-react';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        <p className="tooltip-time"><Clock size={12} /> {label}</p>
        <p className="tooltip-value">
          <span className="tooltip-dot" />
          Errors: <strong>{payload[0].value}</strong>
        </p>
      </div>
    );
  }
  return null;
};

export default function TimelineChart({ data = [], loading = false, totalErrors = 0 }) {
  return (
    <div className="card timeline-card">
      <div className="card-header">
        <div className="card-title-group">
          <Activity size={18} className="card-icon text-accent" />
          <div>
            <h3 className="card-title">Error Occurrence Timeline</h3>
            <p className="card-subtitle">Last 60 minutes aggregated in 5-minute intervals</p>
          </div>
        </div>
        <div className="timeline-meta">
          <span className="timeline-total-badge">
            Total in window: <strong>{totalErrors}</strong>
          </span>
        </div>
      </div>

      <div className="chart-container">
        {loading ? (
          <div className="chart-placeholder">
            <div className="spinner" />
            <span>Loading timeline data...</span>
          </div>
        ) : !data || data.length === 0 ? (
          <div className="chart-placeholder">
            <span>No timeline events recorded</span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="errorGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.45} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#262a36" vertical={false} />
              <XAxis 
                dataKey="time" 
                stroke="#64748b" 
                fontSize={11} 
                tickLine={false}
                axisLine={{ stroke: '#262a36' }}
              />
              <YAxis 
                stroke="#64748b" 
                fontSize={11} 
                tickLine={false}
                axisLine={{ stroke: '#262a36' }}
                allowDecimals={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area 
                type="monotone" 
                dataKey="errors" 
                stroke="#ef4444" 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#errorGradient)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
