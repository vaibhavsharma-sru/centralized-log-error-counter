import React from 'react';
import { X, Cloud, Key, CheckCircle, AlertTriangle, ShieldCheck, Terminal } from 'lucide-react';

export default function AwsStatusModal({ isOpen, onClose, awsStatus }) {
  if (!isOpen) return null;

  const isConnected = awsStatus?.connected;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-group">
            <Cloud size={20} className={isConnected ? "text-success" : "text-warning"} />
            <h3>AWS CloudWatch Configuration & Status</h3>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          {/* Status Banner */}
          <div className={`status-banner ${isConnected ? 'banner-success' : 'banner-warning'}`}>
            {isConnected ? (
              <CheckCircle size={20} className="banner-icon" />
            ) : (
              <AlertTriangle size={20} className="banner-icon" />
            )}
            <div>
              <div className="banner-title">
                {isConnected ? "AWS Connected & Authenticated" : `Status: ${awsStatus?.status || 'NOT_CONNECTED'}`}
              </div>
              <div className="banner-desc">{awsStatus?.message}</div>
            </div>
          </div>

          {/* Details Table */}
          <div className="config-section">
            <h4 className="section-title">Current Environment Details</h4>
            <div className="config-grid">
              <div className="config-item">
                <span className="config-label">AWS Region</span>
                <span className="config-val">{awsStatus?.region || 'us-east-1'}</span>
              </div>
              <div className="config-item">
                <span className="config-label">Log Group</span>
                <span className="config-val">{awsStatus?.log_group || '/centralized-log-error-counter'}</span>
              </div>
              <div className="config-item">
                <span className="config-label">Log Stream</span>
                <span className="config-val">{awsStatus?.log_stream || 'demo-stream'}</span>
              </div>
              <div className="config-item">
                <span className="config-label">Log Group Exists</span>
                <span className="config-val">{awsStatus?.log_group_exists ? 'Yes' : 'No'}</span>
              </div>
              <div className="config-item">
                <span className="config-label">AWS Account ID</span>
                <span className="config-val">{awsStatus?.account_id || 'Not authenticated'}</span>
              </div>
              <div className="config-item">
                <span className="config-label">Credential Source</span>
                <span className="config-val">{awsStatus?.credentials_type || 'None'}</span>
              </div>
            </div>
          </div>

          {/* Configuration Instructions */}
          {!isConnected && (
            <div className="config-section">
              <h4 className="section-title"><Key size={14} /> How to configure AWS Credentials</h4>
              <p className="section-text">
                Update your <code className="code-inline">backend/.env</code> file with credentials from your AWS Management Console or AWS Academy Learner Lab:
              </p>
              <pre className="code-snippet">
{`AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=ASIA...
AWS_SECRET_ACCESS_KEY=...
# Required for AWS Academy / Learner Labs:
AWS_SESSION_TOKEN=IQoJb3JpZ2luX2Vj...

LOG_GROUP_NAME=/centralized-log-error-counter
LOG_STREAM_NAME=demo-stream`}
              </pre>
              <p className="section-text" style={{ marginTop: '8px' }}>
                Then run <code className="code-inline">python backend/generate_sample_logs.py</code> to create the Log Group and push sample test error entries!
              </p>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}
