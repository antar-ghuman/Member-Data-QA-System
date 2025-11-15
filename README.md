# Member Data QA System

Natural language question-answering API for member data.

**Live Demo:** https://member-qa-system-production.up.railway.app

## Quick Start
```bash
curl -X POST "https://member-qa-system-production.up.railway.app/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What does Layla prefer during flights?"}'
```

## Features

- Natural language question answering
- RESTful API endpoint: `POST /ask`
- Simple JSON response: `{"answer": "..."}`
- Web UI at root URL

## Architecture

**Stack:** Python, FastAPI, httpx

**Flow:**
1. Fetch messages from source API
2. Parse user question
3. Extract answer using pattern matching
4. Return JSON response

## Local Setup
```bash
pip install -r requirements.txt
python app.py
```

## Example Questions
```bash
# Based on actual API data:
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What does Layla prefer during flights?"}'
# Answer: "Please remember I prefer aisle seats during my flights."

curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Where does Sophia want to go this Friday?"}'
# Answer: "Please book a private jet to Paris for this Friday."
```

## Bonus 1: Design Approaches

**Chosen: Rule-Based Pattern Matching**
- Fast and deterministic
- No external API dependencies
- Good for structured queries

**Considered:**
- LLM Integration (Claude API) - More accurate but requires API key
- Vector Database - Overkill for this dataset size
- Fine-tuned Model - No training data available

## Bonus 2: Data Insights

### Dataset Observations
- Total messages: 3,349
- Users include: Layla Kawaguchi, Vikram Desai, Sophia Al-Farsi, Armand Dupont, etc.
- Message types: Travel requests, reservations, preferences, contact updates

### Key Finding: Question Mismatch
The assignment provided example questions that don't match the actual API data:
- ❌ "When is Layla planning her trip to London?" - No London trip in data
- ❌ "How many cars does Vikram Desai have?" - No car count in data  
- ❌ "What are Amira's favorite restaurants?" - No user named Amira

**Actual answerable questions:**
- ✅ "What does Layla prefer during flights?" → Aisle seats
- ✅ "Where does Sophia want to go?" → Paris
- ✅ "What event is Armand attending in Milan?" → Opera

### Technical Issues Encountered
1. **Network restrictions** - Render couldn't access API, switched to Railway
2. **PORT variable** - Railway needed Procfile instead of direct uvicorn command
3. **Performance** - Added caching to avoid fetching 900+ messages per request
4. **API errors** - Handles 402 rate limit responses gracefully

## Deployment

Deployed on Railway: https://member-qa-system-production.up.railway.app
```bash
# Railway deployment
git push
# Auto-deploys via Procfile
```
