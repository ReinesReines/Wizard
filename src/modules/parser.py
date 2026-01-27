class EffectParser:
    """
    Parses card effects.
    """
    
    TRIGGERS = ['summon?', 'block?', 'attack?', 'tap?', 'enter?', 'discard?']
    STATIC_ABILITIES = ['haste', 'flying', 'reach', 'entertap', 'unblockable', 'vigilant', 'trample']
    MODIFIERS = ['inc', 'dec']
    ACTIONS = ['gen', 'draw', 'discard', 'heal', 'return', 'count', 'damage', 'destroy',
               'add', 'kill', 'morph', 'revive', 'nomanareset', 'castinc', 'castdec', 'invuln', 'create']
    TARGET_TYPES = ['creature', 'player']
    CONDITIONS = ['attackonly', 'blockonly']
    PLACES = ['graveyard', 'deck', 'hand']
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
            'value': None,
            'amount': None,
            'name': None,
            'target_type': None,
            'creatureid': False,
            'all': False,
            'condition': None
        }
        
        if instruction.strip() in self.STATIC_ABILITIES:
            result['action'] = 'static'
            result['status'] = instruction.strip()
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
        
        if idx < len(tokens) and tokens[idx] == 'all':
            result['all'] = True
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
                idx += 1
            else:
                result['value'] = 1
            
            if idx < len(tokens):
                name_token = tokens[idx]
                if isinstance(name_token, str) and name_token not in self.TARGET_TYPES and name_token != 'creatureid':
                    if '/' not in name_token and name_token not in self.CONDITIONS:
                        result['name'] = name_token
                        idx += 1
            
            if idx < len(tokens):
                if tokens[idx] == 'creatureid':
                    result['creatureid'] = True
                    idx += 1
                else:
                    target_token = tokens[idx]
                    if '/' in target_token:
                        result['target_type'] = target_token.split('/')
                        idx += 1
                    elif target_token in self.TARGET_TYPES:
                        result['target_type'] = target_token
                        idx += 1
        
        elif action == 'gen':
            amount = 1
            colors = []
            if idx < len(tokens):
                if isinstance(tokens[idx], tuple):
                    amount = tokens[idx]
                    idx += 1
                else:
                    try:
                        amount = int(tokens[idx])
                        idx += 1
                    except (ValueError, TypeError):
                        amount = 1
                if idx < len(tokens):
                    colors = tokens[idx].split('/')
            result['field'] = 'mana'
            result['value'] = colors
            result['amount'] = amount
        
        elif action in ['draw', 'discard', 'heal', 'damage']:
            if idx < len(tokens):
                if isinstance(tokens[idx], tuple):
                    result['value'] = tokens[idx]
                    idx += 1
                else:
                    try:
                        result['value'] = int(tokens[idx])
                    except (ValueError, TypeError):
                        result['value'] = 1
                    idx += 1
            else:
                result['value'] = 1
            
            if idx < len(tokens):
                if tokens[idx] == 'creatureid':
                    result['creatureid'] = True
                    idx += 1
                else:
                    target_token = tokens[idx]
                    if '/' in target_token:
                        result['target_type'] = target_token.split('/')
                        idx += 1
                    elif target_token in self.TARGET_TYPES:
                        result['target_type'] = target_token
                        idx += 1

        elif action == 'create':
            if idx < len(tokens):
                if isinstance(tokens[idx], tuple):
                    result['value'] = tokens[idx]
                else:
                    try:
                        result['value'] = int(tokens[idx])
                    except (ValueError, TypeError):
                        result['value'] = 1
                idx += 1
            else:
                result['value'] = 1

            if idx < len(tokens):
                name_token = tokens[idx]
                if isinstance(name_token, str):
                    result['name'] = name_token
                    idx += 1
        
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
        
        elif action in ('destroy', 'kill', 'revive', 'nomanareset', 'invuln'):
            if idx < len(tokens):
                if tokens[idx] == 'creatureid':
                    result['creatureid'] = True
                    idx += 1
                else:
                    target_token = tokens[idx]
                    if '/' in target_token:
                        result['target_type'] = target_token.split('/')
                        idx += 1
                    elif target_token in self.TARGET_TYPES:
                        result['target_type'] = target_token
                        idx += 1
            if action == 'nomanareset':
                result['value'] = True
        
        elif action == 'add':
            if idx < len(tokens):
                result['field'] = tokens[idx]  # status
                idx += 1
            if idx < len(tokens) and tokens[idx] in self.CONDITIONS:
                result['condition'] = tokens[idx]
                idx += 1
            if idx < len(tokens):
                if tokens[idx] == 'creatureid':
                    result['creatureid'] = True
                    idx += 1
                else:
                    target_token = tokens[idx]
                    if '/' in target_token:
                        result['target_type'] = target_token.split('/')
                        idx += 1
                    elif target_token in self.TARGET_TYPES:
                        result['target_type'] = target_token
                        idx += 1
        
        elif action in ('morph', 'castinc', 'castdec'):
            if idx < len(tokens):
                if tokens[idx] == 'creatureid':
                    result['creatureid'] = True
                    idx += 1
                else:
                    result['field'] = tokens[idx]
                    idx += 1
            if action in ('castinc', 'castdec'):
                if idx < len(tokens):
                    result['field'] = tokens[idx]  # att/end
                    idx += 1
                if idx < len(tokens):
                    try:
                        result['value'] = int(tokens[idx])
                    except ValueError:
                        result['value'] = 1
                    idx += 1
            if action == 'morph' and idx < len(tokens):
                result['value'] = tokens[idx]
        
        return result
    
    def _tokenize(self, instruction):
        tokens = []
        current = ""
        depth = 0
        paren_content = ""
        in_quotes = False
        
        for char in instruction:
            if char == '"' and depth == 0:
                if in_quotes:
                    if current.strip():
                        tokens.append(current.strip())
                        current = ""
                    in_quotes = False
                else:
                    if current.strip():
                        tokens.append(current.strip())
                        current = ""
                    in_quotes = True
                continue
            if char == '(':
                if depth == 0:
                    if current.strip():
                        tokens.append(current.strip())
                        current = ""
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    inner_tokens = self._split_paren_tokens(paren_content)
                    tokens.append(tuple(inner_tokens))
                    paren_content = ""
            elif depth > 0:
                paren_content += char
            elif in_quotes:
                current += char
            elif char.isspace():
                if current.strip():
                    tokens.append(current.strip())
                    current = ""
            else:
                current += char
        
        if current.strip():
            tokens.append(current.strip())
        
        return tokens

    def _split_paren_tokens(self, paren_content):
        tokens = []
        current = ""
        in_quotes = False

        for char in paren_content:
            if char == '"':
                in_quotes = not in_quotes
                continue
            if char.isspace() and not in_quotes:
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
        return [inst['status'] for inst in instructions if inst.get('action') == 'static']
    
    def has_trigger(self, effect_string, trigger):
        """Check if effect has specific trigger."""
        return trigger in self.get_triggers(effect_string)
    
    def __repr__(self):
        return f"EffectParser()"
