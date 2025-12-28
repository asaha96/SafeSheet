import { useState } from 'react';
import SQLEditor from './components/SQLEditor';
import SafetyReport from './components/SafetyReport';
import { analyzeSQL } from './services/api';
import { AlertCircle, Loader2 } from 'lucide-react';
import './App.css';

function App() {
  const [sql, setSql] = useState('');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [includeRollback, setIncludeRollback] = useState(true);
  const [includeDryRun, setIncludeDryRun] = useState(true);

  const handleAnalyze = async (sqlToAnalyze) => {
    setLoading(true);
    setError(null);
    setReport(null);

    try {
      const result = await analyzeSQL(sqlToAnalyze, {
        includeRollback,
        includeDryRun,
      });
      setReport(result);
    } catch (err) {
      setError(err.message || 'Failed to analyze SQL');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const exampleQueries = [
    {
      name: 'Dangerous UPDATE',
      sql: "UPDATE users SET status = 'inactive'",
    },
    {
      name: 'Safe UPDATE',
      sql: "UPDATE users SET status = 'active' WHERE id = 1",
    },
    {
      name: 'DROP TABLE',
      sql: 'DROP TABLE users',
    },
    {
      name: 'DELETE without WHERE',
      sql: 'DELETE FROM orders',
    },
  ];

  const loadExample = (exampleSql) => {
    setSql(exampleSql);
    setError(null);
    setReport(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>🛡️ SafeSheet</h1>
          <p>SQL Safety Analysis & Rollback Generation</p>
        </div>
      </header>

      <main className="app-main">
        <div className="container">
          <div className="options-panel">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={includeRollback}
                onChange={(e) => setIncludeRollback(e.target.checked)}
              />
              <span>Generate Rollback Script</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={includeDryRun}
                onChange={(e) => setIncludeDryRun(e.target.checked)}
              />
              <span>Enable Dry Run Simulation</span>
            </label>
          </div>

          <div className="examples-panel">
            <h4>Example Queries:</h4>
            <div className="examples-list">
              {exampleQueries.map((example, idx) => (
                <button
                  key={idx}
                  className="example-button"
                  onClick={() => loadExample(example.sql)}
                >
                  {example.name}
                </button>
              ))}
            </div>
          </div>

          <SQLEditor
            value={sql}
            onChange={setSql}
            onAnalyze={handleAnalyze}
            isLoading={loading}
          />

          {loading && (
            <div className="loading-container">
              <Loader2 className="spinner" size={32} />
              <p>Analyzing SQL...</p>
            </div>
          )}

          {error && (
            <div className="error-container">
              <AlertCircle size={20} />
              <p>{error}</p>
            </div>
          )}

          {report && <SafetyReport report={report} />}
        </div>
      </main>

      <footer className="app-footer">
        <p>
          SafeSheet - Prevent accidental data loss with SQL safety analysis
        </p>
      </footer>
    </div>
  );
}

export default App;
