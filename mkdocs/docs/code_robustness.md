# Code Robustness

## Error Handling
- Basic error handling is present (e.g., try/except for file and image loading).
- Assumes valid data and file presence; some functions may fail if data is missing or corrupted.
- Game state is always expected to be in a valid format.

## Defensive Programming
- Checks for card existence in hand/deck before actions.
- Uses default values and fallbacks for missing assets (e.g., placeholder images).
- Unique card IDs prevent conflicts in hand/board management.

## Limitations
- No concurrency control for game state file (single-process assumption).
- Limited validation of card data structure.
- Some error messages are printed but not always surfaced to the UI.