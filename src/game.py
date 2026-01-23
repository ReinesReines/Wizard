try:
    from .modules.cards import Cards, SummonCard, SpellCard, LandCards
    from .modules.utils import execute_card, enters_tapped, card_has_ability, get_all_keywords
    from .card_index import *
except:
    from modules.cards import Cards, SummonCard, SpellCard, LandCards
    from modules.utils import execute_card, enters_tapped, card_has_ability, get_all_keywords
    from card_index import *

import random
import json
import time
import datetime
import os


class GameEngine:
    def __init__(self, player1, player2, deck1, deck2):
        self.player1 = player1
        self.player2 = player2

        self.deck1 = deck1
        self.deck2 = deck2

        self.battlefield = {}
        # Set path to db folder at same level as src folder
        src_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(src_dir)
        self.game_file = os.path.join(project_root, "db", "game_state.json")
        self.turn = 0
        self.card_id_counter = 1

    def _timestamp(self):
        """Get current timestamp string."""
        return datetime.datetime.now().strftime('%H:%M:%S')

    def _log(self, level, message):
        print(f"[{self._timestamp()}] {level}: {message}")

    def _info(self, message):
        self._log("INFO", message)

    def _warn(self, message):
        self._log("WARN", message)

    def _error(self, message):
        self._log("ERROR", message)
    
    def _load_state(self):
        """Load and return the current game state from JSON."""
        with open(self.game_file, "r") as f:
            return json.load(f)
    
    def _save_state(self, game_state):
        """Save the game state to JSON."""
        with open(self.game_file, "w") as f:
            json.dump(game_state, f, indent=4)
    
    def count(self, target: Cards, deck):
        """Counts the number of target cards in a given deck."""
        x = 0
        for cards in deck:
            if cards.name == target.name:
                x += 1
        return x
    
    def assign_card_ids(self, deck):
        """Assign unique IDs to each card copy in the deck."""
        for card in deck:
            card.id = self.card_id_counter
            self.card_id_counter += 1
    
    def shuffle_deck(self, deck):
        new_deck = []
        while len(deck) > 0:
            to_pop = random.randint(0, len(deck)-1)
            item = deck.pop(to_pop)
            new_deck.append(item)
        return new_deck
    
    def play_creature(self, player, card_id):
        """
        Play a creature from player's hand to the battlefield.
        """
        # Load current game state
        with open(self.game_file, "r") as f:
            game_state = json.load(f)
        
        # Check if player exists
        if player not in game_state:
            self._error(f"Play creature failed: player '{player}' not found.")
            return False
        
        player_data = game_state[player]
        
        # Find card in player's hand by ID
        card_dict = None
        if isinstance(player_data["hand"], dict):
            card_dict = player_data["hand"].get(str(card_id))
        elif isinstance(player_data["hand"], list):
            for c in player_data["hand"]:
                if c.get("id") == card_id:
                    card_dict = c
                    player_data["hand"].remove(c)
                    break
        
        if not card_dict:
            self._error(f"Play creature failed: card ID {card_id} not in {player}'s hand.")
            return False
        
        # Reconstruct card object from dictionary
        card = self._reconstruct_card(card_dict)
        
        if not card:
            self._error(f"Play creature failed: could not reconstruct card ID {card_id}.")
            return False
        
        # Check if it's a creature card
        if not isinstance(card, SummonCard):
            self._error(f"Play creature failed: '{card.name}' is not a creature.")
            return False
        
        # Execute card effects (pass player for graveyard counting)
        executed_card = execute_card(card, game_state, player)
        
        # Check if card enters tapped
        if enters_tapped(executed_card):
            executed_card.tapped = 1
        
        # Extract and set keyword abilities in status
        keywords = get_all_keywords(executed_card)
        executed_card.status = ", ".join(keywords) if keywords else ""
        
        # Add to battlefield
        battlefield_entry = {
            "card": executed_card.to_dict(),
            "action": "attack",  # Default action
            "summoning_sickness": not card_has_ability(executed_card, "haste"),
            "base_attack": executed_card.attack,
            "base_defence": executed_card.defence,
            "damage_taken": 0  # Track combat damage separately from temporary stat changes
        }
        
        # Add to player's creatures on battlefield
        if str(card_id) in player_data["hand"]:
            del player_data["hand"][str(card_id)]
        
        player_data["creatures"][str(card_id)] = battlefield_entry
        
        # Update battlefield state
        game_state[player] = player_data
        
        # Save updated game state
        with open(self.game_file, "w") as f:
            json.dump(game_state, f, indent=4)
        
        self._info(
            f"{player} played {executed_card.name} (ID {card_id}) "
            f"{executed_card.attack}/{executed_card.defence}."
        )
        
        # Check for enter? triggers from other creatures
        self.check_enter_triggers(player, card_id)
        
        # Check for summon? triggers
        self.check_summon_triggers(player, card_id)

        return True

    def _resolve_spell_target_player(self, caster, target):
        """Resolve target player from token (self/opponent/player name)."""
        opponent = self.player2 if caster == self.player1 else self.player1
        if target is None:
            return None
        target_str = str(target).lower()
        if target_str == "self":
            return caster
        if target_str == "opponent":
            return opponent
        if str(target) in (self.player1, self.player2):
            return str(target)
        return None

    def _resolve_spell_target_creature(self, game_state, target_id):
        """Return (owner, creature_data) for a target creature id."""
        if target_id is None:
            return None, None
        target_id_str = str(target_id)
        for owner in [self.player1, self.player2]:
            if target_id_str in game_state[owner]["creatures"]:
                return owner, game_state[owner]["creatures"][target_id_str]
        return None, None

    def _resolve_target_kind(self, player, game_state, target):
        """Return ('creature', owner, creature_data) or ('player', player_name, None)."""
        owner, creature_data = self._resolve_spell_target_creature(game_state, target)
        if owner and creature_data:
            return "creature", owner, creature_data
        target_player = self._resolve_spell_target_player(player, target)
        if target_player:
            return "player", target_player, None
        return None, None, None

    def _validate_spell_target(self, player, card_dict, target):
        """Validate target matches effect target_type (creature/player)."""
        try:
            from .modules.parser import EffectParser
        except:
            from modules.parser import EffectParser

        game_state = self._load_state()
        parser = EffectParser()
        effects = parser.parse(card_dict.get("effect", ""))

        required_target_type = None
        requires_creature_id = False
        for effect in effects:
            if effect.get("trigger"):
                continue
            target_type = effect.get("target_type")
            if effect.get("creatureid"):
                requires_creature_id = True
            if target_type:
                if required_target_type and target_type != required_target_type:
                    self._error("Spell target validation failed: mixed target types.")
                    return False
                required_target_type = target_type

        if requires_creature_id:
            if target is None:
                self._error("Spell target validation failed: creature target required.")
                return False
            owner, _ = self._resolve_spell_target_creature(game_state, target)
            if not owner:
                self._error(f"Spell target validation failed: creature '{target}' not found.")
                return False

        if isinstance(required_target_type, list):
            if target is None:
                self._error("Spell target validation failed: target required.")
                return False
            owner, _ = self._resolve_spell_target_creature(game_state, target)
            target_player = self._resolve_spell_target_player(player, target)
            if not owner and not target_player:
                self._error(f"Spell target validation failed: target '{target}' not found.")
                return False
        elif required_target_type == "creature":
            if target is None:
                self._error("Spell target validation failed: creature target required.")
                return False
            owner, _ = self._resolve_spell_target_creature(game_state, target)
            if not owner:
                self._error(f"Spell target validation failed: creature '{target}' not found.")
                return False
        elif required_target_type == "player":
            if target is None:
                self._error("Spell target validation failed: player target required.")
                return False
            target_player = self._resolve_spell_target_player(player, target)
            if not target_player:
                self._error(f"Spell target validation failed: player '{target}' not found.")
                return False

        return True

    def cast_spell(self, player, card_id, target=None):
        """Cast a spell from hand and apply its effects to the specified target."""
        game_state = self._load_state()

        if player not in game_state:
            self._error(f"Cast spell failed: player '{player}' not found.")
            return False

        card_id_str = str(card_id)
        hand = game_state[player]["hand"]
        if card_id_str not in hand:
            self._error(f"Cast spell failed: card ID {card_id} not in {player}'s hand.")
            return False

        card_dict = hand[card_id_str]
        if card_dict.get("type") != "Spell":
            self._error(f"Cast spell failed: {card_dict.get('name', 'Card')} is not a spell.")
            return False

        if not self._validate_spell_target(player, card_dict, target):
            return False

        generic_cost = card_dict.get("generic_mana", 0)
        sp_mana = card_dict.get("sp_mana", "") or None
        if not self.check_mana_cost(player, generic_cost, sp_mana):
            self._error(f"Cast spell failed: insufficient mana for {card_dict.get('name')}.")
            return False

        if not self.pay_mana(player, generic_cost, sp_mana):
            return False

        if not self.apply_spell_effect(player, card_dict, target):
            return False

        # Reload state to preserve changes from apply_spell_effect (e.g., nomanareset, mana payment)
        game_state = self._load_state()
        hand = game_state[player]["hand"]

        # Move spell from hand to graveyard
        if card_id_str in hand:
            del hand[card_id_str]
        game_state[player]["graveyard"].append(card_dict)
        self._save_state(game_state)

        self._info(f"{player} casts {card_dict.get('name')}.")
        return True

    def apply_spell_effect(self, player, card_dict, target=None):
        """Resolve a spell's effect string against a target."""
        try:
            from .modules.parser import EffectParser
        except:
            from modules.parser import EffectParser

        game_state = self._load_state()
        parser = EffectParser()
        effects = parser.parse(card_dict.get("effect", ""))

        opponent = self.player2 if player == self.player1 else self.player1
        needs_death_check = False
        pending_draws = []
        
        def add_status(card, status):
            existing = card.get("status", "")
            if not existing:
                card["status"] = status
            else:
                statuses = [s.strip() for s in existing.split(",") if s.strip()]
                if status not in statuses:
                    statuses.append(status)
                    card["status"] = ", ".join(statuses)

        def iter_active_creatures(players):
            for owner in players:
                for cid, cdata in game_state[owner]["creatures"].items():
                    yield owner, cid, cdata

        def iter_hand_creatures(owner):
            for cid, card in game_state[owner]["hand"].items():
                if card.get("type") == "Creature":
                    yield owner, cid, card

        for effect in effects:
            if effect.get("trigger"):
                continue
            action = effect.get("action")
            target_type = effect.get("target_type")
            value = effect.get("value", 1)
            if value is None:
                value = 1

            # Determine target kind if target is provided and target_type allows both
            target_kind = None
            target_owner = None
            target_creature = None
            if isinstance(target_type, list):
                target_kind, target_owner, target_creature = self._resolve_target_kind(player, game_state, target)

            if action in ("inc", "dec"):
                field_mapping = {"att": "attack", "end": "defence"}
                card_field = field_mapping.get(effect.get("field"), effect.get("field"))
                delta = value if action == "inc" else -value

                if effect.get("all"):
                    for owner, cid, cdata in iter_active_creatures([self.player1, self.player2]):
                        card = cdata["card"]
                        if card_field in card:
                            card[card_field] += delta
                            if card_field == "attack":
                                cdata["base_attack"] = cdata.get("base_attack", card[card_field]) + delta
                            elif card_field == "defence":
                                cdata["base_defence"] = cdata.get("base_defence", card[card_field]) + delta
                    self._info(f"All creatures {card_field} {'+' if delta>=0 else ''}{delta}.")
                elif effect.get("global"):
                    # Apply to creatures in player's hand
                    for owner, cid, card in iter_hand_creatures(player):
                        if card_field in card:
                            card[card_field] += delta
                    self._info(f"Hand creatures {card_field} {'+' if delta>=0 else ''}{delta}.")
                else:
                    if effect.get("creatureid") or target_type == "creature" or target_kind == "creature":
                        owner, creature_data = self._resolve_spell_target_creature(game_state, target)
                        if not creature_data:
                            self._error(f"Spell resolution failed: creature '{target}' not found.")
                            return False
                        creature_card = creature_data["card"]
                        if card_field in creature_card:
                            creature_card[card_field] += delta
                            if card_field == "attack":
                                creature_data["base_attack"] = creature_data.get("base_attack", creature_card[card_field]) + delta
                            elif card_field == "defence":
                                creature_data["base_defence"] = creature_data.get("base_defence", creature_card[card_field]) + delta
                            self._info(f"{creature_card['name']} {card_field} {'+' if delta>=0 else ''}{delta}.")
                    else:
                        self._error("Spell resolution failed: creature target required.")
                        return False

            elif action == "castinc" or action == "castdec":
                delta = value if action == "castinc" else -value
                field_mapping = {"att": "attack", "end": "defence"}
                card_field = field_mapping.get(effect.get("field"), effect.get("field"))
                owner, creature_data = self._resolve_spell_target_creature(game_state, target)
                if not creature_data:
                    self._error(f"Spell resolution failed: creature '{target}' not found.")
                    return False
                creature_card = creature_data["card"]
                creature_card[card_field] += delta
                if card_field == "attack":
                    creature_data["base_attack"] = creature_data.get("base_attack", creature_card[card_field]) + delta
                elif card_field == "defence":
                    creature_data["base_defence"] = creature_data.get("base_defence", creature_card[card_field]) + delta
                self._info(f"{creature_card['name']} {card_field} {'+' if delta>=0 else ''}{delta}.")

            elif action == "damage":
                if target_type == "creature" or effect.get("creatureid") or target_kind == "creature":
                    owner, creature_data = self._resolve_spell_target_creature(game_state, target)
                    if not creature_data:
                        self._error(f"Spell resolution failed: creature '{target}' not found.")
                        return False
                    creature_card = creature_data["card"]
                    creature_data["damage_taken"] = creature_data.get("damage_taken", 0) + value
                    if not creature_data.get("invuln"):
                        creature_card["defence"] -= value
                    self._info(f"{creature_card['name']} takes {value} damage.")
                    needs_death_check = True
                else:
                    target_player = self._resolve_spell_target_player(player, target)
                    if target is not None and not target_player:
                        self._error(f"Spell resolution failed: player '{target}' not found.")
                        return False
                    if not target_player:
                        target_player = opponent
                    game_state[target_player]["health"] -= value
                    self._info(f"{target_player} takes {value} damage.")

            elif action in ("destroy", "kill"):
                if effect.get("all"):
                    for owner, cid, cdata in list(iter_active_creatures([self.player1, self.player2])):
                        game_state[owner]["graveyard"].append(cdata["card"])
                        del game_state[owner]["creatures"][cid]
                    self._info("All active creatures are destroyed.")
                elif action == "kill" and effect.get("global"):
                    for owner, cid, cdata in list(iter_active_creatures([player])):
                        game_state[owner]["graveyard"].append(cdata["card"])
                        del game_state[owner]["creatures"][cid]
                    self._info(f"{player}'s active creatures are destroyed.")
                else:
                    owner, creature_data = self._resolve_spell_target_creature(game_state, target)
                    if not creature_data:
                        self._error(f"Spell resolution failed: creature '{target}' not found.")
                        return False
                    creature_card = creature_data["card"]
                    game_state[owner]["graveyard"].append(creature_card)
                    del game_state[owner]["creatures"][str(target)]
                    self._info(f"{creature_card['name']} is destroyed.")

            elif action == "add":
                status = effect.get("field")
                condition = effect.get("condition")
                if condition in ("attackonly", "blockonly"):
                    # Restrict status to current attackers/blockers
                    attackers = game_state.get("combat", {}).get("attackers", [])
                    blocks = game_state.get("combat", {}).get("blocks", {})
                    if condition == "attackonly":
                        for cid in attackers:
                            for owner in [self.player1, self.player2]:
                                if cid in game_state[owner]["creatures"]:
                                    add_status(game_state[owner]["creatures"][cid]["card"], status)
                    else:
                        for a_id, b_list in blocks.items():
                            for b_id in b_list:
                                if b_id in game_state[opponent]["creatures"]:
                                    add_status(game_state[opponent]["creatures"][b_id]["card"], status)
                    self._info(f"Status {status} applied to {condition} creatures.")
                else:
                    if effect.get("all"):
                        for owner, cid, cdata in iter_active_creatures([self.player1, self.player2]):
                            add_status(cdata["card"], status)
                    elif effect.get("global"):
                        for owner, cid, cdata in iter_active_creatures([player]):
                            add_status(cdata["card"], status)
                    elif effect.get("creatureid") or target_type == "creature" or target_kind == "creature":
                        owner, creature_data = self._resolve_spell_target_creature(game_state, target)
                        if not creature_data:
                            self._error(f"Spell resolution failed: creature '{target}' not found.")
                            return False
                        add_status(creature_data["card"], status)
                    else:
                        self._error("Spell resolution failed: creature target required.")
                        return False
                    self._info(f"Status applied: {status}.")

            elif action == "morph":
                if not (effect.get("creatureid") or target):
                    self._error("Morph failed: creature target required.")
                    return False
                owner, creature_data = self._resolve_spell_target_creature(game_state, target)
                if not creature_data:
                    self._error(f"Morph failed: creature '{target}' not found.")
                    return False
                new_name = effect.get("value")
                new_card = self._find_card_by_name(new_name)
                if not new_card:
                    self._error(f"Morph failed: card '{new_name}' not found.")
                    return False
                executed = self._reconstruct_card(new_card.to_dict())
                creature_data["card"] = executed.to_dict()
                creature_data["base_attack"] = executed.attack
                creature_data["base_defence"] = executed.defence
                creature_data["damage_taken"] = 0
                creature_data["summoning_sickness"] = True
                self._info(f"Creature {target} morphed into {new_name}.")

            elif action == "revive":
                target_id = target
                revived = False
                for owner in [self.player1, self.player2]:
                    graveyard = game_state[owner]["graveyard"]
                    for idx, card in enumerate(graveyard):
                        if not isinstance(card, dict):
                            continue
                        if str(card.get("id")) == str(target_id):
                            card_obj = self._reconstruct_card(card)
                            if not card_obj:
                                continue
                            game_state[owner]["creatures"][str(target_id)] = {
                                "card": card_obj.to_dict(),
                                "action": "attack",
                                "summoning_sickness": True,
                                "base_attack": card_obj.attack,
                                "base_defence": card_obj.defence,
                                "damage_taken": 0
                            }
                            del graveyard[idx]
                            revived = True
                            self._info(f"{card_obj.name} revived from graveyard.")
                            break
                    if revived:
                        break
                if not revived:
                    self._error(f"Revive failed: creature {target_id} not found in graveyard.")
                    return False

            elif action == "invuln":
                owner, creature_data = self._resolve_spell_target_creature(game_state, target)
                if not creature_data:
                    self._error(f"Invulnerable failed: creature '{target}' not found.")
                    return False
                creature_data["invuln"] = True
                add_status(creature_data["card"], "invuln")
                creature_data["card"]["defence"] = 9999
                self._info(f"{creature_data['card']['name']} becomes invulnerable.")

            elif action == "nomanareset":
                game_state[player]["nomanareset"] = True
                self._info(f"{player} will not reset mana this turn.")

            elif action == "draw":
                target_player = self._resolve_spell_target_player(player, target) if target_type == "player" else player
                if target_player is None:
                    target_player = player
                pending_draws.append((target_player, value))

            elif action == "heal":
                if target_type == "creature" or target_kind == "creature" or effect.get("creatureid"):
                    owner, creature_data = self._resolve_spell_target_creature(game_state, target)
                    if not creature_data:
                        self._error(f"Spell resolution failed: creature '{target}' not found.")
                        return False
                    creature_card = creature_data["card"]
                    base_def = creature_data.get("base_defence", creature_card.get("defence", 0))
                    creature_card["defence"] = min(creature_card["defence"] + value, base_def)
                    creature_data["damage_taken"] = max(0, base_def - creature_card["defence"])
                    self._info(f"{creature_card['name']} heals {value}.")
                else:
                    target_player = self._resolve_spell_target_player(player, target) if target_type == "player" else player
                    max_health = 20
                    game_state[target_player]["health"] = min(game_state[target_player]["health"] + value, max_health)
                    self._info(f"{target_player} heals {value}.")

            elif action == "discard":
                if target_type == "player":
                    target_player = self._resolve_spell_target_player(player, target)
                else:
                    target_player = player
                if target_player is None:
                    target_player = opponent
                if target_player is None:
                    self._error("Discard failed: target player not found.")
                    return False
                hand = game_state[target_player]["hand"]
                if len(hand) < value:
                    discard_ids = list(hand.keys())
                    for cid in discard_ids:
                        game_state[target_player]["graveyard"].append(hand[cid])
                        del hand[cid]
                    self._info(f"{target_player} discards {len(discard_ids)} card(s).")
                else:
                    game_state["pending_discard"] = {
                        "player": target_player,
                        "count": value,
                        "requester": player,
                    }
                    self._info(f"{target_player} must discard {value} card(s).")

        self._save_state(game_state)
        if pending_draws:
            for target_player, value in pending_draws:
                drawn = 0
                for _ in range(value):
                    if self.draw_card(target_player):
                        drawn += 1
                self._info(f"{target_player} draws {drawn} card(s).")
        if needs_death_check:
            self.check_creature_deaths()
        return True

    # ===================
    # CORE GAME LOOP
    # ===================
    
    def draw_card(self, player):
        """Move top card from deck to hand."""
        game_state = self._load_state()
        
        if player not in game_state:
            self._error(f"Draw failed: player '{player}' not found.")
            return False
        
        player_data = game_state[player]
        
        # Check if deck is empty
        if not player_data["deck"]:
            self._warn(f"{player} cannot draw: deck is empty.")
            return False
        
        # Draw top card
        card = player_data["deck"].pop(0)
        card_id = str(card["id"])
        player_data["hand"][card_id] = card
        
        self._save_state(game_state)
        return True
    
    def start_turn(self, player):
        """Initialize turn, increment counter, set active player."""
        game_state = self._load_state()
        
        game_state["turn_number"] = game_state.get("turn_number", 0) + 1
        game_state["current_player"] = player
        game_state["phase"] = "untap"
        game_state["lands_played_this_turn"] = 0
        
        self._info(f"Turn {game_state['turn_number']} begins for {player}.")
        
        self._save_state(game_state)
    
    def untap_step(self, player):
        """Untap all creatures and lands."""
        game_state = self._load_state()
        
        if player not in game_state:
            return
        
        self._info(f"Untap step for {player}.")
        player_data = game_state[player]
        
        # Untap creatures and clear summoning sickness
        for creature_id, creature_data in player_data["creatures"].items():
            # Untap
            if creature_data["card"]["tapped"] == 1:
                creature_data["card"]["tapped"] = 0
                self._info(f"{creature_data['card']['name']} untaps.")
            
            # Clear summoning sickness (affects both tapped and untapped creatures)
            creature_data["summoning_sickness"] = False
        
        # Untap lands
        for land_id, land_data in player_data["lands"].items():
            if land_data["card"]["tapped"] == 1:
                land_data["card"]["tapped"] = 0
                self._info(f"{land_data['card']['name']} untaps.")
        
        game_state["phase"] = "upkeep"
        self._save_state(game_state)
    
    def draw_step(self, player):
        """Draw 1 card (skip turn 1 for starting player)."""
        game_state = self._load_state()
        turn_number = game_state.get("turn_number", 1)
        
        self._info(f"Draw step for {player}.")
        
        # Skip first draw for starting player on turn 1
        if turn_number == 1 and player == self.player1:
            self._info(f"{player} skips draw (turn 1).")
        else:
            self.draw_card(player)
        
        game_state = self._load_state()
        game_state["phase"] = "main_pre"
        self._save_state(game_state)

    def discard_cards(self, player, card_ids):
        """Discard cards from hand."""
        game_state = self._load_state()
        
        if player not in game_state:
            return
        
        player_data = game_state[player]
        for card_id in card_ids:
            if card_id not in player_data["hand"]:
                self._error(f"Discard failed: card ID {card_id} not in {player}'s hand.")
                return False
            card_dict = player_data["hand"][card_id]
            del player_data["hand"][card_id]
            player_data["graveyard"].append(card_dict)
        
        self._save_state(game_state)
        return True
    
    def end_turn(self, player):
        """Run cleanup, clear mana pool, shift to opponent."""
        game_state = self._load_state()
        
        self._info(f"End phase for {player}.")
        
        # Clear temporary effects (attack triggers, etc.)
        self.cleanup_temporary_effects()
        
        # Clear mana pool
        self.clear_mana_pool(player)
        
        game_state = self._load_state()
        game_state["phase"] = "end"
        game_state["lands_played_this_turn"] = 0
        
        self._info(f"{player}'s turn ends.")
        
        self._save_state(game_state)
        self.turn += 1
    
    def clear_mana_pool(self, player):
        """Reset all mana to 0."""
        game_state = self._load_state()
        
        if player not in game_state:
            return
        
        player_data = game_state[player]
        if player_data.get("nomanareset"):
            self._info("Mana pool not reset due to nomanareset.")
            player_data["nomanareset"] = False
            self._save_state(game_state)
            return
        else:
            self._info("Mana pool cleared: blue 0, red 0, green 0.")
        player_data["blue_mana"] = 0
        player_data["red_mana"] = 0
        player_data["green_mana"] = 0
        
        self._save_state(game_state)

    # ===================
    # LAND & MANA SYSTEM
    # ===================
    
    def play_land(self, player, card_id):
        """Move land from hand to lands dict."""
        game_state = self._load_state()
        
        if player not in game_state:
            self._error(f"Play land failed: player '{player}' not found.")
            return False
        
        # Check lands played this turn
        # if game_state.get("lands_played_this_turn", 0) >= 1:
        #     print(f"[{self._timestamp()}] Error: {player} already played a land this turn")
        #     return False
        
        player_data = game_state[player]
        card_id_str = str(card_id)
        
        # Find card in hand
        if card_id_str not in player_data["hand"]:
            self._error(f"Play land failed: card ID {card_id} not in {player}'s hand.")
            return False
        
        card_dict = player_data["hand"][card_id_str]
        
        # Verify it's a land
        if card_dict.get("type") != "Land":
            self._error(f"Play land failed: {card_dict['name']} is not a land.")
            return False
        
        # Reconstruct card
        card = self._reconstruct_card(card_dict)
        
        # Check if enters tapped
        if enters_tapped(card):
            card.tapped = 1
        
        # Move to lands
        del player_data["hand"][card_id_str]
        player_data["lands"][card_id_str] = {
            "card": card.to_dict()
        }
        
        game_state["lands_played_this_turn"] = game_state.get("lands_played_this_turn", 0) + 1
        
        self._info(f"{player} plays land: {card.name}.")
        if card.tapped:
            self._info(f"{card.name} enters tapped.")
        
        self._save_state(game_state)
        return True
    
    def tap_land(self, player, land_id, color_choice=None):
        """Execute 'tap? gen [color]' effect, set tapped=1."""
        game_state = self._load_state()
        
        if player not in game_state:
            return False
        
        player_data = game_state[player]
        land_id_str = str(land_id)
        
        if land_id_str not in player_data["lands"]:
            self._error(f"Tap failed: land ID {land_id} not found.")
            return False
        
        land_data = player_data["lands"][land_id_str]
        
        # Check if already tapped
        if land_data["card"]["tapped"] == 1:
            self._error(f"Tap failed: {land_data['card']['name']} is already tapped.")
            return False
        
        # Tap the land
        land_data["card"]["tapped"] = 1
        
        # Parse effect to generate mana
        effect = land_data["card"].get("effect", "")
        
        # Simple parsing for "tap? gen [color]"
        if "gen" in effect:
            colors = []
            if "green" in effect:
                colors.append("green")
            if "blue" in effect:
                colors.append("blue")
            if "red" in effect:
                colors.append("red")
            
            # Use color_choice if provided, otherwise use first color
            if colors:
                if color_choice and color_choice in colors:
                    color = color_choice
                else:
                    color = colors[0]
                player_data[f"{color}_mana"] += 1
                self._info(
                    f"{player} taps {land_data['card']['name']} for {color}. "
                    f"{color}_mana: {player_data[f'{color}_mana']}"
                )
        
        self._save_state(game_state)
        return True
    
    def check_mana_cost(self, player, generic, sp_mana):
        """Return True if player has enough mana."""
        game_state = self._load_state()
        
        if player not in game_state:
            return False
        
        player_data = game_state[player]
        
        # Get specific mana requirement
        specific_needed = 0
        if sp_mana:
            specific_needed = 1
            color_mana = player_data.get(f"{sp_mana}_mana", 0)
            if color_mana < 1:
                return False
        
        # Calculate total mana available
        total_mana = (player_data.get("blue_mana", 0) + 
                     player_data.get("red_mana", 0) + 
                     player_data.get("green_mana", 0))
        
        # Total needed = generic + specific
        total_needed = generic + specific_needed
        
        return total_mana >= total_needed
    
    def pay_mana(self, player, generic, sp_mana):
        """Deduct colored mana first, then generic from remaining."""
        game_state = self._load_state()
        
        if player not in game_state:
            return False
        
        if not self.check_mana_cost(player, generic, sp_mana):
            self._error("Mana payment failed: insufficient mana.")
            return False
        
        player_data = game_state[player]
        
        # Pay specific mana first
        if sp_mana:
            player_data[f"{sp_mana}_mana"] -= 1
        
        # Pay generic from remaining mana
        remaining = generic
        for color in ["green", "blue", "red"]:
            mana_key = f"{color}_mana"
            available = player_data.get(mana_key, 0)
            to_pay = min(remaining, available)
            player_data[mana_key] -= to_pay
            remaining -= to_pay
            if remaining == 0:
                break
        
        self._info(f"Paid cost: {generic} generic + {sp_mana if sp_mana else 'no color'}.")
        
        self._save_state(game_state)
        return True

    # ===================
    # COMBAT SYSTEM
    # ===================
    
    def declare_attackers(self, player, creature_ids):
        """
        Declare which creatures attack.
        1. Validate creatures can attack (not tapped, no summoning sickness)
        2. Trigger "attack?" effects IMMEDIATELY
        3. Tap creatures (unless vigilant)
        4. Store in combat state
        """
        game_state = self._load_state()
        
        if player not in game_state:
            self._error(f"Declare attackers failed: player '{player}' not found.")
            return False
        
        player_data = game_state[player]
        attackers = []
        
        self._info(f"Declare attackers for {player}.")
        
        for creature_id in creature_ids:
            creature_id_str = str(creature_id)

            if creature_id_str not in player_data["creatures"]:
                self._error(f"Attacker {creature_id} not found on battlefield.")
                continue

            creature_data = player_data["creatures"][creature_id_str]
            card = creature_data["card"]

            # Check if tapped
            if card["tapped"] == 1:
                self._error(f"{card['name']} is tapped and cannot attack.")
                continue

            # Prevent attacking if summoning sickness is true
            if creature_data.get("summoning_sickness", True):
                self._error(f"{card['name']} has summoning sickness and cannot attack.")
                continue

            # Valid attacker
            attackers.append(creature_id_str)

            # Check if vigilant (from status or effect)
            has_vigilant = "vigilant" in card.get("status", "").lower() or "notap" in card.get("status", "").lower()

            # Tap creature unless vigilant
            if not has_vigilant:
                card["tapped"] = 1
                self._info(f"{card['name']} attacks and taps.")
            else:
                self._info(f"{card['name']} attacks (vigilant, stays untapped).")
        
        # Store attackers in combat state
        game_state["combat"]["attackers"] = attackers
        
        self._info(f"Total attackers: {len(attackers)}.")
        
        self._save_state(game_state)
        
        # Check for attack? triggers
        if attackers:
            self.check_attack_triggers(player, [int(aid) for aid in attackers])
        
        return True
    
    def declare_blockers(self, defender, block_assignments):
        """
        Declare which creatures block which attackers.
        block_assignments = {"attacker_id": ["blocker_id1", "blocker_id2"]}
        """
        game_state = self._load_state()
        
        if defender not in game_state:
            self._error(f"Declare blockers failed: player '{defender}' not found.")
            return False
        
        self._info(f"Declare blockers for {defender}.")
        
        defender_data = game_state[defender]
        blocks = {}
        
        for attacker_id, blocker_ids in block_assignments.items():
            attacker_id_str = str(attacker_id)
            
            if attacker_id_str not in game_state["combat"]["attackers"]:
                self._error(f"Block failed: attacker {attacker_id} is not attacking.")
                continue
            
            valid_blockers = []
            
            for blocker_id in blocker_ids:
                blocker_id_str = str(blocker_id)
                
                if blocker_id_str not in defender_data["creatures"]:
                    self._error(f"Block failed: blocker {blocker_id} not found.")
                    continue
                
                # Use can_block() for validation (includes flying/reach/unblockable checks)
                if not self.can_block(blocker_id_str, attacker_id_str):
                    blocker_data = defender_data["creatures"][blocker_id_str]
                    self._error(f"{blocker_data['card']['name']} cannot block (tapped/flying/unblockable).")
                    continue
                
                blocker_data = defender_data["creatures"][blocker_id_str]
                valid_blockers.append(blocker_id_str)
                self._info(f"{blocker_data['card']['name']} blocks attacker {attacker_id}.")
            
            if valid_blockers:
                blocks[attacker_id_str] = valid_blockers
        
        # Store blocks in combat state
        game_state["combat"]["blocks"] = blocks
        
        self._save_state(game_state)
        
        # Check for block? triggers
        all_blockers = []
        for blocker_list in blocks.values():
            all_blockers.extend([int(bid) for bid in blocker_list])
        
        if all_blockers:
            self.check_block_triggers(defender, all_blockers)
        
        return True
    
    def can_attack(self, player, creature_id):
        """Check if creature can attack (not tapped, no summoning sickness)."""
        game_state = self._load_state()
        
        if player not in game_state:
            return False
        
        creature_id_str = str(creature_id)
        player_data = game_state[player]
        
        if creature_id_str not in player_data["creatures"]:
            return False
        
        creature_data = player_data["creatures"][creature_id_str]
        
        if creature_data["card"]["tapped"] == 1:
            return False
        
        if creature_data.get("summoning_sickness", False):
            return False
        
        return True
    
    def cleanup_temporary_effects(self):
        """
        Remove temporary buffs at end of turn (like attack? triggers).
        Restores stats to base, then reapplies combat damage (which is permanent).
        """
        game_state = self._load_state()
        
        for player in [self.player1, self.player2]:
            for creature_id, creature_data in game_state[player]["creatures"].items():
                card = creature_data["card"]
                base_attack = creature_data.get("base_attack")
                base_defence = creature_data.get("base_defence")
                damage_taken = creature_data.get("damage_taken", 0)
                
                # Restore both stats to base (removes temporary buffs/debuffs)
                if base_attack is not None:
                    old_attack = card["attack"]
                    if old_attack != base_attack:
                        card["attack"] = base_attack
                        self._info(
                            f"{card['name']} attack restored: {old_attack} -> {base_attack} "
                            "(temporary buff removed)."
                        )
                
                # Restore defence to base, then reapply combat damage (which persists)
                if base_defence is not None:
                    old_defence = card["defence"]
                    # Restore to base, then subtract damage_taken
                    card["defence"] = base_defence - damage_taken
                    new_defence = card["defence"]
                    if old_defence != new_defence:
                        self._info(
                            f"{card['name']} defence restored: {old_defence} -> {new_defence} "
                            f"(base {base_defence} - {damage_taken} damage)."
                        )

                # Clear invulnerability each turn
                if creature_data.get("invuln"):
                    creature_data["invuln"] = False
                    existing = str(card.get("status", "") or "")
                    statuses = [s.strip() for s in existing.split(",") if s.strip() and s.strip() != "invuln"]
                    card["status"] = ", ".join(statuses)
        
        self._save_state(game_state)

    def calculate_combat_damage(self):
        """
        Build damage queue for all attackers and blockers.
        Handles trample: assigns lethal damage to blockers, excess to player.
        Does NOT apply damage yet - that's done in resolve_damage_queue().
        """
        game_state = self._load_state()
        damage_queue = []
        
        self._info("Combat damage calculation begins.")
        
        # Get current and opposing players
        current_player = game_state["current_player"]
        opponent = self.player2 if current_player == self.player1 else self.player1
        
        attackers = game_state["combat"]["attackers"]
        blocks = game_state["combat"]["blocks"]
        
        for attacker_id in attackers:
            # Get attacker data
            attacker_data = game_state[current_player]["creatures"][attacker_id]
            attacker_card = attacker_data["card"]
            attacker_power = attacker_card["attack"]
            
            # Check if this attacker is blocked
            if attacker_id in blocks:
                blocker_ids = blocks[attacker_id]
                
                # Check if attacker has trample
                has_trample = "trample" in attacker_card.get("status", "").lower()
                
                if len(blocker_ids) == 1:
                    # Single blocker: mutual damage (or trample)
                    blocker_id = blocker_ids[0]
                    blocker_data = game_state[opponent]["creatures"][blocker_id]
                    blocker_card = blocker_data["card"]
                    blocker_power = blocker_card["attack"]
                    blocker_toughness = blocker_card["defence"]
                    
                    if has_trample:
                        # Trample: assign lethal damage to blocker, excess to player
                        lethal_damage = blocker_toughness
                        damage_to_blocker = min(attacker_power, lethal_damage)
                        trample_damage = max(0, attacker_power - lethal_damage)
                        
                        # Damage to blocker
                        damage_queue.append({
                            "source": "creature",
                            "source_id": attacker_id,
                            "target": "creature",
                            "target_id": blocker_id,
                            "target_player": opponent,
                            "damage": damage_to_blocker
                        })
                        
                        # Trample damage to player
                        if trample_damage > 0:
                            damage_queue.append({
                                "source": "creature",
                                "source_id": attacker_id,
                                "target": "player",
                                "target_player": opponent,
                                "damage": trample_damage
                            })
                            self._info(
                                f"{attacker_card['name']} deals {damage_to_blocker} to {blocker_card['name']}, "
                                f"{trample_damage} tramples to {opponent}."
                            )
                        else:
                            self._info(f"{attacker_card['name']} deals {damage_to_blocker} to {blocker_card['name']}.")
                    else:
                        # No trample: all damage goes to blocker
                        damage_queue.append({
                            "source": "creature",
                            "source_id": attacker_id,
                            "target": "creature",
                            "target_id": blocker_id,
                            "target_player": opponent,
                            "damage": attacker_power
                        })
                        self._info(f"{attacker_card['name']} deals {attacker_power} to {blocker_card['name']}.")
                    
                    # Blocker deals damage back to attacker
                    damage_queue.append({
                        "source": "creature", 
                        "source_id": blocker_id,
                        "target": "creature",
                        "target_id": attacker_id,
                        "target_player": current_player,
                        "damage": blocker_power
                    })
                    self._info(f"{blocker_card['name']} deals {blocker_power} to {attacker_card['name']}.")
                
                else:
                    # Multiple blockers: attacker assigns damage in order, all blockers hit back
                    remaining_damage = attacker_power
                    
                    for blocker_id in blocker_ids:
                        blocker_data = game_state[opponent]["creatures"][blocker_id]
                        blocker_card = blocker_data["card"]
                        blocker_toughness = blocker_card["defence"]
                        blocker_power = blocker_card["attack"]
                        
                        # Assign lethal damage to this blocker, then move to next
                        assigned_damage = min(remaining_damage, blocker_toughness)
                        
                        if assigned_damage > 0:
                            damage_queue.append({
                                "source": "creature",
                                "source_id": attacker_id,
                                "target": "creature", 
                                "target_id": blocker_id,
                                "target_player": opponent,
                                "damage": assigned_damage
                            })
                            remaining_damage -= assigned_damage
                            self._info(f"{attacker_card['name']} assigns {assigned_damage} to {blocker_card['name']}.")
                        
                        # Blocker deals damage back to attacker
                        damage_queue.append({
                            "source": "creature",
                            "source_id": blocker_id,
                            "target": "creature",
                            "target_id": attacker_id,
                            "target_player": current_player,
                            "damage": blocker_power
                        })
                        self._info(f"{blocker_card['name']} deals {blocker_power} to {attacker_card['name']}.")
                    
                    # Handle trample: excess damage goes to player
                    if has_trample and remaining_damage > 0:
                        damage_queue.append({
                            "source": "creature",
                            "source_id": attacker_id,
                            "target": "player",
                            "target_player": opponent,
                            "damage": remaining_damage
                        })
                        self._info(f"{attacker_card['name']} tramples {remaining_damage} to {opponent}.")
            
            else:
                # Unblocked attacker: damage opponent directly
                damage_queue.append({
                    "source": "creature",
                    "source_id": attacker_id,
                    "target": "player",
                    "target_player": opponent,
                    "damage": attacker_power
                })
                self._info(f"{attacker_card['name']} deals {attacker_power} to {opponent} (unblocked).")
        
        # Store damage queue
        game_state["combat"]["damage_queue"] = damage_queue
        self._save_state(game_state)
        
        return True

    def resolve_damage_queue(self):
        """
        Apply ALL damage simultaneously from the damage queue.
        Then check for creature deaths.
        """
        game_state = self._load_state()
        damage_queue = game_state["combat"]["damage_queue"]
        
        if not damage_queue:
            self._info("No combat damage to resolve.")
            return True
        
        self._info("Combat damage resolution begins.")
        
        # Apply all damage simultaneously
        for damage_entry in damage_queue:
            target_type = damage_entry["target"]
            damage_amount = damage_entry["damage"]
            
            if target_type == "player":
                # Damage to player health
                target_player = damage_entry["target_player"]
                game_state[target_player]["health"] -= damage_amount
                new_health = game_state[target_player]["health"]
                self._info(f"{target_player} takes {damage_amount} damage. Health: {new_health}.")
                
            elif target_type == "creature":
                # Damage to creature defence
                target_player = damage_entry["target_player"]
                target_id = damage_entry["target_id"]
                
                if target_id in game_state[target_player]["creatures"]:
                    creature_data = game_state[target_player]["creatures"][target_id]
                    creature_card = creature_data["card"]
                    
                    # Track damage separately and apply to current defence
                    old_damage = creature_data.get("damage_taken", 0)
                    creature_data["damage_taken"] = old_damage + damage_amount
                    
                    old_defence = creature_card["defence"]
                    if not creature_data.get("invuln"):
                        creature_card["defence"] -= damage_amount
                    new_defence = creature_card["defence"]
                    
                    self._info(
                        f"{creature_card['name']} takes {damage_amount} damage. "
                        f"Defence: {old_defence} -> {new_defence}."
                    )
        
        # Clear damage queue after resolution
        game_state["combat"]["damage_queue"] = []
        
        # Save state before checking deaths
        self._save_state(game_state)
        
        # Check for creature deaths
        self.check_creature_deaths()
        
        return True

    def check_creature_deaths(self):
        """
        Move creatures with defence ≤ 0 to graveyard.
        Check both players' creatures.
        """
        game_state = self._load_state()
        deaths = []
        
        self._info("State-based actions check.")
        
        # Check all players for dead creatures
        for player in [self.player1, self.player2]:
            if player not in game_state:
                continue
                
            player_data = game_state[player]
            dead_creatures = []
            
            for creature_id, creature_data in player_data["creatures"].items():
                creature_card = creature_data["card"]
                
                if creature_card["defence"] <= 0:
                    dead_creatures.append(creature_id)
                    deaths.append((player, creature_id, creature_card["name"]))
            
            # Move dead creatures to graveyard
            for creature_id in dead_creatures:
                creature_data = player_data["creatures"][creature_id]
                creature_card = creature_data["card"]
                
                # Add to graveyard
                player_data["graveyard"].append(creature_card)
                
                # Remove from battlefield
                del player_data["creatures"][creature_id]
                
                self._info(f"{creature_card['name']} dies and goes to {player}'s graveyard.")
        
        if not deaths:
            self._info("No creatures died.")
        
        self._save_state(game_state)
        return deaths

    def can_block(self, blocker_id, attacker_id):
        """
        Check if blocker can block attacker.
        Handles flying/reach restrictions.
        """
        game_state = self._load_state()
        
        # Get current and opposing players
        current_player = game_state["current_player"]  
        opponent = self.player2 if current_player == self.player1 else self.player1
        
        # Get attacker data
        if str(attacker_id) not in game_state[current_player]["creatures"]:
            return False
        
        # Get blocker data  
        if str(blocker_id) not in game_state[opponent]["creatures"]:
            return False
            
        attacker_data = game_state[current_player]["creatures"][str(attacker_id)]
        blocker_data = game_state[opponent]["creatures"][str(blocker_id)]
        
        attacker_card = attacker_data["card"]
        blocker_card = blocker_data["card"]
        
        # Check if blocker is tapped
        if blocker_card["tapped"] == 1:
            return False
        
        # Check unblockable
        if "unblockable" in attacker_card.get("status", "").lower():
            return False
        
        # Check flying/reach restrictions
        attacker_has_flying = "flying" in attacker_card.get("status", "").lower()
        blocker_has_flying = "flying" in blocker_card.get("status", "").lower()
        blocker_has_reach = "reach" in blocker_card.get("status", "").lower()
        
        # Flying creatures can only be blocked by flying or reach
        if attacker_has_flying and not (blocker_has_flying or blocker_has_reach):
            return False
        
        return True

    def check_win_condition(self):
        """
        Check if any player has won (health ≤ 0 or empty deck).
        Returns winner name or None.
        """
        game_state = self._load_state()
        
        for player in [self.player1, self.player2]:
            if player not in game_state:
                continue
                
            player_data = game_state[player]
            
            # Check health
            if player_data["health"] <= 0:
                opponent = self.player2 if player == self.player1 else self.player1
                self._warn(f"Game over: {player} reduced to {player_data['health']} health.")
                self._info(f"{opponent} wins.")
                return opponent
                
            # Check empty deck (try to draw when deck is empty = lose)  
            if len(player_data["deck"]) == 0:
                opponent = self.player2 if player == self.player1 else self.player1
                self._warn(f"Game over: {player} tried to draw from an empty deck.")
                self._info(f"{opponent} wins.")
                return opponent
        
        return None

    def assign_damage_order(self, attacker_id, blocker_ids):
        """
        For multiple blockers: attacker chooses damage assignment order.
        Returns ordered list of blocker IDs.
        """
        # For now, use the order provided by the player
        # This could be enhanced with interactive damage assignment
        return [str(bid) for bid in blocker_ids]

    def move_to_graveyard(self, player, card_id, from_zone):
        """
        Move card from battlefield/hand to graveyard.
        """
        game_state = self._load_state()
        
        if player not in game_state:
            return False
            
        player_data = game_state[player]
        card_id_str = str(card_id)
        
        if from_zone == "battlefield" and card_id_str in player_data["creatures"]:
            creature_data = player_data["creatures"][card_id_str]
            card_dict = creature_data["card"]
            
            # Add to graveyard
            player_data["graveyard"].append(card_dict)
            
            # Remove from battlefield
            del player_data["creatures"][card_id_str]
            
        elif from_zone == "hand" and card_id_str in player_data["hand"]:
            card_dict = player_data["hand"][card_id_str] 
            
            # Add to graveyard
            player_data["graveyard"].append(card_dict)
            
            # Remove from hand
            del player_data["hand"][card_id_str]
        
        else:
            return False
            
        self._save_state(game_state)
        return True

    def count_graveyard(self, player, card_name):
        """
        Count cards with specific name in player's graveyard.
        Used for graveyard counting effects (Skeleton Army).
        """
        game_state = self._load_state()
        
        if player not in game_state:
            return 0
            
        player_data = game_state[player]
        count = 0
        
        for card_dict in player_data["graveyard"]:
            if card_dict.get("name") == card_name:
                count += 1
                
        return count

    def check_summon_triggers(self, summoning_player, summoning_card_id):
        """
        Check for and execute 'summon?' triggers when a creature is summoned.
        """
        game_state = self._load_state()
        
        self._info("Summon triggers check.")
        
        triggers_fired = False
        
        if summoning_player in game_state:
            creature_data = game_state[summoning_player]["creatures"].get(str(summoning_card_id))
            if creature_data:
                creature_card = creature_data["card"]
                effect = creature_card.get("effect", "")
                if "summon?" in effect:
                    triggers_fired = True
                    self._info(f"{creature_card['name']} triggers (summon?).")
                    self._execute_trigger_effect(summoning_player, str(summoning_card_id), effect, "summon?")
        
        if not triggers_fired:
            self._info("No summon triggers.")
        
        # Note: _execute_trigger_effect handles its own _save_state calls
        return True

    def check_enter_triggers(self, entering_player, entering_card_id):
        """
        Check for and execute 'enter?' triggers when a creature enters.
        ALL creatures on battlefield can trigger when another creature enters.
        """
        game_state = self._load_state()
        
        self._info("Enter triggers check.")
        
        triggers_fired = False
        
        # Check all players' creatures for enter? triggers
        for player in [self.player1, self.player2]:
            if player not in game_state:
                continue
                
            player_data = game_state[player]
            
            for creature_id, creature_data in player_data["creatures"].items():
                creature_card = creature_data["card"]
                effect = creature_card.get("effect", "")
                
                # Check if this creature has enter? trigger
                if "enter?" in effect:
                    # Don't trigger on self (creature entering doesn't trigger itself)
                    if player == entering_player and creature_id == str(entering_card_id):
                        continue
                        
                    triggers_fired = True
                    self._info(f"{creature_card['name']} triggers (enter?).")
                    
                    # Execute the enter? effect on this creature
                    self._execute_trigger_effect(player, creature_id, effect, "enter?")
        
        if not triggers_fired:
            self._info("No enter triggers.")
        
        # Note: _execute_trigger_effect handles its own _save_state calls
        return True

    def check_attack_triggers(self, attacking_player, attacker_ids):
        """
        Check for and execute 'attack?' triggers when creatures attack.
        """
        game_state = self._load_state()
        
        self._info("Attack triggers check.")
        
        triggers_fired = False
        
        for attacker_id in attacker_ids:
            attacker_id_str = str(attacker_id)
            
            if attacker_id_str in game_state[attacking_player]["creatures"]:
                creature_data = game_state[attacking_player]["creatures"][attacker_id_str]
                creature_card = creature_data["card"]
                effect = creature_card.get("effect", "")
                
                # Check if this creature has attack? trigger
                if "attack?" in effect:
                    triggers_fired = True
                    self._info(f"{creature_card['name']} triggers (attack?).")
                    
                    # Execute the attack? effect on this creature
                    self._execute_trigger_effect(attacking_player, attacker_id_str, effect, "attack?")
        
        if not triggers_fired:
            self._info("No attack triggers.")
        
        # Note: _execute_trigger_effect handles its own _save_state calls
        return True

    def check_block_triggers(self, blocking_player, blocker_ids):
        """
        Check for and execute 'block?' triggers when creatures block.
        """
        game_state = self._load_state()
        
        self._info("Block triggers check.")
        
        triggers_fired = False
        
        for blocker_id in blocker_ids:
            blocker_id_str = str(blocker_id)
            
            if blocker_id_str in game_state[blocking_player]["creatures"]:
                creature_data = game_state[blocking_player]["creatures"][blocker_id_str]
                creature_card = creature_data["card"]
                effect = creature_card.get("effect", "")
                
                # Check if this creature has block? trigger
                if "block?" in effect:
                    triggers_fired = True
                    self._info(f"{creature_card['name']} triggers (block?).")
                    
                    # Execute the block? effect on this creature
                    self._execute_trigger_effect(blocking_player, blocker_id_str, effect, "block?")
        
        if not triggers_fired:
            self._info("No block triggers.")
        
        # Note: _execute_trigger_effect handles its own _save_state calls
        return True

    def _execute_trigger_effect(self, player, creature_id, effect_string, trigger_type):
        """
        Execute a specific trigger effect on a creature.
        Parses and applies effects like 'attack? inc att 2; dec end 1'.
        """
        try:
            from .modules.parser import EffectParser
            from .modules.utils import execute_card
        except:
            from modules.parser import EffectParser
            from modules.utils import execute_card
        
        game_state = self._load_state()
        
        if player not in game_state or creature_id not in game_state[player]["creatures"]:
            return False
        
        creature_data = game_state[player]["creatures"][creature_id]
        creature_card = creature_data["card"]

        def add_status(card, status):
            existing = card.get("status", "")
            if not existing:
                card["status"] = status
            else:
                statuses = [s.strip() for s in existing.split(",") if s.strip()]
                if status not in statuses:
                    statuses.append(status)
                    card["status"] = ", ".join(statuses)
        
        # Parse the effect to find the specific trigger
        parser = EffectParser()
        parsed_effects = parser.parse(effect_string)
        
        # Find and execute the matching trigger
        permanent_enter_buff = trigger_type in ("enter?", "enter") and creature_card.get("name") == "Vine Elemental"

        for effect in parsed_effects:
            trigger_without_question = trigger_type.replace("?", "")
            effect_trigger = effect.get("trigger")
            
            # Match both "enter?" and "enter" formats
            if effect_trigger == trigger_type or effect_trigger == trigger_without_question:
                self._info(f"Trigger executes: {effect}")
                
                # Apply the effect to the creature (or globally)
                if effect["action"] in ("inc", "dec"):
                    field = effect["field"]
                    value = effect["value"]
                    sign = 1 if effect["action"] == "inc" else -1
                    
                    # Map parser field names to card field names
                    field_mapping = {"att": "attack", "end": "defence"}
                    card_field = field_mapping.get(field, field)

                    if effect.get("all"):
                        for owner in [self.player1, self.player2]:
                            for cid, cdata in game_state[owner]["creatures"].items():
                                target_card = cdata["card"]
                                if card_field not in target_card:
                                    continue
                                delta = sign * value
                                target_card[card_field] += delta
                                if card_field == "attack":
                                    cdata["base_attack"] = cdata.get("base_attack", target_card[card_field]) + delta
                                elif card_field == "defence":
                                    cdata["base_defence"] = cdata.get("base_defence", target_card[card_field]) + delta
                        self._info(f"All creatures {card_field} {'+' if sign*value>=0 else ''}{sign*value}.")
                    elif effect.get("global"):
                        delta = sign * value
                        for cid, cdata in game_state[player]["creatures"].items():
                            target_card = cdata["card"]
                            if card_field not in target_card:
                                continue
                            target_card[card_field] += delta
                            if card_field == "attack":
                                cdata["base_attack"] = cdata.get("base_attack", target_card[card_field]) + delta
                            elif card_field == "defence":
                                cdata["base_defence"] = cdata.get("base_defence", target_card[card_field]) + delta
                        self._info(f"{player}'s creatures {card_field} {'+' if delta>=0 else ''}{delta}.")
                    else:
                        if card_field in creature_card:
                            old_value = creature_card[card_field]
                            delta = sign * value
                            creature_card[card_field] += delta
                            if permanent_enter_buff:
                                if card_field == "attack":
                                    creature_data["base_attack"] = creature_data.get("base_attack", creature_card[card_field]) + delta
                                elif card_field == "defence":
                                    creature_data["base_defence"] = creature_data.get("base_defence", creature_card[card_field]) + delta
                            new_value = creature_card[card_field]
                            self._info(f"{creature_card['name']} {card_field}: {old_value} -> {new_value}.")

                elif effect["action"] == "add":
                    status = effect.get("field")
                    if effect.get("all"):
                        for owner in [self.player1, self.player2]:
                            for cid, cdata in game_state[owner]["creatures"].items():
                                add_status(cdata["card"], status)
                        self._info(f"Status {status} added to all creatures.")
                    elif effect.get("global"):
                        for cid, card in game_state[player]["hand"].items():
                            if card.get("type") != "Creature":
                                continue
                            add_status(card, status)
                        self._info(f"Status {status} added to hand creatures.")
                    else:
                        add_status(creature_card, status)
                        self._info(f"{creature_card['name']} gains {status}.")

                elif effect["action"] in ("kill", "destroy"):
                    if effect.get("all"):
                        for owner in [self.player1, self.player2]:
                            for cid, cdata in list(game_state[owner]["creatures"].items()):
                                game_state[owner]["graveyard"].append(cdata["card"])
                                del game_state[owner]["creatures"][cid]
                        self._info("All creatures destroyed.")
                    elif effect.get("global"):
                        for cid, cdata in list(game_state[player]["creatures"].items()):
                            game_state[player]["graveyard"].append(cdata["card"])
                            del game_state[player]["creatures"][cid]
                        self._info(f"{player}'s creatures destroyed.")
                    else:
                        game_state[player]["graveyard"].append(creature_card)
                        del game_state[player]["creatures"][str(creature_id)]
                        self._info(f"{creature_card['name']} destroyed.")

                elif effect["action"] == "invuln":
                    creature_data["invuln"] = True
                    add_status(creature_card, "invuln")
                    creature_card["defence"] = 9999
                    self._info(f"{creature_card['name']} becomes invulnerable.")

                elif effect["action"] == "draw":
                    value = effect["value"]
                    player_data = game_state.get(player, {})
                    deck = player_data.get("deck", [])
                    hand = player_data.get("hand", {})
                    drawn = 0
                    for _ in range(value):
                        if not deck:
                            self._warn(f"{player} cannot draw: deck is empty.")
                            break
                        card = deck.pop(0)
                        hand[str(card["id"])] = card
                        drawn += 1
                    self._info(f"{player} draws {drawn} card(s).")
        
        # For grouped effects like "enter? inc att 1; inc end 1", the parser may split them
        # Look for follow-up effects without triggers that should be part of the same group
        last_trigger = None
        for effect in parsed_effects:
            if effect.get("trigger"):
                last_trigger = effect.get("trigger")
            elif last_trigger == trigger_type and not effect.get("trigger"):
                # This is a continuation of the previous trigger
                self._info(f"Trigger grouped effect: {effect}")
                
                if effect["action"] == "inc":
                    field = effect["field"]
                    value = effect["value"]
                    
                    # Map parser field names to card field names
                    field_mapping = {"att": "attack", "end": "defence"}
                    card_field = field_mapping.get(field, field)
                    
                    if effect.get("all"):
                        for owner in [self.player1, self.player2]:
                            for cid, cdata in game_state[owner]["creatures"].items():
                                target_card = cdata["card"]
                                if card_field in target_card:
                                    target_card[card_field] += value
                        self._info(f"All creatures {card_field} +{value}.")
                    elif effect.get("global"):
                        for cid, cdata in game_state[player]["creatures"].items():
                            target_card = cdata["card"]
                            if card_field in target_card:
                                target_card[card_field] += value
                        self._info(f"{player}'s creatures {card_field} +{value}.")
                    else:
                        if card_field in creature_card:
                            old_value = creature_card[card_field]
                            creature_card[card_field] += value
                            if permanent_enter_buff:
                                if card_field == "attack":
                                    creature_data["base_attack"] = creature_data.get("base_attack", creature_card[card_field]) + value
                                elif card_field == "defence":
                                    creature_data["base_defence"] = creature_data.get("base_defence", creature_card[card_field]) + value
                            new_value = creature_card[card_field]
                            self._info(f"{creature_card['name']} {card_field}: {old_value} -> {new_value}.")
        
        # Save the modified creature stats
        self._save_state(game_state)
        
        return True

    def _reconstruct_card(self, card_dict):
        """Reconstruct a card object from a dictionary."""
        card_type = card_dict.get("type")
        
        if card_type == "Creature":
            card = SummonCard(
                name=card_dict.get("name"),
                generic_mana=card_dict.get("generic_mana"),
                sp_mana=card_dict.get("sp_mana"),
                description=card_dict.get("description"),
                att=card_dict.get("attack"),
                end=card_dict.get("defence"),
                effect=card_dict.get("effect")
            )
            # Restore state
            card.id = card_dict.get("id")
            card.tapped = card_dict.get("tapped", 0)
            card.status = card_dict.get("status", "")
            return card
            
        elif card_type == "Land":
            card = LandCards(
                name=card_dict.get("name"),
                generic_mana=card_dict.get("generic_mana"),
                sp_mana=card_dict.get("sp_mana"),
                description=card_dict.get("description"),
                effect=card_dict.get("effect")
            )
            # Restore state
            card.id = card_dict.get("id")
            card.tapped = card_dict.get("tapped", 0)
            card.status = card_dict.get("status", "")
            return card
            
        elif card_type == "Spell":
            card = SpellCard(
                name=card_dict.get("name"),
                generic_mana=card_dict.get("generic_mana"),
                sp_mana=card_dict.get("sp_mana"),
                description=card_dict.get("description"),
                effect=card_dict.get("effect")
            )
            # Restore state  
            card.id = card_dict.get("id")
            card.tapped = card_dict.get("tapped", 0)
            card.status = card_dict.get("status", "")
            return card
        
        else:
            self._warn(f"Unknown card type: {card_type}.")
            return None

    def _find_card_by_name(self, name):
        """Find a card definition by name in card_index."""
        try:
            from . import card_index as card_index_module
        except:
            import card_index as card_index_module
        target = name.strip().lower()
        for value in card_index_module.__dict__.values():
            if hasattr(value, "name") and isinstance(value.name, str):
                if value.name.lower() == target:
                    return value
        return None

    def get_game_state(self):
        """Get the current game state with proper formatting for CLI."""
        game_state = self._load_state()
        
        # Add active_player field for CLI compatibility
        if 'active_player' not in game_state:
            # Determine active player from current_player or default to Player1
            if 'current_player' in game_state and game_state['current_player']:
                game_state['active_player'] = game_state['current_player']
            else:
                # Default to the first player if no current player is set
                game_state['active_player'] = self.player1
        
        # Add turn field if missing
        if 'turn' not in game_state:
            game_state['turn'] = game_state.get('turn_number', 1)
            
        return game_state

    def ready(self):
        """Prepares the game state and variables for the next game."""
        # resets the .json file to an empty JSON object
        ts = time.time()
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        print(f"[{timestamp}] INFO: Game setup begins.")
        
        # Create the db directory if it doesn't exist
        os.makedirs(os.path.dirname(self.game_file), exist_ok=True)
        
        with open(self.game_file, "w") as f:
            json.dump({}, f)
        
        # assign unique IDs to each card copy
        self.assign_card_ids(self.deck1)
        self.assign_card_ids(self.deck2)
        
        # shuffle
        self.deck1 = self.shuffle_deck(self.deck1)
        self.deck2 = self.shuffle_deck(self.deck2)
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        print(f"[{timestamp}] INFO: Decks created and shuffled.")
        
        player1_data = {
                "deck": [card.to_dict() for card in self.deck1],
                "hand": {},
                "graveyard": [],
                "health": 20,
                "creatures": {},
                "lands": {},
                "blue_mana": 0,
                "red_mana": 0,
                "green_mana": 0,
                "queue": {}
        }

        player2_data = {
                "deck": [card.to_dict() for card in self.deck2],
                "hand": {},
                "graveyard": [],
                "health": 20,
                "creatures": {},
                "lands": {},
                "blue_mana": 0,
                "red_mana": 0,
                "green_mana": 0,
                "queue": {}
        }

        game_state = {
            self.player1: player1_data,
            self.player2: player2_data,
            "battlefield": self.battlefield,
            "turn_number": 0,
            "current_player": None,
            "phase": "setup",
            "lands_played_this_turn": 0,
            "combat": {
                "attackers": [],
                "blocks": {},
                "damage_queue": []
            }
        }

        # create battlefield
        with open(self.game_file, "w") as f:
            json.dump(game_state, f, indent=4)

        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        print(f"[{timestamp}] INFO: Game battlefield created.")
