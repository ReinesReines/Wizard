try:
    from .modules.cards import Cards, SummonCard, SpellCard, LandCards
    from .modules.utils import execute_card, enters_tapped, card_has_trigger, get_all_keywords
    from .card_index import *
except:
    from modules.cards import Cards, SummonCard, SpellCard, LandCards
    from modules.utils import execute_card, enters_tapped, card_has_trigger, get_all_keywords
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
            print(f"[{self._timestamp()}] Error: Player '{player}' not found in game state")
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
            print(f"[{self._timestamp()}] Error: Card with ID {card_id} not found in {player}'s hand")
            return False
        
        # Reconstruct card object from dictionary
        card = self._reconstruct_card(card_dict)
        
        if not card:
            print(f"[{self._timestamp()}] Error: Could not reconstruct card from data")
            return False
        
        # Check if it's a creature card
        if not isinstance(card, SummonCard):
            print(f"[{self._timestamp()}] Error: Card '{card.name}' is not a creature")
            return False
        
        # Execute card effects
        executed_card = execute_card(card, game_state)
        
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
            "summoning_sickness": not card_has_trigger(executed_card, "haste")
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
        
        print(f"[{self._timestamp()}] {player} played {executed_card.name} (ID: {card_id}) - {executed_card.attack}/{executed_card.defence}")
        
        # Check for enter? triggers from other creatures
        self.check_enter_triggers(player, card_id)
        
        return True

    # ===================
    # CORE GAME LOOP
    # ===================
    
    def draw_card(self, player):
        """Move top card from deck to hand."""
        game_state = self._load_state()
        
        if player not in game_state:
            print(f"[{self._timestamp()}] Error: Player '{player}' not found")
            return False
        
        player_data = game_state[player]
        
        # Check if deck is empty
        if not player_data["deck"]:
            print(f"[{self._timestamp()}] {player} cannot draw - deck is empty!")
            return False
        
        # Draw top card
        card = player_data["deck"].pop(0)
        card_id = str(card["id"])
        player_data["hand"][card_id] = card
        
        print(f"[{self._timestamp()}] {player} draws: {card['name']} (ID: {card_id})")
        
        self._save_state(game_state)
        return True
    
    def start_turn(self, player):
        """Initialize turn, increment counter, set active player."""
        game_state = self._load_state()
        
        game_state["turn_number"] = game_state.get("turn_number", 0) + 1
        game_state["current_player"] = player
        game_state["phase"] = "untap"
        game_state["lands_played_this_turn"] = 0
        
        print(f"\n[{self._timestamp()}] === TURN {game_state['turn_number']}: {player} ===\n")
        
        self._save_state(game_state)
    
    def untap_step(self, player):
        """Untap all creatures and lands."""
        game_state = self._load_state()
        
        if player not in game_state:
            return
        
        print(f"[{self._timestamp()}] UNTAP STEP:")
        player_data = game_state[player]
        
        # Untap creatures and clear summoning sickness
        for creature_id, creature_data in player_data["creatures"].items():
            # Untap
            if creature_data["card"]["tapped"] == 1:
                creature_data["card"]["tapped"] = 0
                print(f"  [{self._timestamp()}] {creature_data['card']['name']} untaps")
            
            # Clear summoning sickness (affects both tapped and untapped creatures)
            creature_data["summoning_sickness"] = False
        
        # Untap lands
        for land_id, land_data in player_data["lands"].items():
            if land_data["card"]["tapped"] == 1:
                land_data["card"]["tapped"] = 0
                print(f"  [{self._timestamp()}] {land_data['card']['name']} untaps")
        
        game_state["phase"] = "upkeep"
        self._save_state(game_state)
    
    def draw_step(self, player):
        """Draw 1 card (skip turn 1 for starting player)."""
        game_state = self._load_state()
        turn_number = game_state.get("turn_number", 1)
        
        print(f"\n[{self._timestamp()}] DRAW STEP:")
        
        # Skip first draw for starting player on turn 1
        if turn_number == 1 and player == self.player1:
            print(f"  [{self._timestamp()}] {player} skips draw (turn 1)")
        else:
            self.draw_card(player)
        
        game_state = self._load_state()
        game_state["phase"] = "main_pre"
        self._save_state(game_state)
    
    def end_turn(self, player):
        """Run cleanup, clear mana pool, shift to opponent."""
        game_state = self._load_state()
        
        print(f"\n[{self._timestamp()}] END PHASE:")
        
        # Clear mana pool
        self.clear_mana_pool(player)
        
        game_state = self._load_state()
        game_state["phase"] = "end"
        game_state["lands_played_this_turn"] = 0
        
        print(f"  [{self._timestamp()}] {player}'s turn ends\n")
        
        self._save_state(game_state)
    
    def clear_mana_pool(self, player):
        """Reset all mana to 0."""
        game_state = self._load_state()
        
        if player not in game_state:
            return
        
        player_data = game_state[player]
        player_data["blue_mana"] = 0
        player_data["red_mana"] = 0
        player_data["green_mana"] = 0
        
        print(f"  [{self._timestamp()}] Mana pool cleared → blue: 0, red: 0, green: 0")
        
        self._save_state(game_state)

    # ===================
    # LAND & MANA SYSTEM
    # ===================
    
    def play_land(self, player, card_id):
        """Move land from hand to lands dict."""
        game_state = self._load_state()
        
        if player not in game_state:
            print(f"[{self._timestamp()}] Error: Player '{player}' not found")
            return False
        
        # Check lands played this turn
        if game_state.get("lands_played_this_turn", 0) >= 1:
            print(f"[{self._timestamp()}] Error: {player} already played a land this turn")
            return False
        
        player_data = game_state[player]
        card_id_str = str(card_id)
        
        # Find card in hand
        if card_id_str not in player_data["hand"]:
            print(f"[{self._timestamp()}] Error: Card ID {card_id} not in {player}'s hand")
            return False
        
        card_dict = player_data["hand"][card_id_str]
        
        # Verify it's a land
        if card_dict.get("type") != "Land":
            print(f"[{self._timestamp()}] Error: {card_dict['name']} is not a land")
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
        
        print(f"[{self._timestamp()}] {player} plays {card.name}")
        if card.tapped:
            print(f"  [{self._timestamp()}] {card.name} enters tapped")
        
        self._save_state(game_state)
        return True
    
    def tap_land(self, player, land_id):
        """Execute 'tap? gen [color]' effect, set tapped=1."""
        game_state = self._load_state()
        
        if player not in game_state:
            return False
        
        player_data = game_state[player]
        land_id_str = str(land_id)
        
        if land_id_str not in player_data["lands"]:
            print(f"[{self._timestamp()}] Error: Land ID {land_id} not found")
            return False
        
        land_data = player_data["lands"][land_id_str]
        
        # Check if already tapped
        if land_data["card"]["tapped"] == 1:
            print(f"[{self._timestamp()}] Error: {land_data['card']['name']} is already tapped")
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
            
            # For dual lands, choose first color (can be enhanced later)
            if colors:
                color = colors[0]
                player_data[f"{color}_mana"] += 1
                print(f"[{self._timestamp()}] {player} taps {land_data['card']['name']} for {color} → {color}_mana: {player_data[f'{color}_mana']}")
        
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
            print(f"[{self._timestamp()}] Error: Not enough mana")
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
        
        print(f"[{self._timestamp()}] Paid: {generic} generic + {sp_mana if sp_mana else 'none'}")
        
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
            print(f"[{self._timestamp()}] Error: Player '{player}' not found")
            return False
        
        player_data = game_state[player]
        attackers = []
        
        print(f"[{self._timestamp()}] DECLARE ATTACKERS:")
        
        for creature_id in creature_ids:
            creature_id_str = str(creature_id)
            
            if creature_id_str not in player_data["creatures"]:
                print(f"  [{self._timestamp()}] Error: Creature ID {creature_id} not found")
                continue
            
            creature_data = player_data["creatures"][creature_id_str]
            card = creature_data["card"]
            
            # Check if tapped
            if card["tapped"] == 1:
                print(f"  [{self._timestamp()}] Error: {card['name']} is already tapped")
                continue
            
            # Check summoning sickness
            if creature_data.get("summoning_sickness", False):
                print(f"  [{self._timestamp()}] Error: {card['name']} has summoning sickness")
                continue
            
            # Valid attacker
            attackers.append(creature_id_str)
            
            # Check if vigilant (from status or effect)
            has_vigilant = "vigilant" in card.get("status", "").lower() or "notap" in card.get("status", "").lower()
            
            # Tap creature unless vigilant
            if not has_vigilant:
                card["tapped"] = 1
                print(f"  [{self._timestamp()}] {card['name']} attacks (tapped)")
            else:
                print(f"  [{self._timestamp()}] {card['name']} attacks (vigilant - stays untapped)")
        
        # Store attackers in combat state
        game_state["combat"]["attackers"] = attackers
        
        print(f"  [{self._timestamp()}] Total attackers: {len(attackers)}")
        
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
            print(f"[{self._timestamp()}] Error: Player '{defender}' not found")
            return False
        
        print(f"[{self._timestamp()}] DECLARE BLOCKERS:")
        
        defender_data = game_state[defender]
        blocks = {}
        
        for attacker_id, blocker_ids in block_assignments.items():
            attacker_id_str = str(attacker_id)
            
            if attacker_id_str not in game_state["combat"]["attackers"]:
                print(f"  [{self._timestamp()}] Error: {attacker_id} is not attacking")
                continue
            
            valid_blockers = []
            
            for blocker_id in blocker_ids:
                blocker_id_str = str(blocker_id)
                
                if blocker_id_str not in defender_data["creatures"]:
                    print(f"  [{self._timestamp()}] Error: Blocker {blocker_id} not found")
                    continue
                
                # Use can_block() for validation (includes flying/reach/unblockable checks)
                if not self.can_block(blocker_id_str, attacker_id_str):
                    blocker_data = defender_data["creatures"][blocker_id_str]
                    print(f"  [{self._timestamp()}] Error: {blocker_data['card']['name']} cannot block (tapped/flying/unblockable)")
                    continue
                
                blocker_data = defender_data["creatures"][blocker_id_str]
                valid_blockers.append(blocker_id_str)
                print(f"  [{self._timestamp()}] {blocker_data['card']['name']} blocks attacker {attacker_id}")
            
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
        
        # Check tapped
        if creature_data["card"]["tapped"] == 1:
            return False
        
        # Check summoning sickness
        if creature_data.get("summoning_sickness", False):
            return False
        
        return True

    def calculate_combat_damage(self):
        """
        Build damage queue for all attackers and blockers.
        Does NOT apply damage yet - that's done in resolve_damage_queue().
        """
        game_state = self._load_state()
        damage_queue = []
        
        print(f"[{self._timestamp()}] DAMAGE CALCULATION:")
        
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
                
                if len(blocker_ids) == 1:
                    # Single blocker: mutual damage
                    blocker_id = blocker_ids[0]
                    blocker_data = game_state[opponent]["creatures"][blocker_id]
                    blocker_card = blocker_data["card"]
                    blocker_power = blocker_card["attack"]
                    
                    # Queue damage: attacker to blocker, blocker to attacker
                    damage_queue.append({
                        "source": "creature",
                        "source_id": attacker_id,
                        "target": "creature",
                        "target_id": blocker_id,
                        "target_player": opponent,
                        "damage": attacker_power
                    })
                    
                    damage_queue.append({
                        "source": "creature", 
                        "source_id": blocker_id,
                        "target": "creature",
                        "target_id": attacker_id,
                        "target_player": current_player,
                        "damage": blocker_power
                    })
                    
                    print(f"  [{self._timestamp()}] {attacker_card['name']} deals {attacker_power} to {blocker_card['name']}")
                    print(f"  [{self._timestamp()}] {blocker_card['name']} deals {blocker_power} to {attacker_card['name']}")
                
                else:
                    # Multiple blockers: attacker assigns damage, all blockers hit back
                    remaining_damage = attacker_power
                    
                    for blocker_id in blocker_ids:
                        blocker_data = game_state[opponent]["creatures"][blocker_id]
                        blocker_card = blocker_data["card"]
                        blocker_toughness = blocker_card["defence"]
                        blocker_power = blocker_card["attack"]
                        
                        # Assign lethal damage first, then remaining
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
                            print(f"  [{self._timestamp()}] {attacker_card['name']} assigns {assigned_damage} to {blocker_card['name']}")
                        
                        # Blocker deals damage back to attacker
                        damage_queue.append({
                            "source": "creature",
                            "source_id": blocker_id,
                            "target": "creature",
                            "target_id": attacker_id,
                            "target_player": current_player,
                            "damage": blocker_power
                        })
                        print(f"  [{self._timestamp()}] {blocker_card['name']} deals {blocker_power} to {attacker_card['name']}")
            
            else:
                # Unblocked attacker: damage opponent directly
                damage_queue.append({
                    "source": "creature",
                    "source_id": attacker_id,
                    "target": "player",
                    "target_player": opponent,
                    "damage": attacker_power
                })
                print(f"  [{self._timestamp()}] {attacker_card['name']} deals {attacker_power} to {opponent} (unblocked)")
        
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
            print(f"[{self._timestamp()}] No damage to resolve")
            return True
        
        print(f"[{self._timestamp()}] DAMAGE RESOLUTION:")
        
        # Apply all damage simultaneously
        for damage_entry in damage_queue:
            target_type = damage_entry["target"]
            damage_amount = damage_entry["damage"]
            
            if target_type == "player":
                # Damage to player health
                target_player = damage_entry["target_player"]
                game_state[target_player]["health"] -= damage_amount
                new_health = game_state[target_player]["health"]
                print(f"  [{self._timestamp()}] {target_player} takes {damage_amount} damage → Health: {new_health}")
                
            elif target_type == "creature":
                # Damage to creature defence
                target_player = damage_entry["target_player"]
                target_id = damage_entry["target_id"]
                
                if target_id in game_state[target_player]["creatures"]:
                    creature_data = game_state[target_player]["creatures"][target_id]
                    creature_card = creature_data["card"]
                    
                    old_defence = creature_card["defence"]
                    creature_card["defence"] -= damage_amount
                    new_defence = creature_card["defence"]
                    
                    print(f"  [{self._timestamp()}] {creature_card['name']} takes {damage_amount} damage → Defence: {old_defence} → {new_defence}")
        
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
        
        print(f"[{self._timestamp()}] STATE-BASED ACTIONS:")
        
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
                
                print(f"  [{self._timestamp()}] {creature_card['name']} dies → {player}'s graveyard")
        
        if not deaths:
            print(f"  [{self._timestamp()}] No creatures died")
        
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
                print(f"[{self._timestamp()}] GAME OVER: {player} reduced to {player_data['health']} health!")
                print(f"[{self._timestamp()}] {opponent} wins!")
                return opponent
                
            # Check empty deck (try to draw when deck is empty = lose)  
            if len(player_data["deck"]) == 0:
                opponent = self.player2 if player == self.player1 else self.player1
                print(f"[{self._timestamp()}] GAME OVER: {player} tried to draw from empty deck!")
                print(f"[{self._timestamp()}] {opponent} wins!")
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

    def check_enter_triggers(self, entering_player, entering_card_id):
        """
        Check for and execute 'enter?' triggers when a creature enters.
        ALL creatures on battlefield can trigger when another creature enters.
        """
        game_state = self._load_state()
        
        print(f"[{self._timestamp()}] ENTER TRIGGERS:")
        
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
                    print(f"  [{self._timestamp()}] {creature_card['name']} triggers (enter?)")
                    
                    # Execute the enter? effect on this creature
                    self._execute_trigger_effect(player, creature_id, effect, "enter?")
        
        if not triggers_fired:
            print(f"  [{self._timestamp()}] No enter? triggers")
        
        # Note: _execute_trigger_effect handles its own _save_state calls
        return True

    def check_attack_triggers(self, attacking_player, attacker_ids):
        """
        Check for and execute 'attack?' triggers when creatures attack.
        """
        game_state = self._load_state()
        
        print(f"[{self._timestamp()}] ATTACK TRIGGERS:")
        
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
                    print(f"  [{self._timestamp()}] {creature_card['name']} triggers (attack?)")
                    
                    # Execute the attack? effect on this creature
                    self._execute_trigger_effect(attacking_player, attacker_id_str, effect, "attack?")
        
        if not triggers_fired:
            print(f"  [{self._timestamp()}] No attack? triggers")
        
        # Note: _execute_trigger_effect handles its own _save_state calls
        return True

    def check_block_triggers(self, blocking_player, blocker_ids):
        """
        Check for and execute 'block?' triggers when creatures block.
        """
        game_state = self._load_state()
        
        print(f"[{self._timestamp()}] BLOCK TRIGGERS:")
        
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
                    print(f"  [{self._timestamp()}] {creature_card['name']} triggers (block?)")
                    
                    # Execute the block? effect on this creature
                    self._execute_trigger_effect(blocking_player, blocker_id_str, effect, "block?")
        
        if not triggers_fired:
            print(f"  [{self._timestamp()}] No block? triggers")
        
        # Note: _execute_trigger_effect handles its own _save_state calls
        return True

    def _execute_trigger_effect(self, player, creature_id, effect_string, trigger_type):
        """
        Execute a specific trigger effect on a creature.
        Parses and applies effects like 'attack? inc att 2; dec end 1'.
        """
        from .modules.parser import EffectParser
        from .modules.utils import execute_card
        
        game_state = self._load_state()
        
        if player not in game_state or creature_id not in game_state[player]["creatures"]:
            return False
        
        creature_data = game_state[player]["creatures"][creature_id]
        creature_card = creature_data["card"]
        
        # Parse the effect to find the specific trigger
        parser = EffectParser()
        parsed_effects = parser.parse(effect_string)
        
        # Find and execute the matching trigger
        for effect in parsed_effects:
            trigger_without_question = trigger_type.replace("?", "")
            effect_trigger = effect.get("trigger")
            
            # Match both "enter?" and "enter" formats
            if effect_trigger == trigger_type or effect_trigger == trigger_without_question:
                print(f"    [{self._timestamp()}] Executing: {effect}")
                
                # Apply the effect to the creature
                if effect["action"] == "inc":
                    field = effect["field"]
                    value = effect["value"]
                    
                    # Map parser field names to card field names
                    field_mapping = {"att": "attack", "end": "defence"}
                    card_field = field_mapping.get(field, field)
                    
                    if card_field in creature_card:
                        old_value = creature_card[card_field]
                        creature_card[card_field] += value
                        new_value = creature_card[card_field]
                        print(f"    [{self._timestamp()}] {creature_card['name']} {card_field}: {old_value} → {new_value}")
                
                elif effect["action"] == "dec":
                    field = effect["field"]
                    value = effect["value"]
                    
                    # Map parser field names to card field names
                    field_mapping = {"att": "attack", "end": "defence"}
                    card_field = field_mapping.get(field, field)
                    
                    if card_field in creature_card:
                        old_value = creature_card[card_field]
                        creature_card[card_field] -= value
                        new_value = creature_card[card_field]
                        print(f"    [{self._timestamp()}] {creature_card['name']} {card_field}: {old_value} → {new_value}")
        
        # For grouped effects like "enter? inc att 1; inc end 1", the parser may split them
        # Look for follow-up effects without triggers that should be part of the same group
        last_trigger = None
        for effect in parsed_effects:
            if effect.get("trigger"):
                last_trigger = effect.get("trigger")
            elif last_trigger == trigger_type and not effect.get("trigger"):
                # This is a continuation of the previous trigger
                print(f"    [{self._timestamp()}] Executing grouped effect: {effect}")
                
                if effect["action"] == "inc":
                    field = effect["field"]
                    value = effect["value"]
                    
                    # Map parser field names to card field names
                    field_mapping = {"att": "attack", "end": "defence"}
                    card_field = field_mapping.get(field, field)
                    
                    if card_field in creature_card:
                        old_value = creature_card[card_field]
                        creature_card[card_field] += value
                        new_value = creature_card[card_field]
                        print(f"    [{self._timestamp()}] {creature_card['name']} {card_field}: {old_value} → {new_value}")
        
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
            print(f"Unknown card type: {card_type}")
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
        print(f"[{timestamp}] Game setup begins")
        
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
        print(f"[{timestamp}] Deck created and shuffled")
        
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
        print(f"[{timestamp}] Game battlefield created")
