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
"""
FastAPI Server Module for the Cooking and Shopping Assistant.

This module initializes the FastAPI web application, mounts static routes for uploaded
receipts, and exposes API endpoints to:
- Save and list uploaded receipt images.
- Receive user feedback.
- Retrieve and update the current shopping list.
- Read historical purchase records.
"""

import os
import google.auth
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import base64
import json

from google.adk.cli.fast_api import get_fast_api_app
from google.cloud import logging as google_cloud_logging

from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

# Initialize OpenTelemetry telemetry hooks
setup_telemetry()

# Configure standard cloud logging or fallback to local terminal logging if not on GCP
try:
    _, project_id = google.auth.default()
    logging_client = google_cloud_logging.Client()
    logger = logging_client.logger(__name__)
except Exception:
    import logging
    class LocalLogger:
        """Fallback logger that mirrors Google Cloud logging format locally."""
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

# Retrieve CORS origins from environment, defaulting to common React dev ports
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS")
    else ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"]
)
if allow_origins and "*" in allow_origins:
    allow_origins = ["regex:.*"]

# Retrieve log/artifact bucket name configured by cloud orchestration templates
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")

# Define the root of our ADK agents project
AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configure in-memory session persistence (None indicates transient, local storage)
session_service_uri = None

# Configure GCS upload destination for ADK session traces
artifact_service_uri = f"gs://{logs_bucket_name}" if logs_bucket_name else None

# Check GCP credentials for exporting traces
otel_to_cloud = False
try:
    google.auth.default()
    otel_to_cloud = True
except Exception:
    pass

# Instantiate the main FastAPI app container wrapping the ADK workspace agents
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

# Setup local static files server directory to serve uploaded receipt images in the playground UI
upload_dir = os.path.join(AGENT_DIR, "uploaded_receipts")
os.makedirs(upload_dir, exist_ok=True)
app.mount("/receipts", StaticFiles(directory=upload_dir), name="receipts")

class SaveReceiptRequest(BaseModel):
    """Schema representing an uploaded receipt image request."""
    fileName: str
    base64Data: str

@app.post("/save-receipt")
def save_receipt(req: SaveReceiptRequest) -> dict[str, str]:
    """Saves a base64 encoded receipt image to the local uploads directory.

    Args:
        req: The SaveReceiptRequest details with base64 data and filename.

    Returns:
        A dictionary containing the success status and the static path to the saved file.
    
    Raises:
        HTTPException: 500 status code if base64 decoding or file writing fails.
    """
    # Parse out the raw base64 data stream by removing standard data headers
    data = req.base64Data
    if "," in data:
        data = data.split(",")[1]
        
    file_path = os.path.join(upload_dir, req.fileName)
    try:
        # Decode base64 bytes and write them to the upload directory
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(data))
        return {"status": "success", "url": f"/api/receipts/{req.fileName}"}
    except Exception as e:
        logger.warning(f"Failed to save uploaded receipt file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/uploaded-receipts")
def list_uploaded_receipts() -> list[str]:
    """Lists the filenames of all saved receipt images sorted by modification time (newest first).

    Returns:
        A list of file name strings matching common image extensions.

    Raises:
        HTTPException: 500 status code if reading the directory fails.
    """
    try:
        # Filter files by typical image extensions
        files = [f for f in os.listdir(upload_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
        
        # Sort the listing by file creation/modification time descending (newest first)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(upload_dir, x)), reverse=True)
        return files
    except Exception as e:
        logger.warning(f"Failed to list uploaded receipts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collects and logs feedback metrics sent from users in the chat UI.

    Args:
        feedback: The Feedback data object conforming to the pydantic model schema.

    Returns:
        A success status dictionary.
    """
    # Log structured dump of the user feedback metrics
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}

class SaveShoppingListRequest(BaseModel):
    """Schema representing a request to overwrite the active shopping list."""
    content: str

@app.get("/shopping-list", response_class=PlainTextResponse)
def get_shopping_list() -> str:
    """Reads and returns the active markdown shopping list from the project filesystem.

    Returns:
        The markdown string contents of shopping_list.md, or a fallback warning message
        if the shopping list file has not yet been generated.
    """
    path = os.path.join(AGENT_DIR, "shopping_list.md")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Failed to read shopping list: {e}")
            return "Failed to retrieve the current shopping list."
    return "No shopping list generated yet."

@app.post("/shopping-list")
def save_shopping_list(req: SaveShoppingListRequest) -> dict[str, str]:
    """Overwrites or updates the local shopping_list.md file content.

    Args:
        req: The SaveShoppingListRequest body with the new markdown text.

    Returns:
        A success status dictionary.

    Raises:
        HTTPException: 500 status code if filesystem write permissions fail.
    """
    path = os.path.join(AGENT_DIR, "shopping_list.md")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"status": "success"}
    except Exception as e:
        logger.warning(f"Failed to update shopping list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/shopping-history")
def get_shopping_history_data() -> list:
    """Reads and returns the JSON shopping trip history records from disk.

    Returns:
        A list of purchase dictionaries from shopping_history.json. Returns an empty list
        if the file does not exist or fails to parse.
    """
    path = os.path.join(AGENT_DIR, "shopping_history.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to parse shopping history JSON: {e}")
            return []
    return []

# Run FastAPI server locally using uvicorn when executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
