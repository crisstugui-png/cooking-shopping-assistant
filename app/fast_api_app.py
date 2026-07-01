# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os

import google.auth
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from google.cloud import logging as google_cloud_logging

from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

setup_telemetry()
try:
    _, project_id = google.auth.default()
    logging_client = google_cloud_logging.Client()
    logger = logging_client.logger(__name__)
except Exception:
    import logging
    class LocalLogger:
        def __init__(self):
            self.logger = logging.getLogger(__name__)
            # Ensure standard output configuration
            if not self.logger.handlers:
                sh = logging.StreamHandler()
                sh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
                self.logger.addHandler(sh)
                self.logger.setLevel(logging.INFO)
        def log_struct(self, data: dict, severity: str = "INFO"):
            self.logger.info(f"Local Structured Log [{severity}]: {data}")
        def info(self, msg: str):
            self.logger.info(msg)
        def warning(self, msg: str):
            self.logger.warning(msg)
    logger = LocalLogger()
    logger.warning("Google Cloud Credentials not found. Falling back to local logging.")
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS")
    else ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"]
)
if allow_origins and "*" in allow_origins:
    allow_origins = ["regex:.*"]

# Artifact bucket for ADK (created by Terraform, passed via env var)
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# In-memory session configuration - no persistent storage
session_service_uri = None

artifact_service_uri = f"gs://{logs_bucket_name}" if logs_bucket_name else None

otel_to_cloud = False
try:
    google.auth.default()
    otel_to_cloud = True
except Exception:
    pass

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=artifact_service_uri,
    allow_origins=allow_origins,
    session_service_uri=session_service_uri,
    otel_to_cloud=otel_to_cloud,
)
app.title = "cooking-shopping-assistant"
app.description = "API for interacting with the Agent cooking-shopping-assistant"

from fastapi.staticfiles import StaticFiles
upload_dir = os.path.join(AGENT_DIR, "uploaded_receipts")
os.makedirs(upload_dir, exist_ok=True)
app.mount("/receipts", StaticFiles(directory=upload_dir), name="receipts")

class SaveReceiptRequest(BaseModel):
    fileName: str
    base64Data: str

@app.post("/save-receipt")
def save_receipt(req: SaveReceiptRequest):
    """Saves an uploaded receipt image to the local uploads directory."""
    import base64
    from fastapi import HTTPException
    
    # Clean base64 header if present
    data = req.base64Data
    if "," in data:
        data = data.split(",")[1]
        
    file_path = os.path.join(upload_dir, req.fileName)
    try:
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(data))
        return {"status": "success", "url": f"/api/receipts/{req.fileName}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/uploaded-receipts")
def list_uploaded_receipts():
    """Lists the filenames of all saved receipt images."""
    from fastapi import HTTPException
    try:
        files = [f for f in os.listdir(upload_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
        # Sort by creation time (newest first)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(upload_dir, x)), reverse=True)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


from fastapi.responses import PlainTextResponse
import json
from pydantic import BaseModel

class SaveShoppingListRequest(BaseModel):
    content: str

@app.get("/shopping-list", response_class=PlainTextResponse)
def get_shopping_list():
    """Reads the current shopping list from disk."""
    path = os.path.join(AGENT_DIR, "shopping_list.md")
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return "No shopping list generated yet."

@app.post("/shopping-list")
def save_shopping_list(req: SaveShoppingListRequest):
    """Writes the updated shopping list to disk."""
    path = os.path.join(AGENT_DIR, "shopping_list.md")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"status": "success"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/shopping-history")
def get_shopping_history_data():
    """Reads the shopping history from disk."""
    path = os.path.join(AGENT_DIR, "shopping_history.json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
