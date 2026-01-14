"""
Effect Parser for card effects

Parses the effect strings from cards and breaks them down into
structured instructions that can be executed by the game engine.

Syntax Rules:
- First token is trigger if it ends with '?' (summon?, attack?, block?, tap?, enter?)
- Static abilities: haste, flying, entertap, unblockable, vigilant
- Modifiers: inc, dec
- Actions: gen, draw, discard, heal, return, count
- Places: graveyard, deck
- Parentheses for expressions: inc att (graveyard count Skeleton)

Returns: {'trigger', 'raw', 'action', 'field', 'value'}
"""

import re

class EffectParser:
    """
    Parses card effects.
    
    Examples:
        parser.parse("attack? inc att 2")
        # Returns: {'trigger': 'attack?', 'action': 'inc', 'field': 'att', 'value': 2, 'raw': '...'}
        
        parser.parse("inc att (graveyard count Skeleton)")
        # Returns: {'trigger': None, 'action': 'inc', 'field': 'att', 'value': ('graveyard', 'count', 'Skeleton'), 'raw': '...'}
        
        parser.parse("global inc att 1")
        # Returns: {'trigger': None, 'action': 'inc', 'field': 'att', 'value': 1, 'global': True, 'raw': '...'}
    """
    
    TRIGGERS = ['summon?', 'block?', 'attack?', 'tap?', 'enter?']
    STATIC_ABILITIES = ['haste', 'flying', 'entertap', 'unblockable', 'vigilant', 'notap']
    MODIFIERS = ['inc', 'dec']
    ACTIONS = ['gen', 'draw', 'discard', 'heal', 'return', 'count']
    PLACES = ['graveyard', 'deck']
    FIELDS = ['att', 'end']
    
    def __init__(self):
        pass
    
    def parse(self, effect_string):
        """Parse effect string and return list of instruction dictionaries (semicolon-separated)."""
        if not effect_string or effect_string.strip() == "":
            return []
        
        instructions = []
        raw_instructions = effect_string.split(';')
        
        for instruction in raw_instructions:
            instruction = instruction.strip()
            if instruction:
                parsed = self._parse_single(instruction)
                if parsed:
                    instructions.append(parsed)
        
        return instructions
    
    def _parse_single(self, instruction):
        """Parse single instruction into {'trigger', 'raw', 'action', 'field', 'value'}."""
        result = {
            'trigger': None,
            'raw': instruction,
            'action': None,
            'field': None,
            'value': None
        }
        
        if instruction.strip() in self.STATIC_ABILITIES:
            result['action'] = 'static'
            result['field'] = instruction.strip()
            return result
        
        tokens = self._tokenize(instruction)
        if not tokens:
            return None
        
        idx = 0
        
        if tokens[idx].endswith('?'):
            result['trigger'] = tokens[idx]
            idx += 1
        
        if idx >= len(tokens):
            return result
        
        if tokens[idx] == 'global':
            result['global'] = True
            idx += 1
        
        if idx >= len(tokens):
            return result
        
        # Get action
        action = tokens[idx]
        result['action'] = action
        idx += 1
        
        # Parse based on action type
        if action in self.MODIFIERS:
            if idx < len(tokens):
                result['field'] = tokens[idx]
                idx += 1
            
            if idx < len(tokens):
                if isinstance(tokens[idx], tuple):
                    result['value'] = tokens[idx]
                else:
                    try:
                        result['value'] = int(tokens[idx])
                    except ValueError:
                        result['value'] = 1
            else:
                result['value'] = 1
        
        elif action == 'gen':
            if idx < len(tokens):
                colors = tokens[idx].split('/')
                result['field'] = 'mana'
                result['value'] = colors
        
        elif action in ['draw', 'discard', 'heal']:
            if idx < len(tokens):
                try:
                    result['value'] = int(tokens[idx])
                except ValueError:
                    result['value'] = 1
            else:
                result['value'] = 1
        
        elif action == 'count':
            if idx < len(tokens):
                result['field'] = 'count'
                result['value'] = tokens[idx]
        
        elif action == 'return':
            if idx < len(tokens):
                result['field'] = tokens[idx]
                idx += 1
            if idx < len(tokens):
                result['value'] = tokens[idx]
        
        return result
    
    def _tokenize(self, instruction):
        tokens = []
        current = ""
        depth = 0
        paren_content = ""
        
        for char in instruction:
            if char == '(':
                if depth == 0:
                    if current.strip():
                        tokens.append(current.strip())
                        current = ""
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    inner_tokens = paren_content.strip().split()
                    tokens.append(tuple(inner_tokens))
                    paren_content = ""
            elif depth > 0:
                paren_content += char
            elif char.isspace():
                if current.strip():
                    tokens.append(current.strip())
                    current = ""
            else:
                current += char
        
        if current.strip():
            tokens.append(current.strip())
        
        return tokens
    
    def get_triggers(self, effect_string):
        """Get all triggers from an effect string."""
        instructions = self.parse(effect_string)
        return [inst['trigger'] for inst in instructions if inst.get('trigger')]
    
    def get_static_abilities(self, effect_string):
        """Get all static abilities from an effect string."""
        instructions = self.parse(effect_string)
        return [inst['field'] for inst in instructions if inst.get('action') == 'static']
    
    def has_trigger(self, effect_string, trigger):
        """Check if effect has specific trigger."""
        return trigger in self.get_triggers(effect_string)
    
    def __repr__(self):
        return f"EffectParser()"
