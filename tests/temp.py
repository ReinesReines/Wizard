import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from modules.parser import EffectParser
from modules.utils import _resolve_expression

# ============================================
# CHANGE THIS VARIABLE TO TEST DIFFERENT EFFECTS
# ============================================
expression = "global inc att 1"
# ============================================

# Mock game state for testing
mock_game_state = {
    "David": {
        "creatures": {
            "12": {"card": {"name": "Goblin Raider", "attack": 2, "defence": 1}},
            "15": {"card": {"name": "Forest Bear", "attack": 2, "defence": 2}},
            "18": {"card": {"name": "Skeleton", "attack": 2, "defence": 2}},
        }
    }
}

# Parse the expression
parser = EffectParser()
instructions = parser.parse(expression)

print("=" * 60)
print(f"EXPRESSION: '{expression}'")
print("=" * 60)

if not instructions:
    print("No instructions parsed (empty effect or parse error)")
else:
    for i, inst in enumerate(instructions, 1):
        print(f"\nInstruction {i}:")
        print(f"  Raw: {inst.get('raw', 'N/A')}")
        print(f"  Trigger: {inst.get('trigger', 'None')}")
        print(f"  Action: {inst.get('action', 'N/A')}")
        print(f"  Field: {inst.get('field', 'N/A')}")
        print(f"  Value (parsed): {inst.get('value', 'N/A')}")
        
        # Try to resolve dynamic values using the built-in function
        if 'value' in inst:
            resolved = _resolve_expression(inst['value'], mock_game_state)
            if resolved != inst['value']:
                print(f"  Value (resolved): {resolved}")
                if isinstance(inst['value'], tuple) and inst['value'][0] == 'graveyard':
                    print(f"    -> (Found {resolved} {inst['value'][2]}(s) in graveyard)")
        
        # Show any special fields
        if inst.get('status'):
            print(f"  Status: {inst['status']}")
        if inst.get('global'):
            print(f"  Global: {inst['global']}")
        
        # If global effect, simulate applying to all creatures
        if inst.get('global') and inst['action'] == 'inc':
            print(f"\n  APPLYING GLOBAL EFFECT TO ALL CREATURES:")
            print(f"  {'Creature':<20} {'Before':<12} {'After':<12}")
            print(f"  {'-'*20} {'-'*12} {'-'*12}")
            
            for cid, creature_data in mock_game_state["David"]["creatures"].items():
                card = creature_data["card"]
                field = inst['field']
                value = inst.get('value', 1)
                
                # Map short field names to full names
                field_map = {'att': 'attack', 'end': 'defence'}
                actual_field = field_map.get(field, field)
                
                # Capture before value (before modification)
                before_att = card['attack']
                before_def = card['defence']
                
                # Apply the increment
                if actual_field in card:
                    card[actual_field] += value
                
                # Capture after value (after modification)
                after_att = card['attack']
                after_def = card['defence']
                
                before = f"{before_att}/{before_def}"
                after = f"{after_att}/{after_def}"
                
                print(f"  {card['name']:<20} {before:<12} {after:<12}")
