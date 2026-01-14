# Game Integration Guide - Using the Effect Parser

This guide shows you **exactly** how to use the effect parser in your actual game implementation.

## 🎮 Core Game Loop Integration

### 1. Setup Phase

```python
from src.modules.parser import EffectParser
from src.card_index import *

class Game:
    def __init__(self):
        self.parser = EffectParser()
        self.player1 = Player("Player 1")
        self.player2 = Player("Player 2")
        self.battlefield = []
        self.stack = []
    
    def play_card(self, player, card):
        """When a player plays a card"""
        # Pay mana cost
        if not self.can_pay_cost(player, card):
            return False
        
        # Add to battlefield
        self.battlefield.append(card)
        
        # Check for enter-battlefield effects
        self.trigger_effects(card, trigger='enter')
        
        # Trigger other cards that care about summoning
        for other_card in self.battlefield:
            if other_card != card:
                self.trigger_effects(other_card, trigger='summon?')
        
        return True
```

## 🎯 Executing Card Effects

### 2. Trigger System

```python
def trigger_effects(self, card, trigger=None, context=None):
    """
    Execute effects for a specific trigger.
    
    Args:
        card: The card whose effects to execute
        trigger: The trigger event ('attack?', 'tap', 'summon?', etc.)
        context: Additional context (target, damage amount, etc.)
    """
    instructions = self.parser.parse(card.effect)
    
    for inst in instructions:
        # Only execute if trigger matches (or no trigger required)
        inst_trigger = inst.get('trigger')
        
        if trigger and inst_trigger != trigger:
            continue  # Skip if wrong trigger
        
        if not trigger and inst_trigger:
            continue  # Skip triggered abilities when checking static
        
        # Execute the instruction
        self.execute_instruction(card, inst, context)
```

### 3. Execute Individual Instructions

```python
def execute_instruction(self, card, instruction, context=None):
    """Execute a single parsed instruction"""
    action = instruction.get('action')
    
    # STATIC ABILITIES (always active)
    if action == 'static_ability':
        # These don't execute, just affect game rules
        # Check them when needed (see "Checking Abilities" section)
        pass
    
    # STAT MODIFICATION
    elif action == 'inc':
        attr = instruction.get('attribute')
        value = instruction.get('value', 1)
        
        if attr == 'att':
            card.attack += value
            print(f"{card.name} gains +{value} attack")
        elif attr == 'end':
            card.defence += value
            print(f"{card.name} gains +{value} endurance")
    
    elif action == 'dec':
        attr = instruction.get('attribute')
        value = instruction.get('value', 1)
        
        if attr == 'att':
            card.attack -= value
        elif attr == 'end':
            card.defence -= value
    
    # DAMAGE
    elif action == 'damage':
        target = instruction.get('target')
        amount = instruction.get('value', 1)
        
        if target == 'player':
            self.current_defending_player.life -= amount
            print(f"{card.name} deals {amount} damage to player")
        elif target == 'target':
            # Requires target selection
            if context and 'target' in context:
                context['target'].defence -= amount
    
    # CARD ADVANTAGE
    elif action == 'draw':
        amount = instruction.get('value', 1)
        self.draw_cards(self.active_player, amount)
        print(f"Draw {amount} card(s)")
    
    elif action == 'discard':
        amount = instruction.get('value', 1)
        self.discard_cards(self.defending_player, amount)
    
    elif action == 'heal':
        amount = instruction.get('value', 1)
        self.active_player.life += amount
    
    # MANA GENERATION
    elif action == 'gen':
        colors = instruction.get('colors', [])
        # Player chooses which color if multiple
        chosen_color = self.choose_color(colors)
        self.active_player.mana_pool[chosen_color] += 1
    
    # GLOBAL EFFECTS
    elif action == 'global':
        sub_effect = instruction.get('effect')
        # Apply to all other creatures
        for creature in self.battlefield:
            if creature != card and creature.type == 'Creature':
                self.execute_instruction(creature, sub_effect, context)
    
    # GRAVEYARD OPERATIONS
    elif action == 'graveyard':
        operation = instruction.get('operation')
        # Parse the operation (e.g., "count skeleton")
        if 'count' in operation:
            card_type = operation.split('count')[1].strip()
            count = self.count_in_graveyard(card_type)
            # Usually followed by an inc/dec
            return {'count': count}
    
    # SPECIAL ABILITIES
    elif action == 'entertap':
        card.tapped = 1
        print(f"{card.name} enters tapped")
    
    elif action == 'return':
        from_zone = instruction.get('from')
        to_zone = instruction.get('to')
        # Move card between zones
        self.move_card(from_zone, to_zone, context.get('target_card'))
```

## 🛡️ Checking Static Abilities

### 4. Combat & Game Rules

```python
from src.modules.utils import *

def can_attack(self, creature):
    """Check if a creature can attack"""
    # Check if it has defender
    if card_has_ability(creature, 'defender'):
        return False
    
    # Check if it has summoning sickness (no haste)
    if creature.just_played and not can_attack_immediately(creature):
        return False
    
    return True

def can_block(self, blocker, attacker):
    """Check if a blocker can block an attacker"""
    # Unblockable creatures can't be blocked
    if not can_be_blocked(attacker):
        return False
    
    # Flying creatures can only be blocked by flying/reach
    if has_flying(attacker) and not has_flying(blocker):
        return False
    
    return True

def resolve_combat_damage(self, attacker, blocker=None):
    """Resolve combat damage"""
    # Check for triggered abilities on attack
    self.trigger_effects(attacker, trigger='attack?')
    
    if blocker:
        # Check for block triggers
        self.trigger_effects(blocker, trigger='block?')
        
        # First strike damage
        if card_has_ability(attacker, 'first_strike'):
            blocker.defence -= attacker.attack
            if blocker.defence <= 0:
                self.destroy_creature(blocker)
                return  # Blocker died before dealing damage
        
        # Regular damage
        blocker.defence -= attacker.attack
        attacker.defence -= blocker.attack
        
        # Check for lifelink
        if card_has_ability(attacker, 'lifelink'):
            self.active_player.life += attacker.attack
    else:
        # Unblocked - damage to player
        self.defending_player.life -= attacker.attack
        
        # Trigger damage-to-player effects
        self.trigger_effects(attacker, trigger='damage player?')
    
    # Check for deaths
    if attacker.defence <= 0:
        self.destroy_creature(attacker)
    if blocker and blocker.defence <= 0:
        self.destroy_creature(blocker)

def untap_step(self, player):
    """Untap all permanents"""
    for card in self.battlefield:
        if card.controller == player:
            # Check if card has vigilance or notap
            if not taps_when_attacking(card):
                card.tapped = 0
            else:
                card.tapped = 0
```

## 🏗️ Land System

### 5. Playing and Tapping Lands

```python
def play_land(self, player, land):
    """Play a land card"""
    if player.lands_played_this_turn >= 1:
        return False  # Can only play one land per turn
    
    # Add to battlefield
    self.battlefield.append(land)
    land.controller = player
    player.lands_played_this_turn += 1
    
    # Check if it enters tapped
    if enters_tapped(land):
        land.tapped = 1
        print(f"{land.name} enters tapped")
    
    return True

def tap_land_for_mana(self, land):
    """Tap a land to generate mana"""
    if land.tapped:
        return False
    
    # Get available colors
    colors = get_mana_colors(land)
    
    if len(colors) == 1:
        # Auto-tap for that color
        chosen_color = colors[0]
    else:
        # Player chooses
        chosen_color = self.choose_color(colors)
    
    # Add to mana pool
    self.active_player.mana_pool[chosen_color] += 1
    land.tapped = 1
    
    # Trigger tap abilities (if any)
    self.trigger_effects(land, trigger='tap')
    
    return True
```

## 🎲 Activated Abilities

### 6. Tap Abilities

```python
def use_tap_ability(self, card, target=None):
    """Use a card's tap ability"""
    if card.tapped:
        return False  # Already tapped
    
    # Tap the card
    card.tapped = 1
    
    # Execute tap-triggered effects
    context = {'target': target} if target else None
    self.trigger_effects(card, trigger='tap', context=context)
    
    return True

# Example usage:
# Dragon Whelp: "flying; tap damage target 1"
dragon = dragon_whelp
target_creature = opponent_creature

if use_tap_ability(dragon, target=target_creature):
    print(f"{dragon.name} uses tap ability on {target_creature.name}")
```

## 📊 Complex Effect Examples

### 7. Real Card Scenarios

#### Skeleton (Block Trigger)
```python
# Skeleton: "block? inc end 1"

# When skeleton blocks:
skeleton = get_blocking_creature()
self.trigger_effects(skeleton, trigger='block?')

# Parser executes: {'action': 'inc', 'attribute': 'end', 'value': 1}
# Result: skeleton.defence += 1
```

#### Fire Elemental (Attack Trigger)
```python
# Fire Elemental: "attack? damage player 1"

# When fire elemental attacks:
self.trigger_effects(fire_elemental, trigger='attack?')

# Parser executes: {'action': 'damage', 'target': 'player', 'value': 1}
# Result: defending_player.life -= 1
```

#### Vine Elemental (Summon Trigger)
```python
# Vine Elemental: "summon? inc att 1; inc end 1"

# When ANY creature enters battlefield:
for creature in self.battlefield:
    if creature.type == 'Creature':
        self.trigger_effects(creature, trigger='summon?')

# For vine elemental, parser executes:
# 1. {'action': 'inc', 'attribute': 'att', 'value': 1}
# 2. {'action': 'inc', 'attribute': 'end', 'value': 1}
# Result: vine_elemental.attack += 1, vine_elemental.defence += 1
```

#### Alpha Wolf (Global Effect)
```python
# Alpha Wolf: "global inc att 1"

# Check during combat damage calculation:
instructions = self.parser.parse(alpha_wolf.effect)

for inst in instructions:
    if inst['action'] == 'global':
        # Apply +1 attack to all your other creatures
        sub_effect = inst['effect']  # {'action': 'inc', 'attribute': 'att', 'value': 1}
        
        for creature in self.battlefield:
            if creature != alpha_wolf and creature.controller == alpha_wolf.controller:
                creature.attack += 1
```

#### Skeleton Army (Graveyard Synergy)
```python
# Skeleton Army: "graveyard count skeleton; inc att"

# When calculating stats:
instructions = self.parser.parse(skeleton_army.effect)

count = 0
for inst in instructions:
    if inst['action'] == 'graveyard':
        # Count skeletons in graveyard
        count = len([c for c in self.graveyard if 'skeleton' in c.name.lower()])
    elif inst['action'] == 'inc':
        # Apply the count
        skeleton_army.attack += count
```

## 🔄 Turn Structure Example

### 8. Full Turn Flow

```python
def play_turn(self, player):
    """Execute a full turn"""
    
    # 1. UNTAP STEP
    self.untap_step(player)
    
    # 2. DRAW STEP
    self.draw_cards(player, 1)
    
    # 3. MAIN PHASE 1
    # Play lands, creatures, etc.
    
    # 4. COMBAT PHASE
    # Declare attackers
    attackers = player.choose_attackers()
    for attacker in attackers:
        # Check if it taps when attacking
        if taps_when_attacking(attacker):
            attacker.tapped = 1
        
        # Trigger attack effects
        self.trigger_effects(attacker, trigger='attack?')
    
    # Declare blockers
    blockers = self.defending_player.choose_blockers(attackers)
    for blocker in blockers:
        self.trigger_effects(blocker, trigger='block?')
    
    # Resolve combat
    for attacker in attackers:
        blocker = blockers.get(attacker)
        self.resolve_combat_damage(attacker, blocker)
    
    # 5. MAIN PHASE 2
    # Play more cards
    
    # 6. END STEP
    # Clean up temporary effects
    player.mana_pool = {'green': 0, 'blue': 0, 'red': 0}
```

## 💡 Quick Reference

### Common Patterns

```python
# Check if creature can attack immediately
if can_attack_immediately(creature):
    # Has haste, can attack this turn
    pass

# Check if creature is unblockable
if not can_be_blocked(creature):
    # Must go through
    pass

# Get land colors
colors = get_mana_colors(land)

# Execute triggered ability
self.trigger_effects(card, trigger='attack?')

# Check for specific ability
if card_has_ability(card, 'flying'):
    # Handle flying logic
    pass

# Parse all effects
instructions = self.parser.parse(card.effect)
for inst in instructions:
    self.execute_instruction(card, inst)
```

## 🚀 Minimal Working Example

```python
from src.modules.parser import EffectParser
from src.modules.utils import *
from src.card_index import *

class SimpleGame:
    def __init__(self):
        self.parser = EffectParser()
        self.battlefield = []
    
    def attack_with_creature(self, attacker):
        """Simple attack function"""
        print(f"\n{attacker.name} attacks!")
        
        # Trigger attack effects
        instructions = self.parser.parse(attacker.effect)
        
        for inst in instructions:
            if inst.get('trigger') == 'attack?':
                if inst['action'] == 'damage':
                    target = inst['target']
                    value = inst['value']
                    print(f"  Deals {value} damage to {target}!")
                
                elif inst['action'] == 'inc':
                    attr = inst['attribute']
                    value = inst['value']
                    if attr == 'att':
                        attacker.attack += value
                        print(f"  Gains +{value} attack!")

# Test it!
game = SimpleGame()
game.attack_with_creature(fire_elemental)
# Output:
# Fire Elemental attacks!
#   Deals 1 damage to player!

game.attack_with_creature(berserker)
# Output:
# Berserker attacks!
#   Gains +2 attack!
```

## 📝 Summary

**The parser does the hard work of interpreting effects. You just need to:**

1. **Call `parser.parse(card.effect)`** to get structured instructions
2. **Loop through instructions** and check triggers
3. **Execute based on action type** (damage, inc, dec, etc.)
4. **Use utility functions** for common checks (`can_attack_immediately`, `has_flying`, etc.)

The parser converts text like `"attack? damage player 1"` into:
```python
{'trigger': 'attack?', 'action': 'damage', 'target': 'player', 'value': 1}
```

Then your game logic executes it:
```python
if inst['trigger'] == 'attack?':
    if inst['action'] == 'damage':
        defending_player.life -= inst['value']
```

**That's it!** The parser handles all the complex string parsing, you just handle game logic.
