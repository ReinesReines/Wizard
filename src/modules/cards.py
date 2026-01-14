class Cards:
    def __init__(self, name, generic_mana, sp_mana, card_type, description):
        self.name = name
        self.generic_mana = generic_mana
        self.sp_mana = sp_mana
        self.type = card_type
        self.description = description
        self.tapped = 0
        self.status = ""

class SummonCard(Cards):
    def __init__(self, name, generic_mana, sp_mana, description, att, end, effect):
        super().__init__(name, generic_mana, sp_mana, "Creature", description)
        self.attack = att
        self.defence = end
        self.effect = effect

class SpellCard(Cards):
    def __init__(self, name, generic_mana, sp_mana, description, effect):
        super().__init__(name, generic_mana, sp_mana, "Spell", description)
        self.effect = effect

class EnchantmentCards(Cards):
    def __init__(self, name, generic_mana, sp_mana, description, effect):
        super().__init__(name, generic_mana, sp_mana, "Enchantment", description)
        self.effect = effect

class LandCards(Cards):
    def __init__(self, name, generic_mana, sp_mana, description, effect):
        super().__init__(name, generic_mana, sp_mana, "Land", description)
        self.effect = effect
