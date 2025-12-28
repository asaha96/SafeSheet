import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const analyzeSQL = async (sql, options = {}) => {
  const { includeRollback = true, includeDryRun = true, sampleData = null } = options;
  
  try {
    const response = await api.post('/analyze', {
      sql,
      include_rollback: includeRollback,
      include_dry_run: includeDryRun,
      sample_data: sampleData,
    });
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.error || 
      error.response?.data?.detail || 
      'Failed to analyze SQL'
    );
  }
};

export const healthCheck = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    throw new Error('API health check failed');
  }
};

