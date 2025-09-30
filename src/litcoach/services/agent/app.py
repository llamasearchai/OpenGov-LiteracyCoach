import os
import json
from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import yaml

from litcoach.utils.openai_client import chat_with_tools


app = FastAPI(title="Literacy Coach Agent")

CONTENT_URL = os.environ.get("CONTENT_URL", "http://localhost:8002")
ASSESSMENT_URL = os.environ.get("ASSESSMENT_URL", "http://localhost:8003")

with open(
    os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "tutor.yml"),
    "r",
    encoding="utf-8",
) as handle:
    PROMPT_CFG = yaml.safe_load(handle)

SYSTEM_PROMPT = PROMPT_CFG["system"]


def tool_defs() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "lookup_texts",
                "description": "Search leveled texts by lexile, grade, phonics focus, theme",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lexile_min": {"type": "integer"},
                        "lexile_max": {"type": "integer"},
                        "grade_band": {"type": "string"},
                        "phonics_focus": {"type": "string"},
                        "theme": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "rag_search",
                "description": "Semantic search over curated corpus using vector similarity",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "k": {"type": "integer"},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "assess_read_aloud",
                "description": "Compute WCPM and accuracy from read-aloud transcripts",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reference_text": {"type": "string"},
                        "asr_transcript": {"type": "string"},
                        "timestamps": {
                            "type": "array",
                            "items": {"type": "number"},
                        },
                    },
                    "required": ["reference_text", "asr_transcript"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "score_writing",
                "description": "Score a student essay using rubric dimensions and provide feedback",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "essay": {"type": "string"},
                        "grade_level": {"type": "string"},
                        "rubric_name": {"type": "string"},
                    },
                    "required": ["essay", "rubric_name"],
                },
            },
        },
    ]


class Msg(BaseModel):
    role: str
    content: str


class AgentRequest(BaseModel):
    messages: List[Msg]
    mode: str = "tutor"
    student_grade: str | None = None


@app.get("/health")
def health():
    return {"ok": True, "service": "agent"}


async def call_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        if name == "lookup_texts":
            response = await client.post(f"{CONTENT_URL}/texts/search", json=args)
            response.raise_for_status()
            return response.json()
        if name == "rag_search":
            response = await client.post(f"{CONTENT_URL}/rag/search", json=args)
            response.raise_for_status()
            return response.json()
        if name == "assess_read_aloud":
            response = await client.post(f"{ASSESSMENT_URL}/reading/assess", json=args)
            response.raise_for_status()
            return response.json()
        if name == "score_writing":
            response = await client.post(f"{ASSESSMENT_URL}/writing/score", json=args)
            response.raise_for_status()
            return response.json()
    raise HTTPException(status_code=400, detail=f"Unknown tool: {name}")


@app.post("/agent/respond")
async def agent_respond(req: AgentRequest):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
        item.model_dump() for item in req.messages
    ]
    initial = chat_with_tools(messages=messages, tools=tool_defs())
    choice = initial["choices"][0]["message"]
    if "tool_calls" in choice and choice["tool_calls"]:
        tool_results = []
        for call in choice["tool_calls"]:
            fn_name = call["function"]["name"]
            raw_args = call["function"]["arguments"]
            try:
                parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except json.JSONDecodeError:
                parsed_args = {}
            result = await call_tool(fn_name, parsed_args)
            tool_results.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "name": fn_name,
                    "content": json.dumps(result),
                }
            )
        followup_messages = messages + [choice] + tool_results
        second = chat_with_tools(messages=followup_messages, tools=tool_defs())
        final_message = second["choices"][0]["message"]["content"]
        return {"content": final_message}
    return {"content": choice.get("content", "")}


def main():
    import uvicorn

    uvicorn.run("litcoach.services.agent.app:app", host="0.0.0.0", port=8001, reload=False, workers=1)


if __name__ == "__main__":
    main()


