# Data Handling

## Overview
- Game state is stored in a JSON file (`db/game_state.json`).
- Card data is represented as Python dictionaries with keys like `attack`, `defence`, `type`, `effect`, `name`, etc.
- Player hands, decks, graveyards, and battlefield are tracked as dictionaries or lists within the game state.
- Assets (images, fonts) are loaded from the `src/modules/assets` directory.

## Data Flow
- On each action (play card, cast spell, etc.), the game state is loaded, modified, and saved back to disk.
- Card IDs are unique and used as keys for quick lookup.
- Decks are shuffled using Python's `random.shuffle`.

## Assumptions
- The JSON file is always accessible and not corrupted.
- Only one process accesses the game state at a time (no concurrency issues).
- Card data is always valid and complete.

## Example
```python
# Example card dictionary
{
  "id": 1,
  "name": "Forest Bear",
  "type": "Creature",
  "attack": 2,
  "defence": 2,
  "effect": "vigilant"
}
```
