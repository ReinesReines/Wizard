from card_index import _universal_cards
import random

creatures = []
for i in range(20):
    thing = random.choice(_universal_cards)
    if creatures.count(thing) <= 4 and thing.name != "Vergil":
        creatures.append(thing)

print([i.name for i in creatures])