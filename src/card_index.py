from .modules.cards import *

"""
Effects parser

SYNTAX:
; - separator for next instruction
| - split description text
/ - or (for alternative options)

TRIGGERS:
tap         - activates when tapped
attack?     - triggers when attacking
block?      - triggers when blocking
summon?     - triggers when another creature enters the battlefield
damage player? - triggers when dealing damage to a player
enter       - triggers when this card enters the battlefield
graveyard   - checks the graveyard

EFFECTS:
gen [color]         - generates mana of specified color (green/blue/red)
notap               - attacking doesn't cause this creature to tap
inc att [n]         - increase attack by n (default 1)
inc end [n]         - increase endurance/defense by n (default 1)
dec att [n]         - decrease attack by n (default 1)
dec end [n]         - decrease endurance/defense by n (default 1)
global inc att [n]  - increase attack of all other creatures you control
count [type]        - count cards of specified type
draw [n]            - draw n cards
damage target [n]   - deal n damage to target
damage player [n]   - deal n damage to player
discard [n]         - target player discards n cards
heal [n]            - gain n life
return graveyard hand - return creature from graveyard to hand
entertap            - enters the battlefield tapped

KEYWORDS:
haste       - can attack the turn it enters
flying      - can only be blocked by creatures with flying or reach
unblockable - cannot be blocked
vigilance   - doesn't tap when attacking
defender    - cannot attack
first_strike - deals combat damage before other creatures
lifelink    - damage dealt heals you
protection [color] - cannot be targeted/damaged by specified color

EXAMPLES:
tap gen green                    - Tap to generate green mana
attack? damage player 1          - When attacking, deal 1 damage to player
summon? inc att 1; inc end 1     - When creature summoned, gain +1/+1
entertap; tap gen green/blue     - Enters tapped, tap for green or blue mana
"""

# TODO: finish this file

##############
# LAND CARDS #
##############

# Basic lands that generate one mana
forest = LandCards(name="Forest", generic_mana=0, sp_mana="", description="Tap to add one green mana.", effect="tap gen green")
island = LandCards(name="Island", generic_mana=0, sp_mana="", description="Tap to add one blue mana.", effect="tap gen blue")
mountain = LandCards(name="Mountain", generic_mana=0, sp_mana="", description="Tap to add one red mana.", effect="tap gen red")

# Dual lands (enter tapped but produce two colors)
tropical_grove = LandCards(name="Tropical Grove", generic_mana=0, sp_mana="", description="Enters the battlefield tapped.|Tap to add one green or blue mana.", effect="entertap; tap gen green/blue")
volcanic_peak = LandCards(name="Volcanic Peak", generic_mana=0, sp_mana="", description="Enters the battlefield tapped.|Tap to add one red or blue mana.", effect="entertap; tap gen red/blue")
wild_highlands = LandCards(name="Wild Highlands", generic_mana=0, sp_mana="", description="Enters the battlefield tapped.|Tap to add one red or green mana.", effect="entertap; tap gen red/green")


################
# SUMMON CARDS #
################

# Green creatures
slime = SummonCard(name="Slime", generic_mana=1, sp_mana="green", description="Attacking doesn't cause this creature to tap.", att=2, end=2, effect="notap")
bigger_slime = SummonCard(name="Bigger Slime", generic_mana=2, sp_mana="green", description="Attacking doesn't cause this creature to tap.|It's a bigger slime.", att=3, end=3, effect="notap")
forest_bear = SummonCard(name="Forest Bear", generic_mana=1, sp_mana="green", description="A powerful bear from the deep forest.|Why does he look like a dog", att=2, end=2, effect="")
vine_elemental = SummonCard(name="Vine Elemental", generic_mana=3, sp_mana="green", description="Gains +1/+1 when another creature enters the battlefield.|Looks like he's mid boogie", att=2, end=3, effect="summon? inc att 1; inc end 1")
alpha_wolf = SummonCard(name="Alpha Wolf", generic_mana=2, sp_mana="green", description="Other creatures you control get +1 attack.|Sorry, you're not a sigma", att=3, end=2, effect="global inc att 1")

# Blue creatures
skeleton = SummonCard(name="Skeleton", generic_mana=2, sp_mana="blue", description="Haste.\nGains +1 to endurance when blocking.", att=2, end=2, effect="block? inc end 1")
skeleton_army = SummonCard(name="Skeleton Army", generic_mana=3, sp_mana="blue", description="Gains +1 to attack for every skeleton in the graveyard.", att=2, end=2, effect="graveyard count skeleton; inc att each")
phantom_warrior = SummonCard(name="Phantom Warrior", generic_mana=3, sp_mana="blue", description="Cannot be blocked.", att=2, end=3, effect="unblockable")
sea_serpent = SummonCard(name="Sea Serpent", generic_mana=4, sp_mana="blue", description="A powerful sea creature. It's very poisonous.|Ssssss", att=5, end=5, effect="")
arcane_scholar = SummonCard(name="Arcane Scholar", generic_mana=2, sp_mana="blue", description="When this creature enters the battlefield, draw a card.|He is smart", att=1, end=3, effect="summon? draw 1")
vergil = SummonCard(name="Vergil", generic_mana=5, sp_mana="blue", description="Ignores all defences for the opponent.|Deadbeat Dad", att=6, end=6, effect="ignore block")

# Red creatures
goblin_raider = SummonCard(name="Goblin Raider", generic_mana=1, sp_mana="red", description="Haste. This creature can attack the turn it enters.", att=2, end=1, effect="haste")
fire_elemental = SummonCard(name="Fire Elemental", generic_mana=3, sp_mana="red", description="Gains +1 attack when attacking.", att=3, end=2, effect="attack? inc att 1")
dragon_whelp = SummonCard(name="Dragon Whelp", generic_mana=4, sp_mana="red", description="Flying.", att=2, end=3, effect="flying")
berserker = SummonCard(name="Berserker", generic_mana=2, sp_mana="red", description="Gains +2 attack when attacking, but -1 endurance.", att=2, end=3, effect="attack? inc att 2; dec end 1")
