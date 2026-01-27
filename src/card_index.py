try:
    from modules.cards import *
except:
    from .modules.cards import *


##############
# LAND CARDS #
##############

# Basic lands that generate one mana
forest = LandCards(name="Forest", generic_mana=0, sp_mana="", description="Tap to add one green mana.", effect="tap? gen 1 green")
island = LandCards(name="Island", generic_mana=0, sp_mana="", description="Tap to add one blue mana.", effect="tap? gen 1 blue")
mountain = LandCards(name="Mountain", generic_mana=0, sp_mana="", description="Tap to add one red mana.", effect="tap? gen 1 red")

snake_pit = LandCards(name="Snake Pit", generic_mana=0, sp_mana="", description="Enters the battlefield tapped.|Tap to add two green mana.", effect="entertap; tap? gen 2 green")
machine_factory = LandCards(name="Machine Factory", generic_mana=0, sp_mana="", description="Enters the battlefield tapped.|Tap to add two red mana.", effect="entertap; tap? gen 2 red")
sea_of_stars = LandCards(name="Sea of Stars", generic_mana=0, sp_mana="", description="Enters the battlefield tapped.|Tap to add two blue mana.", effect="entertap; tap? gen 2 blue")

land_of_iridesence = LandCards(name="Land of Iridesence", generic_mana=0, sp_mana="", description="Enters the battlefield tapped.|Tap to add one green, blue, or red mana.", effect="entertap; tap? gen 1 green/blue/red")

graveyard = LandCards(name="Graveyard", generic_mana=0, sp_mana="", description="When tapped, it generates blue mana correlating to the number of Skeletons in your graveyard.", effect="tap? gen (graveyard count Skeleton) blue")

# Dual lands (enter tapped but produce two colors)
tropical_grove = LandCards(name="Tropical Grove", generic_mana=0, sp_mana="", description="Enters the battlefield tapped.|Tap to add one green or blue mana.", effect="entertap; tap? gen 1 green/blue")
volcanic_peak = LandCards(name="Volcanic Peak", generic_mana=0, sp_mana="", description="Enters the battlefield tapped.|Tap to add one red or blue mana.", effect="entertap; tap? gen 1 red/blue")
wild_highlands = LandCards(name="Wild Highlands", generic_mana=0, sp_mana="", description="Enters the battlefield tapped.|Tap to add one red or green mana.", effect="entertap; tap? gen 1 red/green")


################
# SUMMON CARDS #
################

# Green creatures
slime = SummonCard(name="Slime", generic_mana=1, sp_mana="green", description="Attacking doesn't cause this creature to tap.", att=2, end=2, effect="vigilant")
bigger_slime = SummonCard(name="Bigger Slime", generic_mana=2, sp_mana="green", description="Attacking doesn't cause this creature to tap.|It's a bigger slime.", att=3, end=3, effect="vigilant")
forest_bear = SummonCard(name="Forest Bear", generic_mana=1, sp_mana="green", description="A powerful bear from the deep forest.|Why does he look like a dog", att=2, end=2, effect="")
vine_elemental = SummonCard(name="Vine Elemental", generic_mana=3, sp_mana="green", description="Gains +1/+1 when another creature enters the battlefield.|Looks like he's mid boogie", att=2, end=3, effect="enter? inc att 1; enter? inc end 1")
alpha_wolf = SummonCard(name="Alpha Wolf", generic_mana=2, sp_mana="green", description="Other creatures you control get +1 attack.|Sorry, you're not a sigma", att=3, end=2, effect="summon? global inc att 1")
stone_giant = SummonCard(name="Stone Giant", generic_mana=2, sp_mana="green", description="Gains +2 to endurance when blocking.|He does not look amused at all...", att=1, end=3, effect="block? inc end 2")
green_wizar = SummonCard(name="Green Wizar", generic_mana=1, sp_mana="green", description="Gains +1 to attack for each green coloured mana you have when it enters the battlefield.|The power of green", att=2, end=6, effect="summon? inc att (mana count green)")
king_slime = SummonCard(name="King Slime", generic_mana=4, sp_mana="green", description="Gives all active slime creatures +1 to attack.|The king of slimes", att=4, end=6, effect="summon? inc att 1 \"Slime\"")
archer = SummonCard(name="Archer", generic_mana=2, sp_mana="green", description="This creature has reach.|His arrows go pretty far", att=2, end=3, effect="reach")
hero = SummonCard(name="Hero", generic_mana=3, sp_mana="green", description="All creatures you control gain +1 to endurance.|So inspiring", att=3, end=3, effect="summon? global inc end 1")

# Blue creatures
skeleton = SummonCard(name="Skeleton", generic_mana=2, sp_mana="blue", description="Haste.\nGains +1 to endurance when blocking.", att=2, end=2, effect="haste; block? inc end 1")
skeleton_army = SummonCard(name="Skeleton Army", generic_mana=3, sp_mana="blue", description="Gains +1 to attack for every skeleton in the graveyard.", att=2, end=2, effect="haste; summon? inc att (graveyard count Skeleton)")
phantom_warrior = SummonCard(name="Phantom Warrior", generic_mana=3, sp_mana="blue", description="Reach. This creature can block flying creatures.", att=2, end=3, effect="reach")
sea_serpent = SummonCard(name="Sea Serpent", generic_mana=4, sp_mana="blue", description="Trample. It's a powerful sea creature.|Ssssss", att=5, end=5, effect="trample")
arcane_scholar = SummonCard(name="Arcane Scholar", generic_mana=2, sp_mana="blue", description="When this creature enters the battlefield, draw a card.|He is smart", att=1, end=3, effect="summon? draw 1")
vergil = SummonCard(name="Vergil", generic_mana=5, sp_mana="blue", description="The Storm that is Approaching. Cannot be blocked.|Deadbeat Dad", att=6, end=6, effect="unblockable")
blue_wizar = SummonCard(name="Blue Wizar", generic_mana=1, sp_mana="blue", description="Gains +1 to attack for each blue coloured mana you have when it enters the battlefield.|The power of blue", att=2, end=6, effect="summon? inc att (mana count blue)")
mind_sorcerer = SummonCard(name="Mind Sorcerer", generic_mana=2, sp_mana="blue", description="An evil sorcerer from the lands between. Draw 1 card when he enters the battlefield.|He reads your mind", att=3, end=4, effect="summon? draw 1")
wanderer = SummonCard(name="Wanderer", generic_mana=2, sp_mana="blue", description="Flying. A powerful wizar forgotten to time. His true ability is unknown.|What's his name again?", att=3, end=4, effect="flying")
mind_flayer = SummonCard(name="Mind Flayer", generic_mana=4, sp_mana="blue", description="A mind-controlling illithid that yearns for dominance. Create an intellect devourer when summoned.", att=5, end=5, effect="create 1 \"Intellect Devourer\"")

# Red creatures
goblin_raider = SummonCard(name="Goblin Raider", generic_mana=1, sp_mana="red", description="Haste. This creature can attack the turn it enters.", att=2, end=1, effect="haste")
fire_elemental = SummonCard(name="Fire Elemental", generic_mana=3, sp_mana="red", description="Gains +1 attack when attacking.", att=3, end=2, effect="attack? inc att 1")
dragon_whelp = SummonCard(name="Dragon Whelp", generic_mana=2, sp_mana="red", description="Flying. This baby dragon will grow to be quite terrifying.", att=3, end=2, effect="flying")
berserker = SummonCard(name="Berserker", generic_mana=2, sp_mana="red", description="Gains +2 attack when attacking, but -1 endurance.", att=2, end=3, effect="attack? inc att 2; attack? dec end 1")
imp = SummonCard(name="Imp", generic_mana=1, sp_mana="red", description="Flying. A very evil creature.", att=2, end=2, effect="flying")
sazael_the_great = SummonCard(name="Sazael the Great", generic_mana=4, sp_mana="red", description="Flying, trample, and gains +2 when attacking. This dragon is pretty great.", att=5, end=5, effect="flying; trample; attack? inc att 2")
red_wizar = SummonCard(name="Red Wizar", generic_mana=1, sp_mana="red", description="Gains +1 to attack for each red coloured mana you have when it enters the battlefield.|The power of red", att=2, end=6, effect="summon? inc att (mana count red)")
intellect_devourer = SummonCard(name="Intellect Devourer", generic_mana=1, sp_mana="red", description="Haste. A repulsive creature that harnesses the intellect of others.|Not that it'd get much from you", att=2, end=2, effect="haste")

# Red spell cards
fireball = SpellCard(name="Fireball", generic_mana=3, sp_mana="red", description="Deal 3 damage to target creature.", effect="damage 3 creatureid")
wild_hunt = SpellCard(name="Wild Hunt", generic_mana=4, sp_mana="red", description="Give all creatures you control trample.", effect="global add trample")
berserk = SpellCard(name="Berserk", generic_mana=2, sp_mana="red", description="Give all creatures +2 attack and -1 endurance.", effect="all inc att 2; all dec end 1")
scorched_earth = SpellCard(name="Scorched Earth", generic_mana=9, sp_mana="red", description="Destroy all active creatures.|swortched erth mate", effect="all destroy")
rot = SpellCard(name="Rot", generic_mana=3, sp_mana="red", description="Force your opponent to discard 2 cards.|brain rot", effect="discard 2 player")
wrath = SpellCard(name="Wrath", generic_mana=3, sp_mana="red", description="Deal 4 damage to a target creature. Discard a card.", effect="destroy creatureid; discard 1")

# Blue spell cards
oath = SpellCard(name="Oath", generic_mana=0, sp_mana="blue", description="You do not reset your mana pool at the end of your turn.", effect="nomanareset")
polymorph_skeleton = SpellCard(name="Skeleton Polymorph", generic_mana=1, sp_mana="blue", description="Morph target creature into a skeleton.|ragh", effect="morph creatureid \"Skeleton\"")
bless = SpellCard(name="Bless", generic_mana=5, sp_mana="blue", description="Give a creature invulnerability.", effect="add invuln creatureid")
wingify = SpellCard(name="Wingify", generic_mana=2, sp_mana="blue", description="Give a creature flying.|wingardium leviosa", effect="add flying creatureid")
eldritch_blast = SpellCard(name="Eldritch Blast", generic_mana=2, sp_mana="blue", description="Deal 2 damage to a target creature. Draw a card.", effect="damage 2 creatureid; draw 1")
magic_missile = SpellCard(name="Magic Missile", generic_mana=1, sp_mana="blue", description="Deal 1 damage to a target creature. Decrease their attack by 1.", effect="damage 1 creatureid; dec att 1 creatureid")

# Green spell cards
healing_word = SpellCard(name="Healing Word", generic_mana=1, sp_mana="green", description="Heal 2 damage from target creature.", effect="heal 2 creatureid")
inspiration = SpellCard(name="Inspiration", generic_mana=2, sp_mana="green", description="Increase a creature's endurance by 1 when it blocks an attack.", effect="castinc creatureid end 1")


# Collections for card_creator.py
_universal_cards = [
    # Green creatures
    slime, bigger_slime, forest_bear, vine_elemental, alpha_wolf, green_wizar, stone_giant, king_slime, archer,
    # Blue creatures
    skeleton, skeleton_army, phantom_warrior, sea_serpent, arcane_scholar, vergil, blue_wizar,
    # Red creatures
    goblin_raider, fire_elemental, dragon_whelp, berserker, imp, sazael_the_great, red_wizar,
]

_land_cards = [
    forest, island, mountain, tropical_grove, volcanic_peak, wild_highlands, snake_pit, machine_factory, sea_of_stars, land_of_iridesence,
]

_spell_cards = [
    fireball, wild_hunt, berserk, oath, polymorph_skeleton, healing_word, eldritch_blast, wrath, rot, bless, wingify, scorched_earth, inspiration, magic_missile,
]