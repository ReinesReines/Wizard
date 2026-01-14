"""
Effect Parser for card effects

Parses the effect strings from cards and breaks them down into
structured instructions that can be executed by the game engine.
"""

class EffectParser:
    """
    Parses card effect strings into structured data.
    
    Example:
        parser = EffectParser()
        instructions = parser.parse("attack? damage player 1; inc att 2")
        # Returns: [
        #     {'trigger': 'attack?', 'action': 'damage', 'target': 'player', 'value': 1},
        #     {'trigger': None, 'action': 'inc', 'attribute': 'att', 'value': 2}
        # ]
    """
    
    # Keywords that can be triggers (end with ?)
    TRIGGERS = ['tap', 'attack?', 'block?', 'summon?', 'damage player?', 'enter']
    
    # Keywords that are static abilities (no trigger needed)
    STATIC_ABILITIES = ['haste', 'flying', 'unblockable', 'vigilance', 'defender', 
                        'first_strike', 'lifelink', 'notap']
    
    # Actions that modify stats
    STAT_MODIFIERS = ['inc', 'dec']
    
    # Actions that deal with cards/game state
    ACTIONS = ['gen', 'damage', 'draw', 'discard', 'heal', 'return', 'count']
    
    # Attributes that can be modified
    ATTRIBUTES = ['att', 'end']
    
    # Valid colors
    COLORS = ['green', 'blue', 'red', 'black', 'white']
    
    def __init__(self):
        self.instructions = []
    
    def parse(self, effect_string):
        """
        Parse an effect string and return a list of instruction dictionaries.
        
        Args:
            effect_string (str): The effect string to parse
            
        Returns:
            list: List of instruction dictionaries
        """
        if not effect_string or effect_string.strip() == "":
            return []
        
        self.instructions = []
        
        # Split by semicolon to get individual instructions
        raw_instructions = effect_string.split(';')
        
        for instruction in raw_instructions:
            instruction = instruction.strip()
            if instruction:
                parsed = self._parse_instruction(instruction)
                if parsed:
                    self.instructions.append(parsed)
        
        return self.instructions
    
    def _parse_instruction(self, instruction):
        """
        Parse a single instruction into a structured dictionary.
        
        Args:
            instruction (str): A single instruction string
            
        Returns:
            dict: Parsed instruction or None if invalid
        """
        tokens = instruction.split()
        if not tokens:
            return None
        
        result = {
            'trigger': None,
            'action': None,
            'raw': instruction
        }
        
        # Check if first token is a trigger
        if tokens[0] in self.TRIGGERS or tokens[0].endswith('?'):
            result['trigger'] = tokens[0]
            tokens = tokens[1:]  # Remove trigger from tokens
        
        if not tokens:
            return result
        
        # Parse the action
        action = tokens[0]
        
        # Static abilities (keywords)
        if action in self.STATIC_ABILITIES:
            result['action'] = 'static_ability'
            result['ability'] = action
            return result
        
        # Mana generation
        if action == 'gen':
            result['action'] = 'gen'
            if len(tokens) > 1:
                # Handle multiple colors with /
                colors = tokens[1].split('/')
                result['colors'] = colors
            return result
        
        # Stat modifiers (inc/dec)
        if action in self.STAT_MODIFIERS:
            result['action'] = action
            if len(tokens) > 1:
                result['attribute'] = tokens[1]
                if len(tokens) > 2:
                    try:
                        result['value'] = int(tokens[2])
                    except ValueError:
                        result['value'] = 1
                else:
                    result['value'] = 1
            return result
        
        # Damage
        if action == 'damage':
            result['action'] = 'damage'
            if len(tokens) > 1:
                result['target'] = tokens[1]
                if len(tokens) > 2:
                    try:
                        result['value'] = int(tokens[2])
                    except ValueError:
                        result['value'] = 1
            return result
        
        # Handle draw
        if action == 'draw':
            result['action'] = 'draw'
            if len(tokens) > 1:
                try:
                    result['value'] = int(tokens[1])
                except ValueError:
                    result['value'] = 1
            else:
                result['value'] = 1
            return result
        
        # Handle discard
        if action == 'discard':
            result['action'] = 'discard'
            if len(tokens) > 1:
                try:
                    result['value'] = int(tokens[1])
                except ValueError:
                    result['value'] = 1
            else:
                result['value'] = 1
            return result
        
        # Handle heal
        if action == 'heal':
            result['action'] = 'heal'
            if len(tokens) > 1:
                try:
                    result['value'] = int(tokens[1])
                except ValueError:
                    result['value'] = 1
            else:
                result['value'] = 1
            return result
        
        # Handle count
        if action == 'count':
            result['action'] = 'count'
            if len(tokens) > 1:
                result['card_type'] = tokens[1]
            return result
        
        # Handle global effects
        if action == 'global':
            result['action'] = 'global'
            result['scope'] = 'all_creatures'
            # Parse the rest as a sub-instruction
            sub_instruction = ' '.join(tokens[1:])
            sub_parsed = self._parse_instruction(sub_instruction)
            if sub_parsed:
                result['effect'] = sub_parsed
            return result
        
        # Handle graveyard operations
        if action == 'graveyard':
            result['action'] = 'graveyard'
            # Parse the rest as what to do with graveyard
            result['operation'] = ' '.join(tokens[1:])
            return result
        
        # Handle return (from graveyard to hand)
        if action == 'return':
            result['action'] = 'return'
            if len(tokens) >= 3:
                result['from'] = tokens[1]  # e.g., 'graveyard'
                result['to'] = tokens[2]    # e.g., 'hand'
            return result
        
        # Handle entertap
        if action == 'entertap':
            result['action'] = 'entertap'
            return result
        
        # Handle protection
        if action == 'protection':
            result['action'] = 'protection'
            if len(tokens) > 1:
                result['color'] = tokens[1]
            return result
        
        # Handle ignore block
        if action == 'ignore':
            result['action'] = 'ignore'
            if len(tokens) > 1:
                result['what'] = tokens[1]
            return result
        
        # Handle block modifier
        if action == 'block':
            result['action'] = 'block_modifier'
            if len(tokens) > 1:
                result['modifier'] = tokens[1]
            return result
        
        # Unknown action
        result['action'] = 'unknown'
        result['tokens'] = tokens
        return result
    
    def get_triggers(self, effect_string):
        """
        Get all triggers from an effect string.
        
        Args:
            effect_string (str): The effect string to parse
            
        Returns:
            list: List of trigger strings
        """
        instructions = self.parse(effect_string)
        return [inst['trigger'] for inst in instructions if inst.get('trigger')]
    
    def has_trigger(self, effect_string, trigger):
        """
        Check if an effect string contains a specific trigger.
        
        Args:
            effect_string (str): The effect string to parse
            trigger (str): The trigger to look for
            
        Returns:
            bool: True if the trigger is present
        """
        return trigger in self.get_triggers(effect_string)
    
    def get_static_abilities(self, effect_string):
        """
        Get all static abilities from an effect string.
        
        Args:
            effect_string (str): The effect string to parse
            
        Returns:
            list: List of static ability names
        """
        instructions = self.parse(effect_string)
        return [inst['ability'] for inst in instructions 
                if inst.get('action') == 'static_ability']
    
    def __repr__(self):
        return f"EffectParser(instructions={len(self.instructions)})"


# Example usage and testing
if __name__ == "__main__":
    parser = EffectParser()
    
    # Test cases
    test_effects = [
        "tap gen green",
        "attack? damage player 1",
        "summon? inc att 1; inc end 1",
        "entertap; tap gen green/blue",
        "haste",
        "flying; tap damage target 1",
        "global inc att 1",
        "graveyard count skeleton; inc att",
        "unblockable",
        "attack? inc att 2; dec end 1",
        "block? inc end 1",
        "damage player? discard 1",
        "summon? draw 1",
        "flying; summon? heal 3",
        "notap",
        "ignore block"
    ]
    
    print("Testing Effect Parser\n" + "="*50)
    for effect in test_effects:
        print(f"\nEffect: '{effect}'")
        result = parser.parse(effect)
        for instruction in result:
            print(f"  -> {instruction}")
