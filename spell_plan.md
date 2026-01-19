# Spell plan

### New Syntax
Add the following syntax support to the parser:
- Add a field called `creatureid` that takes in the `creature_id` argument in `wizard.py` as a placeholder.
- Allow `/` to be an or keyword, such as `creature/player` to be able to take in optional `player` or `creature id`.
- Add `nomanareset` to prevent the mana pool from being reset.
- Update `global` to apply the subsequent commands to all creatures in the player's hand. `global add <status> <attackonly/blockonly: optional>` to apply a static effect to all creatures, take in an optional third argument called `attackonly` or `blockonly` to apply to all attacking creatures or blocking creatures.
- Add an `add <status> creatureid` to apply a status to `creatureid`.
- Add an `all` keyword to apply to **all active creatures**. For example, `all dec end 1` would decrement all creature endurance by 1.
- - Additionally, check every turn if creature endurance is 0 to kill creatures.
- Add a `kill` action to kill the creature in question. Make sure `global kill` and `all kill` apply, with `global kill` killing active creatures and `all kill` wiping out every single active creature.
- `discard <n> <player: optional>` discards `n` cards. `player` is an optional field that passes priority to the opposing player similar to attack/blocking queue. For example, `discard 3 player` forces the opposing player to choose  3 cards to discard. If they have 3 cards or less, discard all.
- `morph creatureid "Name"`: Turns a card of `id` into a specific card into a card of name. For example, `morph 45 "Skeleton"` turns the creature of ID `45` into a new `Skeleton` card.
- `heal <n>` Heals the player by `n`. If healing by `n` surpasses their HP, simply heal to full HP.
- `heal creatureid <n>` heals a creature ID by `n`. If it surpasses their original HP, simply revert to base endurance.
- `castinc/castdec creatureid att/end <n>` create new `castinc` and `castdec` specifically for spell cards to increment/decrement a `creatureid`'s `att` or `dec` by `n`.
- Add a new temporary `invuln` state to make a creature's `end` to be `inf`. However, when comparing stats (such as taking damage) just make their end  `99999`. Invuln wears off on the next turn and the card returns to its base endurance. Make sure to carry over combat damage.
- Add a new `add <status> <creatureid>` typa deal where it adds a `status` to `creatureid`.
- `revive creatureid`: Revives a creatureid if it's a creature.


### Important stuff
Don't give spells any summoning sickness. They can be played during attack/blocking declarations, but creatures can't.

They go to the graveyard after being cast.
