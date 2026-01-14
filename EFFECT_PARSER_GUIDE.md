# Effect Parser Guide

## Overview

The `EffectParser` class interprets card effect strings and converts them into structured data that can be executed by your game engine.

## Quick Start

```python
from src.modules.effect_parser import EffectParser

parser = EffectParser()
instructions = parser.parse("attack? damage player 1; inc att 2")

# Result:
# [
#     {'trigger': 'attack?', 'action': 'damage', 'target': 'player', 'value': 1},
#     {'trigger': None, 'action': 'inc', 'attribute': 'att', 'value': 2}
# ]
```

## Effect Syntax

### Separators
- `;` - Separates multiple instructions
- `|` - Splits description text (not used in effects)
- `/` - Indicates alternative options (e.g., colors)

### Basic Structure
```
[trigger?] action [parameters]
```

## Triggers

Triggers determine when an effect activates:

| Trigger | Description | Example |
|---------|-------------|---------|
| `tap` | Activates when tapped | `tap gen green` |
| `attack?` | When this creature attacks | `attack? damage player 1` |
| `block?` | When this creature blocks | `block? inc end 1` |
| `summon?` | When another creature enters | `summon? inc att 1` |
| `damage player?` | When dealing damage to player | `damage player? discard 1` |
| `enter` | When this enters the battlefield | `enter tap` |

## Actions

### Mana Generation
```
gen [color]           # Generate one color
gen [color/color]     # Generate multiple colors (choose one)
```
**Examples:**
- `tap gen green` - Tap to generate green mana
- `tap gen green/blue` - Tap to generate green or blue mana

### Stat Modifiers
```
inc att [n]    # Increase attack
inc end [n]    # Increase endurance/defense
dec att [n]    # Decrease attack
dec end [n]    # Decrease endurance/defense
```
**Examples:**
- `attack? inc att 2` - Gain +2 attack when attacking
- `block? inc end 1` - Gain +1 endurance when blocking

### Combat Actions
```
damage [target] [n]    # Deal damage
```
**Examples:**
- `attack? damage player 1` - Deal 1 damage when attacking
- `tap damage target 1` - Tap to deal 1 damage

### Card Advantage
```
draw [n]       # Draw cards
discard [n]    # Opponent discards
heal [n]       # Gain life
```
**Examples:**
- `summon? draw 1` - Draw a card when entering
- `damage player? discard 1` - Opponent discards when damaged

### Special Actions
```
global [effect]                # Apply to all creatures
graveyard [operation]          # Interact with graveyard
count [type]                   # Count specific cards
return [from] [to]             # Move cards between zones
entertap                       # Enters battlefield tapped
ignore [what]                  # Ignore game rules
```
**Examples:**
- `global inc att 1` - All creatures get +1 attack
- `graveyard count skeleton; inc att` - +1 attack per skeleton in graveyard
- `entertap; tap gen green/blue` - Enters tapped, taps for mana

## Static Abilities (Keywords)

These are always-active abilities that don't require triggers:

| Keyword | Description |
|---------|-------------|
| `haste` | Can attack immediately |
| `flying` | Can only be blocked by flying/reach |
| `unblockable` | Cannot be blocked |
| `vigilance` | Doesn't tap when attacking |
| `defender` | Cannot attack |
| `first_strike` | Deals combat damage first |
| `lifelink` | Damage heals you |
| `notap` | Attacking doesn't tap this creature |
| `protection [color]` | Protection from a color |

## Parser Methods

### `parse(effect_string)`
Parses an effect string into a list of instruction dictionaries.

```python
parser = EffectParser()
instructions = parser.parse("flying; tap damage target 1")
# Returns list of instruction dicts
```

### `get_triggers(effect_string)`
Extracts all triggers from an effect.

```python
triggers = parser.get_triggers("attack? inc att 2; dec end 1")
# Returns: ['attack?']
```

### `has_trigger(effect_string, trigger)`
Checks if an effect has a specific trigger.

```python
has_attack = parser.has_trigger("attack? damage player 1", "attack?")
# Returns: True
```

### `get_static_abilities(effect_string)`
Extracts all static abilities.

```python
abilities = parser.get_static_abilities("flying; haste")
# Returns: ['flying', 'haste']
```

## Instruction Dictionary Structure

Each parsed instruction returns a dictionary with these possible keys:

```python
{
    'trigger': str or None,      # The trigger (if any)
    'action': str,                # The action type
    'raw': str,                   # Original instruction string
    
    # Action-specific fields:
    'ability': str,               # For static_ability actions
    'colors': list,               # For gen actions
    'attribute': str,             # For inc/dec actions (att/end)
    'value': int,                 # Numeric value
    'target': str,                # Target type
    'scope': str,                 # For global effects
    'effect': dict,               # Nested effect for global
    'operation': str,             # For graveyard actions
    'from': str,                  # For return actions
    'to': str,                    # For return actions
    'what': str,                  # For ignore actions
    # ... and more
}
```

## Real Card Examples

### Basic Land
```python
effect = "tap gen green"
# Tap to generate green mana
```

### Creature with Triggered Ability
```python
effect = "attack? damage player 1"
# When attacking, deal 1 damage to player
```

### Creature with Multiple Effects
```python
effect = "flying; tap damage target 1"
# Has flying, can tap to deal damage
```

### Dual Land
```python
effect = "entertap; tap gen green/blue"
# Enters tapped, taps for green or blue
```

### Growing Creature
```python
effect = "summon? inc att 1; inc end 1"
# Gains +1/+1 when another creature enters
```

### Conditional Buff
```python
effect = "attack? inc att 2; dec end 1"
# +2 attack but -1 endurance when attacking
```

### Lord Effect
```python
effect = "global inc att 1"
# All your other creatures get +1 attack
```

### Graveyard Synergy
```python
effect = "graveyard count skeleton; inc att"
# Gets +1 attack per skeleton in graveyard
```

## Integration Example

```python
from src.modules.effect_parser import EffectParser
from src.modules.utils import parse_card_effect

# Using the parser directly
parser = EffectParser()
card = slime  # Your card object
instructions = parser.parse(card.effect)

# Or use the utility functions
from src.modules.utils import parse_card_effect, get_card_static_abilities

instructions = parse_card_effect(card)
abilities = get_card_static_abilities(card)

# Execute based on game state
for instruction in instructions:
    if instruction['trigger'] == current_trigger:
        # Execute the action
        execute_action(instruction)
```

## Tips for Creating New Cards

1. **Start simple**: Use basic effects first
2. **Combine effects**: Use `;` to chain multiple effects
3. **Add triggers**: Use `?` suffix for triggered abilities
4. **Test parsing**: Use `parser.parse()` to verify syntax
5. **Check examples**: Look at existing cards in `card_index.py`

## Common Patterns

### On-Attack Effects
```python
"attack? damage player 1"
"attack? inc att 2"
```

### On-Block Effects
```python
"block? inc end 1"
```

### Enter Battlefield Effects
```python
"summon? draw 1"
"summon? heal 3"
```

### Tap Abilities
```python
"tap gen green"
"tap damage target 1"
"tap return graveyard hand"
```

### Static Buffs
```python
"global inc att 1"
"global inc end 1"
```

### Multi-Ability Creatures
```python
"flying; haste"
"vigilance; lifelink"
"flying; tap damage target 1"
```

## Troubleshooting

**Effect not parsing?**
- Check for typos in keywords
- Ensure proper semicolon separation
- Verify trigger has `?` suffix
- Check spaces between tokens

**Trigger not firing?**
- Ensure trigger matches exactly (case-sensitive)
- Check if trigger is in TRIGGERS list
- Verify trigger is before the action

**Value not applying?**
- Default value is 1 if not specified
- Check numeric values are valid integers
- Ensure attribute name is correct (att/end)

## Future Enhancements

Potential additions to the parser:
- Cost requirements (e.g., `cost:1 damage target 2`)
- Targeting restrictions (e.g., `target:creature flying`)
- Duration modifiers (e.g., `until end turn`)
- Conditional effects (e.g., `if life < 10`)
- Counter mechanics
- Token generation

---

For more examples, see:
- `demo_parser.py` - Parser demonstration
- `example_game_engine.py` - Integration example
- `card_index.py` - Real card examples
