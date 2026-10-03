# Deployment Guide: Nerve Healthcare Assistant

This guide explains how to deploy the **Nerve Healthcare Assistant** application:
- **Backend API**: Render (via Web Service - Free Tier, No Card Required)
- **Frontend App**: Vercel (via GitHub integration)

---

## 1. Deploying the Backend on Render (Free Tier - No Card Required)

Use the **Web Service** option on Render to deploy completely free without providing credit card details:

1. Log in to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** -> **Web Service**.
3. Select **Build and deploy from a Git repository**, click **Next**, and connect your GitHub repository (`thrithick5/Nerve_Healthcare_Assistant`).
4. Configure the settings as follows:
   - **Name**: `nerve-healthcare-backend` (or any name you choose)
   - **Language**: `Docker`
   - **Branch**: `main`
   - **Region**: **Must match the PostgreSQL database's region** (see the warning below)
   - **Root Directory**: Leave blank (or `./`)
   - **Dockerfile Path**: `./backend/Dockerfile`
   - **Docker Context**: `./backend`
   - **Instance Type**: Select **Free** ($0/month)
5. Expand **Advanced Settings**:
   - **Health Check Path**: `/api/v1/health`
6. Under **Environment Variables**, add the following key-value pairs:
   - `CHROMA_PERSIST_DIR` = `/app/data/chroma_db`
   - `COLLECTION_NAME` = `medical_knowledge`
   - `MISTRAL_MODEL` = `mistral-large-latest`
   - `MISTRAL_EMBEDDING_MODEL` = `mistral-embed`
   - `DEBUG` = `false`
   - `MISTRAL_API_KEY` = `<your-mistral-api-key>`
   - `GOOGLE_CLIENT_ID` = `388676578583-74qqn1h809fk1j9qckrajakt78hutanl.apps.googleusercontent.com`
   - `SECRET_KEY` = `<generate-a-random-secret-key>`
   - `CORS_ORIGINS_EXTRA` = `https://your-vercel-app-name.vercel.app` (Add after deploying on Vercel)

7. Click **Create Web Service**. Render will start building the Docker container and deploy your backend.

> **Do not set `DATABASE_URL` manually.** The app defaults to local SQLite. Set it
> only if you want PostgreSQL — see the section below for the region requirement.

### Using PostgreSQL instead of SQLite

To use a Render PostgreSQL database, set `DATABASE_URL` to its connection string.

**The web service and the database must be in the same region.** Render provides
each database with an *internal* URL whose hostname only resolves from services in
the **same workspace and region**. If the regions differ, startup fails with:

```
psycopg2.OperationalError: could not translate host name "dpg-..." to address
```

Fix it by moving one of the two resources to the other's region in the Render
dashboard, or by using the database's **external** URL (add `?sslmode=require`).

The container already handles this failure gracefully: `scripts/run_migrations.py`
retries with backoff, then starts the API anyway, so a database outage no longer
takes the whole service down. Requests recover automatically once the database
is reachable.

Check which host you are using:

```bash
# Internal (only works same region): dpg-xxxx-a
# External (works anywhere):        dpg-xxxx
```
8. Once deployed, copy your Render backend URL (e.g., `https://nerve-healthcare-backend.onrender.com`).

---

## 2. Deploying the Frontend on Vercel

1. Log in to [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New...** -> **Project**.
3. Import your GitHub repository (`thrithick5/Nerve_Healthcare_Assistant`).
4. In the project setup panel:
   - **Framework Preset**: Vite
   - **Root Directory**: Click **Edit** and select `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Under **Environment Variables**, add:
   - `VITE_API_BASE_URL`: `https://<your-render-backend-url>.onrender.com/api` (replace with your actual Render URL).
   - `VITE_GOOGLE_CLIENT_ID`: `388676578583-74qqn1h809fk1j9qckrajakt78hutanl.apps.googleusercontent.com`
6. Click **Deploy**.

---

## 3. Post-Deployment Verification & Testing

1. Open your Vercel URL (e.g. `https://nerve-healthcare-assistant.vercel.app`).
2. Test user registration / login.
3. Test page refresh on `/chat` or `/history` (verifying SPA rewrites work correctly).
4. Verify chat queries and medical document searching work against the Render backend.

---

## Troubleshooting & Tips

### Login fails with "Network error. Please check your connection."

This message is emitted by the browser-facing API client whenever a request
completes with **no response object**. Historically a *server* fault produced it:
when the database was unreachable, `/auth/login` raised an unhandled
`OperationalError`. Starlette's `ServerErrorMiddleware` sits outside
`CORSMiddleware` and answered with a bare `text/plain` 500 carrying **no
`access-control-allow-origin` header**, so the browser discarded the response.

Database outages now return `503` with a JSON `detail` and correct CORS headers,
so the UI shows *"Database temporarily unavailable. Please try again in a moment."*
instead of blaming the user's connection. Check `/api/v1/health` for the truth:

```json
{"status": "healthy", "version": "2.0.0", "database": "down"}
```

`status` deliberately stays `healthy` while the database is down: Render restarts
any service whose health path stops returning 2xx, which would turn a database
outage into a crash loop.

### Diagnosing an unreachable database

1. Check `database` in `/api/v1/health`.
2. Read the host from the startup logs (passwords are redacted):
   `ERROR [startup.migrations] database unreachable ... host 'dpg-XXXX-a'`.
3. The `-a` suffix marks a **Render internal** hostname. It resolves only inside
   the same Render workspace **and region**, never from the public internet, so
   a public `nslookup` failing is expected and not proof of a fault.
4. Check that the database and web service share a region, and that the
   database has not been deleted. Free Postgres instances expire after 30 days.
5. If the internal hostname no longer resolves publicly *and* the service is in
   the database's region, the instance is gone — provision a new one.

### Removing a manually-set `DATABASE_URL`

If `DATABASE_URL` is set as a manual environment variable on the Render web
service, it **overrides** the value that `fromDatabase.connectionString`
injects. A stale manual value therefore survives a Blueprint re-apply and keeps
pointing at a deleted database. Delete the manual variable so the Blueprint can
inject the current internal URL, or set it to the new database's external URL
with `?sslmode=require`.

- **CORS Errors**: Vercel domain URLs (`https://*.vercel.app`) are automatically allowed by backend regex. If using a custom domain, add it to `CORS_ORIGINS_EXTRA` in Render.
- **404 on Refresh**: `vercel.json` rewrites map all requests to `/index.html`.
- **Blank page / API calls hitting Vercel**: `VITE_API_BASE_URL` is unset, so the client falls back to `/api` on the frontend origin, where the SPA rewrite returns `index.html` instead of JSON. Set it on Vercel to `https://<backend>.onrender.com/api`. A POST to such a path returns `405` from Vercel's static hosting.
- **Render Free Tier Spin-Down**: Free instances on Render spin down after 15 minutes of inactivity. The first request after spin-down may take ~30 seconds to respond as the instance wakes up.
