# API Reference

## Overview

The Literacy Coach API consists of five main services:

- **Gateway** (Port 8000): Web interface and voice interaction
- **Agent** (Port 8001): OpenAI agent orchestration with tool calling
- **Content** (Port 8002): Text catalog and RAG search
- **Assessment** (Port 8003): Reading and writing evaluation
- **Teacher** (Port 8004): Roster management and analytics

## Authentication

All API endpoints require an OpenAI API key set in the `OPENAI_API_KEY` environment variable. The key is validated on each request that requires LLM services.

## Gateway API

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "ok": true,
  "service": "gateway"
}
```

### Voice Turn
```http
POST /api/voice/turn
Content-Type: multipart/form-data
```

**Parameters:**
- `audio` (file): Audio file (webm, mp3, etc.)
- `session_id` (string): Unique session identifier
- `mode` (string): Interaction mode ("tutor", "assessment")
- `grade_level` (string): Student grade level
- `user_id` (string): User identifier
- `reference_text` (string, optional): Reference text for reading assessment

**Response:**
```json
{
  "transcript": "Hello, I need help with reading.",
  "coach_text": "I'd be happy to help you with your reading!",
  "coach_audio_b64_mp3": "base64-encoded-audio-data",
  "session_id": "session_123",
  "latency_ms": 1250
}
```

### Session Management
```http
POST /api/session/reset
Content-Type: application/x-www-form-urlencoded
```

**Parameters:**
- `session_id` (string): Session to reset

**Response:**
```json
{
  "ok": true,
  "session_id": "session_123"
}
```

### Agent Proxy
```http
POST /agent/respond
Content-Type: application/json
```

**Request:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Help me find a story to read."
    }
  ],
  "mode": "tutor",
  "student_grade": "3"
}
```

**Response:**
```json
{
  "content": "I found a great story for you to practice reading!"
}
```

### Writing Assessment
```http
POST /api/writing/score
Content-Type: application/json
```

**Request:**
```json
{
  "user_id": "student_123",
  "class_id": "class_456",
  "assignment_id": "assignment_789",
  "prompt": "Describe your favorite place",
  "essay": "The library is my favorite place...",
  "grade_level": "5",
  "rubric_name": "writing_default"
}
```

**Response:**
```json
{
  "rubric_scores": {
    "ideas": 4,
    "organization": 3,
    "evidence": 3,
    "conventions": 3
  },
  "feedback": "Great work on developing your main idea..."
}
```

## Agent API

### Health Check
```http
GET /health
```

### Agent Response
```http
POST /agent/respond
Content-Type: application/json
```

**Request:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Find me a story about animals."
    }
  ],
  "mode": "tutor",
  "student_grade": "2"
}
```

**Response:**
```json
{
  "content": "Here's a story about a clever fox..."
}
```

## Content API

### Health Check
```http
GET /health
```

### List Texts
```http
GET /texts?limit=20
```

**Response:**
```json
{
  "results": [
    {
      "id": "story_001",
      "title": "The Little Fox",
      "text": "Once upon a time...",
      "lexile": 450,
      "grade_band": "2-4",
      "phonics_focus": " CVC words",
      "theme": "animals"
    }
  ]
}
```

### Search Texts
```http
POST /texts/search
Content-Type: application/json
```

**Request:**
```json
{
  "lexile_min": 200,
  "lexile_max": 600,
  "grade_band": "K-1",
  "theme": "animals",
  "limit": 10
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "story_001",
      "title": "Farm Animals",
      "text": "The cow says moo...",
      "lexile": 350,
      "grade_band": "K-1",
      "theme": "animals"
    }
  ]
}
```

### RAG Search
```http
POST /rag/search
Content-Type: application/json
```

**Request:**
```json
{
  "query": "stories about friendship",
  "k": 5
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "story_002",
      "title": "Best Friends Forever",
      "text": "Excerpt from the story...",
      "lexile": 500
    }
  ]
}
```

## Assessment API

### Health Check
```http
GET /health
```

### Reading Assessment
```http
POST /reading/assess
Content-Type: application/json
```

**Request:**
```json
{
  "reference_text": "The cat sat on the mat.",
  "asr_transcript": "The cat sat on the mat.",
  "timestamps": [0.0, 5.0]
}
```

**Response:**
```json
{
  "wcpm": 72,
  "accuracy": 1.0,
  "errors": []
}
```

### Writing Assessment
```http
POST /writing/score
Content-Type: application/json
```

**Request:**
```json
{
  "prompt": "Write about your favorite hobby",
  "essay": "My favorite hobby is reading...",
  "grade_level": "4",
  "rubric_name": "writing_default"
}
```

**Response:**
```json
{
  "rubric_scores": {
    "ideas": 4,
    "organization": 4,
    "evidence": 3,
    "conventions": 3
  },
  "feedback": "Excellent organization and clear ideas..."
}
```

## Teacher API

### Health Check
```http
GET /health
```

### Class Management
```http
POST /classes
Content-Type: application/json
```

**Request:**
```json
{
  "name": "Grade 3A"
}
```

**Response:**
```json
{
  "id": "class_123",
  "name": "Grade 3A"
}
```

### Roster Management
```http
POST /roster/import?class_id=class_123
Content-Type: text/csv
```

**CSV Format:**
```csv
student_id,student_name
student_001,Alice Johnson
student_002,Bob Smith
```

### Assignment Management
```http
POST /assignments
Content-Type: application/json
```

**Request:**
```json
{
  "class_id": "class_123",
  "type": "reading",
  "title": "Read Chapter 1",
  "details": "story_001"
}
```

### Analytics
```http
GET /analytics/overview?class_id=class_123
```

**Response:**
```json
{
  "class_id": "class_123",
  "reading_samples": 15,
  "avg_wcpm": 85.5,
  "avg_accuracy": 0.92,
  "writing_samples": 8
}
```

## Error Responses

All APIs return appropriate HTTP status codes and error messages:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "OpenAI API key not configured"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

API endpoints are rate limited based on OpenAI API quotas. Consider implementing additional rate limiting for production deployments.

## Data Formats

### Timestamps
All timestamps are in ISO 8601 format: `2024-01-15T10:30:00Z`

### Identifiers
All resource IDs follow the pattern: `{type}_{alphanumeric_string}`

### Text Encoding
All text content is UTF-8 encoded.

## SDK Examples

### Python
```python
import httpx

# Voice interaction
with open("audio.webm", "rb") as audio:
    response = httpx.post(
        "http://localhost:8000/api/voice/turn",
        files={"audio": audio},
        data={
            "session_id": "session_123",
            "mode": "tutor",
            "grade_level": "3"
        }
    )

result = response.json()
print(result["transcript"])
print(result["coach_text"])
```

### JavaScript
```javascript
// Writing assessment
const response = await fetch('http://localhost:8000/api/writing/score', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_id: 'student_123',
    prompt: 'Describe your favorite animal',
    essay: 'My favorite animal is the elephant...',
    grade_level: '2',
    rubric_name: 'writing_default'
  })
});

const result = await response.json();
console.log('Scores:', result.rubric_scores);
console.log('Feedback:', result.feedback);
```

## Webhooks

The Teacher API supports webhooks for real-time notifications:

```http
POST /webhooks/events
Content-Type: application/json
```

**Request:**
```json
{
  "url": "https://your-app.com/webhook",
  "events": ["reading_result", "writing_result"],
  "secret": "your_webhook_secret"
}