import { useState } from 'react';
import SQLEditor from './components/SQLEditor';
import SafetyReport from './components/SafetyReport';
import LangChainReport from './components/LangChainReport';
import { analyzeSQL, validateSQL } from './services/api';
import { AlertCircle, Loader2, Sparkles } from 'lucide-react';
import logo from './assets/logo.png';
import './App.css';

function App() {
  const [sql, setSql] = useState('');
  const [report, setReport] = useState(null);
  const [langchainReport, setLangchainReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [langchainLoading, setLangchainLoading] = useState(false);
  const [error, setError] = useState(null);
  const [langchainError, setLangchainError] = useState(null);
  const [includeRollback, setIncludeRollback] = useState(true);
  const [includeDryRun, setIncludeDryRun] = useState(true);
  const [useLangChain, setUseLangChain] = useState(false);

  const handleAnalyze = async (sqlToAnalyze) => {
    if (useLangChain) {
      handleLangChainValidate(sqlToAnalyze);
    } else {
      setLoading(true);
      setError(null);
      setReport(null);
      setLangchainReport(null);

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
    }
  };

  const handleLangChainValidate = async (sqlToAnalyze) => {
    setLangchainLoading(true);
    setLangchainError(null);
    setLangchainReport(null);
    setReport(null);

    try {
      const result = await validateSQL(sqlToAnalyze);
      setLangchainReport(result);
    } catch (err) {
      setLangchainError(err.message || 'Failed to validate SQL with LangChain');
      console.error('LangChain validation error:', err);
    } finally {
      setLangchainLoading(false);
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

  const loadExample = async (exampleSql) => {
    setSql(exampleSql);
    setError(null);
    setLangchainError(null);
    setReport(null);
    setLangchainReport(null);
    
    // Automatically analyze the example query
    // Small delay to ensure state is updated
    setTimeout(() => {
      handleAnalyze(exampleSql);
    }, 100);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="logo-container">
            <img src={logo} alt="SafeSheet Logo" className="logo-image" />
            <h1>SafeSheet</h1>
          </div>
          <p>SQL Safety Analysis & Rollback Generation</p>
        </div>
      </header>

      <main className="app-main">
        <div className="container">
          <div className="options-panel">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={useLangChain}
                onChange={(e) => setUseLangChain(e.target.checked)}
              />
              <span>
                <Sparkles size={16} style={{ marginRight: '0.5rem', display: 'inline-block' }} />
                Use LangChain Validation
              </span>
            </label>
            {!useLangChain && (
              <>
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
              </>
            )}
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
            isLoading={loading || langchainLoading}
          />

          {(loading || langchainLoading) && (
            <div className="loading-container">
              <Loader2 className="spinner" size={32} />
              <p>{useLangChain ? 'Validating SQL with LangChain...' : 'Analyzing SQL...'}</p>
            </div>
          )}

          {error && (
            <div className="error-container">
              <AlertCircle size={20} />
              <p>{error}</p>
            </div>
          )}

          {langchainError && (
            <div className="error-container">
              <AlertCircle size={20} />
              <p>{langchainError}</p>
            </div>
          )}

          {report && !useLangChain && <SafetyReport report={report} />}

          {langchainReport && useLangChain && (
            <LangChainReport report={langchainReport} />
          )}
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
