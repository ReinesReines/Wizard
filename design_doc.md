# Wizard
Wizard is a card game based off the popular card game known as *Magic the Gathering*. Players play as powerful Wizar (plural: Wizard) in order to try and reduce their opponent's hitpoints to zero. Their primary method to deal damage is by summoning creatures to do their bidding. They can also use spells to try and damage other creatures.

## Assumptions
- Assumes that `game_state.json` has all the required assets and information.
- Uses dictionaries with expected keys.
- That Card IDs are uniquely tied to their respective cards.
- Image files are handled in a specific way
- Placeholders are always available
- Many functions assume that data is valid.
- Assumes that `game_state.json` is always in a valid state.
