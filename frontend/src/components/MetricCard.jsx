import React from 'react';

export default function MetricCard({
  title,
  value,
  subvalue,
  status,
  statusType = 'neutral', // 'success', 'warning', 'danger', 'info'
  icon: Icon,
  badge,
  onClick,
  clickable = false
}) {
  return (
    <div 
      className={`metric-card ${clickable ? 'clickable' : ''}`}
      onClick={clickable ? onClick : undefined}
    >
      <div className="metric-header">
        <span className="metric-title">{title}</span>
        {Icon && (
          <div className={`metric-icon-wrap ${statusType}`}>
            <Icon size={20} />
          </div>
        )}
      </div>

      <div className="metric-body">
        <div className="metric-value-row">
          <span className="metric-value">{value}</span>
          {badge && (
            <span className={`metric-badge ${statusType}`}>
              {badge}
            </span>
          )}
        </div>

        {subvalue && <div className="metric-subvalue">{subvalue}</div>}
        {status && <div className={`metric-status ${statusType}`}>{status}</div>}
      </div>
    </div>
  );
}
