---
name: readable-vibe-coding
description: >
  This skill should be used when the user wants to "write readable code", "document code",
  "vibe code", "refactor code", "add documentation", "write clear code", "implement cleanly",
  or when writing, modifying, or refactoring code of any kind in the project. It ensures
  that the code remains clear, self-documenting, and is heavily annotated with explanations
  rather than using clever "tricks" or implicit shorthand.
metadata:
  author: Antigravity
  version: 1.0.0
---

# Readable Vibe Coding Skill

This skill enforces code readability, clear documentation, and long-term maintainability across all files in this project. It is designed to ensure that even during rapid "vibe coding" sessions, speed does not degrade code quality and that the reasoning behind implementation choices is preserved.

## Code Readability Principles

### 1. Document the "Why", Not Just the "What"
- **Docstrings:** Every class, function, and module must have a clear docstring explaining its purpose, inputs, outputs, and any side effects or assumptions.
- **Inline Comments:** Write inline comments explaining the intent and logic of any complex, mathematical, or non-obvious blocks.
- **Assumptions & Edge Cases:** If code is written rapidly to get something working, add a comment indicating any assumptions made, potential edge cases, or areas that might need future refinement.

### 2. Prioritize Clarity Over Cleverness
- **Explicit is Better than Implicit:** Do not use implicit type conversions or complex one-liner tricks (e.g., deeply nested list comprehensions, complex lambda functions, or bitwise tricks) when standard, readable structures exist.
- **Descriptive Naming:** Variable, function, and class names must be descriptive and pronounceable. Avoid single-letter variable names (except for simple loop counters like `i` or coordinate references like `x, y`).
- **Intermediate Variables:** Break long, complex boolean conditions or mathematical expressions into intermediate variables with descriptive names.

### 3. Maintain Consistent Structure
- **Type Hinting:** Use Python type hints where applicable to make functions self-documenting.
- **Logical Chunking:** Group related operations together and separate them from other blocks with vertical whitespace and explanatory comments.

---

## Examples

### Clever & Terse (BAD)
```python
def p_d(d):
    # Process data and filter
    return [x['val'] * 1.08 if x['taxable'] else x['val'] for x in d if x.get('status') == 'A' and x.get('qty', 0) > 0]
```

### Clear & Documented (GOOD)
```python
def calculate_taxed_totals(items: list[dict]) -> list[float]:
    """
    Calculates the final price (including tax if applicable) for all active items
    with a non-zero quantity.

    Args:
        items: A list of item dictionaries containing 'status', 'qty', 'val', and 'taxable'.

    Returns:
        A list of calculated prices (floats).
    """
    TAX_RATE_MULTIPLIER = 1.08
    final_prices = []

    for item in items:
        # Skip inactive items or items with no quantity
        if item.get("status") != "A" or item.get("qty", 0) <= 0:
            continue

        base_value = item.get("val", 0.0)

        # Apply sales tax of 8% if the item is marked taxable
        if item.get("taxable"):
            item_total = base_value * TAX_RATE_MULTIPLIER
        else:
            item_total = base_value

        final_prices.append(item_total)

    return final_prices
```
