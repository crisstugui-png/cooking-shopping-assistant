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
OCR Module for the Cooking and Shopping Assistant.

This module provides utility functions to extract text, receipts, prices,
and structured data from images using the Google GenAI SDK and Gemini models.
"""

import os
import logging
from google import genai
from google.genai import types

# Setup logger for the OCR module
logger = logging.getLogger(__name__)

def extract_text_from_image(image_bytes: bytes, mime_type: str) -> str:
    """Extracts text, items, prices, names, and recipe details from image bytes using Gemini.
    
    Args:
        image_bytes: The raw binary data of the uploaded image.
        mime_type: The MIME type of the image (e.g., 'image/png', 'image/jpeg').
        
    Returns:
        The extracted text and structured data as a string. Returns an error message
        string if the API call fails or exceptions are raised.
    """
    logger.info(f"Extracting text from image ({len(image_bytes)} bytes, mime_type: {mime_type})")
    
    # Initialize the Gemini GenAI Client.
    # Since GEMINI_API_KEY is present in the environment (or mapped to GOOGLE_API_KEY),
    # the client will automatically configure itself to use Developer API keys.
    client = genai.Client()
    
    try:
        # Convert raw image bytes into a format expected by the GenAI SDK
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type,
        )
        
        # Define instruction prompt directing Gemini on how to extract text
        extraction_prompt = (
            "Extract all text, items, prices, names, dates, and recipe details from this image. "
            "Output only the extracted text/data verbatim or in structured format, no conversational filler."
        )
        
        # Invoke the Gemini model to parse the image content
        response = client.models.generate_content(
            model='gemini-flash-lite-latest',
            contents=[image_part, extraction_prompt]
        )
        
        # Return the response text, falling back to an empty string if it is empty
        return response.text or ""
        
    except Exception as api_exception:
        # Catch and log any API failures or data parsing issues
        logger.error(f"Failed to extract text from image due to an exception: {api_exception}")
        return f"[Image OCR Failed: {str(api_exception)}]"
