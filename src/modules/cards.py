class Cards:
    def __init__(self, generic_mana, sp_mana, card_type, description):
        self.generic_mana = generic_mana
        self.sp_mana = sp_mana
        self.type = card_type
        self.description 

# Subclass for creatures
class CreatureCard(Cards):
    def __init__(self, generic_mana, sp_mana, description, att, end):
        super().__init__(generic_mana, sp_mana, "Creature", description)
        self.attack = att
        self.defence = end

class SpellCard(Cards):
    def __init__(self, generic_mana, sp_mana, description, effect):
        super().__init__(generic_mana, sp_mana, "Spell", description)
        self.effect = effect
        
class EnchantmentCards(Cards):
    def __init__(self, generic_mana, sp_mana, description, effect):
        super().__init__(generic_mana, sp_mana, "Enchantment", description)
        self.effect = effect
