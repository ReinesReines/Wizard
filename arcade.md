# Setup
Use the implementation for `/Users/reines/Wizard/src/wizard.py`

Let the player right click in order to bring up a grey, semi-transparent menu using the `silkscreen` font (found in `/Users/reines/Wizard/src/modules/assets/fonts/Silkscreen-Regular.ttf`) with the following functionality:
- When right-clicking on the card, it must bring up this menu over where it's right clicked on the card. When clicked off, it disappears like a normal menu.
- The text must be in white.
- It shows the following commands when right-clicked on an (inactive) creature card:
- - Play (<generic_cost> <sp_mana>)
- - When played, it pushes the card up to the active section, which is probably just similar to the implementation for your hand cards
- It shows the following commands when right-clicked on an (active) creature card:
- - Attack
- - Nothing should happen so far, just have nothing happen and print "[ID] is attacking"
- It shows the following commands when right-clicked on an (inactive) land card:
- - Play
- - If a card has been played this turn, deselect and print "Can't play land"
- It shows the following commands when right-clicked on an (active) land card:
- - Tap
- - Rotate 90 degrees clockwise when tapped.