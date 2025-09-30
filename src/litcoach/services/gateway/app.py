import os
import time
from typing import Dict, List, Any
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import httpx

from litcoach.utils.openai_client import transcribe_audio, synthesize_speech, b64encode_audio


app = FastAPI(title="Literacy Coach Gateway")

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

AGENT_URL = os.environ.get("AGENT_URL", "http://localhost:8001")
ASSESSMENT_URL = os.environ.get("ASSESSMENT_URL", "http://localhost:8003")
TEACHER_URL = os.environ.get("TEACHER_URL", "http://localhost:8004")
MOCK_MODE = os.environ.get("LITCOACH_MOCK", "").strip().lower() in {"1", "true", "yes", "on"}


class VoiceTurnResponse(BaseModel):
    transcript: str
    coach_text: str
    coach_audio_b64_mp3: str
    session_id: str
    latency_ms: int


class AgentProxyBody(BaseModel):
    messages: List[Dict[str, Any]]
    mode: str = "tutor"
    student_grade: str | None = None


session_histories: Dict[str, List[Dict[str, Any]]] = {}


@app.get("/health")
def health():
    return {"ok": True, "service": "gateway"}


def _file_response(name: str) -> FileResponse:
    return FileResponse(os.path.join(static_dir, name), media_type="text/html")


@app.get("/")
def index():
    return _file_response("index.html")


@app.get("/reader.html")
def reader_page():
    return _file_response("reader.html")


@app.get("/writer.html")
def writer_page():
    return _file_response("writer.html")


@app.get("/teacher.html")
def teacher_page():
    return _file_response("teacher.html")


@app.post("/api/session/reset")
def reset_session(session_id: str = Form(...)):
    session_histories.pop(session_id, None)
    return {"ok": True, "session_id": session_id}


@app.post("/api/voice/turn", response_model=VoiceTurnResponse)
async def voice_turn(
    audio: UploadFile = File(...),
    session_id: str = Form(...),
    mode: str = Form("tutor"),
    grade_level: str = Form("3"),
    user_id: str = Form("anonymous"),
    class_id: str = Form(""),
    assignment_id: str = Form(""),
    reference_text: str = Form(""),
):
    start = time.time()
    audio_bytes = await audio.read()
    transcript = transcribe_audio(audio_bytes, filename=audio.filename or "audio.webm")

    history = session_histories.get(session_id, [])
    user_content = transcript
    if reference_text:
        user_content = f"Read-aloud transcript:\n{transcript}\nReference text:\n{reference_text}"
    history.append({"role": "user", "content": user_content})

    payload = {
        "messages": history,
        "mode": mode,
        "student_grade": grade_level,
    }
    if MOCK_MODE:
        agent_out = {"content": os.environ.get("LITCOACH_MOCK_REPLY", "Let's practice together!")}
    else:
        async with httpx.AsyncClient(timeout=60.0) as client:
            agent_response = await client.post(f"{AGENT_URL}/agent/respond", json=payload)
            agent_response.raise_for_status()
            agent_out = agent_response.json()

    coach_text = agent_out["content"]
    history.append({"role": "assistant", "content": coach_text})
    session_histories[session_id] = history

    if reference_text:
        assess_payload = {
            "reference_text": reference_text,
            "asr_transcript": transcript,
            "timestamps": [0.0, 60.0],
        }
        if MOCK_MODE:
            reading_result = {"wcpm": 120, "accuracy": 0.98, "errors": []}
        else:
            async with httpx.AsyncClient(timeout=30.0) as client:
                assessment_response = await client.post(
                    f"{ASSESSMENT_URL}/reading/assess", json=assess_payload
                )
                assessment_response.raise_for_status()
                reading_result = assessment_response.json()
                try:
                    await client.post(
                        f"{TEACHER_URL}/events/reading_result",
                        json={
                            "user_id": user_id,
                            "class_id": class_id or None,
                            "assignment_id": assignment_id or None,
                            "session_id": session_id,
                            "wcpm": reading_result["wcpm"],
                            "accuracy": reading_result["accuracy"],
                            "errors": reading_result.get("errors", []),
                        },
                    )
                except Exception:
                    pass

    coach_audio = synthesize_speech(coach_text)
    latency_ms = int((time.time() - start) * 1000)
    return JSONResponse(
        {
            "transcript": transcript,
            "coach_text": coach_text,
            "coach_audio_b64_mp3": b64encode_audio(coach_audio),
            "session_id": session_id,
            "latency_ms": latency_ms,
        }
    )


@app.post("/agent/respond")
async def agent_proxy(body: AgentProxyBody):
    if MOCK_MODE:
        return JSONResponse({"content": os.environ.get("LITCOACH_MOCK_REPLY", "Hello from mock agent!")})
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(f"{AGENT_URL}/agent/respond", json=body.model_dump())
        response.raise_for_status()
        return JSONResponse(response.json())


class WritingScoreBody(BaseModel):
    user_id: str = "anonymous"
    class_id: str | None = None
    assignment_id: str | None = None
    prompt: str
    essay: str
    grade_level: str = "5"
    rubric_name: str = "writing_default"


@app.post("/api/writing/score")
async def writing_score(body: WritingScoreBody):
    assess_payload = {
        "prompt": body.prompt,
        "essay": body.essay,
        "grade_level": body.grade_level,
        "rubric_name": body.rubric_name,
    }
    if MOCK_MODE:
        result = {
            "rubric_scores": {"organization": 3, "evidence": 4, "conventions": 3},
            "feedback": "[MOCK] Clear structure with relevant details. Review punctuation."
        }
        return JSONResponse(result)
    async with httpx.AsyncClient(timeout=60.0) as client:
        assessment_response = await client.post(
            f"{ASSESSMENT_URL}/writing/score", json=assess_payload
        )
        assessment_response.raise_for_status()
        result = assessment_response.json()
        try:
            await client.post(
                f"{TEACHER_URL}/events/writing_result",
                json={
                    "user_id": body.user_id,
                    "class_id": body.class_id,
                    "assignment_id": body.assignment_id,
                    "rubric_scores": result["rubric_scores"],
                    "feedback": result["feedback"],
                },
            )
        except Exception:
            pass
    return JSONResponse(result)


def main():
    import uvicorn

    host = os.environ.get("GATEWAY_HOST", "0.0.0.0")
    port = int(os.environ.get("GATEWAY_PORT", "8000"))
    uvicorn.run(
        "litcoach.services.gateway.app:app", host=host, port=port, reload=False, workers=1
    )


if __name__ == "__main__":
    main()

