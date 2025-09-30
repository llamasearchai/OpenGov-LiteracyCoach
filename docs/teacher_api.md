# Teacher API

The Teacher API manages classes, rosters, assignments, and results aggregation.

## Endpoints

-  POST /classes
-  GET /classes
-  GET /classes/{class_id}/students
-  POST /roster/import?class_id=... (Content-Type: text/csv; columns: student_id,student_name)
-  POST /assignments (fields: class_id, type=reading|writing, title, details)
-  GET /classes/{class_id}/assignments
-  POST /events/reading_result
-  POST /events/writing_result
-  GET /analytics/overview?class_id=...

The gateway service calls the events endpoints to log assessment results. The teacher.html UI provides a simple dashboard for interacting with these APIs.


