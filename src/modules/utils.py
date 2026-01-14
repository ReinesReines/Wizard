from .parser import EffectParser

effect_parser = EffectParser()

def parse_card_effect(card):
    """
    Parse a card's effect string.
    """
    if hasattr(card, 'effect'):
        return effect_parser.parse(card.effect)
    return []

def get_card_triggers(card):
    """
    Get all triggers from a card.
    """
    if hasattr(card, 'effect'):
        return effect_parser.get_triggers(card.effect)
    return []

def get_card_static_abilities(card):
    """
    Get all static abilities from a card.
    """
    if hasattr(card, 'effect'):
        return effect_parser.get_static_abilities(card.effect)
    return []

def card_has_ability(card, ability):
    """
    Check if a card has a specific static ability.
    """
    return ability in get_card_static_abilities(card)

def card_has_trigger(card, trigger):
    """
    Check if a card has a specific trigger.
    """
    return trigger in get_card_triggers(card)

def get_instructions_by_trigger(card, trigger):
    """
    Get all instructions for a specific trigger.
    """
    instructions = parse_card_effect(card)
    return [inst for inst in instructions if inst.get('trigger') == trigger]

def get_static_instructions(card):
    """
    Get all instructions without triggers (always active).
    """
    instructions = parse_card_effect(card)
    return [inst for inst in instructions if not inst.get('trigger')]

def can_attack_immediately(card):
    """
    Check if a card can attack the turn it's played (has haste).
    """
    return card_has_ability(card, 'haste')

def can_be_blocked(card):
    """
    Check if a card can be blocked.
    """
    return not card_has_ability(card, 'unblockable')

def has_flying(card):
    """
    Check if a card has flying.
    """
    return card_has_ability(card, 'flying')

def taps_when_attacking(card):
    """
    Check if a card taps when attacking.
    """
    return not (card_has_ability(card, 'vigilance') or card_has_ability(card, 'notap'))

def get_mana_colors(land_card):
    """
    Get the mana colors a land can produce.
    """
    instructions = parse_card_effect(land_card)
    colors = []
    
    for inst in instructions:
        if inst.get('action') == 'gen':
            colors.extend(inst.get('colors', []))
    
    return list(set(colors))  # Remove duplicates

def enters_tapped(card):
    """
    Check if a card enters the battlefield tapped.
    """
    instructions = parse_card_effect(card)
    return any(inst.get('action') == 'entertap' for inst in instructions)

def get_card_summary(card):
    """
    Get a summary of a card's parsed effects.
    """
    return {
        'name': card.name,
        'type': card.type,
        'triggers': get_card_triggers(card),
        'static_abilities': get_card_static_abilities(card),
        'instructions': parse_card_effect(card),
        'effect_string': card.effect if hasattr(card, 'effect') else ''
    }
