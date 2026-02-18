# Hugging Face Space Setup Guide for TempleApp AI Backend

This guide provides step-by-step instructions for deploying the TempleApp AI Backend to Hugging Face Spaces using the Docker SDK.

## 1. Create a New Space

1.  Log in to your [Hugging Face account](https://huggingface.co/).
2.  Click on your profile picture in the top right corner and select **"New Space"**.
3.  **Space Name**: Enter `templeapp-backend` (or your preferred name).
4.  **License**: Select `MIT` or `Apache 2.0` (optional).
5.  **Select the Space SDK**: Choose **Docker**. This is crucial as our application uses a custom Dockerfile.
6.  **Space Hardware**: The default **CPU Basic (2 vCPU, 16 GB RAM)** is sufficient for this application. It's free!
7.  **Visibility**: Choose **Public** or **Private** based on your preference.
8.  Click **"Create Space"**.

## 2. Configure Environment Variables (Secrets)

Before deploying the code, you must set up the environment variables. These are the secrets that allow your app to connect to Gemini, Supabase, Redis, and Cloudinary.

1.  Navigate to your Space's **Settings** tab.
2.  Scroll down to the **"Variables and secrets"** section.
3.  Click **"New secret"** for each of the variables below.

### Required Environment Variables

| Variable Name | Description | Example / Where to find |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google AI Studio API Key for Gemini models. | `AIzaSy...` (Get from [Google AI Studio](https://aistudio.google.com/)) |
| `SUPABASE_URL` | Your Supabase Project URL. | `https://xyz.supabase.co` |
| `SUPABASE_KEY` | Your Supabase `service_role` key (for backend access). | `eyJhbG...` (Settings > API > service_role secret) |
| `UPSTASH_REDIS_URL` | Upstash Redis URL for caching/rate limiting. | `https://romantic-lemur-30294.upstash.io` |
| `UPSTASH_REDIS_TOKEN` | Upstash Redis REST Token. | `5d508f32-4111-46b4-a40b-60efabbe958c` |
| `ADMIN_API_KEY` | A secret key you create to protect your API endpoints. | `my-super-secret-key-123` (You define this) |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary Cloud Name for audio storage. | `dhny7ybpw` |
| `CLOUDINARY_API_KEY` | Cloudinary API Key. | `883562932532487` |
| `CLOUDINARY_API_SECRET` | Cloudinary API Secret. | `wRyF4kWUQyuzO0R2ZR44km5NyTU` |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed frontend domains for CORS. | `https://templeapp-admin.vercel.app,http://localhost:3000` |

> **Note**: Ensure there are no spaces or quotes around the values when entering them in Hugging Face.

## 3. Deploy the Code

You have two options to deploy the code:

### Option A: Upload Files via Browser (Easiest for initial setup)

1.  Go to the **"Files"** tab of your Space.
2.  Click **"Add file"** -> **"Upload files"**.
3.  Drag and drop all the files and folders from your local `templeapp-backend` folder into the upload area.
    *   Ensure the `app` folder, `Dockerfile`, `requirements.txt`, etc., are at the root level.
4.  Commit changes with a message like "Initial commit".
5.  Hugging Face will automatically start building your Docker container.

### Option B: Use Git (Recommended for updates)

1.  Clone the repository locally (you can find the clone command in the "Files" tab menu):
    ```bash
    git clone https://huggingface.co/spaces/YOUR_USERNAME/templeapp-backend
    ```
2.  Copy your local code into this cloned directory.
3.  Push the changes:
    ```bash
    git add .
    git commit -m "Deploying backend"
    git push
    ```

## 4. Monitor Deployment

1.  Click on the **"Logs"** tab in your Space.
2.  You will see the Docker build logs first. This may take a few minutes as it installs Python dependencies and `ffmpeg`.
3.  Once the build finishes, you will see the runtime logs:
    ```
    INFO:     Started server process [1]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://0.0.0.0:7860 (Press CTRL+C to quit)
    ```
4.  If you see "Running on http://0.0.0.0:7860", your backend is live!

## 5. Verify the API

Your API base URL will be:
`https://YOUR_USERNAME-templeapp-backend.hf.space`

You can test the health endpoint (no auth required):
`https://YOUR_USERNAME-templeapp-backend.hf.space/health`

**Expected Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime_seconds": 12,
  "models": {
    "flash": "gemini-2.0-flash-exp",
    "pro": "gemini-1.5-pro"
  }
}
```

For all other endpoints, remember to include the header:
`X-API-Key: YOUR_ADMIN_API_KEY`

## Troubleshooting

-   **Build Fails?** Check the Logs tab. Common issues are missing dependencies in `requirements.txt`.
-   **Runtime Errors?** If the app crashes on startup, it's usually a missing Environment Variable. Double-check your secrets.
-   **500 Errors?** Check the logs for specific Python tracebacks.
