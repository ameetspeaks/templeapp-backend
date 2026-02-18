---
title: Templeapp Backend
emoji: 🕉️
colorFrom: yellow
colorTo: orange
sdk: docker
pinned: false
---

# TempleApp AI Backend

Production-grade Python FastAPI backend hosted as a Hugging Face Space using Docker SDK. This is the AI automation engine for "TempleApp" (templeapp.in).

## Project Configuration

- **Framework**: FastAPI (Python 3.11)
- **Host**: Hugging Face Spaces (Docker SDK)
- **Database**: Supabase
- **Cache**: Upstash Redis
- **AI Models**: Google Gemini (Flash & Pro)

## Environment Variables

For detailed setup instructions, including how to create a Space and configure secrets, see [HUGGINGFACE_SETUP.md](HUGGINGFACE_SETUP.md).

Ensure the following environment variables are set in your Hugging Face Space secrets:

- `GEMINI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `UPSTASH_REDIS_URL`
- `UPSTASH_REDIS_TOKEN`
- `ADMIN_API_KEY`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`
- `ALLOWED_ORIGINS` (Comma separated list of allowed origins)

## Endpoints

### Panchang
- `POST /panchang/generate`
- `POST /panchang/generate-range`
- `GET /panchang/{date}`
- `GET /panchang/list`
- `DELETE /panchang/{date}`

### Blogs
- `POST /blog/generate`
- `POST /blog/generate-batch`
- `GET /blog/list`
- `GET /blog/{id}`
- `PATCH /blog/{id}/publish`
- `PATCH /blog/{id}/unpublish`
- `PUT /blog/{id}`
- `DELETE /blog/{id}`
- `POST /blog/{id}/regenerate`

### Temples
- `POST /temple/add`
- `POST /temple/enrich/{temple_id}`
- `POST /temple/bulk-enrich`
- `GET /temple/list`
- `GET /temple/{id}`
- `PUT /temple/{id}`
- `DELETE /temple/{id}`
- `GET /temple/stats`

### Muhurat
- `POST /muhurat/calculate`
- `GET /muhurat/upcoming`
- `POST /muhurat/monthly-report`
- `GET /muhurat/list`

### Aarti
- `POST /aarti/generate-lyrics`
- `POST /aarti/generate-batch`
- `GET /aarti/list`
- `GET /aarti/{id}`
- `PUT /aarti/{id}`
- `DELETE /aarti/{id}`
- `POST /aarti/fetch-audio/{aarti_id}`
- `POST /aarti/fetch-audio-url/{aarti_id}`
- `POST /aarti/fetch-audio-batch`
- `GET /aarti/audio-status`

### Jobs
- `GET /jobs/status`
- `POST /jobs/trigger/{job_name}`
- `GET /jobs/logs`
- `GET /jobs/logs/summary`

## Local Development

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up `.env` file based on `.env.example`.

4. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```
