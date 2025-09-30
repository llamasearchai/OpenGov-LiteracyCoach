import json
from typing import List, Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel
from litcoach.utils.audio import estimate_speaking_duration_timestamps, tokens
from litcoach.utils.openai_client import chat_with_tools


app = FastAPI(title="Literacy Coach Assessment")


class ReadAloudInput(BaseModel):
    reference_text: str
    asr_transcript: str
    timestamps: List[float] | None = None


class ReadAloudResult(BaseModel):
    wcpm: int
    accuracy: float
    errors: List[Dict[str, Any]]


class WriteInput(BaseModel):
    prompt: str
    essay: str
    grade_level: str
    rubric_name: str


class WriteScore(BaseModel):
    rubric_scores: Dict[str, int]
    feedback: str


@app.get("/health")
def health():
    return {"ok": True, "service": "assessment"}


@app.post("/reading/assess", response_model=ReadAloudResult)
def assess_reading(body: ReadAloudInput):
    reference_tokens = tokens(body.reference_text)
    hypothesis_tokens = tokens(body.asr_transcript)
    correct = sum(
        1 for expected, said in zip(reference_tokens, hypothesis_tokens) if expected.lower() == said.lower()
    )
    accuracy = correct / max(1, len(reference_tokens))
    duration_minutes = estimate_speaking_duration_timestamps(body.timestamps or [0.0, 60.0]) / 60.0
    wcpm = int(round(len(hypothesis_tokens) / max(0.016, duration_minutes)))
    errors = []
    for index, (expected, said) in enumerate(zip(reference_tokens, hypothesis_tokens)):
        if expected.lower() != said.lower():
            errors.append(
                {
                    "pos": index,
                    "expected": expected,
                    "said": said,
                    "type": "mismatch",
                }
            )
    return {"wcpm": wcpm, "accuracy": round(accuracy, 2), "errors": errors}


@app.post("/writing/score", response_model=WriteScore)
def score_writing(body: WriteInput):
    system_message = (
        "Score the student's writing using the rubric. Return JSON with rubric_scores (1-4 per dimension) "
        "and feedback (specific next steps)."
    )
    user_message = (
        f"Rubric: {body.rubric_name}\nGrade level: {body.grade_level}\n"
        f"Prompt:\n{body.prompt}\nEssay:\n{body.essay}\n"
        "Return a JSON object with fields rubric_scores and feedback."
    )
    response = chat_with_tools(
        messages=[{"role": "system", "content": system_message}, {"role": "user", "content": user_message}],
        tools=None,
        temperature=0.0,
    )
    content = response["choices"][0]["message"]["content"]
    try:
        parsed: Dict[str, Any] = {}
        parsed = json.loads(content)
        raw_scores = parsed.get("rubric_scores", {})
        feedback = parsed.get("feedback", "")
        clean_scores: Dict[str, int] = {}
        for key, value in raw_scores.items():
            try:
                clean_scores[key] = int(value)
            except Exception:
                clean_scores[key] = 3
        return {"rubric_scores": clean_scores, "feedback": feedback}
    except Exception:
        return {
            "rubric_scores": {
                "ideas": 3,
                "organization": 3,
                "evidence": 3,
                "conventions": 3,
            },
            "feedback": content,
        }


def main():
    import uvicorn

    uvicorn.run(
        "litcoach.services.assessment.app:app", host="0.0.0.0", port=8003, reload=False, workers=1
    )


if __name__ == "__main__":
    main()


