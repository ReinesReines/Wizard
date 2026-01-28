from typing import Any, Dict


class Cards:
    """
    Base class for a generic card.
    """
    def __init__(
        self,
        name: str,
        generic_mana: int,
        sp_mana: str,
        card_type: str,
        description: str,
    ) -> None:
        """
        Initialize a Cards instance.

        name
            Name of the card.
        generic_mana
            Cost in generic (colourless) mana.
        sp_mana
            Specific mana or colour required to play the card.
        card_type
            The card's type.
        description
            Text displayed on the card. Use '|' to separate flavour text.
        """
        self.name = name
        self.generic_mana = generic_mana
        self.sp_mana = sp_mana
        self.type = card_type
        self.description = description
        self.tapped = 0
        self.status = ""
        self.id = 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Return a dictionary representation of the card.

        Returns -> dict
            Dictionary containing the card's serializable fields.
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "generic_mana": self.generic_mana,
            "sp_mana": self.sp_mana,
            "type": self.type,
            "description": self.description,
            "tapped": self.tapped,
            "status": self.status,
        }


class SummonCard(Cards):
    """
    A creature card
    """

    def __init__(self, name: str, generic_mana: int, sp_mana: str, description: str, att: int, end: int, effect: Any) -> None:
        """
        Initialize a SummonCard.

        name
            Name of the summon card.
        generic_mana
            Generic mana cost.
        sp_mana
            Specific mana requirement.
        description
            Description text for the card.
        att
            Attack value.
        end
            Defence (endurance/health) value.
        effect
            Effect descriptor; structure is application-specific.
        """
        super().__init__(name, generic_mana, sp_mana, "Creature", description)
        self.attack = att
        self.defence = end
        self.effect = effect

    def to_dict(self) -> Dict[str, Any]:
        """
        Return a dictionary representation of the card.

        Returns -> dict
            Dictionary containing the card's serializable fields.
        """
        data = super().to_dict()
        data.update(
            {
                "attack": self.attack,
                "defence": self.defence,
                "effect": self.effect,
            }
        )
        return data


class SpellCard(Cards):
    """A spell card representing a one-time effect."""

    def __init__(self, name: str, generic_mana: int, sp_mana: str, description: str, effect: Any) -> None:
        """
        Initialize a SpellCard.

        name
            Name of the spell.
        generic_mana
            Generic mana cost.
        sp_mana
            Specific mana requirement.
        description
            Description text for the card.
        effect
            Effect descriptor for the spell.
        """
        super().__init__(name, generic_mana, sp_mana, "Spell", description)
        self.effect = effect

    def to_dict(self) -> Dict[str, Any]:
        """
        Return a dictionary representation of the card.

        Returns -> dict
            Dictionary containing the card's serializable fields.
        """
        data = super().to_dict()
        data["effect"] = self.effect
        return data

class LandCards(Cards):
    """A land card that generates mana."""

    def __init__(self, name: str, generic_mana: int, sp_mana: str, description: str, effect: Any) -> None:
        """Initialize a LandCards instance.

        name
            Name of the land.
        generic_mana
            Generic mana cost (often 0 for lands).
        sp_mana
            Specific mana type produced or required.
        description
            Description text for the land.
        effect
            Effect descriptor for the land (for example, mana production).
        """
        super().__init__(name, generic_mana, sp_mana, "Land", description)
        self.effect = effect

    def to_dict(self) -> Dict[str, Any]:
        """
        Return a dictionary representation of the card.

        Returns -> dict
            Dictionary containing the card's serializable fields.
        """
        data = super().to_dict()
        data["effect"] = self.effect
        return data
