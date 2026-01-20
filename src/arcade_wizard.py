import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import arcade

from .wizard import Wizard
from .modules.utils import get_land_colors


SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Wizard - Arcade"

CARD_WIDTH = 110
CARD_HEIGHT = 154
CARD_PADDING = 12

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "modules", "assets")
CARD_ASSETS_DIR = os.path.join(ASSETS_DIR, "cards")
PLACEHOLDER_CARD = os.path.join(ASSETS_DIR, "placeholder.png")


@dataclass
class CardSlot:
    card_id: str
    owner: str
    zone: str
    name: str
    card_type: str
    rect: Tuple[float, float, float, float]


class WizardArcadeGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.DARK_SLATE_BLUE)

        self.wizard = Wizard("Player 1", "Player 2")
        self.selected_slot: Optional[CardSlot] = None
        self.target_slot: Optional[CardSlot] = None
        self.target_player: Optional[str] = None
        self.pending_attackers: List[str] = []
        self.pending_blocks: Dict[str, List[str]] = {}

        self.card_textures: Dict[str, arcade.Texture] = {}
        self.card_slots: List[CardSlot] = []

        self.status_message = ""
        self.status_timer = 0.0

    def setup(self):
        self.wizard.start()

    def on_draw(self):
        self.clear()
        self.card_slots = []

        state = self.wizard.game.get_game_state()
        current_player = self.wizard.current_player()
        opponent = self.wizard.p2 if current_player == self.wizard.p1 else self.wizard.p1

        self._draw_header(state, current_player, opponent)
        self._draw_board(state, current_player, opponent)
        self._draw_hand(state, current_player)
        self._draw_status()
        self._draw_controls()

    def on_update(self, delta_time: float):
        if self.status_timer > 0:
            self.status_timer -= delta_time
            if self.status_timer <= 0:
                self.status_message = ""

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        clicked = self._find_slot(x, y)
        if not clicked:
            return

        if button == arcade.MOUSE_BUTTON_LEFT:
            self.selected_slot = clicked
            self.target_slot = None
            self.target_player = None
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self.target_slot = clicked
            self.target_player = None

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.ESCAPE:
            arcade.close_window()
            return

        if symbol == arcade.key.P:
            self._play_selected_card()
        elif symbol == arcade.key.T:
            self._tap_selected_land()
        elif symbol == arcade.key.A:
            self._toggle_attacker()
        elif symbol == arcade.key.SPACE:
            self._confirm_combat_step()
        elif symbol == arcade.key.E:
            self._end_turn()
        elif symbol == arcade.key.C:
            self._cast_selected_spell()
        elif symbol == arcade.key.R:
            self._tap_selected_land(choice="red")
        elif symbol == arcade.key.G:
            self._tap_selected_land(choice="green")
        elif symbol == arcade.key.B:
            self._tap_selected_land(choice="blue")
        elif symbol == arcade.key.KEY_1:
            self.target_player = self.wizard.p1
            self.target_slot = None
        elif symbol == arcade.key.KEY_2:
            self.target_player = self.wizard.p2
            self.target_slot = None

    def _draw_header(self, state, current_player, opponent):
        mana = self.wizard.show_mana(current_player)
        hp_current = self.wizard.get_health(current_player)
        hp_opponent = self.wizard.get_health(opponent)
        phase = state.get("phase", "main_pre")

        header = f"Turn: {state.get('turn_number', 1)} | Phase: {phase}"
        arcade.draw_text(header, 20, SCREEN_HEIGHT - 30, arcade.color.LIGHT_GRAY, 14)

        stats = f"{current_player} HP: {hp_current} | Mana R:{mana['R']} G:{mana['G']} B:{mana['B']}"
        arcade.draw_text(stats, 20, SCREEN_HEIGHT - 50, arcade.color.LIGHT_GRAY, 12)
        arcade.draw_text(f"{opponent} HP: {hp_opponent}", 20, SCREEN_HEIGHT - 70, arcade.color.LIGHT_GRAY, 12)

    def _draw_board(self, state, current_player, opponent):
        self._draw_zone_row(
            state, opponent, "creatures", SCREEN_HEIGHT - 130, label="Opponent Creatures"
        )
        self._draw_zone_row(
            state, opponent, "lands", SCREEN_HEIGHT - 300, label="Opponent Lands"
        )
        self._draw_zone_row(
            state, current_player, "creatures", 320, label="Your Creatures"
        )
        self._draw_zone_row(
            state, current_player, "lands", 170, label="Your Lands"
        )

    def _draw_hand(self, state, current_player):
        hand = list(state[current_player]["hand"].items())
        count = len(hand)
        positions = self._layout_row(count, 60)
        arcade.draw_text("Your Hand", 20, 100, arcade.color.LIGHT_GRAY, 12)

        for (card_id, card), (x, y) in zip(hand, positions):
            slot = self._draw_card(card_id, current_player, "hand", card, x, y)
            if slot:
                self.card_slots.append(slot)

    def _draw_zone_row(self, state, owner, zone, y, label):
        cards = list(state[owner][zone].items())
        count = len(cards)
        positions = self._layout_row(count, y)
        arcade.draw_text(label, 20, y + (CARD_HEIGHT / 2) + 14, arcade.color.LIGHT_GRAY, 12)

        for (card_id, card_data), (x, y_pos) in zip(cards, positions):
            card = card_data["card"] if isinstance(card_data, dict) and "card" in card_data else card_data
            slot = self._draw_card(card_id, owner, zone, card, x, y_pos)
            if slot:
                self.card_slots.append(slot)

    def _draw_card(self, card_id, owner, zone, card, x, y):
        name = card.get("name", "<unknown>")
        card_type = card.get("type", "Unknown")
        texture = self._get_card_texture(name, card_type)

        if hasattr(arcade, "draw_texture_rectangle"):
            arcade.draw_texture_rectangle(x, y, CARD_WIDTH, CARD_HEIGHT, texture)
        elif hasattr(arcade, "draw_lrwh_rectangle_textured"):
            arcade.draw_lrwh_rectangle_textured(
                x - CARD_WIDTH / 2,
                y - CARD_HEIGHT / 2,
                CARD_WIDTH,
                CARD_HEIGHT,
                texture,
            )
        else:
            sprite = arcade.Sprite()
            sprite.texture = texture
            sprite.center_x = x
            sprite.center_y = y
            sprite.width = CARD_WIDTH
            sprite.height = CARD_HEIGHT
            if hasattr(sprite, "draw"):
                sprite.draw()
            elif hasattr(sprite, "render"):
                sprite.render()

        if card_type == "Creature":
            stats = f"{card.get('attack', '-')}/{card.get('defence', '-')}"
            arcade.draw_text(stats, x - CARD_WIDTH / 2 + 6, y - CARD_HEIGHT / 2 + 6, arcade.color.WHITE, 10)
        elif card_type == "Land":
            tapped = card.get("tapped", 0)
            if tapped:
                arcade.draw_text("T", x + CARD_WIDTH / 2 - 14, y - CARD_HEIGHT / 2 + 6, arcade.color.YELLOW, 12)

        name_label = name if len(name) <= 14 else f"{name[:12]}.."
        arcade.draw_text(name_label, x - CARD_WIDTH / 2 + 6, y + CARD_HEIGHT / 2 - 18, arcade.color.WHITE, 10)

        rect = (x - CARD_WIDTH / 2, y - CARD_HEIGHT / 2, CARD_WIDTH, CARD_HEIGHT)
        slot = CardSlot(str(card_id), owner, zone, name, card_type, rect)
        self._draw_slot_highlights(slot)
        return slot

    def _draw_slot_highlights(self, slot: CardSlot):
        if self.selected_slot and slot.card_id == self.selected_slot.card_id and slot.zone == self.selected_slot.zone:
            arcade.draw_rectangle_outline(
                slot.rect[0] + slot.rect[2] / 2,
                slot.rect[1] + slot.rect[3] / 2,
                slot.rect[2] + 6,
                slot.rect[3] + 6,
                arcade.color.YELLOW,
                3,
            )
        if self.target_slot and slot.card_id == self.target_slot.card_id and slot.zone == self.target_slot.zone:
            arcade.draw_rectangle_outline(
                slot.rect[0] + slot.rect[2] / 2,
                slot.rect[1] + slot.rect[3] / 2,
                slot.rect[2] + 6,
                slot.rect[3] + 6,
                arcade.color.AQUA,
                3,
            )

        if slot.card_id in self.pending_attackers:
            arcade.draw_rectangle_outline(
                slot.rect[0] + slot.rect[2] / 2,
                slot.rect[1] + slot.rect[3] / 2,
                slot.rect[2] + 10,
                slot.rect[3] + 10,
                arcade.color.ORANGE,
                3,
            )

    def _draw_status(self):
        if self.status_message:
            arcade.draw_text(self.status_message, 20, 20, arcade.color.ALMOND, 12)

    def _draw_controls(self):
        controls = (
            "Controls: Left Click select | Right Click target | "
            "P play | C cast | T tap | A queue attacker | SPACE confirm | E end turn | "
            "R/G/B choose mana | 1/2 target player"
        )
        arcade.draw_text(controls, 20, 0, arcade.color.LIGHT_GRAY, 10)

    def _layout_row(self, count, y):
        if count == 0:
            return []
        total_width = count * CARD_WIDTH + (count - 1) * CARD_PADDING
        start_x = (SCREEN_WIDTH - total_width) / 2 + CARD_WIDTH / 2
        return [(start_x + idx * (CARD_WIDTH + CARD_PADDING), y) for idx in range(count)]

    def _find_slot(self, x, y):
        for slot in self.card_slots:
            sx, sy, sw, sh = slot.rect
            if sx <= x <= sx + sw and sy <= y <= sy + sh:
                return slot
        return None

    def _get_card_texture(self, name, card_type):
        key = f"{name}|{card_type}"
        if key in self.card_textures:
            return self.card_textures[key]

        filename = name.lower().replace(" ", "_") + ".png"
        path = os.path.join(CARD_ASSETS_DIR, filename)
        if not os.path.exists(path):
            path = PLACEHOLDER_CARD
        texture = arcade.load_texture(path)
        self.card_textures[key] = texture
        return texture

    def _play_selected_card(self):
        if not self.selected_slot or self.selected_slot.zone != "hand":
            self._set_status("Select a card in hand to play.")
            return

        state = self.wizard.game.get_game_state()
        player = self.wizard.current_player()
        hand = state[player]["hand"]
        card = hand.get(self.selected_slot.card_id)
        if not card:
            self._set_status("Card no longer in hand.")
            return

        card_type = card.get("type")
        if card_type == "Land":
            if self.wizard.card_played_this_turn >= 1:
                self._set_status("You already played a land this turn.")
                return
            if self.wizard.play_land(self.selected_slot.card_id, player):
                self._set_status(f"Played land: {card.get('name')}")
        elif card_type == "Spell":
            self._set_status("Use C to cast spells (optional target).")
        else:
            generic_cost = card.get("generic_mana", 0)
            color_cost = card.get("sp_mana", "") or None
            if not self.wizard.game.check_mana_cost(player, generic_cost, color_cost):
                self._set_status("Not enough mana to play that creature.")
                return
            if not self.wizard.game.pay_mana(player, generic_cost, color_cost):
                self._set_status("Mana payment failed.")
                return
            self.wizard.play_creature(self.selected_slot.card_id, player)
            self._set_status(f"Played creature: {card.get('name')}")

    def _cast_selected_spell(self):
        if not self.selected_slot or self.selected_slot.zone != "hand":
            self._set_status("Select a spell in hand to cast.")
            return

        state = self.wizard.game.get_game_state()
        player = self.wizard.current_player()
        hand = state[player]["hand"]
        card = hand.get(self.selected_slot.card_id)
        if not card or card.get("type") != "Spell":
            self._set_status("Selected card is not a spell.")
            return

        target = None
        if self.target_slot:
            target = self.target_slot.card_id
        elif self.target_player:
            target = self.target_player

        if self.wizard.cast_spell(self.selected_slot.card_id, target, player=player):
            self._set_status(f"Casted {card.get('name')}")
        else:
            self._set_status("Spell casting failed.")

    def _tap_selected_land(self, choice=None):
        if not self.selected_slot or self.selected_slot.zone != "lands":
            self._set_status("Select a land to tap.")
            return

        state = self.wizard.game.get_game_state()
        player = self.selected_slot.owner
        land = state[player]["lands"].get(self.selected_slot.card_id, {}).get("card", {})
        colors = get_land_colors(land.get("effect", ""))
        if len(colors) > 1 and not choice:
            self._set_status(f"Choose mana color: {'/'.join(colors)} (R/G/B).")
            return
        if choice and choice not in colors:
            self._set_status("That color is not available on this land.")
            return

        if self.wizard.tap_land(self.selected_slot.card_id, choice, player=player):
            self._set_status(f"Tapped {land.get('name')}.")

    def _toggle_attacker(self):
        if not self.selected_slot or self.selected_slot.zone != "creatures":
            self._set_status("Select a creature to queue as attacker.")
            return

        player = self.wizard.current_player()
        if self.selected_slot.owner != player:
            self._set_status("You can only attack with your creatures.")
            return

        card_id = self.selected_slot.card_id
        if card_id in self.pending_attackers:
            self.pending_attackers.remove(card_id)
        else:
            self.pending_attackers.append(card_id)
        self._set_status(f"Queued attackers: {', '.join(self.pending_attackers) or 'none'}")

    def _confirm_combat_step(self):
        player = self.wizard.current_player()

        if self.wizard.combat_phase is None and self.pending_attackers:
            self.wizard.begin_combat(player)

        if self.wizard.combat_phase == "attackers":
            if not self.pending_attackers:
                self._set_status("No attackers queued.")
                return
            self.wizard.queue_attackers(player, self.pending_attackers)
            self.wizard.game.declare_attackers(player, self.pending_attackers)
            state = self.wizard.game.get_game_state()
            if state.get("combat", {}).get("attackers"):
                self.pending_attackers = []
                self.wizard.pass_priority_to_blocker()
                self._set_status("Attackers confirmed. Defender assign blockers.")
            else:
                self._set_status("No valid attackers declared.")
            return

        if self.wizard.combat_phase == "blockers":
            defender = self.wizard.combat_defender
            if defender != player:
                self._set_status("Defender has priority to confirm blocks.")
                return
            if self.selected_slot and self.target_slot:
                self._queue_blocker_assignment()
                return
            if not self.pending_blocks:
                self._set_status("No blockers queued.")
                return
            self.wizard.game.declare_blockers(defender, self.pending_blocks)
            self.pending_blocks = {}
            self.wizard.confirm_combat()
            self._set_status("Combat resolved.")
            return

    def _queue_blocker_assignment(self):
        if self.wizard.combat_phase != "blockers":
            self._set_status("Not in blockers phase.")
            return

        defender = self.wizard.combat_defender
        if self.selected_slot.owner != defender:
            self._set_status("Select your blocker and right-click attacker to assign.")
            return

        if not self.target_slot or self.target_slot.zone != "creatures":
            self._set_status("Right-click an attacker to set a block target.")
            return

        state = self.wizard.game.get_game_state()
        attacker_id = self.target_slot.card_id
        if attacker_id not in state.get("combat", {}).get("attackers", []):
            self._set_status("Target is not an attacking creature.")
            return
        blocker_id = self.selected_slot.card_id
        lst = self.pending_blocks.get(attacker_id, [])
        if blocker_id in lst:
            self._set_status("Blocker already assigned.")
            return
        lst.append(blocker_id)
        self.pending_blocks[attacker_id] = lst
        self._set_status(f"Queued blocker {blocker_id} -> attacker {attacker_id}")

    def _end_turn(self):
        player = self.wizard.current_player()
        state = self.wizard.game.get_game_state()
        hand_ids = list(state[player]["hand"].keys())
        if len(hand_ids) > 7:
            discard = hand_ids[: len(hand_ids) - 7]
            self.wizard.game.discard_cards(player, discard)

        self.wizard.game.end_turn(player)
        self.wizard.start_new_turn()
        self.pending_attackers = []
        self.pending_blocks = {}
        self._set_status("Turn ended.")

    def _set_status(self, message: str):
        self.status_message = message
        self.status_timer = 3.0
