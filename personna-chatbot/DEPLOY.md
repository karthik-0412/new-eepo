# Deployment with Docker Compose

This guide shows how to deploy the project using Docker Compose (single host). It builds two containers: `backend` (FastAPI) and `frontend` (built with Vite and served by nginx).

Important: Do NOT commit your API token to the repository. Use an env file on the host (not checked in) or use your cloud provider's secret store.

1. Create a production env file for the backend (example `backend/.env.production`):

```
HF_API_TOKEN=your_real_hf_token_here
HF_MODEL=google/flan-t5-small
```

2. Build and start with docker-compose:

```powershell
docker compose build
docker compose up -d
```

3. Verify:

- Frontend available at http://<your-host>:5173 (served by nginx)
- Backend API at http://<your-host>:8000/docs

4. Notes & alternatives
- If you prefer separate hosting: deploy the frontend to Vercel/Netlify and the backend to Render/Fly/Railway.
- For heavy model workloads, prefer using the Hugging Face Inference API or a managed GPU host.
