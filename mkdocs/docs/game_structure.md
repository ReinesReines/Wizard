# Game Structure

## High-Level Flow

```mermaid
graph TD
    A[Start Game] --> B[Initialize Players & Decks]
    B --> C[Draw Opening Hands]
    C --> D[Main Game Loop]
    D --> E[Player Turn]
    E --> F[Untap, Draw, Main, Combat, End]
    F --> G[Check Win Condition]
    G -->|No Winner| D
    G -->|Winner| H[Game Over]
```

## Main Components
- **Wizard**: High-level game controller, manages turns and player actions.
- **GameEngine**: Handles game state, rules, and core logic.
- **Card Objects**: Represent creatures, lands, and spells.
- **UI (main.py)**: Handles rendering and user interaction.

## State Transitions
- State is updated after every action (play, cast, attack, etc.).
- Each phase (untap, draw, main, combat, end) is handled in sequence.

## Example Turn Flow
1. Untap step
2. Draw step
3. Main phase (play cards, lands, spells)
4. Combat phase (declare attackers/blockers, resolve damage)
5. End phase (cleanup, discard, check win)
