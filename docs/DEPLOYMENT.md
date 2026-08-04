# Deployment Guide: Nerve Healthcare Assistant

This guide explains how to deploy the **Nerve Healthcare Assistant** application:
- **Backend API**: Render (via Docker / Blueprint)
- **Frontend App**: Vercel (via GitHub integration)

---

## 1. Deploying the Backend on Render

### Method A: Render Blueprints (Recommended)
1. Push your latest code changes to your GitHub repository: `https://github.com/thrithick5/Nerve_Healthcare_Assistant`.
2. Log in to [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** -> **Blueprint**.
4. Connect your GitHub repository (`thrithick5/Nerve_Healthcare_Assistant`).
5. Render will automatically read `render.yaml`.
6. Fill in the required secret environment variables in the Render Dashboard:
   - `MISTRAL_API_KEY`: Your Mistral AI key.
   - `GOOGLE_CLIENT_ID`: Your Google OAuth Client ID.
   - `SECRET_KEY`: A secure random string for JWT session tokens.
   - `CORS_ORIGINS_EXTRA`: (Optional) Your Vercel frontend URL, e.g. `https://your-app-name.vercel.app`.
7. Click **Apply**. Render will build the Docker container and deploy the backend.

### Method B: Manual Web Service Setup
1. Click **New +** -> **Web Service**.
2. Select repository `Nerve_Healthcare_Assistant`.
3. Set Environment to **Docker**.
4. Set Docker Command to `Dockerfile Path`: `./backend/Dockerfile` and Build Context: `./backend`.
5. Health Check Path: `/api/v1/health`.
6. Add environment variables listed in `backend/.env.example`.

Once deployed, copy your Render backend URL (e.g. `https://nerve-healthcare-backend.onrender.com`).

---

## 2. Deploying the Frontend on Vercel

1. Log in to [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New...** -> **Project**.
3. Import your GitHub repository (`thrithick5/Nerve_Healthcare_Assistant`).
4. In the project setup panel:
   - **Framework Preset**: Vite
   - **Root Directory**: Select `frontend` (or click **Edit** and choose the `frontend` folder).
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

- **CORS Errors**: Check `CORS_ORIGINS_EXTRA` in Render. Note that Vercel domain URLs (`https://*.vercel.app`) are automatically allowed by backend regex. If using a custom domain, add it to `CORS_ORIGINS_EXTRA`.
- **404 on Refresh**: `vercel.json` rewrites are configured to map all requests to `/index.html`. Make sure `frontend/vercel.json` is included in your git commit.
- **Database Persistence**: SQLite database runs inside the container data volume. For production deployments with persistent database needs across rebuilds, configure a Render PostgreSQL database URL in `DATABASE_URL`.
