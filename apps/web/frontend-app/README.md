# BADHABINOT Web Client

React + TypeScript frontend for the BADHABINOT platform.

## Local development

1. Copy `.env.example` to `.env`.
2. Start the backend stack from the repository root.
3. Run:

```powershell
npm install
npm run dev
```

The app runs at `http://localhost:5173` and proxies API traffic to `http://localhost:8080` by default.

## Production-like local container

The root Docker Compose file can also build and serve this client through Nginx.
