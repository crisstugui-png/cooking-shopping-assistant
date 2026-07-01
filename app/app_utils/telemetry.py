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
Telemetry Module for the Cooking and Shopping Assistant.

This module initializes and configures OpenTelemetry and Google GenAI telemetry hooks.
It handles setting the environment variables needed to export trace metrics and
log prompt-response pairs to a Google Cloud Storage (GCS) bucket when configured.
"""

import logging
import os


def setup_telemetry() -> str | None:
    """Configures OpenTelemetry and GenAI telemetry with GCS log exporting.

    This function checks if the `LOGS_BUCKET_NAME` environment variable is defined.
    If present, and telemetry message capture is enabled, it populates the environment
    variables needed for the GenAI SDK's built-in OTel exporter to write telemetry logs.

    Returns:
        The GCS bucket name (string) if configured, or None if logging is disabled.
    """
    # Fetch the destination Google Cloud Storage bucket name for logging traces.
    gcs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")
    
    # Check if the GenAI prompt-response message content capture is enabled.
    # When enabled, it captures details of requests and responses.
    capture_content = os.environ.get(
        "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "false"
    )
    
    # Enable exporting only if a bucket is specified and content capture is active
    if gcs_bucket_name and capture_content != "false":
        logging.info(
            f"Prompt-response logging enabled - exporting metadata only to bucket: gs://{gcs_bucket_name}"
        )
        
        # Configure logging mode to only capture metadata (preventing sensitive prompts/responses leakage)
        os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "NO_CONTENT"
        
        # Set default format for completion logs to JSON Lines (JSONL)
        os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_UPLOAD_FORMAT", "jsonl")
        
        # Define hook action to upload trace records on completion of calls
        os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_COMPLETION_HOOK", "upload")
        
        # Enable stability features for late-stage experimental OpenTelemetry semantic conventions
        os.environ.setdefault(
            "OTEL_SEMCONV_STABILITY_OPT_IN", "gen_ai_latest_experimental"
        )
        
        # Set telemetry service resource attributes to tag trace outputs
        commit_sha = os.environ.get("COMMIT_SHA", "dev")
        os.environ.setdefault(
            "OTEL_RESOURCE_ATTRIBUTES",
            f"service.namespace=cooking-shopping-assistant,service.version={commit_sha}",
        )
        
        # Construct and set the direct GCS upload path URI
        export_path = os.environ.get("GENAI_TELEMETRY_PATH", "completions")
        os.environ.setdefault(
            "OTEL_INSTRUMENTATION_GENAI_UPLOAD_BASE_PATH",
            f"gs://{gcs_bucket_name}/{export_path}",
        )
    else:
        logging.info(
            "Prompt-response logging is currently disabled. To enable it, set environment variables: "
            "LOGS_BUCKET_NAME=gs://your-bucket and OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT"
        )

    return gcs_bucket_name
