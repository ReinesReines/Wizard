import sys
import os
import random
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from game import GameEngine
from card_index import (
    # Creatures
    slime, bigger_slime, forest_bear, vine_elemental, alpha_wolf,
    skeleton, skeleton_army, phantom_warrior, sea_serpent, arcane_scholar, vergil,
    goblin_raider, fire_elemental, dragon_whelp, berserker,
    # Lands
    forest, island, mountain, tropical_grove, volcanic_peak, wild_highlands
)
from modules.utils import *

class Wizard:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        creature_pool = [
            slime, bigger_slime, forest_bear, vine_elemental, alpha_wolf,
            skeleton, phantom_warrior, arcane_scholar, goblin_raider, 
            fire_elemental, dragon_whelp, berserker
        ]
        
        land_pool = [
            forest, forest, forest, island, island, island,
            mountain, mountain, tropical_grove, volcanic_peak
        ]

        import copy
        
        # Create separate deck copies for each player to avoid ID conflicts
        deck1_lands = [copy.deepcopy(random.choice(land_pool)) for _ in range(20)]
        deck1_creatures = [copy.deepcopy(random.choice(creature_pool)) for _ in range(18)]
        deck1 = deck1_lands + deck1_creatures
        random.shuffle(deck1)
        
        deck2 = copy.deepcopy(creature_pool) + copy.deepcopy(creature_pool) + copy.deepcopy(land_pool)
        deck2_lands = [copy.deepcopy(random.choice(land_pool)) for _ in range(20)]
        deck2_creatures = [copy.deepcopy(random.choice(creature_pool)) for _ in range(18)]
        deck2 = deck2_lands + deck2_creatures
        random.shuffle(deck2)

        self.game = GameEngine(p1, p2, deck1, deck2)
        self.game.current_turn_drawn = False
    
        self.mulligan_available = {p1: True, p2: True}
        self.game.ready()

        for _ in range(7):
            self.game.draw_card(p1)
            self.game.draw_card(p2)

    def current_player(self):
        state = self.game.get_game_state()
        return state["current_player"]
    
    def start_new_turn(self):
        state = self.game.get_game_state()
        current_turn = state.get("turn_number", 0) + 1
        
        if current_turn % 2 == 1:
            self.game.start_turn(self.p1)
        else:
            self.game.start_turn(self.p2)
        
        state = self.game.get_game_state()
        player = state["current_player"]
        
        self.game.untap_step(player)

        if not (current_turn == 1 and player == self.p1):
            self.game.draw_step(player)
            print(f"Draw: {player} draws a card")
        self.current_turn_drawn = False

    def show_hand(self):
        state = self.game.get_game_state()
        current_player = state["current_player"]
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

    def show_board(self):
        state = self.game.get_game_state()
        current_player = state["current_player"]
        creatures = state[current_player]["creatures"]
        lands = state[current_player]["lands"]
        
        board_cards = []
        
        for card_id, creature_data in creatures.items():
            card = creature_data['card']
            board_cards.append({
                'id': card_id,
                'name': card['name'],
                'type': 'Creature',
                'attack': card.get('attack'),
                'defence': card.get('defence'),
                'tapped': creature_data.get('tapped', False),
                'status': creature_data.get('status', [])
            })
        
        for card_id, land_data in lands.items():
            card = land_data['card']
            board_cards.append({
                'id': card_id,
                'name': card['name'],
                'type': 'Land',
                'tapped': land_data.get('tapped', False)
            })
        
        return board_cards

    def play_creature(self, creature_id):
        state = self.game.get_game_state()
        current_player = state["current_player"]
        if creature_id not in state[current_player]["hand"]:
            print("Invalid ID. Are you sure this card exists?")
        self.game.play_creature(current_player, creature_id)

    def play_land(self, land_id):
        state = self.game.get_game_state()
        current_player = state["current_player"]
        if land_id not in state[current_player]["hand"]:
            print("Invalid ID. Are you sure this card exists?")
        self.game.play_land(current_player, land_id)

    def end_turn(self):
        state = self.game.get_game_state()
        current_player = state["current_player"]
        self.game.end_turn(current_player)
        # self.game.cleanup_temporary_effects()

    def tap_land(self, land_id, choice=None):
        state = self.game.get_game_state()
        current_player = state["current_player"]
        
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
        self.game.declare_attackers(player, creature_ids)

    def declare_blockers(self, defender, block_assignments):
        self.game.declare_blockers(defender, block_assignments)

    def show_mana(self):
        state = self.game.get_game_state()
        current_player = state["current_player"]
        return {
            "green": state[current_player].get("green_mana", 0),
            "blue": state[current_player].get("blue_mana", 0),
            "red": state[current_player].get("red_mana", 0)
        }
    
    def show_deck(self):
        state = self.game.get_game_state()
        current_player = state["current_player"]
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
    
    def resolve_combat(self):
        state = self.game.get_game_state()
        current_player = state["current_player"]
        
        self.game.calculate_combat_damage()
        self.game.resolve_damage_queue()
        
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
    print("Welcome to the Wizard Command Line Interface. This version is currently in Beta. Bugs and errors are to be expected.\nType \"help\" for more information.\n\n")
    while True:
        player = wiz.current_player()
        command = input("{player}> ")

        # commands
        if command == "help":
            print("COMMANDS:")
            print("  land <id>     - Play land")
            print("  play <id>     - Play creature")
            print("  tap <id> [color] - Tap for mana (dual lands need color)")
            print("  attack <ids>  - Declare attackers")
            print("  block <pairs> - Declare blockers")
            print("  end           - End turn")
            print("  mulligan      - Redraw opening hand (first turn only)")
            print("  hand          - Show your hand")
            print("  board         - Show battlefield")
            print("  state         - Show full game state")
            print("  graveyard     - Show graveyard")
            print("  deck          - Show deck\n")
            print("ADMIN COMMANDS:")
            print("  mana <c> <n>  - Add mana")
            print("  admindraw [card] - Draw card")

        elif command == "exit" or command == "quit" or command == "q":
            print("Quitting...")
            sys.exit()
        
        elif command == "hand":
            a = wiz.show_hand()
            for item in a:
                print(f"[{item["id"]}] {item["name"]} | {item["generic_mana"]}")
    