import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { loader } from '@monaco-editor/react';
import { Loader2 } from 'lucide-react';

// Configure Monaco Editor loader
loader.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' } });

const SQLEditor = ({ value, onChange, onAnalyze, isLoading }) => {
  const [sql, setSql] = useState(value || '');

  // Sync with external value changes (e.g., when example buttons are clicked)
  useEffect(() => {
    if (value !== undefined && value !== sql) {
      setSql(value || '');
    }
  }, [value]);

  const handleEditorChange = (newValue) => {
    setSql(newValue || '');
    if (onChange) {
      onChange(newValue || '');
    }
  };

  const handleAnalyze = () => {
    if (sql.trim()) {
      onAnalyze(sql);
    }
  };

  const handleKeyDown = (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
      e.preventDefault();
      handleAnalyze();
    }
  };

  return (
    <div className="sql-editor-container">
      <div className="editor-header">
        <h3>SQL Editor</h3>
        <div className="editor-actions">
          <button
            onClick={handleAnalyze}
            disabled={!sql.trim() || isLoading}
            className="analyze-button"
          >
            {isLoading ? (
              <>
                <Loader2 size={16} style={{ marginRight: '0.5rem', display: 'inline-block' }} />
                Analyzing...
              </>
            ) : (
              'Analyze SQL'
            )}
          </button>
          <span className="hint">Press Ctrl+Enter to analyze</span>
        </div>
      </div>
      <div className="editor-wrapper">
        <Editor
          height="400px"
          defaultLanguage="sql"
          language="sql"
          value={sql}
          onChange={handleEditorChange}
          onMount={(editor) => {
            editor.onKeyDown(handleKeyDown);
          }}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            wordWrap: 'on',
            automaticLayout: true,
            tabSize: 2,
            formatOnPaste: true,
            formatOnType: true,
          }}
        />
      </div>
    </div>
  );
};

export default SQLEditor;

