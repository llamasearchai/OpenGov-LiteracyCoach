from io import BytesIO
import base64
import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from openai import OpenAI


def _is_mock_mode() -> bool:
    flag = os.environ.get("LITCOACH_MOCK", "").strip().lower()
    return flag in {"1", "true", "yes", "on"}


def get_client() -> OpenAI:
    if _is_mock_mode():
        # In mock mode we shouldn't hit the network or real SDK.
        # Any caller that relies on the client should instead branch
        # on mock mode prior to calling into the SDK.
        raise RuntimeError("OpenAI client not available in LITCOACH_MOCK mode")
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required")
    return OpenAI(api_key=key)


def _cache_dir() -> str:
    cache_path = os.path.join(os.getcwd(), "data", "runtime")
    os.makedirs(cache_path, exist_ok=True)
    return cache_path


def _hash_str(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def transcribe_audio(file_bytes: bytes, filename: str = "audio.webm") -> str:
    if _is_mock_mode():
        return os.environ.get("LITCOACH_MOCK_TRANSCRIPT", "Hello coach")
    client = get_client()
    model = os.environ.get("LITCOACH_TRANSCRIBE_MODEL", "whisper-1")
    buffer = BytesIO(file_bytes)
    buffer.name = filename
    result = client.audio.transcriptions.create(
        model=model,
        file=buffer,
    )
    return result.text


def synthesize_speech(text: str, voice: str = "alloy") -> bytes:
    model = os.environ.get("LITCOACH_TTS_MODEL", "tts-1")
    cache_key = _hash_str(f"{model}|{voice}|{text}")
    cache_path = os.path.join(_cache_dir(), f"tts_{cache_key}.mp3")
    if _is_mock_mode():
        # Deterministic mock audio bytes
        return ("MOCKMP3:" + cache_key).encode("utf-8")
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as handle:
            return handle.read()

    client = get_client()
    with client.audio.speech.with_streaming_response.create(
        model=model,
        voice=voice,
        input=text,
        format="mp3",
    ) as response:
        audio_bytes = response.read()

    with open(cache_path, "wb") as handle:
        handle.write(audio_bytes)
    return audio_bytes


def chat_with_tools(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    temperature: float = 0.4,
) -> Dict[str, Any]:
    if _is_mock_mode():
        # Produce a deterministic, minimal OpenAI-like dict structure
        last_user = next((m for m in reversed(messages) if m.get("role") == "user"), {})
        user_text = last_user.get("content", "")
        content = os.environ.get(
            "LITCOACH_MOCK_REPLY",
            f"[MOCK ASSISTANT] I heard: {user_text[:80]}"
        )
        return {
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": content},
                }
            ]
        }
    client = get_client()
    model = os.environ.get("LITCOACH_AGENT_MODEL", "gpt-4o-mini")
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        tools=tools,
        tool_choice="auto" if tools else "none",
    )
    return response.to_dict()


def embedding(text: str) -> List[float]:
    model = os.environ.get("LITCOACH_EMBED_MODEL", "text-embedding-3-small")
    cache_key = _hash_str(f"{model}|{text}")
    cache_path = os.path.join(_cache_dir(), f"emb_{cache_key}.json")
    if _is_mock_mode():
        # Stable pseudo-embedding derived from hash
        h = hashlib.sha256(text.encode("utf-8")).digest()
        # Produce 16 floats in [0,1)
        return [int(h[i]) / 255.0 for i in range(16)]
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    client = get_client()
    response = client.embeddings.create(model=model, input=text)
    vector = response.data[0].embedding
    with open(cache_path, "w", encoding="utf-8") as handle:
        json.dump(vector, handle)
    return vector


def b64encode_audio(mp3_bytes: bytes) -> str:
    return base64.b64encode(mp3_bytes).decode("utf-8")

