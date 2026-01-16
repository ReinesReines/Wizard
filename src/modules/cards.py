class Cards:
    def __init__(self, name, generic_mana, sp_mana, card_type, description):
        self.name = name
        self.generic_mana = generic_mana
        self.sp_mana = sp_mana
        self.type = card_type
        self.description = description
        self.tapped = 0
        self.status = ""
        self.id = 0
    
    def to_dict(self):
        """Convert card to dictionary for JSON serialization"""
        return {
            "id": str(self.id),
            "name": self.name,
            "generic_mana": self.generic_mana,
            "sp_mana": self.sp_mana,
            "type": self.type,
            "description": self.description,
            "tapped": self.tapped,
            "status": self.status
        }

class SummonCard(Cards):
    def __init__(self, name, generic_mana, sp_mana, description, att, end, effect):
        super().__init__(name, generic_mana, sp_mana, "Creature", description)
        self.attack = att
        self.defence = end
        self.effect = effect
    
    def to_dict(self):
        """Convert summon card to dictionary"""
        data = super().to_dict()
        data.update({
            "attack": self.attack,
            "defence": self.defence,
            "effect": self.effect
        })
        return data

class SpellCard(Cards):
    def __init__(self, name, generic_mana, sp_mana, description, effect):
        super().__init__(name, generic_mana, sp_mana, "Spell", description)
        self.effect = effect
    
    def to_dict(self):
        """Convert spell card to dictionary"""
        data = super().to_dict()
        data["effect"] = self.effect
        return data

class EnchantmentCards(Cards):
    def __init__(self, name, generic_mana, sp_mana, description, effect):
        super().__init__(name, generic_mana, sp_mana, "Enchantment", description)
        self.effect = effect
    
    def to_dict(self):
        """Convert enchantment card to dictionary"""
        data = super().to_dict()
        data["effect"] = self.effect
        return data

class LandCards(Cards):
    def __init__(self, name, generic_mana, sp_mana, description, effect):
        super().__init__(name, generic_mana, sp_mana, "Land", description)
        self.effect = effect
    
    def to_dict(self):
        """Convert land card to dictionary"""
        data = super().to_dict()
        data["effect"] = self.effect
        return data
