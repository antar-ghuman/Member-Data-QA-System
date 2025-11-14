# Deployment Guide

This guide covers multiple deployment options for the Member Data QA System.

## Quick Start: Render (Recommended)

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect repository → Auto-deploys with Dockerfile
4. Access at: `https://your-app.onrender.com`

## Other Platforms

### Railway
```bash
git push
# Go to railway.app → New Project → Deploy from repo
```

### Google Cloud Run
```bash
gcloud run deploy member-qa-system --source . --allow-unauthenticated
```

### Heroku
```bash
heroku container:push web && heroku container:release web
```

See full deployment instructions with examples for all platforms in the main README.

## Testing Deployment

```bash
curl -X POST "https://your-app.onrender.com/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "When is Layla planning her trip to London?"}'
```
