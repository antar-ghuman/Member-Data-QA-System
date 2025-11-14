# Member Data Question-Answering System

A natural language question-answering API service that answers questions about member data from a third-party API.

## 🚀 Live Demo

**API Endpoint:** `[Your deployment URL]/ask`

Try it with:
```bash
curl -X POST "https://your-deployment-url/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "When is Layla planning her trip to London?"}'
```

## 📋 Features

- **Natural Language Processing**: Ask questions in plain English
- **Automatic Data Fetching**: Retrieves and processes all member messages from the API
- **Intelligent Answering**: Uses Claude AI (with rule-based fallback) to extract answers
- **RESTful API**: Simple JSON-based interface
- **Health Monitoring**: Built-in health check endpoints
- **CORS Enabled**: Can be called from web applications

## 🏗️ Architecture

### Tech Stack
- **Framework**: FastAPI (Python)
- **HTTP Client**: httpx (async support)
- **AI Engine**: Claude API (with rule-based fallback)
- **Deployment**: Docker container (deployable to any cloud platform)

### System Flow
1. Receive question via POST /ask endpoint
2. Fetch all member messages from source API (with pagination)
3. Group and structure messages by user
4. Send to Claude API with context and question
5. Return extracted answer

## 🎯 API Usage

### Ask a Question

**Endpoint:** `POST /ask`

**Request Body:**
```json
{
  "question": "When is Layla planning her trip to London?"
}
```

**Response:**
```json
{
  "answer": "Layla is planning her trip to London in March."
}
```

### Example Questions
- "When is Layla planning her trip to London?"
- "How many cars does Vikram Desai have?"
- "What are Amira's favorite restaurants?"
- "Where does Marcus work?"
- "What hobbies does Sarah mention?"

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "api_connected": true
}
```

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- pip

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd member-qa-system
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python app.py
```

The API will be available at `http://localhost:8000`

### Test the API

```bash
# Ask a question
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "When is Layla planning her trip to London?"}'

# Check health
curl "http://localhost:8000/health"
```

## 🐳 Docker Deployment

### Build the image:
```bash
docker build -t member-qa-system .
```

### Run the container:
```bash
docker run -p 8000:8000 member-qa-system
```

### Deploy to Cloud Run (GCP):
```bash
gcloud run deploy member-qa-system \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Deploy to Render:
1. Push code to GitHub
2. Connect repository to Render
3. Select "Docker" as environment
4. Deploy

### Deploy to Railway:
```bash
railway up
```

## 📊 Bonus 1: Design Approaches Considered

### Approach 1: Direct LLM Integration (Chosen Approach)
**Description:** Fetch all messages, format them as context, and send to Claude API with the question.

**Pros:**
- Most accurate for complex, nuanced questions
- Handles ambiguous queries well
- Can understand context and relationships
- Natural language understanding built-in

**Cons:**
- Requires API key and external dependency
- Higher latency (API calls)
- Token costs for large datasets
- Rate limits

**Why Chosen:** Best balance of accuracy and simplicity for the use case. Natural language understanding is critical for varied question formats.

---

### Approach 2: Vector Database + Semantic Search
**Description:** Convert messages to embeddings, store in vector DB (Pinecone/Weaviate), perform semantic search, and generate answers.

**Pros:**
- Fast retrieval for large datasets
- Scalable to millions of messages
- Lower per-query cost
- Good for similarity-based questions

**Cons:**
- Requires embedding generation and storage
- Additional infrastructure (vector DB)
- More complex setup
- Overkill for this dataset size

**Why Not Chosen:** Dataset is small enough (~100-1000 messages) that full-scan is fast. Adds unnecessary complexity.

---

### Approach 3: Rule-Based Pattern Matching
**Description:** Parse questions using regex/NLP patterns, extract entities, and match against structured data.

**Pros:**
- Fast and deterministic
- No external dependencies
- Predictable behavior
- Low latency

**Cons:**
- Brittle - breaks with question variations
- Requires extensive pattern library
- Hard to maintain
- Poor handling of complex queries

**Why Not Chosen:** Too rigid for natural language variations. Would require constant updates for new question patterns.

---

### Approach 4: Fine-tuned Model
**Description:** Fine-tune a smaller model (BERT/T5) specifically on member data Q&A pairs.

**Pros:**
- Optimized for specific domain
- No per-query API costs
- Can be deployed locally
- Fast inference

**Cons:**
- Requires training data creation
- Time-intensive to train
- Needs GPUs for inference
- Difficult to update with new data

**Why Not Chosen:** No training data available. Overhead not justified for this use case.

---

### Approach 5: Hybrid: Retrieval + LLM
**Description:** Use keyword/semantic search to retrieve relevant messages, then use LLM only on filtered subset.

**Pros:**
- Reduced token usage
- Faster than full-context LLM
- More scalable
- Lower costs

**Cons:**
- Risk of missing relevant messages in retrieval
- Added complexity
- Two-stage errors

**Why Not Chosen:** Current dataset size doesn't require optimization. Could be future enhancement for scale.

---

### Approach 6: Knowledge Graph
**Description:** Build a graph of entities (users, places, items) and relationships from messages, then query the graph.

**Pros:**
- Excellent for relationship queries
- Structured reasoning
- Fast queries once built
- Visual representation

**Cons:**
- Complex entity extraction required
- Graph construction overhead
- Maintenance complexity
- Limited to structured queries

**Why Not Chosen:** Over-engineered for straightforward Q&A. Messages don't have complex relationships.

---

## 📈 Bonus 2: Data Insights & Anomalies

### Dataset Analysis

#### 1. **Data Structure Observations**
- **Message Format**: Each message contains: id, user_id, user_name, timestamp, message
- **User Distribution**: Messages are grouped by user_name (not user_id)
- **Timestamp Format**: ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)

#### 2. **Potential Anomalies**

##### Missing or Null Values
- **Issue**: Some messages may have empty or null `message` fields
- **Impact**: Can cause parsing errors or incomplete answers
- **Recommendation**: Add null checks and filtering

##### Duplicate Messages
- **Issue**: Same message appears multiple times for a user
- **Impact**: Could skew answers (e.g., overcounting items)
- **Recommendation**: Deduplicate based on message content + timestamp

##### Inconsistent Name Formats
- **Issue**: Same user might appear as "John Smith" and "J. Smith"
- **Impact**: QA system treats them as different users
- **Recommendation**: Name normalization or use user_id as primary key

##### Timestamp Anomalies
- **Issue**: Future timestamps or timestamps far in the past
- **Impact**: Affects "recent" or "when" queries
- **Recommendation**: Validate timestamp ranges

##### Unstructured Data in Messages
- **Issue**: Messages are free-form text with inconsistent formatting
- **Impact**: Makes structured extraction difficult (dates, numbers, etc.)
- **Recommendation**: Use NER or LLM-based extraction

##### Mixed Languages
- **Issue**: Messages may be in different languages
- **Impact**: Pattern matching and entity extraction may fail
- **Recommendation**: Add language detection and translation

##### Ambiguous References
- **Issue**: Pronouns ("it", "there") without clear antecedents
- **Impact**: Hard to resolve what is being referred to
- **Recommendation**: Maintain conversation context

##### Date Ambiguity
- **Issue**: Dates like "March" without year, or relative dates ("next month")
- **Impact**: Cannot determine absolute dates
- **Recommendation**: Use message timestamp as reference point

#### 3. **Data Quality Metrics**

To be calculated on actual dataset:
- Message count per user (distribution)
- Average message length
- Null/empty message ratio
- Unique vs total message count (detect duplicates)
- Timestamp range and gaps
- Character encoding issues

#### 4. **Suggested Data Validation**

```python
def validate_messages(messages):
    issues = []
    
    for msg in messages:
        # Check required fields
        if not msg.get("message"):
            issues.append(f"Empty message for user {msg.get('user_name')}")
        
        # Check timestamp validity
        try:
            ts = datetime.fromisoformat(msg.get("timestamp", "").replace("Z", "+00:00"))
            if ts > datetime.now() or ts.year < 2000:
                issues.append(f"Invalid timestamp: {msg.get('timestamp')}")
        except:
            issues.append(f"Malformed timestamp: {msg.get('timestamp')}")
        
        # Check for user_id/user_name mismatch
        if msg.get("user_id") and not msg.get("user_name"):
            issues.append(f"Missing user_name for user_id {msg.get('user_id')}")
    
    return issues
```

---

## 🔍 Testing

### Unit Tests
```bash
pytest tests/
```

### Integration Tests
```bash
# Test against live API
python -m pytest tests/integration/
```

### Manual Testing
See `examples/test_queries.json` for sample questions.

---

## 📝 Future Enhancements

1. **Caching**: Cache API responses to reduce latency
2. **Rate Limiting**: Implement rate limits to prevent abuse
3. **Authentication**: Add API key authentication
4. **Logging**: Comprehensive logging for debugging and analytics
5. **Monitoring**: Prometheus metrics and Grafana dashboards
6. **A/B Testing**: Compare LLM vs rule-based approaches
7. **Streaming**: Support streaming responses for long answers
8. **Multi-language**: Support questions in multiple languages
9. **Conversation History**: Maintain context across multiple questions
10. **Confidence Scores**: Return confidence level with answers

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

---

## 📄 License

MIT License

---

## 📧 Contact

For questions or issues, please open a GitHub issue.
