# BADHABINOT Web Client

React + TypeScript frontend for the BADHABINOT platform.

## Local development

1. Configure the repository root `.env`.
2. Start the backend stack from the repository root.
3. Run:

```powershell
npm install
npm run dev
```

The app runs at `http://localhost:5173` and proxies API traffic to `http://localhost:8080` by default.

## Production-like local container

From the repository root:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Then open `http://localhost:3000`.

The frontend build reads `VITE_API_BASE_URL` from the repository root `.env`.

Container flow:

- `frontend-app` builds the Vite app into static assets.
- Nginx serves the SPA on port `80` inside the container and publishes it to `FRONTEND_PORT` on the host.
- `/api/*` and `/actuator/*` are proxied by Nginx to `api-gateway:8080`, so the browser uses the same `localhost:3000` origin for UI and API traffic.
