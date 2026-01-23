# Design Choices

## Data Storage
- Chose JSON for game state for simplicity and human readability.
- Card data as Python dicts allows flexible, dynamic attributes.

## Game Logic
- Split responsibilities: `Wizard` for high-level flow, `GameEngine` for rules/state, UI for rendering.
- Used unique card IDs to avoid ambiguity in hand/board management.
- Decks are shuffled and drawn from as lists, hands/board are dicts for fast lookup.

## UI/UX
- Used Pygame for rendering and input handling.
- Card images and fonts are loaded dynamically, with fallbacks for missing assets.

## Assumptions
- Two-player game, fixed structure.
- All assets and data files are present and valid.
- No concurrent access to game state file.

## Trade-offs
- Simplicity over scalability (single JSON file, no DB).
- Fast prototyping, but less robust for multiplayer/online play.
