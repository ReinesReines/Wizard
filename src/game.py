from modules.cards import Cards, SummonCard, SpellCard
from modules.utils import execute_card, enters_tapped, card_has_trigger, get_all_keywords
from card_index import *
import random
import json
import time
import datetime


class GameEngine:
    def __init__(self, player1, player2, deck1, deck2):
        self.player1 = player1
        self.player2 = player2

        self.deck1 = deck1
        self.deck2 = deck2

        self.battlefield = {}
        self.game_file = "db/game_state.json"
        self.turn = 0
        self.card_id_counter = 1

    def _timestamp(self):
        """Get current timestamp string."""
        return datetime.datetime.now().strftime('%H:%M:%S')
    
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
                effect=card_dict.get("effect", "")
            )
        elif card_type == "Spell":
            card = SpellCard(
                name=card_dict.get("name"),
                generic_mana=card_dict.get("generic_mana"),
                sp_mana=card_dict.get("sp_mana"),
                description=card_dict.get("description"),
                effect=card_dict.get("effect", "")
            )
        else:
            return None
        
        # Restore card state
        card.id = card_dict.get("id", 0)
        card.tapped = card_dict.get("tapped", 0)
        card.status = card_dict.get("status", "")
        
        return card

    def ready(self):
        """Prepares the game state and variables for the next game."""
        # resets the .json file to an empty JSON object
        ts = time.time()
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        print(f"[{timestamp}] Game setup begins")
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
            "battlefield": self.battlefield
        }

        # create battlefield
        with open(self.game_file, "w") as f:
            json.dump(game_state, f, indent=4)

        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        print(f"[{timestamp}] Game battlefield created")

if __name__ == "__main__":
    # Create game instance
    game = GameEngine("David", "Max", 
                      [vine_elemental, forest_bear, berserker, arcane_scholar, goblin_raider, sea_serpent, skeleton,
                       dragon_whelp, bigger_slime, goblin_raider, vine_elemental, arcane_scholar, skeleton_army,
                       forest_bear, slime], 
                      [alpha_wolf, skeleton, slime, slime, arcane_scholar, bigger_slime, fire_elemental, goblin_raider,
                       phantom_warrior, arcane_scholar, vine_elemental, fire_elemental, berserker, skeleton_army, bigger_slime])
    
    # Initialize game
    game.ready()
    
    # Test play_creature: Add some cards to David's hand for testing
    print(f"\n[{game._timestamp()}] === Testing play_creature ===\n")
    
    # Load game state and add cards to David's hand
    with open(game.game_file, "r") as f:
        game_state = json.load(f)
    
    # Move first 3 cards from deck to hand
    david_data = game_state["David"]
    for i in range(min(3, len(david_data["deck"]))):
        card = david_data["deck"].pop(0)
        card_id = card["id"]
        david_data["hand"][str(card_id)] = card
        print(f"[{game._timestamp()}] Added {card['name']} (ID: {card_id}) to David's hand")
    
    # Save updated state
    with open(game.game_file, "w") as f:
        json.dump(game_state, f, indent=4)
    
    # Get a card ID from hand to play
    if david_data["hand"]:
        test_card_id = int(list(david_data["hand"].keys())[0])
        test_card_name = david_data["hand"][str(test_card_id)]["name"]
        
        print(f"\n[{game._timestamp()}] Attempting to play {test_card_name} (ID: {test_card_id})")
        success = game.play_creature("David", test_card_id)
        
        if success:
            print(f"[{game._timestamp()}] ✓ Successfully played creature!")
        else:
            print(f"[{game._timestamp()}] ✗ Failed to play creature")
    
    print(f"\n[{game._timestamp()}] === Test complete ===")

    