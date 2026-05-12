"""
Demo receiver — run alongside the Streamlit app during live demos.
Usage:  python receiver.py   (or: venv/bin/python receiver.py)

Accepts:  POST http://<your-laptop-ip>:8765/demo
Body:     {"company": "TutorBridge", "brief": "We are building..."}

Writes the payload to /tmp/demo_brief.json, which app.py reads on demand.
"""
import json, pathlib
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn

DEMO_FILE = pathlib.Path("/tmp/demo_brief.json")


async def receive_demo(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON"}, status_code=400)

    company = data.get("company", "").strip()
    brief = data.get("brief", "").strip()

    if not company or not brief:
        return JSONResponse({"error": "company and brief are required"}, status_code=400)

    DEMO_FILE.write_text(json.dumps({"company": company, "brief": brief}))
    return JSONResponse({"status": "ok", "company": company})


app = Starlette(routes=[Route("/demo", receive_demo, methods=["POST"])])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8765)
