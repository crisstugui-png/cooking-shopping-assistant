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
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

def extract_text_from_image(image_bytes: bytes, mime_type: str) -> str:
    """Extracts text, items, prices, names, and recipe details from image bytes using Gemini.
    
    Args:
        image_bytes: The raw bytes of the image.
        mime_type: The mime type of the image (e.g. image/png, image/jpeg).
        
    Returns:
        The extracted text as a string.
    """
    logger.info(f"Extracting text from image ({len(image_bytes)} bytes, mime_type: {mime_type})")
    
    # Initialize the client. Since GEMINI_API_KEY is present in the environment,
    # it will automatically connect using the Developer API.
    client = genai.Client()
    
    try:
        response = client.models.generate_content(
            model='gemini-flash-lite-latest',
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                ),
                "Extract all text, items, prices, names, dates, and recipe details from this image. "
                "Output only the extracted text/data verbatim or in structured format, no conversational filler."
            ]
        )
        return response.text or ""
    except Exception as e:
        logger.error(f"Failed to extract text from image: {e}")
        return f"[Image OCR Failed: {str(e)}]"
