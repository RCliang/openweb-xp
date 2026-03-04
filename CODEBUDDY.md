# CODEBUDDY.md

This file provides guidance to CodeBuddy Code when working with code in this repository.

## Project Overview

Open WebUI is a self-hosted AI platform with a Python FastAPI backend and SvelteKit frontend. It supports multiple LLM backends (Ollama, OpenAI-compatible APIs) and includes RAG capabilities, real-time collaboration, and an extensible tools/functions system.

## Development Commands

### Backend
```bash
# Start development server (from project root)
cd backend && uvicorn open_webui.main:app --reload --port 8080

# Run backend tests
pytest backend/open_webui/test/

# Format backend code
black backend/ --exclude ".venv/|/venv/"

# Lint backend code
pylint backend/
```

### Frontend
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production (outputs to build/)
npm run build

# Type checking
npm run check

# Lint frontend
npm run lint

# Format frontend code
npm run format

# Run frontend tests
npm run test:frontend

# E2E tests (Cypress)
npm run cy:open
```

### Docker
```bash
# Build image
docker build -t open-webui .

# Run with Docker Compose
docker-compose up -d
```

## Architecture

### Backend Structure (`backend/open_webui/`)
- `main.py` - FastAPI application entry point, middleware setup, router registration
- `config.py` - Runtime configuration management with persistent settings
- `env.py` - Environment variable definitions and initialization
- `routers/` - API route handlers (auths, chats, models, ollama, openai, retrieval, etc.)
- `models/` - SQLAlchemy database models with Pydantic schemas
- `internal/` - Database connection, migrations (Alembic + legacy peewee)
- `socket/` - Socket.IO server for real-time features
- `retrieval/` - RAG/document retrieval system with vector store support
- `utils/` - Utility functions (auth, audit, logger, etc.)

API patterns:
- Core APIs: `/api/v1/{resource}`
- Model proxies: `/ollama/*`, `/openai/*`, `/api/chat/completions`
- WebSocket: `/ws` (Socket.IO)

### Frontend Structure (`src/`)
- `routes/` - SvelteKit file-based routing
  - `(app)/` - Authenticated routes (chat interface, admin, workspace)
  - `auth/` - Authentication pages
- `lib/`
  - `stores/index.ts` - Svelte stores for state management (config, user, models, chats, etc.)
  - `apis/` - API client modules matching backend routers
  - `components/` - Svelte components organized by feature (chat/, admin/, common/)
  - `utils/` - Frontend utilities

### Database
- ORM: SQLAlchemy with Pydantic models
- Default: SQLite at `{DATA_DIR}/webui.db`
- Options: PostgreSQL, SQLCipher
- Migrations: Alembic (`backend/open_webui/migrations/`)

### Configuration
- Environment variables defined in `backend/open_webui/env.py`
- Persistent runtime config via `PersistentConfig` class (stored in DB)
- Redis support for distributed sessions and WebSocket scaling

### Real-time Features
- Socket.IO server at `/ws`
- Used for: chat updates, active users, collaborative editing (Yjs/CRDT), channels

## Key Patterns

### Adding a New API Endpoint
1. Create route in `backend/open_webui/routers/{resource}.py`
2. Register in `backend/open_webui/main.py` imports
3. Create API client in `src/lib/apis/{resource}/index.ts`
4. Update stores if needed in `src/lib/stores/index.ts`

### Database Model Pattern
Each model file in `models/` typically contains:
- SQLAlchemy Table class (Base)
- Pydantic models for validation/response
- Table class with CRUD methods

### Chat Processing Flow
1. Request arrives at `/api/chat/completions`
2. Middleware processes payload (tools, RAG, filters)
3. Dispatched to appropriate backend (Ollama/OpenAI/custom)
4. Streaming response via SSE
5. Real-time updates via Socket.IO

## Python Requirements
- Python 3.11 - 3.12 (not 3.13+)
- Node.js 18.13.0 - 22.x.x

## Testing
- Backend: pytest (tests in `backend/open_webui/test/`)
- Frontend: vitest
- E2E: Cypress (`cypress/e2e/`)
