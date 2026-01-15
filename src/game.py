from modules.cards import Cards, SummonCard, SpellCard
from card_index import _land_cards
import random
import json



class GameEngine:
    def __init__(self, deck1, deck2):
        self.deck1 = deck1
        self.deck2 = deck2
        self.battlefield = []
        self.game_file = "game_state.json"

    def count(self, target: Cards, deck):
        """counts the number of target cards in a given deck."""
        x = 0
        for cards in deck:
            if cards.name == target.name:
                x += 1
        return x
    
    def shuffle_deck(self, deck):
        new_deck = []
        while len(deck) > 0:
            to_pop = random.randint(0, len(deck)-1)
            print(len(deck))
            item = deck.pop(to_pop)
            new_deck.append(item)
        return new_deck

    def ready(self):
        """prepares the game state and variables for the next game."""
        # resets the .json file to an empty JSON object
        with open(self.game_file, "w") as f:
            json.dump({}, f)
        
        self.deck1 = self.shuffle_deck(self.deck1)
        self.deck1 = self.shuffle_deck(self.deck1)


if __name__ == "__main__":
    game = GameEngine([], [])
    