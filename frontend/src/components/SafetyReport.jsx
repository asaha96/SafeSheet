import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { AlertTriangle, CheckCircle, XCircle, Info, Copy } from 'lucide-react';
import { useState } from 'react';

const SafetyReport = ({ report }) => {
  const [copied, setCopied] = useState(false);

  if (!report || !report.data) {
    return null;
  }

  const data = report.data;
  const riskLevel = data.risk_level;
  const riskEmoji = {
    Low: '✅',
    Medium: '⚠️',
    High: '🚨',
  };

  const riskColor = {
    Low: '#10b981', // green
    Medium: '#f59e0b', // yellow
    High: '#ef4444', // red
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="safety-report">
      <div className="report-header">
        <h2>Safety Report</h2>
        <div
          className="risk-badge"
          style={{ backgroundColor: riskColor[riskLevel] + '20', color: riskColor[riskLevel] }}
        >
          <span className="risk-emoji">{riskEmoji[riskLevel]}</span>
          <span className="risk-level">Risk Level: {riskLevel}</span>
        </div>
      </div>

      <div className="report-section">
        <h3>
          <Info size={20} />
          Statement Information
        </h3>
        <div className="info-grid">
          <div className="info-item">
            <label>Statement Type:</label>
            <span>{data.statement_type}</span>
          </div>
          <div className="info-item">
            <label>Tables Affected:</label>
            <span>{data.impact?.tables_affected || 0}</span>
          </div>
          <div className="info-item">
            <label>Columns Affected:</label>
            <span>{data.impact?.columns_affected || 0}</span>
          </div>
          <div className="info-item">
            <label>Has WHERE Clause:</label>
            <span>{data.impact?.has_where_clause ? 'Yes' : 'No'}</span>
          </div>
        </div>
      </div>

      {data.impact?.tables && data.impact.tables.length > 0 && (
        <div className="report-section">
          <h3>Affected Tables</h3>
          <div className="tables-list">
            {data.impact.tables.map((table, idx) => (
              <span key={idx} className="table-tag">
                {table}
              </span>
            ))}
          </div>
        </div>
      )}

      {data.warnings && data.warnings.length > 0 && (
        <div className="report-section warnings-section">
          <h3>
            <AlertTriangle size={20} />
            Warnings
          </h3>
          <div className="warnings-list">
            {data.warnings.map((warning, idx) => (
              <div key={idx} className="warning-item">
                {warning}
              </div>
            ))}
          </div>
        </div>
      )}

      {data.explanation && (
        <div className="report-section">
          <h3>Explanation</h3>
          <p className="explanation-text">{data.explanation}</p>
        </div>
      )}

      {data.rollback_script && (
        <div className="report-section rollback-section">
          <div className="section-header-with-action">
            <h3>Rollback Script</h3>
            <button
              className="copy-button"
              onClick={() => copyToClipboard(data.rollback_script)}
              title="Copy to clipboard"
            >
              <Copy size={16} />
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <div className="code-block">
            <SyntaxHighlighter
              language="sql"
              style={vscDarkPlus}
              customStyle={{ margin: 0, borderRadius: '8px' }}
            >
              {data.rollback_script}
            </SyntaxHighlighter>
          </div>
        </div>
      )}

      {data.rollback_error && (
        <div className="report-section error-section">
          <h3>
            <XCircle size={20} />
            Rollback Generation Error
          </h3>
          <p className="error-text">{data.rollback_error}</p>
        </div>
      )}

      {data.dry_run && (
        <div className="report-section">
          <h3>Dry Run Simulation</h3>
          <div className="dry-run-info">
            <div className="info-item">
              <label>Simulation Status:</label>
              <span>
                {data.dry_run.simulation_successful ? (
                  <CheckCircle size={16} className="success-icon" />
                ) : (
                  <XCircle size={16} className="error-icon" />
                )}
                {data.dry_run.simulation_successful ? 'Successful' : 'Limited (no tables)'}
              </span>
            </div>
            {data.dry_run.estimated_rows_affected !== null && (
              <div className="info-item">
                <label>Estimated Rows Affected:</label>
                <span>{data.dry_run.estimated_rows_affected}</span>
              </div>
            )}
            {data.dry_run.note && (
              <div className="info-item" style={{ gridColumn: '1 / -1', padding: '0.75rem', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '6px', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                <Info size={16} style={{ marginRight: '0.5rem', display: 'inline-block', color: '#60a5fa' }} />
                <span style={{ color: '#cbd5e1' }}>{data.dry_run.note}</span>
              </div>
            )}
            {data.dry_run.error && (
              <div className="error-text" style={{ 
                background: data.dry_run.note ? 'rgba(59, 130, 246, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                color: data.dry_run.note ? '#60a5fa' : '#fca5a5',
                border: data.dry_run.note ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)'
              }}>
                {data.dry_run.error}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SafetyReport;

