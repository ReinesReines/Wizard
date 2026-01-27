import sys
import os
import random
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

try:
    from .game import GameEngine
except:
    from game import GameEngine
from card_index import (
    # Creatures
    slime, bigger_slime, forest_bear, vine_elemental, alpha_wolf,
    skeleton, skeleton_army, phantom_warrior, sea_serpent, arcane_scholar, vergil,
    goblin_raider, fire_elemental, dragon_whelp, berserker, imp, sazael_the_great, red_wizar,
    blue_wizar, green_wizar, stone_giant, king_slime, archer, 
    # Lands
    forest, island, mountain, tropical_grove, volcanic_peak, wild_highlands, snake_pit, machine_factory, sea_of_stars, land_of_iridesence,
    # Spells
    fireball, wild_hunt, berserk, oath, polymorph_skeleton, healing_word, eldritch_blast, wrath, rot, bless, wingify, scorched_earth, inspiration, magic_missile,
)
from modules.utils import *

class Wizard:
    def __init__(self, p1, p2, deck1=None, deck2=None):
        self.p1 = p1
        self.p2 = p2
        if deck1 is None or deck2 is None:
            creature_pool = [
                slime, bigger_slime, forest_bear, vine_elemental, alpha_wolf,
                skeleton, phantom_warrior, arcane_scholar, goblin_raider, 
                fire_elemental, dragon_whelp, berserker, skeleton_army, sea_serpent, imp, sazael_the_great, red_wizar,
                blue_wizar, green_wizar, stone_giant, king_slime, archer, vergil,
            ]
            
            land_pool = [
                forest, forest, forest, island, island, island,
                mountain, mountain, tropical_grove, volcanic_peak, wild_highlands,
                snake_pit, machine_factory, sea_of_stars, land_of_iridesence,
            ]

            spell_pool = [
                fireball, wild_hunt, berserk, oath, polymorph_skeleton, healing_word, eldritch_blast,
                wrath, rot, bless, wingify, scorched_earth, inspiration, magic_missile,
            ]

            import copy
            
            # Create separate deck copies for each player to avoid ID conflicts
            deck1_lands = [copy.deepcopy(random.choice(land_pool)) for _ in range(28)]
            deck1_creatures = [copy.deepcopy(random.choice(creature_pool)) for _ in range(24)]
            deck1_spells = [copy.deepcopy(random.choice(spell_pool)) for _ in range(16)]
            deck1 = deck1_lands + deck1_creatures + deck1_spells
            random.shuffle(deck1)
            
            deck2_lands = [copy.deepcopy(random.choice(land_pool)) for _ in range(28)]
            deck2_creatures = [copy.deepcopy(random.choice(creature_pool)) for _ in range(24)]
            deck2_spells = [copy.deepcopy(random.choice(spell_pool)) for _ in range(16)]
            deck2 = deck2_lands + deck2_creatures + deck2_spells
            random.shuffle(deck2)

        self.game = GameEngine(p1, p2, deck1, deck2)
        self.game.current_turn_drawn = False
    
        self.mulligan_available = {p1: True, p2: True}
        self.game.ready()

        for _ in range(7):
            self.game.draw_card(p1)
            self.game.draw_card(p2)

        self.action_queue = []
        self.combat_phase = None
        self.priority_player = None
        self.pending_attackers = []
        self.pending_blocks = {}
        self.combat_attacker = None
        self.combat_defender = None
        self.combat_used_turn = False
        self.card_played_this_turn = 0

    def current_player(self):
        state = self.game.get_game_state()
        return state["current_player"]
    
    def start_new_turn(self):
        self.game.cleanup_temporary_effects()
        self.card_played_this_turn = 0
        self.combat_used_turn = False
        self.game.check_creature_deaths()
        
        state = self.game.get_game_state()
        current_turn_number = state.get("turn_number", 0)
        next_turn_number = current_turn_number + 1
        
        if next_turn_number % 2 == 1:
            current_player = self.p1
        else:
            current_player = self.p2

        # Discard down to 7 happens after draw step (use updated hand size)
        
        # Start the turn so current_player/turn_number are set in game state
        self.game.start_turn(current_player)
        
        state = self.game.get_game_state()
        player = state["current_player"]
        turn_number = state.get("turn_number", 1)
        
        # Clear priority_player so the prompt shows the correct current player
        self.priority_player = None
        
        self.game.clear_mana_pool(player)
        self.game.untap_step(player)

        if not (turn_number == 1 and player == self.p1) and not (turn_number == 2 and player == self.p2):
            self.game.draw_step(player)
            print(f"Draw: {player} draws a card")
        self.current_turn_drawn = False

        # Discard step moved to end of turn

    def show_hand(self, player=None):
        state = self.game.get_game_state()
        current_player = player or state["current_player"]
        hand = state[current_player]["hand"]

        hand_cards = []
        for card_id, card_data in hand.items():
            hand_cards.append({
                'id': card_id,
                'name': card_data['name'],
                'type': card_data.get('type', 'Unknown'),
                'generic_mana': card_data.get('generic_mana', 0),
                'sp_mana': card_data.get('sp_mana', ''),
                'attack': card_data.get('attack'),
                'defence': card_data.get('defence')
            })
        
        return hand_cards

    def show_board(self, player=None):
        state = self.game.get_game_state()
        current_player = player or state["current_player"]
        creatures = state[current_player]["creatures"]
        lands = state[current_player]["lands"]
        
        board_cards = []
        
        for card_id, creature_data in creatures.items():
            card = creature_data['card']
            tapped = creature_data.get('tapped', card.get('tapped', False))
            board_cards.append({
                'id': card_id,
                'name': card['name'],
                'type': 'Creature',
                'attack': card.get('attack'),
                'defence': card.get('defence'),
                'tapped': bool(tapped),
                'status': creature_data.get('status', [])
            })
        
        for card_id, land_data in lands.items():
            card = land_data['card']
            tapped = land_data.get('tapped', card.get('tapped', False))
            board_cards.append({
                'id': card_id,
                'name': card['name'],
                'type': 'Land',
                'tapped': bool(tapped)
            })
        
        return board_cards

    def play_creature(self, creature_id, player=None):
        self.card_played_this_turn += 1
        state = self.game.get_game_state()
        current_player = player or state["current_player"]
        if creature_id not in state[current_player]["hand"]:
            print("Invalid ID. Are you sure this card exists?")
        self.game.play_creature(current_player, creature_id)

    def add_status(self, card_dict, status):
        """
        Adds a status to a card, preventing duplicate static statuses (e.g., 'flying', 'vigilant', etc.).
        """
        if not status:
            return
        # Normalize to list
        if isinstance(card_dict.get('status'), list):
            statuses = card_dict['status']
        elif isinstance(card_dict.get('status'), str):
            statuses = [s.strip() for s in card_dict['status'].split(',') if s.strip()]
        else:
            statuses = []

        # Normalize new status
        if isinstance(status, list):
            new_statuses = status
        else:
            new_statuses = [status]

        # Only add if not already present (case-insensitive)
        for s in new_statuses:
            if not any(s.lower() == existing.lower() for existing in statuses):
                statuses.append(s)
        card_dict['status'] = statuses

    def add_status_to_creature(self, player, creature_id, status):
        """
        Adds a status to a creature on the board, preventing duplicates.
        """
        state = self.game.get_game_state()
        creature = state[player]["creatures"].get(creature_id)
        if creature:
            self.add_status(creature['card'], status)
            self.game._save_state(state)

    def play_land(self, land_id, player=None):
        self.card_played_this_turn += 1
        state = self.game.get_game_state()
        current_player = player or state["current_player"]
        if land_id not in state[current_player]["hand"]:
            print("Invalid ID. Are you sure this card exists?")
        self.game.play_land(current_player, land_id)

    def cast_spell(self, spell_id, target, player=None):
        state = self.game.get_game_state()
        current_player = player or state["current_player"]
        if spell_id not in state[current_player]["hand"]:
            print("Invalid ID. Are you sure this card exists?")
            return False
        success = self.game.cast_spell(current_player, spell_id, target)
        if success:
            self.card_played_this_turn += 1
        return success

    def mulligan(self):
        state = self.game.get_game_state()
        player = state["current_player"]
        turn_number = state.get("turn_number", 1)

        if self.card_played_this_turn > 0:
            print("Mulligan not allowed after playing a card.")
            return False

        if not (
            (player == self.p1 and turn_number == 1) or
            (player == self.p2 and turn_number == 2)
        ):
            print("Mulligan only available on your first turn.")
            return False

        hand = state[player]["hand"]
        deck = state[player]["deck"]

        deck.extend(list(hand.values()))
        state[player]["hand"] = {}

        random.shuffle(deck)
        self.game._save_state(state)

        for _ in range(7):
            self.game.draw_card(player)

        print(f"{player} mulligans and draws 7 cards.")
        return True

    def tap_land(self, land_id, choice=None, player=None):
        state = self.game.get_game_state()
        current_player = player or state["current_player"]
        
        if land_id not in state[current_player]["lands"]:
            print(f"Invalid ID. Are you sure this card exists?")
            return False
        
        land_card = state[current_player]["lands"][land_id]["card"]
        effect = land_card.get("effect", "")
        colors = get_land_colors(effect)
        
        if len(colors) == 0:
            print(f"I don't know how you triggered this error, but you did...")
            return False
        
        if len(colors) == 1:
            choice = colors[0]
        else:
            choice = choice
            if choice is None:
                print(f"Must specify choice.")
                return False
            if choice not in colors:
                print(f"Invalid choice.")
                return False
        
        self.game.tap_land(current_player, land_id, choice)
        return True

    def declare_attackers(self, player, creature_ids):
        return self.queue_attackers(player, creature_ids)

    def declare_blockers(self, defender, block_assignments):
        return self.queue_blockers(defender, block_assignments)

    def get_health(self, player=None):
        state = self.game.get_game_state()
        current_player = player or state["current_player"]
        return state[current_player]["health"]

    def begin_combat(self, attacker):
        if self.combat_used_turn:
            print("Combat already resolved this turn.")
            return False
        defender = self.p2 if attacker == self.p1 else self.p1
        self.combat_phase = "attackers"
        self.priority_player = attacker
        self.pending_attackers = []
        self.pending_blocks = {}
        self.combat_attacker = attacker
        self.combat_defender = defender
        return defender

    def queue_attackers(self, player, creature_ids):
        if self.combat_phase != "attackers" or self.priority_player != player:
            print("Not your priority to declare attackers.")
            return False
        self.pending_attackers = creature_ids
        return True

    def pass_priority_to_blocker(self):
        if self.combat_phase != "attackers" or not self.combat_attacker:
            print("Not in attack step.")
            return False
        self.combat_phase = "blockers"
        self.priority_player = self.combat_defender
        return True

    def queue_blockers(self, defender, block_assignments):
        if self.combat_phase != "blockers" or self.priority_player != defender:
            print("Not your priority to declare blockers.")
            return False
        self.pending_blocks = block_assignments
        return True

    def cancel_combat(self):
        self.combat_phase = None
        self.priority_player = None
        self.pending_attackers = []
        self.pending_blocks = {}
        self.combat_attacker = None
        self.combat_defender = None
        return True

    def confirm_combat(self):
        if self.combat_phase != "blockers" or not self.combat_attacker or not self.combat_defender:
            print("Blockers not declared yet.")
            return [False, ""]

        self.combat_phase = None
        self.priority_player = None
        self.pending_attackers = []
        self.pending_blocks = {}
        self.combat_attacker = None
        self.combat_defender = None

        return self.resolve_combat()

    def show_mana(self, player=None):
        state = self.game.get_game_state()
        current_player = player or state["current_player"]
        pdata = state[current_player]
        r = pdata.get("red_mana", 0)
        g = pdata.get("green_mana", 0)
        b = pdata.get("blue_mana", 0)
        return {
            "R": r,
            "G": g,
            "B": b,
            "Generic": r + g + b
        }
    
    def show_deck(self, player=None):
        state = self.game.get_game_state()
        current_player = player or state["current_player"]
        deck = state[current_player]["deck"]

        deck_cards = []
        for card_data in deck:  # deck is a list, not dict - no card_id to unpack
            deck_cards.append({
                'id': card_data.get('id'),
                'name': card_data['name'],
                'type': card_data.get('type', 'Unknown'),
                'generic_mana': card_data.get('generic_mana', 0),
                'sp_mana': card_data.get('sp_mana', ''),
                'attack': card_data.get('attack'),
                'defence': card_data.get('defence')
            })
        
        return deck_cards

    def show_graveyard(self, player=None):
        state = self.game.get_game_state()
        current_player = player or state["current_player"]
        graveyard = state[current_player].get("graveyard", [])
        graveyard_cards = []
        for card in graveyard:
            if isinstance(card, dict):
                graveyard_cards.append({
                    'id': card.get('id'),
                    'name': card.get('name', '<unknown>'),
                    'type': card.get('type', 'Unknown'),
                    'generic_mana': card.get('generic_mana', 0),
                    'sp_mana': card.get('sp_mana', ''),
                    'attack': card.get('attack'),
                    'defence': card.get('defence')
                })
            else:
                graveyard_cards.append({
                    'id': str(card),
                    'name': '<unknown>',
                    'type': 'Unknown',
                    'generic_mana': 0,
                    'sp_mana': '',
                    'attack': None,
                    'defence': None
                })
        return graveyard_cards

    def draw_card_by_id(self, card_id, player=None):
        state = self.game.get_game_state()
        current_player = player or state["current_player"]
        deck = state[current_player]["deck"]
        hand = state[current_player]["hand"]
        
        # Search for card in deck (deck is a list)
        card_to_draw = None
        card_index = None
        for i, card in enumerate(deck):
            # Check both string and int ID matches
            if str(card.get("id")) == str(card_id) or card.get("id") == card_id:
                card_to_draw = card
                card_index = i
                break
        
        if card_to_draw is None:
            print(f"Card with ID {card_id} not found in deck.")
            return False
        
        # Remove card from deck
        deck.pop(card_index)
        
        # Add to hand with card ID as key
        card_id_str = str(card_to_draw.get("id"))
        hand[card_id_str] = card_to_draw
        
        # Save state
        self.game._save_state(state)
        print(f"Drew {card_to_draw.get('name', 'card')} ({card_id_str})")
        return True
        

    def resolve_combat(self):
        state = self.game.get_game_state()
        current_player = state["current_player"]
        
        self.game.calculate_combat_damage()
        self.game.resolve_damage_queue()
        self.combat_used_turn = True
        
        state = self.game.get_game_state()
        
        if state[self.p1]["health"] <= 0:
            return [True, self.p1]
        elif state[self.p2]["health"] <= 0:
            return [True, self.p2]
        else:
            return [False, ""]

    def start(self):
        self.start_new_turn()


if __name__ == '__main__':
    wiz = Wizard("Player1", "Player2")
    wiz.start()
    print("\nWelcome to the Wizard Command Line Interface. This version is currently in Beta. Bugs and errors are to be expected.\nType \"help\" for more information.\n")
    while True:
        player = wiz.priority_player or wiz.current_player()
        command = input(f"{player}> ")
        # commands
        if command == "help":
            print("COMMANDS:")
            # print("  land <id>     - Play land")
            print("  help          - Shows this command")
            print("  play <id>     - Play creature")    # done
            print("  cast <id> [target] - Cast spell (optional target)")
            print("  tap <id> [color] - Tap for mana (dual lands need color)")  # done
            print("  attack <ids>  - Declare attackers")
            print("  block <pairs> - Declare blockers")
            print("  end           - End turn") # done
            print("  mulligan      - Redraw opening hand (first turn only)")    # done
            print("  hand          - Show your hand")   # done
            print("  board         - Show battlefield") # done
            print("  state         - Show full game state") # done
            print("  graveyard     - Show graveyard")
            print("  deck          - Show deck\n")
            print("  about <id>    - Shows information about a card")
            print("ADMIN COMMANDS:")
            print("  mana <c> <n>  - Add mana") # done
            print("  admindraw [card] - Draw card")
            print("")

        elif command == "exit" or command == "quit" or command == "q":
            print("Quitting...")
            sys.exit()

        # elif command.startswith("admindraw "):
        #     # draws the card specified
        #     card_name = command.split(" ")[1]
        #     wiz.game.draw_card(player, card_name)
        #     print(f"[{card_name}] drawn")
        
        elif command == "hand":
            a = wiz.show_hand(player)
            print(f"\n{player}'s Hand ({len(a)} cards):\n---------------------------------")
            if not a:
                print("Hand is empty.\n")
                continue
            for item in a:
                type_label = {
                    "Creature": "CREATURE",
                    "Land": "LAND",
                    "Spell": "SPELL"
                }.get(item.get("type"), "CARD")
                mana = (
                    f"{item['generic_mana']}"
                    f"{'+R' if item['sp_mana'] == 'red' else '+G' if item['sp_mana'] == 'green' else '' if item['sp_mana'] == '' else '+B'}"
                )
                stats = ""
                if item.get("attack") is not None and item.get("defence") is not None:
                    stats = f" | {item['attack']}/{item['defence']}"
                print(f"[{item['id']}] {item['name']} ({mana}) - {type_label}{stats}")
            print()
            
        elif command == "graveyard":
            a = wiz.show_graveyard(player)
            print(f"\n{player}'s Graveyard ({len(a)} cards):\n---------------------------------")
            if not a:
                print("Graveyard is empty.")
            else:
                for item in a:
                    mana = (
                        f"{item['generic_mana']}"
                        f"{'+R' if item['sp_mana'] == 'red' else '+G' if item['sp_mana'] == 'green' else '' if item['sp_mana'] == '' else '+B'}"
                    )
                    print(f"[{item['id']}] {item['name']} ({mana})")
            print()

        elif command == "deck":
            a = wiz.show_deck(player)
            print(f"\n{player}'s Deck ({len(a)} cards):\n---------------------------------")
            if not a:
                print("Deck is empty.")
            else:
                type_counts = {"Creature": 0, "Land": 0, "Spell": 0, "Other": 0}
                for item in a:
                    t = item.get("type", "Other")
                    if t not in type_counts:
                        t = "Other"
                    type_counts[t] += 1
                    print(f"[{item['id']}] {item['name']} ({item['generic_mana']}"
                          f"{'+R' if item['sp_mana'] == 'red' else '+G' if item['sp_mana'] == 'green' else '' if item['sp_mana'] == '' else '+B'})")
                print(f"\nTypes: C {type_counts['Creature']} | L {type_counts['Land']} | S {type_counts['Spell']} | O {type_counts['Other']}")
            print()

        elif command == "enemydeck":
            a = wiz.show_deck(wiz.p2 if player == wiz.p1 else wiz.p1)
            opponent = wiz.p2 if player == wiz.p1 else wiz.p1
            print(f"\n{opponent}'s Deck ({len(a)} cards):\n---------------------------------")
            if not a:
                print("Deck is empty.")
            else:
                type_counts = {"Creature": 0, "Land": 0, "Spell": 0, "Other": 0}
                for item in a:
                    t = item.get("type", "Other")
                    if t not in type_counts:
                        t = "Other"
                    type_counts[t] += 1
                    print(f"[{item['id']}] {item['name']} ({item['generic_mana']}"
                          f"{'+R' if item['sp_mana'] == 'red' else '+G' if item['sp_mana'] == 'green' else '' if item['sp_mana'] == '' else '+B'})")
                print(f"\nTypes: C {type_counts['Creature']} | L {type_counts['Land']} | S {type_counts['Spell']} | O {type_counts['Other']}")
            print()

        elif command == "enemyhand":
            a = wiz.show_hand(wiz.p2 if player == wiz.p1 else wiz.p1)
            opponent = wiz.p2 if player == wiz.p1 else wiz.p1
            print(f"\n{opponent}'s Hand ({len(a)} cards):\n---------------------------------")
            if not a:
                print("Hand is empty.")
            else:
                for item in a:
                    type_label = {
                        "Creature": "CREATURE",
                        "Land": "LAND",
                        "Spell": "SPELL"
                    }.get(item.get("type"), "CARD")
                    stats = ""
                    if item.get("attack") is not None and item.get("defence") is not None:
                        stats = f" | {item['attack']}/{item['defence']}"
                    print(f"[{item['id']}] {item['name']} ({item['generic_mana']}"
                          f"{'+R' if item['sp_mana'] == 'red' else '+G' if item['sp_mana'] == 'green' else '' if item['sp_mana'] == '' else '+B'}) - {type_label}{stats}")
            print()

        elif command == "board":
            mana = wiz.show_mana(player)
            state = wiz.game.get_game_state()
            turn_number = state.get("turn_number", 0)
            current_player = state.get("current_player", player)
            print(f"\n{player}'s Status\n---------------------------------")
            print(f"Turn: {turn_number} | Active: {current_player}")
            print(f"Health: {wiz.get_health(player)}")
            print(f"Mana: R {mana['R']} | G {mana['G']} | B {mana['B']} | Total {mana['Generic']}")
            print(f"R: {mana['R']}")
            print(f"G: {mana['G']}")
            print(f"B: {mana['B']}")
            print(f"Generic: {mana['Generic']}")
            a = wiz.show_board(player)
            has_creatures = any(item.get('type') == 'Creature' for item in a)
            has_lands = any(item.get('type') == 'Land' for item in a)

            print(f"\n{player}'s Active Creatures:\n---------------------------------")
            if not has_creatures:
                print("No creatures active.")
            else:
                for item in a:
                    if item['type'] == 'Creature':
                        stats = ""
                        if item.get("attack") is not None and item.get("defence") is not None:
                            stats = f" {item['attack']}/{item['defence']}"
                        status = item.get("status", [])
                        status_label = f" | {', '.join(status)}" if status else ""
                        print(f"[{item['id']}] {item['name']}{stats} ({'tapped' if item['tapped'] else 'untapped'}){status_label}")

            print(f"\n{player}'s Active Lands:\n---------------------------------")
            if not has_lands:
                print("No lands active.")
            else:
                for item in a:
                    if item['type'] == 'Land':
                        print(f"[{item['id']}] {item['name']} ({'tapped' if item['tapped'] else 'untapped'})")
            print('\n')

        elif command == "state":
            state = wiz.game.get_game_state()
            players = [wiz.p1, wiz.p2]

            print("\nGame Summary\n---------------------------------")
            print(f"Turn: {state.get('turn_number', 0)} | Active: {state.get('current_player', '-')}")
            print(f"{wiz.p1}: {state[wiz.p1].get('health', 0)} HP | Hand {len(state[wiz.p1].get('hand', {}))} | Deck {len(state[wiz.p1].get('deck', []))} | Graveyard {len(state[wiz.p1].get('graveyard', []))}")
            print(f"{wiz.p2}: {state[wiz.p2].get('health', 0)} HP | Hand {len(state[wiz.p2].get('hand', {}))} | Deck {len(state[wiz.p2].get('deck', []))} | Graveyard {len(state[wiz.p2].get('graveyard', []))}")

            for p in players:
                creatures = state[p]["creatures"]
                lands = state[p]["lands"]

                print(f"\n{p}'s Active Creatures:\n---------------------------------")
                if not creatures:
                    print("No creatures active.")
                else:
                    for cid, cdata in creatures.items():
                        card = cdata["card"]
                        tapped = cdata.get("tapped", card.get("tapped", False))
                        stats = ""
                        if card.get("attack") is not None and card.get("defence") is not None:
                            stats = f" {card.get('attack')}/{card.get('defence')}"
                        status = cdata.get("status", "")
                        status_label = f" | {status}" if status else ""
                        print(f"[{cid}] {card['name']}{stats} ({'tapped' if tapped else 'untapped'}){status_label}")

                print(f"\n{p}'s Active Lands:\n---------------------------------")
                if not lands:
                    print("No lands active.")
                else:
                    for lid, ldata in lands.items():
                        card = ldata["card"]
                        tapped = ldata.get("tapped", card.get("tapped", False))
                        print(f"[{lid}] {card['name']} ({'tapped' if tapped else 'untapped'})")

                print()

        elif command == "mulligan":
            wiz.mulligan()

        elif command == "end":
            # Check if the player is the attacker and has queued attackers but hasn't confirmed
            if wiz.combat_phase == "attackers" and wiz.combat_attacker == player and wiz.pending_attackers:
                print("You must confirm your attackers before ending your turn. Use 'confirm' to declare attackers.")
                continue
            # Check if the player is the defender and has not confirmed blockers
            if wiz.combat_phase == "blockers" and wiz.combat_defender == player:
                print("You must confirm blockers before ending your turn. Use 'confirm' to resolve combat.")
                continue
            # Discard down to 7 at end of turn
            state = wiz.game.get_game_state()
            hand_length = len(state[player]["hand"])
            if hand_length > 7:
                a = wiz.show_hand(player)
                for item in a:
                    type_label = {
                        "Creature": "CREATURE",
                        "Land": "LAND",
                        "Spell": "SPELL"
                    }.get(item.get("type"), "CARD")
                    print(f"[{type_label}] [{item['id']}] {item['name']} ({item['generic_mana']}"
                          f"{'+R' if item['sp_mana'] == 'red' else '+G' if item['sp_mana'] == 'green' else '' if item['sp_mana'] == '' else '+B'})")

                print(f"You have {hand_length} cards in your hand. Please discard {hand_length - 7} cards.")
                while True:
                    discard_cards = input("Enter the IDs of the cards you want to discard: ").split()
                    if len(discard_cards) == hand_length - 7:
                        wiz.game.discard_cards(player, discard_cards)
                        break
                    elif len(discard_cards) > hand_length - 7:
                        print("You cannot discard more cards than you have in your hand. Please try again.")
                    else:
                        print(f"You must discard {hand_length - 7} cards. Please try again.")
            print("Turn complete.")
            wiz.start_new_turn()

        elif command.startswith("play "):
            # Only allow playing if not in combat
            if wiz.combat_phase is not None:
                print("You cannot play cards during combat.")
                continue

            parts = command.split()
            if len(parts) != 2:
                print("Usage: play <id>")
            else:
                card_id = parts[1]
                state = wiz.game.get_game_state()
                current_player = player
                hand = state[current_player]["hand"]

                if card_id not in hand:
                    print("Invalid ID. Are you sure this card exists?")
                else:
                    card = hand[card_id]
                    card_type = card.get("type", "")

                    # Also, only let them play one land per turn.
                    if wiz.card_played_this_turn >= 1 and card_type == "Land":
                        print("You have already played a card this turn.")
                        continue

                    if card_type == "Land":
                        wiz.play_land(card_id, current_player)
                    elif card_type == "Spell":
                        print("Use 'cast <id> <target>' to cast spells.")
                    else:
                        generic_cost = card.get("generic_mana", 0)
                        color_cost = card.get("sp_mana", "")

                        pdata = state[current_player]
                        r = pdata.get("red_mana", 0)
                        g = pdata.get("green_mana", 0)
                        b = pdata.get("blue_mana", 0)
                        total_mana = r + g + b
                        color_mana = {"red": r, "green": g, "blue": b}.get(color_cost, 0)

                        if color_cost and color_mana < 1:
                            print("Not enough colored mana.")
                        elif total_mana < (generic_cost + (1 if color_cost else 0)):
                            print("Not enough total mana.")
                        else:
                            # pay mana via engine; only play if payment succeeds
                            paid = wiz.game.pay_mana(current_player, generic_cost, color_cost if color_cost else None)
                            if not paid:
                                print("Payment failed, card not played.")
                            else:
                                wiz.play_creature(card_id, current_player)
                                # show remaining mana
                                mana = wiz.show_mana(current_player)
                                print(f"Remaining mana: R - {mana['R']} G - {mana['G']} B - {mana['B']} (Total: {mana['Generic']})")

        elif command.startswith("cast "):
            parts = command.split()
            if len(parts) not in (2, 3):
                print("Usage: cast <spell_id> [target_id|player]")
            else:
                spell_id = parts[1]
                target = parts[2] if len(parts) == 3 else None
                state = wiz.game.get_game_state()
                current_player = player
                hand = state[current_player]["hand"]
                if spell_id not in hand:
                    print("Invalid ID. Are you sure this card exists?")
                else:
                    card = hand[spell_id]
                    if card.get("type", "") != "Spell":
                        print("That card is not a spell. Use 'play' instead.")
                    else:
                        wiz.cast_spell(spell_id, target, player=current_player)

        elif command.startswith("admindraw "):
            parts = command.split()
            if len(parts) != 2:
                print("Usage: admindraw <card_id>")
            else:
                card_id = parts[1]
                if wiz.draw_card_by_id(card_id, player):
                    print(f"Card {card_id} drawn successfully.")
        
        elif command.startswith("tap "):
            parts = command.split()
            if len(parts) not in (2, 3):
                print("Usage: tap <id> [color]")
            else:
                land_id = parts[1]
                choice = parts[2] if len(parts) == 3 else None
                wiz.tap_land(land_id, choice, player=player)
        
        elif command.startswith("mana "):
            parts = command.split()
            if len(parts) != 3:
                print("Usage: mana <n> <color>")
            else:
                try:
                    amount = int(parts[1])
                    color = parts[2].lower()
                    if color not in ("red", "green", "blue"):
                        print("Color must be red, green, or blue.")
                    else:
                        state = wiz.game.get_game_state()
                        current_player = player
                        key = f"{color}_mana"
                        state[current_player][key] = state[current_player].get(key, 0) + amount
                        wiz.game._save_state(state)
                        print(f"Added {amount} {color} mana to {current_player}.")
                except ValueError:
                    print("Amount must be an integer.")

        elif command.startswith("about "):
            parts = command.split()
            if len(parts) != 2:
                print("Usage: about <id>")
            else:
                cid = parts[1]
                state = wiz.game.get_game_state()
                found = None
                zone = ""
                owner = ""
                for p in (wiz.p1, wiz.p2):
                    hand = state[p].get("hand", {})
                    if cid in hand:
                        found = hand[cid]
                        zone = "hand"
                        owner = p
                        break
                    cre = state[p].get("creatures", {})
                    if cid in cre:
                        found = cre[cid].get("card", {})
                        zone = "battlefield"
                        owner = p
                        break
                    lands = state[p].get("lands", {})
                    if cid in lands:
                        found = lands[cid].get("card", {})
                        zone = "lands"
                        owner = p
                        break
                    for c in state[p].get("deck", []):
                        if str(c.get("id")) == cid or c.get("id") == cid:
                            found = c
                            zone = "deck"
                            owner = p
                            break
                    if found:
                        break
                    for c in state[p].get("graveyard", []):
                        if str(c.get("id")) == cid or c.get("id") == cid:
                            found = c
                            zone = "graveyard"
                            owner = p
                            break
                    if found:
                        break

                if not found:
                    print("Card not found.")
                else:
                    name = found.get("name", "<unknown>")
                    attack = found.get("attack")
                    endurance = found.get("defence")
                    desc = found.get("description") or found.get("desc") or found.get("text") or ""
                    effect = found.get("effect", "")
                    generic = found.get("generic_mana", found.get("generic_cost", 0))
                    colour = found.get("sp_mana", found.get("color", ""))

                    print(f"\nName: {name}")
                    print(f"Attack: {attack if attack is not None else '-'}")
                    print(f"Endurance: {endurance if endurance is not None else '-'}")
                    print(f"Description: {desc if desc else '-'}")
                    print(f"Effect: {effect if effect else '-'}")
                    print(f"Generic cost: {generic}")
                    print(f"Colour: {colour if colour else '-'}")
                    print("\n")

        elif command.startswith("attack "):
            parts = command.split()
            if len(parts) < 2:
                print("Usage: attack <id> <id2> ...")
            else:
                attacker_ids = parts[1:]
                # prefer the recorded combat attacker when in attackers phase
                player = wiz.combat_attacker if (wiz.combat_phase == "attackers" and wiz.combat_attacker) else wiz.current_player()
                if wiz.combat_phase is None:
                    wiz.begin_combat(player)
                if wiz.combat_phase != "attackers" or wiz.priority_player != player:
                    print("It's not your priority to declare attackers.")
                else:   
                    wiz.queue_attackers(player, attacker_ids)
                    print(f"Queued attackers: {', '.join(attacker_ids)}")
        
        elif command.startswith("block "):
            parts = command.split()
            if len(parts) != 3:
                print("Usage: block <blocker_id> <attacker_id>")
            else:
                blocker_id, attacker_id = parts[1], parts[2]
                # prefer the recorded combat defender when in blockers phase
                defender = wiz.combat_defender if (wiz.combat_phase == "blockers" and wiz.combat_defender) else wiz.current_player()
                if wiz.combat_phase != "blockers" or wiz.priority_player != defender:
                    print("Not your priority to declare blockers.")
                else:
                    state = wiz.game.get_game_state()
                    combat_attackers = state.get("combat", {}).get("attackers", [])
                    active_attackers = wiz.pending_attackers or combat_attackers
                    if attacker_id not in active_attackers:
                        print("That attacker is not declared (or wrong id).")
                    else:
                        defender_creatures = state[defender].get("creatures", {})
                        if blocker_id not in defender_creatures:
                            print("Blocker not found on your battlefield.")
                        else:
                            bdata = defender_creatures[blocker_id]
                            bcard = bdata.get("card", {})
                            tapped = bdata.get("tapped", bcard.get("tapped", False))
                            if tapped:
                                print("Blocker is tapped and cannot block.")
                            else:
                                already_used = any(
                                    blocker_id in (v if isinstance(v, list) else [v])
                                    for v in wiz.pending_blocks.values()
                                )
                                if already_used:
                                    print("This creature is already assigned to block.")
                                else:
                                    new_blocks = {**wiz.pending_blocks}
                                    lst = new_blocks.get(attacker_id, [])
                                    if isinstance(lst, str):
                                        lst = [lst]
                                    lst = list(lst)
                                    lst.append(blocker_id)
                                    new_blocks[attacker_id] = lst
                                    if wiz.queue_blockers(defender, new_blocks):
                                        print(f"Queued blocker {blocker_id} → attacker {attacker_id}")
                                    else:
                                        print("Failed to queue blocker.")
        elif command == "preview":
            if wiz.combat_phase is None:
                print("No combat queued.")
            else:
                state = wiz.game.get_game_state()
                atk = wiz.combat_attacker
                dfd = wiz.combat_defender
                combat_attackers = state.get("combat", {}).get("attackers", [])
                display_attackers = wiz.pending_attackers or combat_attackers

                def card_brief(owner, cid):
                    zone = state[owner].get("creatures", {})
                    c = zone.get(cid, {}).get("card", {})
                    if not c:
                        return f"{cid} (unknown)"
                    return f"{cid} {c.get('name')} ({c.get('attack','-')}/{c.get('defence','-')})"

                print(f"Phase: {wiz.combat_phase}  (Attacker: {atk}  Defender: {dfd})\n")

                # show attackers (queued or already declared)
                print("Queued attackers:")
                if not display_attackers:
                    print("  (none)")
                else:
                    for cid in display_attackers:
                        owner = wiz.combat_attacker
                        print("  -", card_brief(owner, cid))

                # if defender or blockers phase, show current blocker assignments
                if wiz.combat_phase == "blockers" or wiz.current_player() == wiz.combat_defender:
                    print("\nPending blocks (attacker -> [blockers]):")
                    if not wiz.pending_blocks:
                        print("  (none)")
                    else:
                        for a_id, b_list in wiz.pending_blocks.items():
                            if isinstance(b_list, str):
                                b_list = [b_list]
                            names = []
                            for b in b_list:
                                names.append(card_brief(wiz.combat_defender, b))
                            print(f"  - {card_brief(wiz.combat_attacker, a_id)} -> {', '.join(names)}")

                print("\nHints:")
                if wiz.combat_phase == "attackers" and wiz.priority_player == wiz.combat_attacker:
                    print("  - attacker: use 'confirm' to declare these attackers and pass priority to defender")
                if wiz.combat_phase == "blockers" and wiz.priority_player == wiz.combat_defender:
                    print("  - defender: use 'confirm' to lock blockers and resolve combat")
                print("  - use 'cancel' to abort the queued combat\n")

        elif command == "confirm":
            if wiz.combat_phase is None:
                print("No combat to confirm.")
            elif wiz.combat_phase == "attackers":
                if wiz.priority_player != wiz.combat_attacker:
                    print("You don't have priority to confirm attackers.")
                elif not wiz.pending_attackers:
                    print("No attackers queued.")
                else:
                    # Declare attackers and pass priority to defender for blockers
                    wiz.game.declare_attackers(wiz.combat_attacker, wiz.pending_attackers)
                    state = wiz.game.get_game_state()
                    declared_attackers = state.get("combat", {}).get("attackers", [])
                    if not declared_attackers:
                        print("No valid attackers were declared. Priority remains with attacker.")
                    else:
                        wiz.pending_attackers = []
                        wiz.pass_priority_to_blocker()
                        print(f"Attackers declared — priority passed to {wiz.combat_defender} to declare blockers.")
                        print(f"Priority: {wiz.priority_player} may now declare blockers (use 'block <blocker_id> <attacker_id>' or 'preview').")
            elif wiz.combat_phase == "blockers":
                if wiz.priority_player != wiz.combat_defender:
                    print("You don't have priority to confirm blockers.")
                else:
                    # Declare blockers, resolve combat, then pass priority back to attacker
                    wiz.game.declare_blockers(wiz.combat_defender, wiz.pending_blocks)
                    wiz.pending_blocks = {}
                    # Combat resolution
                    won, loser = wiz.confirm_combat()
                    if won:
                        print(f"Combat resolved — {loser} lost the game.")
                    else:
                        print("Combat resolved.")
                    wiz.combat_phase = None
                    # Return priority to attacker for post-combat main phase
                    wiz.priority_player = wiz.combat_attacker
                    print(f"Priority returned to {wiz.combat_attacker} for post-combat actions.")
            else:
                print("Cannot confirm in current phase.")

        elif command == "cancel":
            if wiz.combat_phase is None:
                print("Nothing to cancel.")
            else:
                # Allow cancelling queued combat in local CLI — clears pending attackers/blocks
                wiz.cancel_combat()
                wiz.action_queue = []
                print("Queued combat cancelled.")
    