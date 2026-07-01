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
import json
import datetime
import logging
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

# File path to store the budget history
HISTORY_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "shopping_history.json"))

def finish_recipe(recipe_name: str, ingredients: list[str], quantities: list[str], tool_context: ToolContext) -> dict:
    """Call this tool when the recipe discussion is complete and a recipe has been selected.
    This tool stores the recipe details in the workflow state and prepares to move to the shopping assistant.

    Args:
        recipe_name: The name of the chosen recipe.
        ingredients: A list of ingredient names (e.g. ['eggs', 'milk', 'flour']).
        quantities: A list of quantities corresponding to each ingredient (e.g. ['2', '1 cup', '200g']).
    """
    logger.info(f"finish_recipe called for recipe: {recipe_name}")
    
    # Store in the session state
    tool_context.state["recipe_name"] = recipe_name
    tool_context.state["recipe_ingredients"] = ingredients
    tool_context.state["recipe_quantities"] = quantities
    tool_context.state["recipe_ready"] = True
    
    # Reset the active agent because the cooking task is complete
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
    """
    logger.info(f"record_purchase called with {len(items)} items")
    
    if not date:
        date = datetime.date.today().isoformat()
        
    processed_items = []
    total = 0.0
    
    for item in items:
        name = item.get("name", "Unknown Item")
        try:
            price = float(item.get("price", 0.0))
        except (ValueError, TypeError):
            price = 0.0
            
        try:
            qty = int(item.get("quantity", 1))
        except (ValueError, TypeError):
            qty = 1
            
        processed_items.append({
            "name": name,
            "price": price,
            "quantity": qty
        })
        total += price * qty
        
    record = {
        "date": date,
        "items": processed_items,
        "total_cost": round(total, 2)
    }
    
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except Exception as e:
            logger.error(f"Error reading history file: {e}")
            history = []
            
    history.append(record)
    
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
    """
    logger.info("get_shopping_history called")
    if not os.path.exists(HISTORY_FILE):
        return []
        
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading history file: {e}")
        return []
