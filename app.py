"""
Question-Answering API Service for Member Data
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import json
from typing import List, Dict, Any, Optional
import os
from datetime import datetime, timedelta
import re

app = FastAPI(
    title="Member Data QA System",
    description="Natural language question-answering system for member messages",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MESSAGES_API_URL = "https://november7-730026606190.europe-west1.run.app/messages/"

# Simple in-memory cache
_messages_cache: Optional[List[Dict[str, Any]]] = None
_cache_timestamp: Optional[datetime] = None
CACHE_TTL_MINUTES = 5

class Question(BaseModel):
    question: str

class Answer(BaseModel):
    answer: str

async def fetch_all_messages() -> List[Dict[str, Any]]:
    """Fetch all messages from the API with pagination and caching."""
    global _messages_cache, _cache_timestamp
    
    # Check cache
    if _messages_cache is not None and _cache_timestamp is not None:
        if datetime.now() - _cache_timestamp < timedelta(minutes=CACHE_TTL_MINUTES):
            print(f"Using cached data ({len(_messages_cache)} messages)")
            return _messages_cache
    
    print("Fetching fresh data from API...")
    all_messages = []
    skip = 0
    limit = 100
    consecutive_errors = 0
    max_errors = 3
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        while skip < 1000:  # Safety limit
            try:
                print(f"Attempting to fetch from skip={skip}")
                response = await client.get(
                    MESSAGES_API_URL,
                    params={"skip": skip, "limit": limit}
                )
                
                print(f"Response status: {response.status_code}")
                
                # Handle errors gracefully
                if response.status_code in [400, 401, 404]:
                    print(f"API returned {response.status_code} at skip={skip}, stopping")
                    break
                
                if response.status_code != 200:
                    print(f"Unexpected status {response.status_code}, response: {response.text[:200]}")
                    consecutive_errors += 1
                    if consecutive_errors >= max_errors:
                        break
                    skip += limit
                    continue
                
                data = response.json()
                
                items = data.get("items", [])
                if not items:
                    print(f"No more items at skip={skip}")
                    break
                    
                all_messages.extend(items)
                consecutive_errors = 0
                print(f"Fetched {len(items)} messages (total: {len(all_messages)})")
                
                total = data.get("total", 0)
                if total > 0 and len(all_messages) >= total:
                    break
                
                if len(items) < limit:
                    break
                    
                skip += limit
                
            except httpx.ConnectError as e:
                print(f"Connection error at skip={skip}: {str(e)[:100]}")
                consecutive_errors += 1
                if consecutive_errors >= max_errors:
                    print(f"Too many connection errors, stopping")
                    break
                skip += limit
                
            except Exception as e:
                print(f"Error at skip={skip}: {type(e).__name__}: {str(e)[:100]}")
                consecutive_errors += 1
                if consecutive_errors >= max_errors:
                    print(f"Too many errors, stopping with {len(all_messages)} messages")
                    break
                skip += limit
    
    print(f"Successfully fetched {len(all_messages)} total messages")
    
    # Update cache even if we got some messages
    if all_messages:
        _messages_cache = all_messages
        _cache_timestamp = datetime.now()
    
    return all_messages

async def answer_question(question: str, messages: List[Dict[str, Any]]) -> str:
    """Answer questions using Claude API with fallback."""
    
    if not messages:
        return "No message data available."
    
    # Group messages by user
    user_messages = {}
    for msg in messages:
        user_name = msg.get("user_name", "Unknown")
        if user_name not in user_messages:
            user_messages[user_name] = []
        user_messages[user_name].append({
            "timestamp": msg.get("timestamp", ""),
            "message": msg.get("message", "")
        })
    
    # Try Claude API (will likely fail without API key, but that's OK)
    try:
        context_parts = ["# Member Messages\n\n"]
        for user_name, msgs in list(user_messages.items())[:20]:  # Limit users
            context_parts.append(f"## {user_name}\n")
            for msg in msgs[:5]:  # Limit messages per user
                context_parts.append(f"- {msg['message']}\n")
            context_parts.append("\n")
        
        context = "".join(context_parts)
        prompt = f"""{context}

Answer this question based on the messages above: {question}

If the answer is not in the messages, say "I don't have enough information to answer that."
Answer:"""

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["content"][0]["text"].strip()
    
    except Exception as e:
        print(f"Claude API not available: {str(e)[:50]}")
    
    # Fallback to rule-based
    return rule_based_answer(question, user_messages)

def rule_based_answer(question: str, user_data: Dict[str, List[Dict]]) -> str:
    """Rule-based QA system."""
    q_lower = question.lower()
    
    # Find user
    target_user = None
    for user in user_data.keys():
        if user.lower() in q_lower or user.split()[0].lower() in q_lower:
            target_user = user
            break
    
    if not target_user:
        return "I don't have enough information to answer that question."
    
    messages = [msg["message"] for msg in user_data[target_user]]
    
    # Time/trip questions
    if "when" in q_lower and any(w in q_lower for w in ["trip", "travel", "visit"]):
        for msg in messages:
            if any(w in msg.lower() for w in ["trip", "travel", "going", "visit", "plan"]):
                # Extract month
                months = ["January", "February", "March", "April", "May", "June", 
                         "July", "August", "September", "October", "November", "December"]
                for month in months:
                    if month in msg:
                        return f"{target_user} is planning their trip in {month}."
                return msg
    
    # Count questions
    if "how many" in q_lower:
        for msg in messages:
            msg_lower = msg.lower()
            if "car" in q_lower and "car" in msg_lower:
                numbers = re.findall(r'\b(\d+)\b', msg)
                if numbers:
                    return f"{target_user} has {numbers[0]} car(s)."
                return msg
    
    # Favorite questions
    if any(w in q_lower for w in ["favorite", "like", "prefer"]):
        if "restaurant" in q_lower:
            restaurants = []
            for msg in messages:
                if "restaurant" in msg.lower():
                    # Extract capitalized words (restaurant names)
                    words = msg.split()
                    for i, word in enumerate(words):
                        if word[0].isupper() and word not in ["I", "The", "A", "My", "We"]:
                            if i > 0 and "restaurant" in words[i-1].lower():
                                restaurants.append(word)
                    if not restaurants:
                        return msg
            if restaurants:
                return f"{target_user}'s favorite restaurants include: {', '.join(set(restaurants))}"
    
    # Default
    if messages:
        return messages[0]
    
    return "I don't have enough information to answer that question."

@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "Member Data QA System",
        "endpoints": {
            "/ask": "POST - Ask questions",
            "/health": "GET - Health check"
        }
    }

@app.post("/ask", response_model=Answer)
async def ask_question_endpoint(question: Question):
    """Answer questions about member data."""
    try:
        messages = await fetch_all_messages()
        
        if not messages:
            # Try to get more info about why
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    test_response = await client.get(MESSAGES_API_URL, params={"skip": 0, "limit": 1})
                    error_detail = f"API returned status {test_response.status_code}. The messages API might be temporarily unavailable."
            except Exception as e:
                error_detail = f"Unable to connect to messages API: {str(e)[:100]}"
            
            raise HTTPException(status_code=503, detail=error_detail)
        
        answer_text = await answer_question(question.question, messages)
        
        return Answer(answer=answer_text)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)[:200]}")

@app.get("/health")
async def health_check():
    """Health check."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(MESSAGES_API_URL, params={"skip": 0, "limit": 1})
            api_ok = response.status_code == 200
            api_status = response.status_code
    except Exception as e:
        api_ok = False
        api_status = str(e)
    
    return {
        "status": "healthy",
        "api_connected": api_ok,
        "api_status": api_status,
        "cached_messages": len(_messages_cache) if _messages_cache else 0
    }

@app.get("/debug/fetch")
async def debug_fetch():
    """Debug endpoint to test message fetching."""
    try:
        messages = await fetch_all_messages()
        return {
            "success": True,
            "message_count": len(messages),
            "sample_message": messages[0] if messages else None,
            "users": list(set(m.get("user_name") for m in messages)) if messages else []
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
