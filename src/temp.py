from card_index import _universal_cards, _land_cards
from modules.parser import EffectParser
from modules.card_creator import create_card
import os

def test_land_card_generation():
    """Generate card images for all land cards"""
    print("=" * 60)
    print("LAND CARD GENERATOR - Creating cards for all lands")
    print("=" * 60)
    
    for land in _land_cards:
        card_filename = land.name.lower().replace(" ", "_") + ".png"
        output_path = os.path.join("modules", "assets", "cards", card_filename)
        
        # Check if land image exists
        land_image_path = os.path.join("modules", "assets", "lands", card_filename)
        if not os.path.exists(land_image_path):
            print(f"⚠ {land.name:20s} - No image found at {land_image_path}")
        
        card_data = {
            'name': land.name,
            'generic_mana': land.generic_mana,
            'sp_mana': land.sp_mana,
            'description': land.description,
            'effect': land.effect,
            'att': 0,
            'end': 0
        }
        
        try:
            create_card(card_data, output_path)
            print(f"✓ {land.name:20s} → {card_filename}")
        except Exception as e:
            print(f"✗ {land.name:20s} - Failed: {e}")
    
    print("\n" + "=" * 60)
    print(f"Generated {len(_land_cards)} land cards!")
    print("=" * 60)

def test_parser():
    """Test parser against all card effects in card_index.py"""
    all_cards = _universal_cards + _land_cards
    parser = EffectParser()
    
    print("=" * 60)
    print("PARSER TEST - Testing all effects from card_index.py")
    print("=" * 60)
    
    passed = 0
    failed = 0
    errors = []
    
    for card in all_cards:
        effect = card.effect
        
        # Skip empty effects
        if not effect or effect.strip() == "":
            print(f"✓ {card.name:20s} - No effect (OK)")
            passed += 1
            continue
        
        try:
            # Attempt to parse the effect
            parsed = parser.parse(effect)
            print(f"✓ {card.name:20s} - '{effect}'")
            if parsed:
                for instruction in parsed:
                    print(f"  → {instruction}")
            passed += 1
        except Exception as e:
            print(f"✗ {card.name:20s} - FAILED")
            print(f"  Effect: '{effect}'")
            print(f"  Error: {e}")
            failed += 1
            errors.append((card.name, effect, str(e)))
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if errors:
        print("\nFAILED EFFECTS:")
        for name, effect, error in errors:
            print(f"  • {name}: '{effect}'")
            print(f"    Error: {error}")
    else:
        print("\n✓ All effects parsed successfully!")
    
    # Test individual instruction types
    print("\n" + "=" * 60)
    print("INSTRUCTION TYPE COVERAGE")
    print("=" * 60)
    
    all_effects = [card.effect for card in all_cards if card.effect]
    effect_str = " ".join(all_effects)
    
    instruction_types = {
        "Triggers": ["tap?", "attack?", "block?", "enter?"],
        "Actions": ["gen", "draw", "discard", "heal", "count", "return"],
        "Modifiers": ["inc", "dec"],
        "Keywords": ["haste", "flying", "unblockable", "vigilant", "notap", "entertap"],
        "Special": ["global", "graveyard count"]
    }
    
    for category, instructions in instruction_types.items():
        print(f"\n{category}:")
        for inst in instructions:
            found = inst in effect_str
            status = "✓" if found else "✗"
            print(f"  {status} {inst}")

if __name__ == "__main__":
    test_parser()