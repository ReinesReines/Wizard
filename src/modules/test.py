from parser import *
from utils import *
from cards import *

print("=== STATIC ABILITY TESTS ===\n")

# Test flying
dragon = SummonCard(name="Dragon", generic_mana=4, sp_mana="red", description="Flying", att=4, end=4, effect="flying")
print(f"{dragon.name} has flying: {has_flying(dragon)}")
print(f"{dragon.name} can be blocked: {can_be_blocked(dragon)}")

# Test haste
goblin = SummonCard(name="Goblin", generic_mana=1, sp_mana="red", description="Haste", att=2, end=1, effect="haste")
print(f"\n{goblin.name} has haste: {card_has_ability(goblin, 'haste')}")
print(f"{goblin.name} can attack immediately: {can_attack_immediately(goblin)}")

# Test unblockable
phantom = SummonCard(name="Phantom", generic_mana=3, sp_mana="blue", description="Cannot be blocked", att=2, end=3, effect="unblockable")
print(f"\n{phantom.name} is unblockable: {card_has_ability(phantom, 'unblockable')}")
print(f"{phantom.name} can be blocked: {can_be_blocked(phantom)}")

# Test vigilant
knight = SummonCard(name="Knight", generic_mana=2, sp_mana="green", description="Vigilance", att=3, end=2, effect="vigilant")
print(f"\n{knight.name} has vigilant: {card_has_ability(knight, 'vigilant')}")
print(f"{knight.name} taps when attacking: {taps_when_attacking(knight)}")

# Test entertap
land = LandCards(name="Temple", generic_mana=0, sp_mana="", description="Enters tapped", effect="entertap; tap gen blue")
print(f"\n{land.name} enters tapped: {enters_tapped(land)}")

# Test notap
slime = SummonCard(name="Slime", generic_mana=1, sp_mana="green", description="Doesn't tap when attacking", att=2, end=2, effect="notap")
print(f"\n{slime.name} has notap: {card_has_ability(slime, 'notap')}")
print(f"{slime.name} taps when attacking: {taps_when_attacking(slime)}")

# Test multiple abilities
powerful = SummonCard(name="Powerful Creature", generic_mana=5, sp_mana="blue", description="Flying, Haste", att=5, end=5, effect="flying; haste")
print(f"\n{powerful.name} static abilities: {get_card_static_abilities(powerful)}")
print(f"{powerful.name} has flying: {has_flying(powerful)}")
print(f"{powerful.name} can attack immediately: {can_attack_immediately(powerful)}")