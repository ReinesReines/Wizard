try:
    from .parser import EffectParser
    from .cards import *
except:
    from parser import EffectParser
    from cards import *

effect_parser = EffectParser()

# ====================
# PARSING FUNCTIONS
# ====================

def parse_card_effect(card: Cards) -> list:
    """Parse a card's effect string."""
    if hasattr(card, 'effect'):
        return effect_parser.parse(card.effect)
    return []

def get_card_triggers(card: Cards) -> list:
    """Get all triggers from a card."""
    if hasattr(card, 'effect'):
        return effect_parser.get_triggers(card.effect)
    return []

def get_card_static_abilities(card: Cards) -> list:
    """Get all static abilities from a card."""
    if hasattr(card, 'effect'):
        return effect_parser.get_static_abilities(card.effect)
    return []

def card_has_ability(card: Cards, ability) -> bool:
    """Check if a card has a specific static ability."""
    return ability in get_card_static_abilities(card)

def card_has_trigger(card: Cards, trigger) -> bool:
    """Check if a card has a specific trigger."""
    return trigger in get_card_triggers(card)

def get_instructions_by_trigger(card: Cards, trigger) -> list:
    """Get all instructions for a specific trigger."""
    instructions = parse_card_effect(card)
    return [inst for inst in instructions if inst.get('trigger') == trigger]

def get_static_instructions(card: Cards) -> list:
    """Get all instructions without triggers (always active)."""
    instructions = parse_card_effect(card)
    return [inst for inst in instructions if not inst.get('trigger')]

# ====================
# ABILITY CHECKS
# ====================

def can_attack_immediately(card: Cards) -> bool:
    """Check if a card can attack the turn it's played (has haste)."""
    return card_has_ability(card, 'haste')

def can_be_blocked(card: Cards) -> bool:
    """Check if a card can be blocked."""
    return not card_has_ability(card, 'unblockable')

def has_flying(card: Cards) -> bool:
    """Check if a card has flying."""
    return card_has_ability(card, 'flying')

def taps_when_attacking(card: Cards) -> bool:
    """Check if a card taps when attacking."""
    return not card_has_ability(card, 'vigilant')

def enters_tapped(card: Cards) -> bool:
    """Check if a card enters the battlefield tapped."""
    return card_has_ability(card, 'entertap')

def get_all_keywords(card: Cards) -> list:
    """Extract all keyword abilities from a card's effect."""
    keywords = ['haste', 'flying', 'reach', 'unblockable', 'vigilant', 'entertap', 'trample']
    return [kw for kw in keywords if card_has_ability(card, kw)]

# ====================
# LAND UTILITIES
# ====================

def get_mana_colors(land_card: Cards) -> list:
    """Get the mana colors a land can produce."""
    instructions = parse_card_effect(land_card)
    colors = []
    
    for inst in instructions:
        if inst.get('action') == 'gen':
            colors.extend(inst.get('value', []))
    
    return list(set(colors))

def is_dual_land(land_effect):
    """Check if a land effect string represents a dual land (produces multiple mana types)."""
    return "/" in land_effect

def get_land_colors(land_effect):
    if not land_effect:
        return []
    instructions = effect_parser.parse(land_effect)
    colors = []
    for inst in instructions:
        if inst.get('action') == 'gen':
            colors.extend(inst.get('value', []))
    return list(set(colors))

# ====================
# EXECUTION ENGINE
# ====================

def execute_card(card: Cards, game_state=None, player=None):
    """
    Execute card effects and return modified card with computed values.
    """
    if not isinstance(card, SummonCard):
        return card
    
    import copy
    executed_card = copy.deepcopy(card)
    
    instructions = parse_card_effect(card)
    
    for inst in instructions:
        if inst.get('trigger'):
            continue
        
        action = inst.get('action')
        
        if action == 'inc':
            field = inst.get('field')
            value = inst.get('value')
            
            if isinstance(value, tuple):
                value = _resolve_expression(value, game_state, player)
            
            if field == 'att':
                executed_card.attack += value
            elif field == 'end':
                executed_card.defence += value
        
        elif action == 'dec':
            field = inst.get('field')
            value = inst.get('value')
            
            if isinstance(value, tuple):
                value = _resolve_expression(value, game_state, player)
            
            if field == 'att':
                executed_card.attack -= value
            elif field == 'end':
                executed_card.defence -= value
    
    return executed_card

def _resolve_expression(expr, game_state, player=None):
    """Resolve expression tuple like ('graveyard', 'count', 'Skeleton') to int value."""
    if not isinstance(expr, tuple) or len(expr) == 0:
        return 0
    
    if len(expr) >= 3 and expr[1] == 'count' and game_state and player and player in game_state:
        place = expr[0]
        subject = expr[2]
        if isinstance(subject, str):
            subject = subject.strip('"').strip("'")

        player_data = game_state[player]

        if place == 'mana':
            if not isinstance(subject, str) or not subject:
                return 0
            color = subject.lower()
            return player_data.get(f"{color}_mana", 0)

        if place in ['graveyard', 'deck', 'hand']:
            cards_in_place = player_data.get(place, [])
            if isinstance(cards_in_place, dict):
                cards_iter = cards_in_place.values()
            else:
                cards_iter = cards_in_place
            count = 0
            for card in cards_iter:
                if isinstance(card, dict) and card.get('name') == subject:
                    count += 1
                elif hasattr(card, 'name') and card.name == subject:
                    count += 1
            return count
    
    return 0

def count_in_graveyard(graveyard, card_name) -> int:
    """Count specific cards in graveyard."""
    return sum(1 for card in graveyard if hasattr(card, 'name') and card.name == card_name)

def count_in_deck(deck, card_name) -> int:
    """Count specific cards in deck."""
    return sum(1 for card in deck if hasattr(card, 'name') and card.name == card_name)

# ====================
# CARD SUMMARY
# ====================

def get_card_summary(card: Cards) -> dict:
    """Get a summary of a card's parsed effects."""
    return {
        'name': card.name,
        'type': card.type,
        'triggers': get_card_triggers(card),
        'static_abilities': get_card_static_abilities(card),
        'instructions': parse_card_effect(card),
        'effect_string': card.effect if hasattr(card, 'effect') else ''
    }

# ====================
# TURN PHASE HELPERS
# ====================

def untap_all(cards: Cards) -> list:
    """
    Untap all cards unless they have an upkeep condition preventing it.
    Used at the beginning phase of a turn.
    Returns list of cards that were untapped.
    """
    untapped = []
    for card in cards:
        if hasattr(card, 'tapped'):
            card.status = 0
    return untapped

# ====================
# EXTRAS (idk where to put these)
# ====================

def global_buff(source: Cards, targets: list, game_state=None):
    import copy
    modified_cards = []

    instructions = parse_card_effect(source)
    
    for target in targets:
        if not isinstance(target, SummonCard):
            continue
            
        modified_target = copy.deepcopy(target)
        
        for inst in instructions:
            if inst.get('trigger'):
                continue    # skip
            action = inst.get('action')
            
            if action == 'inc':
                field = inst.get('field')
                value = inst.get('value')
                
                if isinstance(value, tuple):
                    value = _resolve_expression(value, game_state)
                
                if field == 'att':
                    modified_target.attack += value
                elif field == 'end':
                    modified_target.defence += value
            
            elif action == 'dec':
                field = inst.get('field')
                value = inst.get('value')
                
                if isinstance(value, tuple):
                    value = _resolve_expression(value, game_state)
                
                if field == 'att':
                    modified_target.attack -= value
                elif field == 'end':
                    modified_target.defence -= value
        
            modified_cards.append(modified_target)
    
    return modified_cards
