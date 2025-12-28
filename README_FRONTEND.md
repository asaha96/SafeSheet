# SafeSheet - Full Stack Application

SafeSheet now includes both a command-line interface and a modern web frontend!

## Architecture

```
SafeSheet/
├── backend/          # FastAPI backend API
│   ├── main.py       # API server
│   └── requirements.txt
├── frontend/         # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── SQLEditor.jsx
│   │   │   └── SafetyReport.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   └── App.jsx
│   └── package.json
└── safesheet/        # Core SafeSheet library
```

## Quick Start

### Option 1: Use Startup Scripts

**Terminal 1 - Backend:**
```bash
./start_backend.sh
```

**Terminal 2 - Frontend:**
```bash
./start_frontend.sh
```

### Option 2: Manual Setup

**1. Start Backend API:**
```bash
cd backend
source ../venv/bin/activate
pip install -r requirements.txt
python main.py
```
Backend runs on `http://localhost:8000`

**2. Start Frontend:**
```bash
cd frontend
npm install
npm run dev
```
Frontend runs on `http://localhost:5173`

## Features

### Web Interface
- ✨ Modern dark-themed UI
- 📝 Monaco Editor with SQL syntax highlighting
- ⚡ Real-time SQL analysis
- 📊 Visual safety reports with risk indicators
- 🔄 Rollback script generation
- 🧪 Dry-run simulation results
- 📋 One-click copy to clipboard
- 🎯 Example queries for quick testing

### API Endpoints
- `GET /` - API information
- `GET /health` - Health check
- `POST /analyze` - Analyze SQL statement

## API Usage

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "UPDATE users SET status = '\''inactive'\''",
    "include_rollback": true,
    "include_dry_run": true
  }'
```

## Development

### Backend Development
- FastAPI with automatic API documentation at `http://localhost:8000/docs`
- CORS enabled for frontend
- Error handling and validation

### Frontend Development
- React 18 with Vite
- Hot Module Replacement (HMR)
- Monaco Editor for SQL editing
- Responsive design

## Production Build

**Frontend:**
```bash
cd frontend
npm run build
```

**Backend:**
The backend can be deployed with any ASGI server (uvicorn, gunicorn, etc.)

## Environment Variables

**Backend (.env in project root):**
```
ANTHROPIC_API_KEY=your_key_here
# OR
OPENAI_API_KEY=your_key_here
```

**Frontend (.env in frontend/):**
```
VITE_API_URL=http://localhost:8000
```

## Troubleshooting

1. **CORS errors**: Make sure backend is running and CORS is configured
2. **API connection failed**: Check `VITE_API_URL` in frontend `.env`
3. **Monaco Editor not loading**: Ensure `@monaco-editor/react` is installed
4. **Backend import errors**: Make sure you're in the virtual environment

