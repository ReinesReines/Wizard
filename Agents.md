# Wizard - MTG-Style Card Game

## Project Overview
A Magic: The Gathering inspired card game with custom cards, mana system, and combat mechanics. Built with Python, uses JSON for game state persistence, and implements an effect parser for dynamic card abilities.

---

## MTG Rules & Mechanics

### Core Concepts

**Turn Structure:**
1. **Untap Step** - Untap all your permanents (creatures, lands)
2. **Upkeep Step** - Trigger upkeep effects (if any)
3. **Draw Step** - Draw 1 card (skip on turn 1 for starting player)
4. **Main Phase (Pre-Combat)** - Play lands, cast creatures, tap lands for mana
5. **Combat Phase** - Declare attackers → Declare blockers → Resolve damage
6. **Main Phase (Post-Combat)** - Play more cards if you have mana
7. **End Phase** - Cleanup temporary effects, clear mana pool

### Mana System

**Lands produce mana when tapped:**
- Forest → green mana
- Island → blue mana  
- Mountain → red mana
- Dual lands → choice of two colors (enter tapped)

**Mana Costs:**
- Cards have a cost like "3 red" = 3 generic + 1 red (total 4 mana)
- Generic mana can be paid with ANY color
- Colored mana MUST be paid with that specific color
- Example: Fire Elemental (3 red) needs 3 generic + 1 red = 4 total

**Rules:**
- Mana pools clear at end of turn
- Can only play 1 land per turn
- Must have enough mana to cast spells/creatures

### Combat System

**Tapping:**
- Creatures tap when attacking (unless vigilant)
- Tapped creatures CANNOT attack or block
- Creatures untap at start of your turn
- Blocking does NOT tap creatures

**Combat Flow:**
1. **Declare Attackers** (active player)
   - Choose which creatures attack
   - Tap attackers (unless vigilant)
   - Trigger "attack?" effects NOW
   
2. **Declare Blockers** (defending player)
   - Choose which creatures block which attackers
   - Flying creatures can only be blocked by flying/reach
   - Unblockable creatures can't be blocked
   - Trigger "block?" effects NOW
   
3. **Damage Resolution**
   - Build damage queue (calculate all damage)
   - Apply ALL damage simultaneously
   - Unblocked attackers damage the defending player
   - Blocked attackers exchange damage with blockers
   - Multiple blockers: attacker assigns damage order, all deal back
   
4. **State-Based Actions**
   - Creatures with defence ≤ 0 die and go to graveyard

**Summoning Sickness:**
- Creatures can't attack the turn they enter (unless haste)
- Creatures CAN block the turn they enter

### Keywords

**Static Abilities:**
- `haste` - Can attack immediately (no summoning sickness)
- `flying` - Can only be blocked by flying or reach creatures
- `reach` - Can block flying creatures
- `unblockable` - Cannot be blocked
- `vigilant` - Doesn't tap when attacking
- `entertap` - Enters the battlefield tapped

**Triggers:**
- `tap?` - When this card is tapped
- `attack?` - When this creature attacks
- `block?` - When this creature blocks
- `enter?` - When this card enters the battlefield

**Actions:**
- `gen [color]` - Generate mana (tap? gen green)
- `draw [n]` - Draw cards
- `inc [field] [n]` - Increase attack/defence
- `dec [field] [n]` - Decrease attack/defence
- `damage [n] [target]` - Deal damage (damage 3 player / damage 2 creature)
- `destroy [target]` - Destroy creature (destroy creature)
- `discard [n]` - Opponent discards cards (discard 2)
- `heal [n]` - Restore health (heal 4)

**Special:**
- `global` - Effect applies to all your creatures (Alpha Wolf)
- `(graveyard count X)` - Dynamic value from graveyard (Skeleton Army)

---

## Functions to Implement

### Phase Management
```python
def start_turn(self, player)
    # Initialize turn, increment counter, set active player

def untap_step(self, player)
    # Untap all creatures and lands
    # Skip creatures with skip_untap flag

def upkeep_step(self, player)
    # Trigger "upkeep?" effects (future)

def draw_step(self, player)
    # Draw 1 card (skip turn 1 for starting player)

def advance_phase(self)
    # Progress: untap → upkeep → draw → main_pre → combat → main_post → end

def end_turn(self, player)
    # Run cleanup_step(), clear_mana_pool(), shift to opponent
```

### Land & Mana System
```python
def play_land(self, player, card_id)
    # Move land from hand to lands dict
    # Check lands_played_this_turn <= 1
    # Apply "entertap" if needed

def tap_land(self, player, land_id)
    # Execute "tap? gen [color]" effect
    # Update blue_mana/red_mana/green_mana
    # Set tapped = 1

def check_mana_cost(self, player, generic, sp_mana)
    # Return True if player has enough mana

def pay_mana(self, player, generic, sp_mana)
    # Deduct colored mana first, then generic from remaining
    # Update mana pool

def clear_mana_pool(self, player)
    # Reset all mana to 0 (called at cleanup)
```

### Combat System
```python
def declare_attackers(self, player, creature_ids: list[str])
    # 1. Validate: check summoning_sickness, tapped
    # 2. Trigger "attack?" effects IMMEDIATELY
    # 3. Tap creatures (unless vigilant)
    # 4. Store in game_state["combat"]["attackers"]

def declare_blockers(self, defender, block_assignments: dict[str, list[str]])
    # block_assignments = {"attacker_id": ["blocker_id1", "blocker_id2"]}
    # 1. Validate: flying/reach, unblockable checks
    # 2. Trigger "block?" effects IMMEDIATELY
    # 3. Store in game_state["combat"]["blocks"]

def assign_damage_order(self, attacker_id, blocker_ids: list[str])
    # For multiple blockers: attacker chooses order
    # Returns ordered list

def calculate_combat_damage(self)
    # Build damage_queue (NO stat changes yet)
    # For each attacker:
    #   - Unblocked: queue damage to player
    #   - 1 blocker: mutual damage
    #   - Multiple: distribute damage, all hit back
    # Store in game_state["combat"]["damage_queue"]

def resolve_damage_queue(self)
    # Apply ALL damage simultaneously
    # creature["card"]["defence"] -= damage (modify in place)
    # game_state[player]["health"] -= damage
    # Call check_creature_deaths()

def check_creature_deaths(self)
    # Find creatures with defence ≤ 0
    # Move to graveyard, delete from battlefield

def can_attack(self, player, creature_id: str)
    # Check summoning_sickness == False, tapped == 0

def can_block(self, blocker_id, attacker_id)
    # Check flying/reach, unblockable
```

### Stat & Effect Management
```python
def apply_temporary_buff(self, creature_id, field, value, duration="end_of_turn")
    # Track buffs that expire (Berserker, Fire Elemental)

def apply_global_effect(self, player, card)
    # Handle "global inc att 1" (Alpha Wolf)
    # Apply to all player's creatures

def cleanup_temporary_effects(self)
    # Remove expired buffs at cleanup step

def update_creature_stats(self, creature_id)
    # Recalculate: base + global + temporary + graveyard counts
```

### Card & Zone Movement
```python
def draw_card(self, player)
    # Move top card from deck to hand

def move_to_graveyard(self, player, card_id, from_zone)
    # Move card to graveyard from battlefield/hand

def discard_card(self, player, card_id)
    # Hand → graveyard

def count_graveyard(self, player, card_name)
    # For "graveyard count Skeleton"
```

### Trigger System
```python
def check_enter_triggers(self, card)
    # Execute "enter?" effects

def check_attack_triggers(self, creature_ids: list[str])
    # Execute "attack?" for all attackers

def check_block_triggers(self, blocker_ids: list[str])
    # Execute "block?" for all blockers
```

### Sorcery System
```python
def cast_sorcery(self, player, card_id)
    # Validate: check phase (must be main phase)
    # Check and pay mana cost
    # Resolve effect immediately
    # Move card from hand to graveyard

def apply_sorcery_effect(self, player, card)
    # Parse effect string and execute
    # Handle: damage, draw, destroy, discard, heal, stat buffs

def deal_damage(self, amount, target, source)
    # target = "player" or creature_id
    # Apply damage to health or creature defence

def destroy_creature(self, creature_id)
    # Move creature to graveyard regardless of defence

def force_discard(self, player, count)
    # Opponent discards N cards from hand
```

### Helper Functions
```python
def has_keyword(self, card, keyword)
    # Check for haste, flying, vigilant, reach, unblockable

def is_tapped(self, player, card_id, zone)
    # Check tapped status

def get_creature(self, player, creature_id: str)
    # Retrieve creature dict from battlefield

def validate_action(self, player, action, phase)
    # Check if action is legal in current phase
```

### Game Flow Control
```python
def execute_turn(self, player)
    # Run full turn loop

def check_win_condition(self)
    # Check health ≤ 0, empty deck

def get_game_state(self)
    # Return formatted state for display
```

---

## Game Simulation Example

### Turn 3 - David's Turn
```
[10:01:00] === TURN 3: David ===

UNTAP STEP:
  [10:01:00] Forest Bear untaps
  [10:01:00] Forest untaps

DRAW STEP:
  [10:01:01] David draws: Skeleton

MAIN PHASE (PRE-COMBAT):
  [10:01:05] David plays Island
  [10:01:08] David taps Forest for green → green_mana: 1
  [10:01:09] David taps Island for blue → blue_mana: 1
  [10:01:13] David plays Skeleton (costs 1 generic + 1 blue)
    → Pays: 1 green + 1 blue ✓
    → Skeleton enters (2/2, haste)
    → status: "haste"
  [10:01:18] David passes priority

COMBAT PHASE:
  [10:01:19] DECLARE ATTACKERS:
    → David attacks with: Forest Bear, Skeleton (has haste!)
    → Forest Bear taps
    → Skeleton taps
  
  [10:01:23] DECLARE BLOCKERS:
    → Max: "Goblin Raider blocks Forest Bear"
    → Goblin Raider (2/1) blocks Forest Bear (2/2)
    → Skeleton is UNBLOCKED
  
  [10:01:25] DAMAGE RESOLUTION:
    → Forest Bear deals 2 to Goblin Raider (2/1 → 2/-1)
    → Goblin Raider deals 2 to Forest Bear (2/2 → 2/0)
    → Skeleton deals 2 to Max (20 → 18)
    
  [10:01:26] STATE-BASED ACTIONS:
    → Goblin Raider dies → Max's graveyard
    → Forest Bear dies → David's graveyard

MAIN PHASE (POST-COMBAT):
  [10:01:28] David passes

END PHASE:
  [10:01:29] Cleanup: Mana pool cleared
    → green_mana: 0, blue_mana: 0

Battlefield:
  David: Skeleton (2/2, tapped)
  Max: (empty)

Health: David 20, Max 18
```

### Combat Example: Multiple Blockers
```
Berserker (5/2) attacks → triggers "attack? inc att 2; dec end 1"
→ Berserker becomes 5/2 temporarily

Max blocks with Slime (2/2) + Goblin Raider (2/1)

DAMAGE ASSIGNMENT (David chooses order):
  → Assign to Slime first: 2 damage (lethal)
  → Assign to Goblin: 3 damage (overkill)

DAMAGE RESOLUTION (simultaneous):
  → Berserker deals 2 to Slime (2/2 → 2/0) ✗
  → Berserker deals 3 to Goblin (2/1 → 2/-2) ✗
  → Slime deals 2 to Berserker (5/2 → 5/0) ✗
  → Goblin deals 2 to Berserker (5/0 → 5/-2) ✗

Result: All three creatures die!
```

---

## Design Decisions & Limits

### What We're Implementing

✓ **Full MTG Turn Structure** - All phases from untap to cleanup  
✓ **Mana System** - 3 colors (red, blue, green), generic costs  
✓ **Combat System** - Attackers, blockers, simultaneous damage  
✓ **Keywords** - haste, flying, reach, vigilant, unblockable, entertap  
✓ **Triggers** - tap?, attack?, block?, enter?  
✓ **Effect Parser** - Dynamic card abilities from text strings  
✓ **Global Effects** - Alpha Wolf buffs all creatures  
✓ **Graveyard Counting** - Skeleton Army scales with graveyard  
✓ **Temporary Buffs** - Combat buffs that expire at cleanup  
✓ **Sorceries** - One-time spell cards with various effects  

### Simplifications

✓ **Sorceries** - One-time spells castable during main phase  
✗ **No Instants** - Can't cast spells during combat/opponent's turn  
✗ **No Priority Passing** - Simplified turn structure  
✗ **No Stack** - Effects resolve immediately  
✗ **No Artifacts/Enchantments** - Future expansion  
✗ **Limited Triggers** - Only tap?, attack?, block?, enter?  
✗ **No Planeswalkers** - Not implemented  
✗ **No Graveyard Recursion** - Can count graveyard but not return cards (yet)  
✗ **3 Colors Only** - Red, Blue, Green (no White, Black)  

### Field Name Mapping

**Important:** Parser uses abbreviated field names, but card objects use full names:
- Parser: `att` / `end`
- Card objects: `attack` / `defence`
- **Must map between them:** `{'att': 'attack', 'end': 'defence'}`

### Card ID System

- All card IDs are **strings** (not integers)
- Stored as dict keys: `creatures["12"]`, not `creatures[12]`
- Maintained for JSON serialization consistency

### Damage Queue System

**Why queue damage before applying?**
- Ensures simultaneous damage resolution
- Both creatures in combat deal their damage even if one would die first
- Example: 2/2 vs 2/2 → both die (not first to deal damage survives)

### Keyword Changes Made

- **Removed:** `notap` (redundant with vigilant)
- **Kept:** `vigilant` as standard MTG keyword
- **Added:** `reach` for blocking flyers

---

## Current Card List

### Creatures (15)

**Green:**
- Slime (1 green, 2/2, vigilant)
- Bigger Slime (2 green, 3/3, vigilant)
- Forest Bear (1 green, 2/2)
- Vine Elemental (3 green, 2/3, enter? inc att 1; inc end 1)
- Alpha Wolf (2 green, 3/2, global inc att 1)

**Blue:**
- Skeleton (2 blue, 2/2, haste; block? inc end 1)
- Skeleton Army (3 blue, 2/2, haste; inc att (graveyard count Skeleton))
- Phantom Warrior (3 blue, 2/3, haste)
- Sea Serpent (4 blue, 5/5)
- Arcane Scholar (2 blue, 1/3, draw 1)
- Vergil (5 blue, 6/6, unblockable)

**Red:**
- Goblin Raider (1 red, 2/1, haste)
- Fire Elemental (3 red, 3/2, attack? inc att 1)
- Dragon Whelp (4 red, 2/3, flying)
- Berserker (2 red, 2/3, attack? inc att 2; dec end 1)

### Lands (6)

**Basic:**
- Forest (tap? gen green)
- Island (tap? gen blue)
- Mountain (tap? gen red)

**Dual (enter tapped):**
- Tropical Grove (entertap; tap? gen green/blue)
- Volcanic Peak (entertap; tap? gen red/blue)
- Wild Highlands (entertap; tap? gen red/green)

### Sorceries (Examples)

**Green:**
- Giant Growth (0 green, inc att 3; inc end 3 - target creature)
- Regrowth (1 green, return creature from graveyard to hand)

**Blue:**
- Divination (2 blue, draw 2)
- Mind Rot (2 blue, discard 2)

**Red:**
- Lightning Strike (2 red, damage 3 creature/player)
- Flame Slash (1 red, damage 4 creature)
- Lava Axe (4 red, damage 5 player)

---

## Implementation Priority

### Phase 1: Core Game Loop
1. `draw_card()`, `start_turn()`, `end_turn()`, `untap_step()`
2. `play_land()`, `tap_land()`, `clear_mana_pool()`
3. Basic turn progression without combat

### Phase 2: Combat System
1. `declare_attackers()`, `declare_blockers()`
2. `calculate_combat_damage()`, `resolve_damage_queue()`
3. `check_creature_deaths()`, `can_attack()`, `can_block()`

### Phase 3: Effects & Triggers
1. Trigger system (`check_enter_triggers()`, `check_attack_triggers()`, etc.)
2. Temporary buff tracking (`apply_temporary_buff()`, `cleanup_temporary_effects()`)
3. Global effects (`apply_global_effect()`)

### Phase 4: Advanced Features
1. Sorcery system (`cast_sorcery()`, `apply_sorcery_effect()`)
2. Sorcery-specific actions (`deal_damage()`, `destroy_creature()`, `force_discard()`)
3. Enter-the-battlefield triggers
4. Graveyard counting mechanics
5. Multiple blockers damage assignment
6. Win condition checking

---

## Testing

Use `tests/temp.py` for effect parser testing:
```python
# Change expression to test different effects
expression = "global inc att 1"
expression = "attack? inc att 2; dec end 1"
expression = "inc att (graveyard count Skeleton)"
```

The test script will:
- Parse the effect
- Show parsed instructions
- Resolve dynamic values (graveyard counts)
- Simulate applying to mock creatures

---

## File Structure

```
Wizard/
├── src/
│   ├── game.py              # Main GameEngine class
│   ├── card_index.py        # All card definitions + syntax docs
│   ├── modules/
│   │   ├── cards.py         # Card classes (SummonCard, LandCards, etc.)
│   │   ├── parser.py        # EffectParser for parsing card effects
│   │   ├── utils.py         # Helper functions (execute_card, triggers, etc.)
│   │   └── card_creator.py  # Generate card images
│   └── modules/assets/
│       ├── cards/           # Generated card images
│       ├── lands/           # Land artwork
│       └── fonts/           # Silkscreen font
├── tests/
│   └── temp.py             # Effect parser testing
├── db/
│   └── game_state.json     # Persistent game state
└── Agents.md               # This file
```

---

## Next Steps

1. Implement Phase 1 functions (core game loop)
2. Test basic turn progression
3. Add combat system (Phase 2)
4. Test combat with simple creatures
5. Add trigger system (Phase 3)
6. Test complex cards (Berserker, Alpha Wolf, Skeleton Army)
7. Implement sorcery system (Phase 4)
8. Add parser actions for sorceries (damage, destroy, discard, heal)
9. Test sorcery cards (Lightning Strike, Divination, etc.)

---

**Version:** 1.0  
**Last Updated:** January 16, 2026  
**Status:** Design complete, ready for implementation
