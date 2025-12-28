# SafeSheet Frontend

React frontend for SafeSheet - SQL Safety Analysis Tool.

## Features

- 🎨 Modern, dark-themed UI
- 📝 Monaco Editor for SQL editing with syntax highlighting
- ⚡ Real-time SQL analysis
- 📊 Comprehensive safety reports with risk indicators
- 🔄 Rollback script generation
- 🧪 Dry-run simulation results
- 📋 Copy-to-clipboard functionality

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Configuration

Create a `.env` file (or use the existing one) to configure the API URL:

```
VITE_API_URL=http://localhost:8000
```

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Development

- Uses Vite for fast development
- React 18
- Monaco Editor for SQL editing
- Axios for API calls
- Lucide React for icons
- React Syntax Highlighter for code display
