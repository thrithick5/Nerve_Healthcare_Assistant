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
   - **Region**: Choose the closest location (e.g., Singapore or Oregon)
   - **Root Directory**: Leave blank (or `./`)
   - **Dockerfile Path**: `./backend/Dockerfile`
   - **Docker Context**: `./backend`
   - **Instance Type**: Select **Free** ($0/month)
5. Expand **Advanced Settings**:
   - **Health Check Path**: `/api/v1/health`
6. Under **Environment Variables**, add the following key-value pairs:
   - `DATABASE_URL` = `sqlite:///./data/healthcare.db`
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

- **CORS Errors**: Vercel domain URLs (`https://*.vercel.app`) are automatically allowed by backend regex. If using a custom domain, add it to `CORS_ORIGINS_EXTRA` in Render.
- **404 on Refresh**: `vercel.json` rewrites map all requests to `/index.html`.
- **Render Free Tier Spin-Down**: Free instances on Render spin down after 15 minutes of inactivity. The first request after spin-down may take ~30 seconds to respond as the instance wakes up.
