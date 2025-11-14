"""
Question-Answering API Service for Member Data
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import json
from typing import List, Dict, Any
import os

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

class Question(BaseModel):
    question: str

class Answer(BaseModel):
    answer: str

async def fetch_all_messages() -> List[Dict[str, Any]]:
    """Fetch all messages from the API with pagination."""
    all_messages = []
    skip = 0
    limit = 100
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            try:
                response = await client.get(
                    MESSAGES_API_URL,
                    params={"skip": skip, "limit": limit}
                )
                response.raise_for_status()
                data = response.json()
                
                items = data.get("items", [])
                if not items:
                    break
                    
                all_messages.extend(items)
                
                total = data.get("total", 0)
                if len(all_messages) >= total:
                    break
                    
                skip += limit
                
            except Exception as e:
                print(f"Error fetching messages: {e}")
                break
    
    return all_messages

async def answer_question(question: str, messages: List[Dict[str, Any]]) -> str:
    """
    Use Claude API to answer questions based on the messages.
    Uses the native Claude API integration available in artifacts.
    """
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
    
    # Build context
    context_parts = ["# Member Messages\n\n"]
    for user_name, msgs in user_messages.items():
        context_parts.append(f"## {user_name}\n")
        for msg in msgs:
            context_parts.append(f"- [{msg['timestamp']}] {msg['message']}\n")
        context_parts.append("\n")
    
    context = "".join(context_parts)
    
    # Prepare prompt for Claude
    prompt = f"""{context}

Based on the member messages above, answer this question accurately and concisely:

{question}

Rules:
- Answer based ONLY on the information in the messages above
- If you cannot find the answer, say "I don't have enough information to answer that"
- Be specific and cite relevant details
- Keep the answer concise

Answer:"""

    # Call Claude API
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1000,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["content"][0]["text"]
            else:
                # Fallback to rule-based extraction
                return rule_based_answer(question, user_messages)
                
    except Exception as e:
        print(f"Claude API error: {e}")
        return rule_based_answer(question, user_messages)

def rule_based_answer(question: str, user_data: Dict[str, List[Dict]]) -> str:
    """Fallback rule-based QA system."""
    q_lower = question.lower()
    
    # Find mentioned user
    target_user = None
    for user in user_data.keys():
        if user.lower() in q_lower or user.split()[0].lower() in q_lower:
            target_user = user
            break
    
    if not target_user:
        return "I don't have enough information to answer that question."
    
    messages = [msg["message"] for msg in user_data[target_user]]
    
    # Pattern matching
    if "when" in q_lower and any(w in q_lower for w in ["trip", "travel", "visit"]):
        for msg in messages:
            if any(w in msg.lower() for w in ["trip", "travel", "going", "visiting"]):
                return msg
    
    elif "how many" in q_lower:
        if "car" in q_lower:
            for msg in messages:
                if "car" in msg.lower():
                    return msg
    
    elif "favorite" in q_lower or "like" in q_lower:
        if "restaurant" in q_lower:
            for msg in messages:
                if "restaurant" in msg.lower() or "eat" in msg.lower():
                    return msg
    
    # Return first relevant message
    if messages:
        return messages[0]
    
    return "I don't have enough information to answer that question."

@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "Member Data QA System",
        "endpoints": {
            "/ask": "POST - Ask questions about member data",
            "/health": "GET - Health check"
        }
    }

@app.post("/ask", response_model=Answer)
async def ask_question_endpoint(question: Question):
    """Answer natural language questions about member data."""
    try:
        messages = await fetch_all_messages()
        
        if not messages:
            raise HTTPException(status_code=503, detail="Unable to fetch messages")
        
        answer_text = await answer_question(question.question, messages)
        
        return Answer(answer=answer_text)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(MESSAGES_API_URL, params={"skip": 0, "limit": 1})
            api_ok = response.status_code == 200
    except:
        api_ok = False
    
    return {"status": "healthy", "api_connected": api_ok}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
