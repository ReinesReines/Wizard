try:
    from modules.cards import *
except:
    from .modules.cards import *

"""
Effects parser

SYNTAX:
; - separator for next instruction
| - split description text
/ - or (for alternative options)

TRIGGERS (all end with ?):
tap?        - activates when tapped
attack?     - triggers when attacking
block?      - triggers when blocking
enter?      - triggers when this card enters the battlefield

MODIFIERS:
inc [field] [n]     - increase field by n (default 1)
dec [field] [n]     - decrease field by n (default 1)

ACTIONS:
gen [color]         - generates mana of specified color (green/blue/red)
draw [n]            - draw n cards
discard [n]         - target player discards n cards
heal [n]            - gain n life
count [type]        - count cards of specified type
return [from] [to]  - move card between zones

STATIC ABILITIES (keywords):
haste       - can attack the turn it enters
flying      - can only be blocked by creatures with flying or reach
reach       - can block creatures with flying
unblockable - cannot be blocked
vigilant    - doesn't tap when attacking
entertap    - enters the battlefield tapped

SPECIAL:
global              - applies effect to all your creatures
(graveyard count X) - dynamic value from graveyard

EXAMPLES:
tap? gen green                     - Tap to generate green mana
attack? inc att 1                  - Gain +1 attack when attacking
enter? draw 1                      - Draw a card when entering
inc att (graveyard count Skeleton) - +1 attack per skeleton in graveyard
entertap; tap? gen green/blue      - Enters tapped, tap for green or blue mana
vigilant                           - Doesn't tap when attacking
haste; flying                      - Can attack immediately and can only be blocked by flying creatures
"""

# TODO: finish this file

##############
# LAND CARDS #
##############

# Basic lands that generate one mana
forest = LandCards(name="Forest", generic_mana=0, sp_mana="", description="Tap to add one green mana.", effect="tap? gen green")
island = LandCards(name="Island", generic_mana=0, sp_mana="", description="Tap to add one blue mana.", effect="tap? gen blue")
mountain = LandCards(name="Mountain", generic_mana=0, sp_mana="", description="Tap to add one red mana.", effect="tap? gen red")

# Dual lands (enter tapped but produce two colors)
tropical_grove = LandCards(name="Tropical Grove", generic_mana=0, sp_mana="", description="Enters the battlefield tapped.|Tap to add one green or blue mana.", effect="entertap; tap? gen green/blue")
volcanic_peak = LandCards(name="Volcanic Peak", generic_mana=0, sp_mana="", description="Enters the battlefield tapped.|Tap to add one red or blue mana.", effect="entertap; tap? gen red/blue")
wild_highlands = LandCards(name="Wild Highlands", generic_mana=0, sp_mana="", description="Enters the battlefield tapped.|Tap to add one red or green mana.", effect="entertap; tap? gen red/green")


################
# SUMMON CARDS #
################

# Green creatures
slime = SummonCard(name="Slime", generic_mana=1, sp_mana="green", description="Attacking doesn't cause this creature to tap.", att=2, end=2, effect="vigilant")
bigger_slime = SummonCard(name="Bigger Slime", generic_mana=2, sp_mana="green", description="Attacking doesn't cause this creature to tap.|It's a bigger slime.", att=3, end=3, effect="vigilant")
forest_bear = SummonCard(name="Forest Bear", generic_mana=1, sp_mana="green", description="A powerful bear from the deep forest.|Why does he look like a dog", att=2, end=2, effect="")
vine_elemental = SummonCard(name="Vine Elemental", generic_mana=3, sp_mana="green", description="Gains +1/+1 when another creature enters the battlefield.|Looks like he's mid boogie", att=2, end=3, effect="enter? inc att 1; inc end 1")
alpha_wolf = SummonCard(name="Alpha Wolf", generic_mana=2, sp_mana="green", description="Other creatures you control get +1 attack.|Sorry, you're not a sigma", att=3, end=2, effect="global inc att 1")

# Blue creatures
skeleton = SummonCard(name="Skeleton", generic_mana=2, sp_mana="blue", description="Haste.\nGains +1 to endurance when blocking.", att=2, end=2, effect="haste; block? inc end 1")
skeleton_army = SummonCard(name="Skeleton Army", generic_mana=3, sp_mana="blue", description="Gains +1 to attack for every skeleton in the graveyard.", att=2, end=2, effect="haste; inc att (graveyard count Skeleton)")
phantom_warrior = SummonCard(name="Phantom Warrior", generic_mana=3, sp_mana="blue", description="Haste. This creature can attack instantly.", att=2, end=3, effect="haste")
sea_serpent = SummonCard(name="Sea Serpent", generic_mana=4, sp_mana="blue", description="A powerful sea creature. It's very poisonous.|Ssssss", att=5, end=5, effect="")
arcane_scholar = SummonCard(name="Arcane Scholar", generic_mana=2, sp_mana="blue", description="When this creature enters the battlefield, draw a card.|He is smart", att=1, end=3, effect="draw 1")
vergil = SummonCard(name="Vergil", generic_mana=5, sp_mana="blue", description="The Storm that is Approaching. Cannot be blocked.|Deadbeat Dad", att=6, end=6, effect="unblockable")

# Red creatures
goblin_raider = SummonCard(name="Goblin Raider", generic_mana=1, sp_mana="red", description="Haste. This creature can attack the turn it enters.", att=2, end=1, effect="haste")
fire_elemental = SummonCard(name="Fire Elemental", generic_mana=3, sp_mana="red", description="Gains +1 attack when attacking.", att=3, end=2, effect="attack? inc att 1")
dragon_whelp = SummonCard(name="Dragon Whelp", generic_mana=4, sp_mana="red", description="Flying. This baby dragon will grow to be quite terrifying.", att=2, end=3, effect="flying")
berserker = SummonCard(name="Berserker", generic_mana=2, sp_mana="red", description="Gains +2 attack when attacking, but -1 endurance.", att=2, end=3, effect="attack? inc att 2; dec end 1")

_universal_cards = [slime, bigger_slime, forest_bear, vine_elemental, alpha_wolf, skeleton, skeleton_army, phantom_warrior, sea_serpent, arcane_scholar,
                    vergil, goblin_raider, fire_elemental, dragon_whelp, berserker]
_land_cards = [forest, island, mountain, tropical_grove, volcanic_peak, wild_highlands]