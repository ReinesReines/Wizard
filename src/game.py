from .modules.cards import Cards, SummonCard, SpellCard
from card_index import _land_cards
import random
import json

class GameEngine:
    def __init__(self):
        self.deck1 = []
        self.deck2 = []
        self.battlefield = []
        self.game_file = "game_state.json"

    def count(self, target: Cards, deck):
        """counts the number of target cards in a given deck."""
        x = 0
        for cards in deck:
            if cards.name == target.name:
                x += 1
        return x
    
    def shuffle_deck(self, ):
        pass

    def ready(self):
        """prepares the game state and variables for the next game."""
        # resets the .json file to an empty JSON object
        with open(self.game_file, "w") as f:
            json.dump({}, f)
