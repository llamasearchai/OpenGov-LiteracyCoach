from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel
from litcoach.services.teacher_api.db import (
    init_schema,
    add_class,
    list_classes,
    upsert_student,
    enroll_student,
    class_students,
    create_assignment,
    class_assignments,
    add_reading_result,
    add_writing_result,
    analytics_overview,
)
import csv
import io
import json


app = FastAPI(title="Literacy Coach Teacher API")


@app.on_event("startup")
def startup():
    init_schema()


@app.get("/health")
def health():
    return {"ok": True, "service": "teacher"}


class ClassCreate(BaseModel):
    name: str


@app.post("/classes")
def create_class(body: ClassCreate):
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="name required")
    return add_class(body.name.strip())


@app.get("/classes")
def get_classes():
    return {"results": list_classes()}


@app.get("/classes/{class_id}/students")
def get_class_students(class_id: str):
    return {"results": class_students(class_id)}


@app.post("/roster/import")
async def roster_import(request: Request, class_id: str = Query(...)):
    content_type = request.headers.get("content-type", "")
    if "text/csv" not in content_type:
        raise HTTPException(status_code=400, detail="Content-Type must be text/csv")
    raw = await request.body()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8")))
    for row in reader:
        student_id = row.get("student_id")
        name = row.get("student_name")
        if not student_id or not name:
            continue
        upsert_student(student_id.strip(), name.strip())
        enroll_student(class_id, student_id.strip())
    return {"ok": True}


class AssignmentCreate(BaseModel):
    class_id: str
    type: str
    title: str
    details: str


@app.post("/assignments")
def create_assign(body: AssignmentCreate):
    if body.type not in ("reading", "writing"):
        raise HTTPException(status_code=400, detail="type must be reading or writing")
    return create_assignment(body.class_id, body.type, body.title.strip(), body.details.strip())


@app.get("/classes/{class_id}/assignments")
def get_assignments(class_id: str):
    return {"results": class_assignments(class_id)}


class ReadingResult(BaseModel):
    user_id: str
    class_id: str | None = None
    assignment_id: str | None = None
    session_id: str
    wcpm: int
    accuracy: float
    errors: List[Dict[str, Any]] | None = None


@app.post("/events/reading_result")
def post_reading_result(body: ReadingResult):
    add_reading_result(
        body.user_id,
        body.class_id,
        body.assignment_id,
        body.session_id,
        body.wcpm,
        body.accuracy,
    )
    return {"ok": True}


class WritingResult(BaseModel):
    user_id: str
    class_id: str | None = None
    assignment_id: str | None = None
    rubric_scores: Dict[str, int]
    feedback: str


@app.post("/events/writing_result")
def post_writing_result(body: WritingResult):
    add_writing_result(
        body.user_id,
        body.class_id,
        body.assignment_id,
        json.dumps(body.rubric_scores),
        body.feedback,
    )
    return {"ok": True}


@app.get("/analytics/overview")
def analytics(class_id: str = Query(...)):
    return analytics_overview(class_id)


def main():
    import uvicorn

    uvicorn.run(
        "litcoach.services.teacher_api.app:app", host="0.0.0.0", port=8004, reload=False, workers=1
    )


if __name__ == "__main__":
    main()


