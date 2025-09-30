# Architecture

-  Gateway (FastAPI)
    - Serves static web UI (Reader, Writer, Teacher)
    - Voice turn endpoint:
        1) Accepts recorded audio
        2) Speech-to-text via OpenAI
        3) Sends conversation context to Agent
        4) Synthesizes TTS from Agent response
        5) Returns transcript, text feedback, and base64 MP3

-  Agent Orchestrator (FastAPI)
    - Loads tutor system prompt
    - Uses OpenAI chat with tool-calling
    - Tools call:
        - Content service for leveled text search and RAG
        - Assessment service for reading and writing evaluation
    - Returns final assistant message text

-  Content (FastAPI + SQLite)
    - Ingests texts.json on startup
    - Ensures embeddings for texts
    - Filtering by metadata (lexile, grade_band, phonics_focus, theme)
    - RAG search by cosine similarity

-  Assessment (FastAPI)
    - Reading assess: WCPM, accuracy, simple error list
    - Writing score: LLM-based rubric scorer with JSON parsing

-  Teacher API (FastAPI + SQLite)
    - Manages classes, roster imports, assignments, analytics
    - Logs reading and writing results from gateway

-  Data Flow
    - Browser → Gateway: Audio / REST
    - Gateway → OpenAI: STT and TTS
    - Gateway → Agent: Messages
    - Agent → Tools: HTTP calls to Content, Assessment
    - Gateway → Teacher API: Result logging

-  Testing
    - Unit tests mock OpenAI and external HTTP
    - Tox orchestrates pytest

-  Packaging & Build
    - pyproject with hatch build backend
    - uv used in Dockerfiles for fast installs
    - docker-compose orchestrates five services


