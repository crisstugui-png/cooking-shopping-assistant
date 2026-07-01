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
Tools Module for the Cooking and Shopping Assistant.

This module provides tools for:
- Completing a recipe discussion and transitioning the state.
- Recording grocery purchases and appending them to local JSON history.
- Retrieving overall grocery shopping history.
"""

import os
import json
import datetime
import logging
from google.adk.tools import ToolContext

# Setup logger for the Tools module
logger = logging.getLogger(__name__)

# File path where the local budget and shopping history is stored in JSON format.
# Resolves to a file in the parent project directory.
HISTORY_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "shopping_history.json"))

def finish_recipe(recipe_name: str, ingredients: list[str], quantities: list[str], tool_context: ToolContext) -> dict:
    """Call this tool when the recipe discussion is complete and a recipe has been selected.
    This tool stores the recipe details in the workflow state and prepares to move to the shopping assistant.

    Args:
        recipe_name: The name of the chosen recipe.
        ingredients: A list of ingredient names (e.g. ['eggs', 'milk', 'flour']).
        quantities: A list of quantities corresponding to each ingredient (e.g. ['2', '1 cup', '200g']).
        tool_context: The shared ToolContext containing session and state information.

    Returns:
        A dictionary indicating the success status and details of the saved recipe.
    """
    logger.info(f"finish_recipe called for recipe: {recipe_name}")
    
    # Store the finalized recipe details inside the ToolContext session state.
    # These will be read by the downstream shopping assistant node.
    tool_context.state["recipe_name"] = recipe_name
    tool_context.state["recipe_ingredients"] = ingredients
    tool_context.state["recipe_quantities"] = quantities
    tool_context.state["recipe_ready"] = True
    
    # Clear the active agent route so the workflow router knows the cooking session has ended
    # and transitions the flow control.
    tool_context.state["active_agent"] = None

    return {
        "status": "success",
        "message": f"Recipe '{recipe_name}' has been finalized and ingredients forwarded to the shopping list generator.",
        "recipe_name": recipe_name,
        "ingredients_count": len(ingredients)
    }

def record_purchase(items: list[dict], date: str = None) -> dict:
    """Appends a new purchase record to the local shopping history.
    Call this tool ONLY when the user explicitly confirms they have actually purchased/bought the items.
    DO NOT call this tool for recipe discussions, shopping lists, or planned future trips.

    Args:
        items: A list of items purchased. Each item must be a dictionary with 'name' (str), 'price' (float), and optional 'quantity' (int, default 1). E.g. [{"name": "eggs", "price": 4.99, "quantity": 1}]
        date: The date of purchase in YYYY-MM-DD format. Defaults to today's date if not provided.

    Returns:
        A dictionary containing the success or error status, a descriptive message, and the saved record data.
    """
    logger.info(f"record_purchase called with {len(items)} items")
    
    # Fallback to today's date if date is unspecified or empty
    if not date:
        date = datetime.date.today().isoformat()
        
    processed_items = []
    total_cost = 0.0
    
    # Process and sanitize each item in the purchase list
    for item in items:
        # Default name if missing
        name = item.get("name", "Unknown Item")
        
        # Coerce price to float, defaulting to 0.0 on error
        try:
            price = float(item.get("price", 0.0))
        except (ValueError, TypeError):
            logger.warning(f"Failed parsing price for item '{name}', defaulting to 0.0")
            price = 0.0
            
        # Coerce quantity to int, defaulting to 1 on error
        try:
            qty = int(item.get("quantity", 1))
        except (ValueError, TypeError):
            logger.warning(f"Failed parsing quantity for item '{name}', defaulting to 1")
            qty = 1
            
        processed_items.append({
            "name": name,
            "price": price,
            "quantity": qty
        })
        # Keep a running total of the purchase cost
        total_cost += price * qty
        
    # Construct the final record schema
    record = {
        "date": date,
        "items": processed_items,
        "total_cost": round(total_cost, 2)
    }
    
    history = []
    # If the history file already exists, read and parse the current records
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except Exception as e:
            logger.error(f"Error reading history file: {e}")
            history = []
            
    # Append the new record to the list
    history.append(record)
    
    # Write the updated records back to the local history file
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"Error writing history file: {e}")
        return {"status": "error", "message": f"Failed to save purchase history: {str(e)}"}
        
    return {
        "status": "success",
        "message": f"Recorded purchase of {len(processed_items)} items on {date}. Total cost: ${record['total_cost']:.2f}.",
        "record": record
    }

def get_shopping_history() -> list:
    """Reads and returns the complete shopping history from shopping_history.json.
    Use this tool when answering queries about past grocery expenses, costs, and purchase details.

    Returns:
        A list of purchase records, where each record contains 'date', a list of 'items', and 'total_cost'.
        Returns an empty list if no history file exists or if reading fails.
    """
    logger.info("get_shopping_history called")
    
    # If file doesn't exist, return empty history list
    if not os.path.exists(HISTORY_FILE):
        return []
        
    # Read, parse, and return JSON content
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading history file: {e}")
        return []
