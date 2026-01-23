import os
import math
import pygame
from PIL import Image

from src.modules.card_creator import create_card, update_card_stats
from src.modules.parser import EffectParser
from src.modules.utils import get_land_colors
from src.wizard import Wizard

WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (106, 92, 125)
CARD_SPACING = 10
HAND_MARGIN = 8
CARD_SCALE = 0.5

ASSETS_PATH = os.path.join(os.path.dirname(__file__), "src", "modules", "assets")
CARDS_PATH = os.path.join(ASSETS_PATH, "cards")
TEMP_PATH = os.path.join(ASSETS_PATH, "temp")
PLACEHOLDER_PATH = os.path.join(ASSETS_PATH, "placeholder.png")
SILK_PATH = os.path.join(ASSETS_PATH, "fonts", "Silkscreen-Regular.ttf")
HAS_PLAYED_LAND = False

os.makedirs(TEMP_PATH, exist_ok=True)
for filename in os.listdir(TEMP_PATH):
    if filename.endswith(".png"):
        try:
            os.remove(os.path.join(TEMP_PATH, filename))
        except OSError:
            pass

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Wizard")

image_cache = {}
pil_cache = {}
hand_hitboxes = []
land_hitboxes = []
creature_hitboxes = []
active_creature_hitboxes = []
hovered_card_id = None
selected_card_id = None
active_selected_card_id = None
creature_deck_rect = None
label_rects = {}
label_draw_queue = []
view_player = None
creature_rects = {}
active_creature_rects = {}
selected_blocker_id = None
notifications = []
attacker_select_id = None
prev_creature_stats = {}
prev_creature_status = {}
prev_hand_ids = {}
last_drawn_id = {}
discard_state = {
    "active": False,
    "player": None,
    "required": 0,
    "discarded": 0,
    "return_player": None,
}
draw_animation = {
    "active": False,
    "card_id": None,
    "card": None,
    "start": None,
    "end": None,
    "start_ms": 0,
    "duration_ms": 450,
    "player": None,
    "queue": [],
}
combat_prompt_state = {
    "visible": False,
    "mode": None,
    "lines": [],
    "rect": None,
    "confirm_rect": None,
    "cancel_rect": None,
}
hover_state = {
    "card_id": None,
    "start_ms": 0,
    "card": None,
    "rect": None,
}
hover_label_state = {
    "visible": False,
    "lines": [],
    "anchor_rect": None,
}
popup_state = {
    "visible": False,
    "message": "",
    "rect": None,
    "close_rect": None,
    "lines": [],
    "font_size": 16,
}
popup_shown = False
game_over_state = {"active": False, "winner": None, "loser": None}

try:
    card_font = pygame.font.Font(SILK_PATH, 18)
    menu_font = pygame.font.Font(SILK_PATH, 16)
    label_font = pygame.font.Font(SILK_PATH, 14)
except Exception:
    card_font = pygame.font.Font(None, 18)
    menu_font = pygame.font.Font(None, 16)
    label_font = pygame.font.Font(None, 14)

context_menu = {"visible": False, "rects": [], "actions": []}


def get_default_image_path(card_name):
    filename = card_name.lower().replace(" ", "_") + ".png"
    default_path = os.path.join(CARDS_PATH, filename)
    if os.path.exists(default_path):
        return default_path
    return PLACEHOLDER_PATH


def load_image(path):
    if path in image_cache:
        return image_cache[path]
    if not path or not os.path.isfile(path):
        path = PLACEHOLDER_PATH
    try:
        image = pygame.image.load(path).convert_alpha()
    except pygame.error:
        if path != PLACEHOLDER_PATH and os.path.isfile(PLACEHOLDER_PATH):
            image = pygame.image.load(PLACEHOLDER_PATH).convert_alpha()
        else:
            raise
    image_cache[path] = image
    return image


def load_pil_image(path):
    if path in pil_cache:
        return pil_cache[path]
    if not path or not os.path.isfile(path):
        path = PLACEHOLDER_PATH
    try:
        image = Image.open(path).convert("RGBA")
    except Exception:
        if path != PLACEHOLDER_PATH and os.path.isfile(PLACEHOLDER_PATH):
            image = Image.open(PLACEHOLDER_PATH).convert("RGBA")
        else:
            raise
    pil_cache[path] = image
    return image


def needs_temp_image(card_dict, creature_entry):
    if not creature_entry:
        return False
    attack = card_dict.get("attack")
    defence = card_dict.get("defence")
    if attack is None or defence is None:
        return False
    return True


def build_temp_image(card_id, card_dict):
    card_obj = wiz.game._reconstruct_card(card_dict)
    if not card_obj:
        return None
    temp_name = f"{card_id}_{card_dict.get('attack')}_{card_dict.get('defence')}.png"
    temp_path = os.path.join(TEMP_PATH, temp_name)
    if not os.path.exists(temp_path):
        base_path = card_dict.get("image_path") or get_default_image_path(card_dict.get("name", ""))
        if base_path and os.path.exists(base_path):
            update_card_stats(card_obj, temp_path, base_path)
        else:
            create_card(card_obj, temp_path)
    return temp_path


def update_image_paths(game_state):
    changed = False

    def set_image_path(card_id, card_dict, creature_entry=None):
        nonlocal changed
        if needs_temp_image(card_dict, creature_entry):
            temp_path = build_temp_image(card_id, card_dict)
            if temp_path and card_dict.get("image_path") != temp_path:
                card_dict["image_path"] = temp_path
                changed = True
            return

        default_path = get_default_image_path(card_dict.get("name", ""))
        if card_dict.get("image_path") != default_path:
            card_dict["image_path"] = default_path
            changed = True

    for player in [wiz.p1, wiz.p2]:
        for card_id, card_dict in game_state[player]["hand"].items():
            set_image_path(card_id, card_dict)

        for card_id, creature_entry in game_state[player]["creatures"].items():
            card_dict = creature_entry.get("card", {})
            set_image_path(card_id, card_dict, creature_entry)

        for card_id, land_entry in game_state[player]["lands"].items():
            card_dict = land_entry.get("card", {})
            set_image_path(card_id, card_dict)

        for card_dict in game_state[player].get("graveyard", []):
            if isinstance(card_dict, dict):
                set_image_path(card_dict.get("id"), card_dict)

        for card_dict in game_state[player].get("deck", []):
            if isinstance(card_dict, dict):
                set_image_path(card_dict.get("id"), card_dict)

    if changed:
        wiz.game._save_state(game_state)


def render_card_by_name(card_dict):
    image_path = card_dict.get("image_path") or get_default_image_path(card_dict.get("name", ""))
    return load_image(image_path)


def render_image(card_dict, x, y):
    image_path = card_dict.get("image_path") or get_default_image_path(card_dict.get("name", ""))
    pil_image = load_pil_image(image_path)
    scaled_size = (
        max(1, int(pil_image.width * CARD_SCALE)),
        max(1, int(pil_image.height * CARD_SCALE)),
    )
    pil_image = pil_image.resize(scaled_size, Image.NEAREST)
    surface = pygame.image.fromstring(pil_image.tobytes(), pil_image.size, "RGBA")
    rect = surface.get_rect()
    rect.bottomleft = (x, y)
    screen.blit(surface, rect)
    return rect


def render_image_rotated(card_dict, x, y, angle):
    image_path = card_dict.get("image_path") or get_default_image_path(card_dict.get("name", ""))
    pil_image = load_pil_image(image_path)
    scaled_size = (
        max(1, int(pil_image.width * CARD_SCALE)),
        max(1, int(pil_image.height * CARD_SCALE)),
    )
    pil_image = pil_image.resize(scaled_size, Image.NEAREST)
    surface = pygame.image.fromstring(pil_image.tobytes(), pil_image.size, "RGBA")
    surface = pygame.transform.rotate(surface, angle)
    rect = surface.get_rect()
    rect.bottomleft = (x, y)
    screen.blit(surface, rect)
    return rect


def is_vigilant_card(card_dict):
    status = str(card_dict.get("status", "")).lower()
    effect = str(card_dict.get("effect", "")).lower()
    return "vigilant" in status or "vigilant" in effect or "notap" in status


def render_land_image(card_dict, x, y, tapped=False):
    image_path = card_dict.get("image_path") or get_default_image_path(card_dict.get("name", ""))
    pil_image = load_pil_image(image_path)
    scaled_size = (
        max(1, int(pil_image.width * CARD_SCALE)),
        max(1, int(pil_image.height * CARD_SCALE)),
    )
    pil_image = pil_image.resize(scaled_size, Image.NEAREST)
    surface = pygame.image.fromstring(pil_image.tobytes(), pil_image.size, "RGBA")
    if tapped:
        surface = pygame.transform.rotate(surface, -90)
    rect = surface.get_rect()
    rect.bottomleft = (x, y)
    screen.blit(surface, rect)
    return rect

announce_state = {"message": "", "until_ms": 0}

def announce(message, duration_ms=2000):
    message = str(message or "").strip()
    if not message:
        return
    announce_state["message"] = message
    announce_state["until_ms"] = pygame.time.get_ticks() + duration_ms

def render_announce():
    if not announce_state.get("message"):
        return
    if pygame.time.get_ticks() > announce_state.get("until_ms", 0):
        announce_state["message"] = ""
        return
    try:
        font = pygame.font.Font(SILK_PATH, 48)
    except Exception:
        font = pygame.font.Font(None, 48)
    text = font.render(announce_state["message"], True, (255, 255, 255))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)

def render_hand(game_state, player, start_x=None, exclude_ids=None):
    global hand_hitboxes
    hand_hitboxes = []

    hand = game_state[player]["hand"]
    if exclude_ids is None:
        exclude_ids = set()
    else:
        exclude_ids = set(exclude_ids)
    grouped = {"Creature": [], "Land": [], "Spell": [], "Other": []}
    for card_id, card_dict in hand.items():
        card_type = card_dict.get("type", "Other")
        grouped.get(card_type, grouped["Other"]).append((card_id, card_dict))

    ordered_groups = [g for g in ("Creature", "Land", "Spell", "Other") if grouped[g]]

    placeholder = load_pil_image(PLACEHOLDER_PATH)
    card_width = max(1, int(placeholder.width * CARD_SCALE))
    card_height = max(1, int(placeholder.height * CARD_SCALE))

    hand_step = max(18, int(card_width * 0.4))
    group_gap = max(10, int(card_width * 0.2))

    x = HAND_MARGIN if start_x is None else start_x
    base_y = HEIGHT - HAND_MARGIN

    draw_queue = []
    for gi, group_name in enumerate(ordered_groups):
        for card_id, card_dict in grouped[group_name]:
            draw_queue.append((card_id, card_dict, x))
            x += hand_step
        if gi < len(ordered_groups) - 1:
            x += group_gap

    last_id = last_drawn_id.get(player)
    if last_id:
        last_item = None
        for i, (card_id, card_dict, card_x) in enumerate(draw_queue):
            if card_id == last_id:
                last_item = draw_queue.pop(i)
                break
        if last_item:
            draw_queue.append(last_item)
            x = HAND_MARGIN if start_x is None else start_x
            for idx, (card_id, card_dict, _) in enumerate(draw_queue):
                draw_queue[idx] = (card_id, card_dict, x)
                x += hand_step

    # draw order: normal cards first, then hovered, then selected (on top)
    for card_id, card_dict, card_x in draw_queue:
        if card_id in (hovered_card_id, selected_card_id):
            continue
        if card_id in exclude_ids:
            if draw_animation.get("active") and draw_animation.get("card_id") == card_id and draw_animation.get("end") is None:
                draw_animation["end"] = (card_x, base_y)
            continue
        rect = render_image(card_dict, card_x, base_y)
        hand_hitboxes.append({"id": card_id, "rect": rect, "card": card_dict, "zone": "hand"})

    for card_id, card_dict, card_x in draw_queue:
        if card_id != hovered_card_id or card_id == selected_card_id:
            continue
        if card_id in exclude_ids:
            if draw_animation.get("active") and draw_animation.get("card_id") == card_id and draw_animation.get("end") is None:
                draw_animation["end"] = (card_x, base_y)
            continue
        rect = render_image(card_dict, card_x, base_y - max(12, card_height // 8))
        hand_hitboxes.append({"id": card_id, "rect": rect, "card": card_dict, "zone": "hand"})

    for card_id, card_dict, card_x in draw_queue:
        if card_id != selected_card_id:
            continue
        if card_id in exclude_ids:
            if draw_animation.get("active") and draw_animation.get("card_id") == card_id and draw_animation.get("end") is None:
                draw_animation["end"] = (card_x, base_y)
            continue
        rect = render_image(card_dict, card_x, base_y - max(20, card_height // 6))
        hand_hitboxes.append({"id": card_id, "rect": rect, "card": card_dict, "zone": "hand"})
        draw_pulse_outline(rect, (255, 255, 255), (220, 220, 220))


def render_creature_row(game_state, player, y, align="left", filter_fn=None, attack_ids=None, rotate_attackers=False, animate=False):
    global creature_hitboxes, creature_rects
    creatures = list(game_state[player]["creatures"].items())
    if filter_fn:
        creatures = [(cid, cdata) for cid, cdata in creatures if filter_fn(cdata)]
    if not creatures:
        return
    if attack_ids is None:
        attack_ids = set()
    else:
        attack_ids = set(str(cid) for cid in attack_ids)

    placeholder = load_pil_image(PLACEHOLDER_PATH)
    card_width = max(1, int(placeholder.width * CARD_SCALE))
    total_width = (card_width * len(creatures)) + CARD_SPACING * (len(creatures) - 1)

    if align == "right":
        x = max(HAND_MARGIN, WIDTH - HAND_MARGIN - total_width)
    elif align == "center":
        x = max(HAND_MARGIN, (WIDTH - total_width) // 2)
    else:
        x = HAND_MARGIN

    for card_id, creature_entry in creatures:
        card_dict = creature_entry.get("card", {})
        should_rotate = rotate_attackers and str(card_id) in attack_ids and not is_vigilant_card(card_dict)
        wobble = 0
        if animate and hovered_card_id == card_id:
            wobble = int(math.sin(pygame.time.get_ticks() / 140) * 3)
        if should_rotate:
            rect = render_image_rotated(card_dict, x, y + wobble, -90)
        else:
            rect = render_image(card_dict, x, y + wobble)
        creature_hitboxes.append({"id": card_id, "rect": rect, "owner": player, "card": card_dict, "zone": "creatures"})
        creature_rects[str(card_id)] = rect
        if animate and selected_blocker_id == card_id:
            pygame.draw.rect(screen, (100, 200, 255), rect.inflate(6, 6), 2)
        x += rect.width + CARD_SPACING


def render_active_creature_deck(
    game_state,
    player,
    y,
    align="center",
    filter_fn=None,
    attack_ids=None,
    attack_offset=0,
    animate=False,
    alert=False,
    alert_ids=None,
):
    global creature_hitboxes, active_creature_hitboxes, active_creature_rects
    active_creature_hitboxes = []
    creatures = list(game_state[player]["creatures"].items())
    if filter_fn:
        creatures = [(cid, cdata) for cid, cdata in creatures if filter_fn(cdata)]
    if not creatures:
        return
    if attack_ids is None:
        attack_ids = set()
    else:
        attack_ids = set(str(cid) for cid in attack_ids)
    if alert_ids is None:
        alert_ids = set()
    else:
        alert_ids = set(str(cid) for cid in alert_ids)

    placeholder = load_pil_image(PLACEHOLDER_PATH)
    card_width = max(1, int(placeholder.width * CARD_SCALE))
    card_height = max(1, int(placeholder.height * CARD_SCALE))
    card_step = max(18, int(card_width * 0.4))
    total_width = card_width + card_step * (len(creatures) - 1)

    if align == "right":
        x = max(HAND_MARGIN, WIDTH - HAND_MARGIN - total_width)
    elif align == "center":
        x = max(HAND_MARGIN, (WIDTH - total_width) // 2)
    else:
        x = HAND_MARGIN

    draw_queue = []
    for card_id, creature_entry in creatures:
        card_dict = creature_entry.get("card", {})
        draw_queue.append((card_id, card_dict, x))
        x += card_step

    extra_offset = max(8, int(card_height * 0.2)) if alert else 0

    for card_id, card_dict, card_x in draw_queue:
        if card_id in (hovered_card_id, active_selected_card_id):
            continue
        y_offset = attack_offset if str(card_id) in attack_ids else 0
        anim_bob = 0
        if animate:
            anim_bob = int(math.sin((pygame.time.get_ticks() + card_x) / 240) * 2)
        rect = render_image(card_dict, card_x, y + y_offset + anim_bob + extra_offset)
        hit = {"id": card_id, "rect": rect, "owner": player, "card": card_dict, "zone": "active"}
        active_creature_hitboxes.append(hit)
        creature_hitboxes.append(hit)
        active_creature_rects[str(card_id)] = rect
        if alert and str(card_id) in alert_ids:
            draw_pulse_outline(rect, (200, 60, 60), (255, 120, 120))

    for card_id, card_dict, card_x in draw_queue:
        if card_id != hovered_card_id or card_id == active_selected_card_id:
            continue
        y_offset = attack_offset if str(card_id) in attack_ids else 0
        wobble = int(math.sin(pygame.time.get_ticks() / 140) * 3) if animate else 0
        rect = render_image(card_dict, card_x, y - max(12, card_height // 8) + y_offset + wobble + extra_offset)
        hit = {"id": card_id, "rect": rect, "owner": player, "card": card_dict, "zone": "active"}
        active_creature_hitboxes.append(hit)
        creature_hitboxes.append(hit)
        active_creature_rects[str(card_id)] = rect
        if animate:
            draw_pulse_outline(rect, (255, 255, 255), (120, 200, 255))
        if alert and str(card_id) in alert_ids:
            draw_pulse_outline(rect, (200, 60, 60), (255, 120, 120))

    for card_id, card_dict, card_x in draw_queue:
        if card_id != active_selected_card_id:
            continue
        y_offset = attack_offset if str(card_id) in attack_ids else 0
        wobble = int(math.sin(pygame.time.get_ticks() / 120) * 4) if animate else 0
        rect = render_image(card_dict, card_x, y - max(20, card_height // 6) + y_offset + wobble + extra_offset)
        hit = {"id": card_id, "rect": rect, "owner": player, "card": card_dict, "zone": "active"}
        active_creature_hitboxes.append(hit)
        creature_hitboxes.append(hit)
        active_creature_rects[str(card_id)] = rect
        if animate:
            draw_pulse_outline(rect, (255, 215, 0), (255, 255, 255))
        if alert and str(card_id) in alert_ids:
            draw_pulse_outline(rect, (200, 60, 60), (255, 120, 120))


def render_land_row(game_state, player, y, align="left"):
    global land_hitboxes
    lands = list(game_state[player]["lands"].items())
    if not lands:
        return

    placeholder = load_pil_image(PLACEHOLDER_PATH)
    card_width = max(1, int(placeholder.width * CARD_SCALE))
    card_height = max(1, int(placeholder.height * CARD_SCALE))
    land_step = max(18, int(card_width * 0.4))
    total_width = card_width + land_step * (len(lands) - 1)

    if align == "right":
        x = max(HAND_MARGIN, WIDTH - HAND_MARGIN - total_width)
    elif align == "center":
        x = max(HAND_MARGIN, (WIDTH - total_width) // 2)
    else:
        x = HAND_MARGIN

    draw_queue = []
    for card_id, land_entry in lands:
        card_dict = land_entry.get("card", {})
        draw_queue.append((card_id, land_entry, card_dict, x))
        x += land_step

    for card_id, land_entry, card_dict, land_x in draw_queue:
        if card_id == hovered_card_id:
            continue
        tapped = land_entry.get("tapped", card_dict.get("tapped", False))
        rect = render_land_image(card_dict, land_x, y, tapped=bool(tapped))
        land_hitboxes.append({"id": card_id, "rect": rect, "owner": player, "card": card_dict, "zone": "lands"})

    for card_id, land_entry, card_dict, land_x in draw_queue:
        if card_id != hovered_card_id:
            continue
        tapped = land_entry.get("tapped", card_dict.get("tapped", False))
        rect = render_land_image(card_dict, land_x, y - max(12, card_height // 8), tapped=bool(tapped))
        land_hitboxes.append({"id": card_id, "rect": rect, "owner": player, "card": card_dict, "zone": "lands"})


def render_enemy_hand(game_state, player, y, align="center"):
    enemy = wiz.p2 if player == wiz.p1 else wiz.p1
    hand = list(game_state[enemy]["hand"].items())
    if not hand:
        return

    placeholder = load_pil_image(PLACEHOLDER_PATH)
    card_width = max(1, int(placeholder.width * CARD_SCALE))
    total_width = (card_width * len(hand)) + CARD_SPACING * (len(hand) - 1)

    if align == "right":
        x = max(HAND_MARGIN, WIDTH - HAND_MARGIN - total_width)
    elif align == "center":
        x = max(HAND_MARGIN, (WIDTH - total_width) // 2)
    else:
        x = HAND_MARGIN

    for _, card_dict in hand:
        rect = render_image(card_dict, x, y)
        x += rect.width + CARD_SPACING


def render_graveyard_row(game_state, player, y, align="right"):
    graveyard = list(game_state[player].get("graveyard", []))[-7:]
    if not graveyard:
        return

    placeholder = load_pil_image(PLACEHOLDER_PATH)
    card_width = max(1, int(placeholder.width * CARD_SCALE))
    card_height = max(1, int(placeholder.height * CARD_SCALE))
    step = max(18, int(card_width * 0.4))

    if align == "right":
        x = WIDTH - HAND_MARGIN - card_width
    elif align == "center":
        x = max(HAND_MARGIN, (WIDTH - card_width) // 2)
    else:
        x = HAND_MARGIN

    for card_dict in reversed(graveyard):
        rect = render_image(card_dict, x, y)
        x -= step


def draw_label(text, x, y, align="left", key=None, draw_bg=True):
    label_surface = label_font.render(text, True, (240, 240, 240))
    rect = label_surface.get_rect()
    if align == "center":
        rect.midtop = (x, y)
    elif align == "right":
        rect.topright = (x, y)
    else:
        rect.topleft = (x, y)
    pad = 4
    if draw_bg:
        bg = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        screen.blit(bg, (rect.x - pad, rect.y - pad))
    screen.blit(label_surface, rect)
    if key:
        label_rects[key] = pygame.Rect(rect.x - pad, rect.y - pad, rect.width + pad * 2, rect.height + pad * 2)


def render_zone_labels():
    for text, x, y, align, key, draw_bg in label_draw_queue:
        draw_label(text, x, y, align=align, key=key, draw_bg=draw_bg)


def draw_pulse_outline(rect, color_a, color_b, width=2):
    if not rect:
        return
    pulse = (pygame.time.get_ticks() // 200) % 2
    color = color_a if pulse else color_b
    pygame.draw.rect(screen, color, rect.inflate(6, 6), width)


def get_deck_layout():
    placeholder = load_pil_image(PLACEHOLDER_PATH)
    card_width = max(1, int(placeholder.width * CARD_SCALE))
    card_height = max(1, int(placeholder.height * CARD_SCALE))
    deck_x = HAND_MARGIN
    deck_y = HEIGHT - HAND_MARGIN
    hand_start_x = HAND_MARGIN
    return deck_x, deck_y, card_width, card_height, hand_start_x


def render_deck_pile(game_state, player, deck_x, deck_y, shift_x=0):
    deck = game_state.get(player, {}).get("deck", [])
    if not deck:
        return
    draw_count = min(3, len(deck))
    for i in range(draw_count - 1, -1, -1):
        offset = i * 3
        rect = render_image({"image_path": PLACEHOLDER_PATH}, deck_x + shift_x + offset, deck_y - offset)
        pygame.draw.rect(screen, (30, 30, 30), rect, 1)


def detect_draw_animation(game_state, player):
    if not player:
        return
    hand = game_state.get(player, {}).get("hand", {})
    current_ids = set(hand.keys())
    prev_ids = prev_hand_ids.get(player)
    if prev_ids is None:
        prev_hand_ids[player] = current_ids
        return
    new_ids = list(current_ids - prev_ids)
    if new_ids:
        for card_id in new_ids:
            draw_animation["queue"].append(
                {
                    "player": player,
                    "card_id": card_id,
                    "card": hand.get(card_id),
                }
            )

    if draw_animation.get("queue") and not draw_animation.get("active"):
        next_draw = draw_animation["queue"].pop(0)
        card_id = next_draw.get("card_id")
        card_dict = next_draw.get("card")
        last_drawn_id[player] = card_id
        deck_x, deck_y, _, _, _ = get_deck_layout()
        draw_animation.update(
            {
                "active": True,
                "card_id": card_id,
                "card": card_dict,
                "start": (deck_x, deck_y),
                "end": None,
                "start_ms": pygame.time.get_ticks(),
                "player": player,
            }
        )
    prev_hand_ids[player] = current_ids


def render_draw_animation():
    if not draw_animation.get("active"):
        return
    start = draw_animation.get("start")
    end = draw_animation.get("end")
    card = draw_animation.get("card")
    if not start or not end or not card:
        return
    now = pygame.time.get_ticks()
    elapsed = now - draw_animation.get("start_ms", 0)
    duration = max(1, draw_animation.get("duration_ms", 450))
    t = min(1.0, elapsed / duration)
    ease = t * (2 - t)
    x = int(start[0] + (end[0] - start[0]) * ease)
    y = int(start[1] + (end[1] - start[1]) * ease)
    render_image(card, x, y)
    if t >= 1.0:
        draw_animation["active"] = False
        if draw_animation.get("queue"):
            next_draw = draw_animation["queue"].pop(0)
            card_id = next_draw.get("card_id")
            card_dict = next_draw.get("card")
            last_drawn_id[next_draw.get("player")] = card_id
            deck_x, deck_y, _, _, _ = get_deck_layout()
            draw_animation.update(
                {
                    "active": True,
                    "card_id": card_id,
                    "card": card_dict,
                    "start": (deck_x, deck_y),
                    "end": None,
                    "start_ms": pygame.time.get_ticks(),
                    "player": next_draw.get("player"),
                }
            )


def add_notification(message):
    message = str(message or "").strip()
    if not message:
        return
    notifications.insert(0, message)
    del notifications[5:]


def render_notifications():
    if not notifications:
        return
    x = HAND_MARGIN
    y = HAND_MARGIN
    for message in notifications[:3]:
        draw_label(message, x, y, align="left", draw_bg=True)
        y += label_font.get_linesize() + 12


def parse_spell_effects(card_dict):
    try:
        parser = EffectParser()
        return parser.parse(card_dict.get("effect", ""))
    except Exception:
        return []


def get_spell_targeting(card_dict):
    effects = parse_spell_effects(card_dict)
    needs_creature = False
    needs_player = False
    actions = set()
    for effect in effects:
        actions.add(effect.get("action"))
        target_type = effect.get("target_type")
        if effect.get("creatureid"):
            needs_creature = True
        if target_type:
            if isinstance(target_type, list):
                if "creature" in target_type:
                    needs_creature = True
                if "player" in target_type:
                    needs_player = True
            elif target_type == "creature":
                needs_creature = True
            elif target_type == "player":
                needs_player = True
    scope = "any"
    if "heal" in actions:
        scope = "friendly"
    elif "damage" in actions:
        scope = "enemy_active"
    return {
        "needs_creature": needs_creature,
        "needs_player": needs_player,
        "scope": scope,
    }


def get_discard_value(card_dict):
    effects = parse_spell_effects(card_dict)
    for effect in effects:
        if effect.get("action") == "discard":
            return int(effect.get("value", 1) or 1)
    return None


def get_status_list(card_dict):
    status_text = str(card_dict.get("status", "") or "")
    statuses = [s.strip() for s in status_text.split(",") if s.strip()]
    effect_text = str(card_dict.get("effect", "") or "")
    if effect_text:
        parser = EffectParser()
        for effect in parser.parse(effect_text):
            if effect.get("action") == "static":
                status = effect.get("status")
                if status:
                    statuses.append(status)
    seen = set()
    deduped = []
    for status in statuses:
        if status not in seen:
            seen.add(status)
            deduped.append(status)
    return deduped


def has_invuln_status(card_dict):
    statuses = [s.lower() for s in get_status_list(card_dict)]
    return "invuln" in statuses


def format_stat_value(value, is_invuln=False):
    if is_invuln:
        return "inf"
    if value is None:
        return "-"
    return str(value)


def format_card_stats(card_dict):
    attack = card_dict.get("attack")
    defence = card_dict.get("defence")
    return (
        format_stat_value(attack),
        format_stat_value(defence, is_invuln=has_invuln_status(card_dict)),
    )


def format_defence_after(card_dict, defence_value):
    if has_invuln_status(card_dict):
        return "inf"
    if defence_value is None:
        return "-"
    return str(defence_value)


def tap_all_lands(game_state, player):
    if player != wiz.current_player():
        popup("Only the active player can tap lands")
        return False
    lands = game_state.get(player, {}).get("lands", {})
    if not lands:
        popup("No lands to tap")
        return False
    tapped_any = False
    for land_id, land_entry in lands.items():
        land_card = land_entry.get("card", {})
        tapped = land_entry.get("tapped", land_card.get("tapped", False))
        if tapped:
            continue
        colors = get_land_colors(land_card.get("effect", ""))
        choice = colors[0] if colors else None
        if wiz.tap_land(land_id, choice, player=player):
            tapped_any = True
            color_text = choice if choice else "mana"
            add_notification(f"{player} tapped {land_card.get('name', 'a land')} for {color_text}")
    if not tapped_any:
        popup("All lands are already tapped")
        return False
    return True


def can_show_mulligan(game_state, player):
    current_player = game_state.get("current_player")
    turn_number = game_state.get("turn_number", 1)
    allowed_turn = (player == wiz.p1 and turn_number == 1) or (player == wiz.p2 and turn_number == 2)
    if not allowed_turn:
        return False
    if player != current_player:
        return False
    if wiz.card_played_this_turn > 0:
        return False
    return True


def activate_pending_discard(state):
    pending_discard = state.get("pending_discard")
    if not pending_discard or discard_state.get("active"):
        return
    discard_state["active"] = True
    discard_state["player"] = pending_discard.get("player")
    discard_state["required"] = pending_discard.get("count", 0)
    discard_state["discarded"] = 0
    discard_state["return_player"] = pending_discard.get("requester")
    wiz.priority_player = pending_discard.get("player")
    target_player = pending_discard.get("player")
    required = pending_discard.get("count", 0)
    announce(f"{target_player} must discard {required} card(s)")
    add_notification(f"{target_player} must discard {required} card(s)")


def check_game_over(state):
    if game_over_state.get("active"):
        return True
    p1_health = state.get(wiz.p1, {}).get("health", 0)
    p2_health = state.get(wiz.p2, {}).get("health", 0)
    if p1_health > 0 and p2_health > 0:
        return False
    loser = wiz.p1 if p1_health <= 0 else wiz.p2
    winner = wiz.p2 if loser == wiz.p1 else wiz.p1
    game_over_state.update({"active": True, "winner": winner, "loser": loser})
    add_notification(f"GAME OVER - {winner} wins")
    announce(f"GAME OVER - {winner} wins", duration_ms=9999999)
    return True


def clear_pending_discard():
    state = wiz.game.get_game_state()
    if "pending_discard" in state:
        del state["pending_discard"]
        wiz.game._save_state(state)


def detect_creature_stat_changes(game_state):
    global prev_creature_stats, prev_creature_status
    current = {}
    current_status = {}
    changed = False
    for player in (wiz.p1, wiz.p2):
        creatures = game_state.get(player, {}).get("creatures", {})
        for cid, cdata in creatures.items():
            card = cdata.get("card", {})
            attack = card.get("attack")
            defence = card.get("defence")
            current[(player, str(cid))] = (attack, defence)
            current_status[(player, str(cid))] = ", ".join(get_status_list(card))

    for key, stats in current.items():
        prev = prev_creature_stats.get(key)
        if prev and stats:
            prev_att, prev_def = prev
            new_att, new_def = stats
            if new_att is not None and prev_att is not None and new_att != prev_att:
                player, cid = key
                name = game_state[player]["creatures"].get(cid, {}).get("card", {}).get("name", cid)
                delta = new_att - prev_att
                verb = "gains" if delta > 0 else "loses"
                add_notification(f"{name} {verb} {abs(delta)} attack")
                card_dict = game_state[player]["creatures"][cid]["card"]
                base_path = card_dict.get("image_path")
                if base_path and os.path.exists(base_path):
                    update_card_stats(wiz.game._reconstruct_card(card_dict), base_path, base_path)
                    changed = True
            if new_def is not None and prev_def is not None and new_def != prev_def:
                player, cid = key
                name = game_state[player]["creatures"].get(cid, {}).get("card", {}).get("name", cid)
                delta = new_def - prev_def
                verb = "gains" if delta > 0 else "loses"
                add_notification(f"{name} {verb} {abs(delta)} defence")
                card_dict = game_state[player]["creatures"][cid]["card"]
                base_path = card_dict.get("image_path")
                if base_path and os.path.exists(base_path):
                    update_card_stats(wiz.game._reconstruct_card(card_dict), base_path, base_path)
                    changed = True
        prev_status = prev_creature_status.get(key)
        new_status = current_status.get(key)
        if prev_status is not None and new_status is not None and prev_status != new_status:
            player, cid = key
            name = game_state[player]["creatures"].get(cid, {}).get("card", {}).get("name", cid)
            status_label = new_status if new_status else "no status"
            add_notification(f"{name} status: {status_label}")
            if hover_label_state.get("visible") and str(hovered_card_id) == str(cid):
                card_dict = game_state[player]["creatures"][cid]["card"]
                hover_label_state["lines"] = build_hover_label_lines(card_dict)

    prev_creature_stats = current
    prev_creature_status = current_status
    if changed:
        wiz.game._save_state(game_state)


def build_combat_summary_lines(pre_state, damage_queue):
    lines = []
    attacker_player = pre_state.get("current_player")
    defender_player = wiz.p2 if attacker_player == wiz.p1 else wiz.p1
    attackers = pre_state.get("combat", {}).get("attackers", [])
    blocks = pre_state.get("combat", {}).get("blocks", {})

    damage_to = {}
    player_damage = {}
    direct_damage_by_attacker = {}
    for entry in damage_queue:
        if entry.get("target") == "creature":
            key = (entry.get("target_player"), str(entry.get("target_id")))
            damage_to[key] = damage_to.get(key, 0) + entry.get("damage", 0)
        elif entry.get("target") == "player":
            target_player = entry.get("target_player")
            player_damage[target_player] = player_damage.get(target_player, 0) + entry.get("damage", 0)
            source_id = entry.get("source_id")
            if source_id is not None:
                direct_damage_by_attacker[str(source_id)] = direct_damage_by_attacker.get(str(source_id), 0) + entry.get("damage", 0)

    for attacker_id in attackers:
        blocker_ids = blocks.get(attacker_id, [])
        if not blocker_ids:
            attacker_entry = pre_state.get(attacker_player, {}).get("creatures", {}).get(str(attacker_id), {})
            attacker_card = attacker_entry.get("card", {})
            attacker_name = attacker_card.get("name", str(attacker_id))
            attacker_att, attacker_end = format_card_stats(attacker_card)
            direct_damage = direct_damage_by_attacker.get(str(attacker_id), 0)
            if direct_damage:
                lines.append(
                    f"{attacker_name} ({attacker_att}/{attacker_end}) -> "
                    f"{defender_player} takes {direct_damage}"
                )
            continue
        attacker_entry = pre_state.get(attacker_player, {}).get("creatures", {}).get(str(attacker_id), {})
        attacker_card = attacker_entry.get("card", {})
        attacker_name = attacker_card.get("name", str(attacker_id))
        attacker_att, attacker_end = format_card_stats(attacker_card)
        attacker_stats = (attacker_att, attacker_end)
        attacker_damage = damage_to.get((attacker_player, str(attacker_id)), 0)
        attacker_dead = (
            attacker_card.get("defence") is not None
            and attacker_card.get("defence") - attacker_damage <= 0
        )

        for blocker_id in blocker_ids:
            blocker_entry = pre_state.get(defender_player, {}).get("creatures", {}).get(str(blocker_id), {})
            blocker_card = blocker_entry.get("card", {})
            blocker_name = blocker_card.get("name", str(blocker_id))
            blocker_att, blocker_end = format_card_stats(blocker_card)
            blocker_stats = (blocker_att, blocker_end)
            blocker_damage = damage_to.get((defender_player, str(blocker_id)), 0)
            blocker_dead = (
                blocker_card.get("defence") is not None
                and blocker_card.get("defence") - blocker_damage <= 0
            )

            attacker_def_after = (
                attacker_card.get("defence") - attacker_damage
                if attacker_card.get("defence") is not None
                else attacker_card.get("defence")
            )
            blocker_def_after = (
                blocker_card.get("defence") - blocker_damage
                if blocker_card.get("defence") is not None
                else blocker_card.get("defence")
            )
            attacker_def_display = format_defence_after(attacker_card, attacker_def_after)
            blocker_def_display = format_defence_after(blocker_card, blocker_def_after)

            if attacker_dead and blocker_dead:
                outcome = "both die"
            elif blocker_dead:
                outcome = f"{blocker_name} dies"
            elif attacker_dead:
                outcome = f"{attacker_name} dies"
            else:
                outcome = "no deaths"

            lines.append(
                f"{attacker_name} ({attacker_stats[0]}/{attacker_stats[1]}) vs "
                f"{blocker_name} ({blocker_stats[0]}/{blocker_stats[1]}) | "
                f"took {attacker_damage}/{blocker_damage} | "
                f"end {attacker_def_display}/{blocker_def_display} ({outcome})"
            )

    for player_name, damage in player_damage.items():
        start_health = pre_state.get(player_name, {}).get("health", 0)
        end_health = max(0, start_health - damage)
        lines.append(f"{player_name} loses {damage} health ({start_health} -> {end_health})")

    if not lines:
        lines.append("No combat damage this turn.")

    return lines


def build_hover_label_lines(card_dict):
    description = str(card_dict.get("description", "") or "")
    parts = description.split("|", 1)
    rules_text = parts[0].strip()
    flavor_text = parts[1].strip() if len(parts) > 1 else ""

    max_width = int(WIDTH * 0.35)
    lines = []
    if rules_text:
        lines.extend(wrap_text(rules_text, label_font, max_width))
    else:
        name = str(card_dict.get("name", "") or "").strip()
        if name:
            lines.append(name)
    lines.append("------")
    if flavor_text:
        lines.extend(wrap_text(flavor_text, label_font, max_width))
    else:
        lines.append("N/A")

    lines.append("")
    generic = card_dict.get("generic_mana", 0)
    sp_mana = str(card_dict.get("sp_mana", "") or "").strip()
    sp_display = sp_mana if sp_mana else "none"
    lines.append(f"cost: {generic} + {sp_display}")

    att, end = format_card_stats(card_dict)
    if "attack" in card_dict and card_dict.get("attack") is not None:
        lines.append(f"att: {att}")
    if "defence" in card_dict and card_dict.get("defence") is not None:
        lines.append(f"end: {end}")
    statuses = get_status_list(card_dict)
    if statuses:
        lines.append(f"status: {', '.join(statuses)}")

    return lines


def render_hover_label():
    if not hover_label_state.get("visible"):
        return
    lines = hover_label_state.get("lines", [])
    if not lines:
        return

    line_height = label_font.get_linesize()
    text_width = max(label_font.size(line)[0] for line in lines)
    pad = 6
    width = text_width + pad * 2
    height = line_height * len(lines) + pad * 2

    anchor_rect = hover_label_state.get("anchor_rect")
    if anchor_rect:
        x = anchor_rect.right + 8
        y = anchor_rect.top
    else:
        x, y = pygame.mouse.get_pos()

    if x + width > WIDTH - HAND_MARGIN:
        if anchor_rect:
            x = anchor_rect.left - width - 8
        else:
            x = WIDTH - HAND_MARGIN - width
    if y + height > HEIGHT - HAND_MARGIN:
        y = HEIGHT - HAND_MARGIN - height
    x = max(HAND_MARGIN, x)
    y = max(HAND_MARGIN, y)

    bg = pygame.Surface((width, height), pygame.SRCALPHA)
    bg.fill((20, 20, 20, 210))
    screen.blit(bg, (x, y))
    # pygame.draw.rect(screen, (220, 220, 220), pygame.Rect(x, y, width, height), 1)

    text_x = x + pad
    text_y = y + pad
    for line in lines:
        text_surface = label_font.render(line, True, (245, 245, 245))
        screen.blit(text_surface, (text_x, text_y))
        text_y += line_height


def get_combat_attacker():
    return getattr(wiz, "combat_attacker", None)


def get_combat_defender():
    return getattr(wiz, "combat_defender", None)


def get_attacker_ids(game_state):
    if getattr(wiz, "combat_phase", None) == "attackers":
        return list(getattr(wiz, "pending_attackers", []))
    if getattr(wiz, "combat_phase", None) == "blockers":
        attackers = game_state.get("combat", {}).get("attackers", [])
        if attackers:
            return attackers
        return list(getattr(wiz, "pending_attackers", []))
    return []


def get_combat_button_labels(game_state, player, action_label_y, label_height):
    buttons = []
    y = action_label_y + label_height + 8
    confirm_x = WIDTH - HAND_MARGIN - 220

    if getattr(wiz, "combat_phase", None) == "attackers" and getattr(wiz, "priority_player", None) == player:
        if getattr(wiz, "pending_attackers", []):
            buttons.append(("Confirm", confirm_x, y, "combat_confirm"))
    elif getattr(wiz, "combat_phase", None) == "blockers" and getattr(wiz, "priority_player", None) == player:
        buttons.append(("Confirm", confirm_x, y, "combat_confirm"))
    return buttons


def build_attackers_preview_lines(game_state, attacker_ids):
    lines = ["Attackers:"]
    creatures = game_state.get(get_combat_attacker() or "", {}).get("creatures", {})
    if not attacker_ids:
        lines.append("(none)")
    else:
        for cid in attacker_ids:
            card = creatures.get(str(cid), {}).get("card", {})
            name = card.get("name", str(cid))
            att, end = format_card_stats(card)
            statuses = get_status_list(card)
            status_text = f" [{', '.join(statuses)}]" if statuses else ""
            lines.append(f"- {name} ({att}/{end}){status_text}")
    return lines


def build_blockers_preview_lines(game_state, block_assignments):
    lines = ["Blocks:"]
    defender = get_combat_defender()
    attacker = get_combat_attacker()
    defender_creatures = game_state.get(defender or "", {}).get("creatures", {})
    attacker_creatures = game_state.get(attacker or "", {}).get("creatures", {})
    if not block_assignments:
        lines.append("No defenders declared.")
    else:
        for attacker_id, blocker_ids in block_assignments.items():
            atk_card = attacker_creatures.get(str(attacker_id), {}).get("card", {})
            atk_name = atk_card.get("name", str(attacker_id))
            atk_att, atk_end = format_card_stats(atk_card)
            for blocker_id in blocker_ids:
                blk_card = defender_creatures.get(str(blocker_id), {}).get("card", {})
                blk_name = blk_card.get("name", str(blocker_id))
                blk_att, blk_end = format_card_stats(blk_card)
                lines.append(
                    f"- {blk_name} ({blk_att}/{blk_end}) -> {atk_name} ({atk_att}/{atk_end})"
                )
    return lines


def show_combat_prompt(mode, lines):
    combat_prompt_state.update(
        {
            "visible": True,
            "mode": mode,
            "lines": lines,
            "rect": None,
            "confirm_rect": None,
            "cancel_rect": None,
        }
    )


def render_combat_prompt():
    if not combat_prompt_state.get("visible"):
        return

    lines = combat_prompt_state.get("lines", [])
    if not lines:
        return

    font = get_popup_font(18)
    line_height = font.get_linesize()
    text_width = max(font.size(line)[0] for line in lines)
    text_height = line_height * len(lines)
    pad = 12

    rect_width = min(int(WIDTH * 0.7), text_width + pad * 2 + 20)
    rect_height = min(int(HEIGHT * 0.5), text_height + pad * 2 + 36)
    rect = pygame.Rect(0, 0, rect_width, rect_height)
    rect.center = (WIDTH // 2, HEIGHT // 2)

    bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 190))
    screen.blit(bg, rect.topleft)

    text_x = rect.left + pad
    text_y = rect.top + pad
    for line in lines:
        text_surface = font.render(line, True, (245, 245, 245))
        screen.blit(text_surface, (text_x, text_y))
        text_y += line_height

    button_w = 90
    button_h = 24
    confirm_rect = pygame.Rect(rect.right - pad - button_w, rect.bottom - pad - button_h, button_w, button_h)
    pygame.draw.rect(screen, (40, 120, 40), confirm_rect, 0)
    pygame.draw.rect(screen, (220, 220, 220), confirm_rect, 1)
    confirm_text = menu_font.render("Confirm", True, (255, 255, 255))
    confirm_text_rect = confirm_text.get_rect(center=confirm_rect.center)
    screen.blit(confirm_text, confirm_text_rect)

    cancel_rect = pygame.Rect(confirm_rect.left - button_w - 8, confirm_rect.top, button_w, button_h)
    pygame.draw.rect(screen, (120, 40, 40), cancel_rect, 0)
    pygame.draw.rect(screen, (220, 220, 220), cancel_rect, 1)
    cancel_text = menu_font.render("Cancel", True, (255, 255, 255))
    cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
    screen.blit(cancel_text, cancel_text_rect)

    combat_prompt_state["rect"] = rect
    combat_prompt_state["confirm_rect"] = confirm_rect
    combat_prompt_state["cancel_rect"] = cancel_rect


def render_combat_lines(game_state):
    if getattr(wiz, "combat_phase", None) != "blockers":
        if attacker_select_id:
            rect = creature_rects.get(str(attacker_select_id))
            if rect:
                pygame.draw.rect(screen, (255, 215, 0), rect.inflate(6, 6), 2)
        return

    attacker_ids = set(str(cid) for cid in get_attacker_ids(game_state))
    pending_blocks = getattr(wiz, "pending_blocks", {})

    for attacker_id, blocker_ids in pending_blocks.items():
        attacker_rect = active_creature_rects.get(str(attacker_id)) or creature_rects.get(str(attacker_id))
        if not attacker_rect:
            continue
        for blocker_id in blocker_ids:
            blocker_rect = creature_rects.get(str(blocker_id))
            if not blocker_rect:
                continue
            start = blocker_rect.center
            end = attacker_rect.midbottom
            pygame.draw.line(screen, (60, 200, 60), start, end, 3)

    if selected_blocker_id:
        attacker_rect = None
        if hovered_card_id and str(hovered_card_id) in attacker_ids:
            attacker_rect = active_creature_rects.get(str(hovered_card_id))
        if attacker_rect:
            blocker_rect = creature_rects.get(str(selected_blocker_id))
            if blocker_rect:
                pygame.draw.line(screen, (255, 255, 255), blocker_rect.center, attacker_rect.midbottom, 2)
        else:
            blocker_rect = creature_rects.get(str(selected_blocker_id))
            if blocker_rect:
                pygame.draw.line(screen, (255, 255, 255), blocker_rect.center, pygame.mouse.get_pos(), 1)
                pygame.draw.rect(screen, (100, 200, 255), blocker_rect.inflate(6, 6), 2)

    if attacker_select_id:
        rect = creature_rects.get(str(attacker_select_id))
        if rect:
            pygame.draw.rect(screen, (255, 215, 0), rect.inflate(6, 6), 2)


def clear_blockers_ui():
    global selected_blocker_id, attacker_select_id
    selected_blocker_id = None
    attacker_select_id = None
    if getattr(wiz, "combat_phase", None) == "blockers":
        defender = get_combat_defender() or wiz.current_player()
        wiz.pending_blocks = {}
        wiz.queue_blockers(defender, {})
        add_notification("Blockers cleared")
        announce("Blockers cleared")


def reset_combat_ui():
    global selected_blocker_id, attacker_select_id
    selected_blocker_id = None
    attacker_select_id = None
    if getattr(wiz, "combat_phase", None):
        wiz.cancel_combat()
        game_state = wiz.game.get_game_state()
        attacker = get_combat_attacker()
        attackers = game_state.get("combat", {}).get("attackers", [])
        if attacker and attackers:
            creatures = game_state.get(attacker, {}).get("creatures", {})

            def remove_status(card, status):
                existing = str(card.get("status", "") or "")
                statuses = [s.strip() for s in existing.split(",") if s.strip()]
                if status in statuses:
                    statuses = [s for s in statuses if s != status]
                    card["status"] = ", ".join(statuses)

            for cid in attackers:
                entry = creatures.get(str(cid))
                if not entry:
                    continue
                card = entry.get("card", {})
                if card.get("tapped"):
                    card["tapped"] = 0
                remove_status(card, "attack")
            wiz.game._save_state(game_state)
    combat_prompt_state["visible"] = False
    # add_notification("Combat cancelled")


def start_new_turn_ui():
    global HAS_PLAYED_LAND, selected_card_id, active_selected_card_id
    HAS_PLAYED_LAND = False
    selected_card_id = None
    active_selected_card_id = None
    reset_combat_ui()
    wiz.start_new_turn()
    add_notification("Turn ended")
    announce(f"{wiz.current_player()}'s turn")


def toggle_attacker(game_state, player, creature_id):
    global attacker_select_id
    creature_id = str(creature_id)
    if getattr(wiz, "combat_phase", None) is None:
        wiz.begin_combat(player)
    if getattr(wiz, "combat_phase", None) != "attackers" or getattr(wiz, "priority_player", None) != player:
        return False
    if not wiz.game.can_attack(player, creature_id):
        popup("That creature cannot attack")
        return False
    pending = list(getattr(wiz, "pending_attackers", []))
    if creature_id in pending:
        pending.remove(creature_id)
        creature = game_state[player]["creatures"].get(creature_id, {}).get("card", {})
        att, end = format_card_stats(creature)
        add_notification(f"Attacker removed: {creature.get('name', creature_id)} ({att}/{end})")
        if attacker_select_id == creature_id:
            attacker_select_id = None
    else:
        pending.append(creature_id)
        creature = game_state[player]["creatures"].get(creature_id, {}).get("card", {})
        att, end = format_card_stats(creature)
        add_notification(f"Attacker queued: {creature.get('name', creature_id)} ({att}/{end})")
        attacker_select_id = creature_id
    wiz.queue_attackers(player, pending)
    if pending:
        add_notification(f"Attackers selected: {len(pending)}")
    else:
        attacker_select_id = None
    return True


def assign_blocker(game_state, defender, blocker_id, attacker_id):
    blocker_id = str(blocker_id)
    attacker_id = str(attacker_id)
    if getattr(wiz, "combat_phase", None) != "blockers" or getattr(wiz, "priority_player", None) != defender:
        return False
    attacker_ids = set(str(cid) for cid in get_attacker_ids(game_state))
    if attacker_id not in attacker_ids:
        popup("That creature is not attacking")
        return False

    defender_creatures = game_state[defender].get("creatures", {})
    if blocker_id not in defender_creatures:
        return False
    if not wiz.game.can_block(blocker_id, attacker_id):
        popup("That creature cannot block")
        return False

    new_blocks = {k: list(v) for k, v in getattr(wiz, "pending_blocks", {}).items()}
    for a_id in list(new_blocks.keys()):
        if blocker_id in new_blocks.get(a_id, []):
            new_blocks[a_id] = [b for b in new_blocks[a_id] if b != blocker_id]
            if not new_blocks[a_id]:
                new_blocks.pop(a_id, None)

    if attacker_id in new_blocks and blocker_id in new_blocks[attacker_id]:
        new_blocks[attacker_id] = [b for b in new_blocks[attacker_id] if b != blocker_id]
        if not new_blocks[attacker_id]:
            new_blocks.pop(attacker_id, None)
        blk_card = defender_creatures.get(blocker_id, {}).get("card", {})
        blk_att, blk_end = format_card_stats(blk_card)
        add_notification(f"Blocker removed: {blk_card.get('name', blocker_id)} ({blk_att}/{blk_end})")
    else:
        lst = new_blocks.get(attacker_id, [])
        lst.append(blocker_id)
        new_blocks[attacker_id] = lst
        blk_card = defender_creatures.get(blocker_id, {}).get("card", {})
        atk_card = game_state.get(get_combat_attacker() or "", {}).get("creatures", {}).get(attacker_id, {}).get("card", {})
        blk_att, blk_end = format_card_stats(blk_card)
        atk_att, atk_end = format_card_stats(atk_card)
        add_notification(
            f"Blocker queued: {blk_card.get('name', blocker_id)} ({blk_att}/{blk_end}) -> "
            f"{atk_card.get('name', attacker_id)} ({atk_att}/{atk_end})"
        )

    wiz.queue_blockers(defender, new_blocks)
    return True


def confirm_attackers(game_state):
    global attacker_select_id
    attacker = get_combat_attacker() or wiz.current_player()
    pending = list(getattr(wiz, "pending_attackers", []))
    if not pending:
        return False
    if getattr(wiz, "combat_phase", None) != "attackers":
        return False
    wiz.game.declare_attackers(attacker, pending)
    wiz.pending_attackers = []
    wiz.pass_priority_to_blocker()
    add_notification(f"{attacker} confirms {len(pending)} attacker(s)")
    # announce(f"{get_combat_defender()} assign blockers")
    attacker_select_id = None
    return True


def confirm_blockers(game_state):
    defender = get_combat_defender() or wiz.current_player()
    pending = getattr(wiz, "pending_blocks", {})
    if getattr(wiz, "combat_phase", None) != "blockers":
        return False
    wiz.game.declare_blockers(defender, pending)
    total_blocks = sum(len(v) for v in pending.values())
    add_notification(f"{defender} confirms {total_blocks} blocker(s)")
    wiz.pending_blocks = {}
    attacker = get_combat_attacker()
    pre_state = wiz.game.get_game_state()
    wiz.game.calculate_combat_damage()
    state_with_queue = wiz.game.get_game_state()
    damage_queue = state_with_queue.get("combat", {}).get("damage_queue", [])
    summary_lines = build_combat_summary_lines(pre_state, damage_queue)
    wiz.game.resolve_damage_queue()
    state = wiz.game.get_game_state()

    wiz.combat_phase = None
    wiz.priority_player = None
    wiz.pending_attackers = []
    wiz.pending_blocks = {}
    wiz.combat_attacker = None
    wiz.combat_defender = None

    won = state.get(wiz.p1, {}).get("health", 0) <= 0 or state.get(wiz.p2, {}).get("health", 0) <= 0
    loser = wiz.p1 if state.get(wiz.p1, {}).get("health", 0) <= 0 else wiz.p2 if state.get(wiz.p2, {}).get("health", 0) <= 0 else ""
    opposing = wiz.p2 if defender == wiz.p1 else wiz.p1
    wiz.priority_player = attacker or opposing
    add_notification("Combat resolved")
    popup("\n".join(summary_lines))
    if won:
        add_notification(f"{loser} lost the game")
    return True


def render_battlefield(game_state, player):
    global land_hitboxes, creature_hitboxes, label_rects, label_draw_queue, active_creature_hitboxes
    global creature_rects, active_creature_rects
    land_hitboxes = []
    creature_hitboxes = []
    active_creature_hitboxes = []
    creature_rects = {}
    active_creature_rects = {}
    label_rects = {}
    label_draw_queue = []

    enemy = wiz.p2 if player == wiz.p1 else wiz.p1
    placeholder = load_pil_image(PLACEHOLDER_PATH)
    card_height = max(1, int(placeholder.height * CARD_SCALE))
    row_gap = max(12, int(card_height * 0.2))
    label_height = label_font.get_linesize()
    label_gap = max(6, int(card_height * 0.1))

    def queue_zone_label(text, x, y, align="left", key=None, draw_bg=True):
        label_draw_queue.append((text, x, y, align, key, draw_bg))

    def is_active_creature(creature_entry):
        card = creature_entry.get("card", {})
        status = str(card.get("status", "")).lower()
        return bool(card.get("tapped")) or "attack" in status or "block" in status

    enemy_creatures = list(game_state[enemy]["creatures"].items())

    top_label_y = HAND_MARGIN + 200
    top_creatures_y = top_label_y + label_height + label_gap + card_height

    bottom_row_y = HEIGHT - HAND_MARGIN
    bottom_label_y = bottom_row_y - card_height - label_height - label_gap

    min_middle_label_y = top_creatures_y + row_gap
    max_middle_label_y = bottom_label_y - label_height - label_gap - card_height - row_gap
    middle_label_y = (top_creatures_y + bottom_label_y) // 2
    middle_label_y = max(min_middle_label_y, middle_label_y)
    middle_label_y = min(middle_label_y, max_middle_label_y if max_middle_label_y > min_middle_label_y else min_middle_label_y)
    middle_creatures_y = middle_label_y + label_height + label_gap + card_height

    bottom_hand_y = bottom_row_y
    bottom_lands_y = bottom_row_y
    bottom_creatures_y = bottom_row_y

    attacker_ids = get_attacker_ids(game_state)
    attack_offset = max(6, int(card_height * 0.15))
    enemy_alert = (
        getattr(wiz, "combat_phase", None) == "blockers"
        and getattr(wiz, "priority_player", None) == player
    )
    enemy_ready_ids = []
    if enemy_alert and enemy == get_combat_attacker():
        enemy_ready_ids = [str(cid) for cid in attacker_ids]
    if enemy_creatures:
        queue_zone_label("Enemy active creatures", WIDTH // 2, top_label_y, align="center", key="enemy_active")
        render_active_creature_deck(
            game_state,
            enemy,
            top_creatures_y,
            align="center",
            filter_fn=None,
            attack_ids=attacker_ids if enemy == get_combat_attacker() else [],
            attack_offset=attack_offset,
            animate=False,
            alert=enemy_alert,
            alert_ids=enemy_ready_ids,
        )

    creatures_label_y = middle_creatures_y - label_height - label_gap
    queue_zone_label("Creatures", HAND_MARGIN, creatures_label_y, align="left", key="creatures")
    render_creature_row(
        game_state,
        player,
        middle_creatures_y,
        align="left",
        attack_ids=attacker_ids if player == get_combat_attacker() else [],
        rotate_attackers=player == get_combat_attacker(),
        animate=True,
    )

    hand_label_y = bottom_hand_y - card_height - label_height - label_gap - 225
    lands_label_y = bottom_lands_y - card_height - label_height - label_gap - 225
    graveyard_label_y = bottom_creatures_y - card_height - label_height - label_gap - 225

    mana_label_y = lands_label_y - label_height - 20
    mana_gap = 12
    mana_texts = ["Green: " + str(game_state[player]["green_mana"]), "Blue: " + str(game_state[player]["blue_mana"]), "Red: " + str(game_state[player]["red_mana"])]
    mana_widths = [label_font.size(text)[0] for text in mana_texts]
    mana_total_width = sum(mana_widths) + mana_gap * (len(mana_texts) - 1)
    mana_start_x = (WIDTH - mana_total_width) // 2
    mana_x = mana_start_x
    for text, width in zip(mana_texts, mana_widths):
        queue_zone_label(text, mana_x, mana_label_y, align="left", key=f"mana_{text.lower()}", draw_bg=False)
        mana_x += width + mana_gap

    queue_zone_label("Hand", HAND_MARGIN, hand_label_y, align="left", key="hand")
    lands_x = WIDTH // 2
    queue_zone_label("Lands", lands_x, lands_label_y, align="center", key="lands")
    tap_all_x = lands_x + label_font.size("Lands")[0] // 2 + 14
    queue_zone_label("Tap All", tap_all_x, lands_label_y, align="left", key="tap_all_lands")
    queue_zone_label("Graveyard", WIDTH - HAND_MARGIN, graveyard_label_y, align="right", key="graveyard")

    action_label_y = bottom_row_y - card_height - label_height - label_gap - 10
    combat_buttons = get_combat_button_labels(game_state, player, action_label_y, label_height)
    if combat_buttons:
        for text, x, y, key in combat_buttons:
            queue_zone_label(text, x, y, align="right", key=key)
    if discard_state.get("active") and discard_state.get("player") == player:
        queue_zone_label("Confirm", WIDTH - HAND_MARGIN - 220, action_label_y + label_height + 8, align="right", key="discard_confirm")

    priority_name = wiz.priority_player or wiz.current_player()
    priority_health = game_state.get(priority_name, {}).get("health", 0)
    queue_zone_label(
        f"Priority: {priority_name} ({priority_health}/20)",
        WIDTH - HAND_MARGIN,
        HAND_MARGIN,
        align="right",
        key="priority",
    )

    if can_show_mulligan(game_state, player):
        queue_zone_label("Mulligan", WIDTH - HAND_MARGIN - 100, action_label_y + label_height + 8, align="right", key="mulligan")
    queue_zone_label(
        "End Turn",
        WIDTH - HAND_MARGIN,
        action_label_y + label_height + 8, # + label_height + 8,
        align="right",
        key="end_turn",
    )

    render_land_row(game_state, player, bottom_lands_y, align="center")
    render_graveyard_row(game_state, player, bottom_creatures_y, align="right")

def show_land_context_menu(land_entry, pos):
    global context_menu
    card_dict = land_entry.get("card", {})
    colors = get_land_colors(card_dict.get("effect", ""))

    options = []
    if len(colors) == 1:
        options.append((f"Tap {colors[0].title()}", colors[0]))
    elif len(colors) > 1:
        for color in colors:
            options.append((f"Tap {color.title()}", color))
    else:
        options.append(("Tap", None))

    menu_width = 160
    item_height = 22
    menu_height = item_height * len(options) + 8
    x, y = pos
    x = min(x, WIDTH - menu_width - HAND_MARGIN)
    y = min(y, HEIGHT - menu_height - HAND_MARGIN)

    rects = []
    actions = []
    for i, (label, color) in enumerate(options):
        rect = pygame.Rect(x + 6, y + 4 + i * item_height, menu_width - 12, item_height)
        rects.append((rect, label))
        actions.append(color)

    context_menu = {
        "visible": True,
        "rect": pygame.Rect(x, y, menu_width, menu_height),
        "rects": rects,
        "actions": actions,
        "land_id": land_entry.get("id"),
        "kind": "land",
    }


def show_hand_context_menu(card_entry, pos):
    global context_menu
    menu_width = 160
    item_height = 22
    options = [("Discard", "discard")]
    if card_entry.get("type") == "Spell":
        targeting = get_spell_targeting(card_entry)
        if not targeting.get("needs_creature"):
            options.insert(0, ("Cast", "cast"))
    menu_height = item_height * len(options) + 8
    x, y = pos
    x = min(x, WIDTH - menu_width - HAND_MARGIN)
    y = min(y, HEIGHT - menu_height - HAND_MARGIN)

    rects = []
    actions = []
    for i, (label, action) in enumerate(options):
        rect = pygame.Rect(x + 6, y + 4 + i * item_height, menu_width - 12, item_height)
        rects.append((rect, label))
        actions.append(action)

    context_menu = {
        "visible": True,
        "rect": pygame.Rect(x, y, menu_width, menu_height),
        "rects": rects,
        "actions": actions,
        "card_id": card_entry.get("id"),
        "kind": "hand",
    }

def render_context_menu():
    if not context_menu.get("visible"):
        return
    rect = context_menu["rect"]
    menu_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    menu_surface.fill((0, 0, 0, 200))
    screen.blit(menu_surface, rect.topleft)
    pygame.draw.rect(screen, (200, 200, 200), rect, 1)

    for item_rect, label in context_menu.get("rects", []):
        text_surface = menu_font.render(label, True, (240, 240, 240))
        screen.blit(text_surface, (item_rect.x + 4, item_rect.y + 2))


def show_creature_context_menu(creature_entry, pos):
    global context_menu
    card_dict = creature_entry.get("card", {})
    menu_width = 160
    item_height = 22
    options = [("Attack", "attack")]
    menu_height = item_height * len(options) + 8

    x, y = pos
    x = min(x, WIDTH - menu_width - HAND_MARGIN)
    y = min(y, HEIGHT - menu_height - HAND_MARGIN)

    rects = []
    actions = []
    for i, (label, action) in enumerate(options):
        rect = pygame.Rect(x + 6, y + 4 + i * item_height, menu_width - 12, item_height)
        rects.append((rect, label))
        actions.append(action)

    context_menu = {
        "visible": True,
        "rect": pygame.Rect(x, y, menu_width, menu_height),
        "rects": rects,
        "actions": actions,
        "creature_id": creature_entry.get("id"),
        "kind": "creature",
        "name": card_dict.get("name"),
    }

def get_selected_anchor():
    if not selected_card_id:
        return None
    for hit in hand_hitboxes:
        if hit["id"] == selected_card_id:
            rect = hit["rect"]
            return rect.centerx, rect.top
    return None

def get_popup_font(size):
    try:
        return pygame.font.Font(SILK_PATH, size)
    except Exception:
        return pygame.font.Font(None, size)


def wrap_text(message, font, max_width):
    words = message.replace("\n", " \n ").split(" ")
    lines = []
    current = []
    for word in words:
        if word == "\n":
            lines.append(" ".join(current).strip())
            current = []
            continue
        test_line = " ".join(current + [word]).strip()
        if font.size(test_line)[0] <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current).strip())
            current = [word]
    if current:
        lines.append(" ".join(current).strip())
    return [line for line in lines if line]


def popup(message):
    global popup_state
    message = str(message or "").strip()
    if not message:
        popup_state["visible"] = False
        return

    max_width = int(WIDTH * 0.65)
    max_height = int(HEIGHT * 0.4)
    font_size = 20
    min_font_size = 12

    lines = []
    while font_size >= min_font_size:
        font = get_popup_font(font_size)
        lines = wrap_text(message, font, max_width)
        line_height = font.get_linesize()
        text_height = line_height * len(lines)
        if text_height <= max_height:
            break
        font_size -= 1

    popup_state.update(
        {
            "visible": True,
            "message": message,
            "lines": lines,
            "font_size": font_size,
        }
    )


def render_popup():
    if not popup_state.get("visible"):
        return

    font = get_popup_font(popup_state.get("font_size", 16))
    lines = popup_state.get("lines", [])
    if not lines:
        return

    line_height = font.get_linesize()
    text_width = max(font.size(line)[0] for line in lines)
    text_height = line_height * len(lines)
    pad = 12

    rect_width = min(int(WIDTH * 0.7), text_width + pad * 2 + 20)
    rect_height = min(int(HEIGHT * 0.5), text_height + pad * 2 + 12)
    rect = pygame.Rect(0, 0, rect_width, rect_height)
    rect.center = (WIDTH // 2, HEIGHT // 2)

    bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 190))
    screen.blit(bg, rect.topleft)
    # pygame.draw.rect(screen, (220, 220, 100), rect, 1)

    close_size = 18
    close_rect = pygame.Rect(
        rect.right - close_size - pad + 5,
        rect.top + pad - 5,
        close_size,
        close_size,
    )
    pygame.draw.rect(screen, (180, 60, 60), close_rect, 0)
    pygame.draw.rect(screen, (255, 220, 220), close_rect, 1)
    close_font = get_popup_font(12)
    close_surface = close_font.render("X", True, (255, 255, 255))
    close_text_rect = close_surface.get_rect(center=close_rect.center)
    screen.blit(close_surface, close_text_rect)

    text_x = rect.left + pad
    text_y = rect.top + pad + 6
    for line in lines:
        text_surface = font.render(line, True, (245, 245, 245))
        screen.blit(text_surface, (text_x, text_y))
        text_y += line_height

    popup_state["rect"] = rect
    popup_state["close_rect"] = close_rect

def move_selected_to_creatures(game_state, player):
    global selected_card_id
    if not selected_card_id:
        return False
    hand = game_state[player]["hand"]
    card = hand.get(str(selected_card_id))
    if not card or card.get("type") != "Creature":
        return False
    generic_cost = card.get("generic_mana", 0)
    color_cost = card.get("sp_mana", "") or None
    if not wiz.game.check_mana_cost(player, generic_cost, color_cost):
        popup("Insufficient mana")
        return False
    if not wiz.game.pay_mana(player, generic_cost, color_cost):
        popup("Insufficient mana")
        return False
    if not wiz.game.play_creature(player, selected_card_id):
        return False
    add_notification(f"{player} has played {card.get('name', 'a creature')}")
    selected_card_id = None
    return True


def move_selected_to_lands(game_state, player):
    global HAS_PLAYED_LAND
    global selected_card_id
    if not selected_card_id:
        return False
    hand = game_state[player]["hand"]
    card = hand.get(str(selected_card_id))
    if not card or card.get("type") != "Land":
        return False
    
    if not HAS_PLAYED_LAND:
      wiz.play_land(selected_card_id, player=player)
      HAS_PLAYED_LAND = True
      add_notification(f"{player} has played {card.get('name', 'a land')}")
    else:
      popup("You can only play one land per turn")
      return False
    selected_card_id = None
    return True

def handle_target_selection(selected_id, target_id):
    state = wiz.game.get_game_state()
    player = wiz.current_player()
    hand = state.get(player, {}).get("hand", {})
    card = hand.get(str(selected_id))
    if not card or card.get("type") != "Spell":
        print(f"Selected card {selected_id} -> target {target_id}")
        return False

    targeting = get_spell_targeting(card)
    if not targeting.get("needs_creature"):
        return False

    if targeting.get("scope") == "friendly":
        if str(target_id) not in state.get(player, {}).get("creatures", {}):
            popup("Choose a friendly creature")
            return False
    elif targeting.get("scope") == "enemy_active":
        enemy = wiz.p2 if player == wiz.p1 else wiz.p1
        if str(target_id) not in state.get(enemy, {}).get("creatures", {}):
            popup("Choose an enemy creature")
            return False

    discard_value = get_discard_value(card)
    opponent = wiz.p2 if player == wiz.p1 else wiz.p1
    opponent_hand = len(state.get(opponent, {}).get("hand", {}))
    if wiz.cast_spell(selected_id, target_id, player=player):
        add_notification(f"{player} cast {card.get('name', 'a spell')}")
        if discard_value and opponent_hand < discard_value:
            add_notification(f"{opponent} discarded all cards")
        activate_pending_discard(wiz.game.get_game_state())
        return True
    return False

# Handle left-click interactions
def handle_left_click(game_state, player, pos):
    global selected_card_id, active_selected_card_id, context_menu, popup_state, selected_blocker_id
    if game_over_state.get("active"):
        return

    if context_menu.get("visible"):
        clicked_option = False
        for idx, (rect, _) in enumerate(context_menu.get("rects", [])):
            if rect.collidepoint(pos):
                clicked_option = True
                menu_kind = context_menu.get("kind")
                action = context_menu.get("actions", [None])[idx]
                if menu_kind == "land":
                    land_id = context_menu.get("land_id")
                    if land_id:
                        wiz.tap_land(land_id, action, player=player)
                        land_entry = game_state[player]["lands"].get(str(land_id), {})
                        land_card = land_entry.get("card", {})
                        color_text = action if action else "mana"
                        add_notification(f"{player} has tapped {land_card.get('name', 'a land')} for {color_text}")
                elif menu_kind == "creature":
                    creature_id = context_menu.get("creature_id")
                    if creature_id and action == "attack":
                        toggle_attacker(game_state, player, creature_id)
                elif menu_kind == "hand":
                    card_id = context_menu.get("card_id")
                    hand = game_state.get(player, {}).get("hand", {})
                    card = hand.get(card_id, {})
                    if card_id and action == "discard":
                        force_discard = discard_state.get("active") and discard_state.get("player") == player
                        if force_discard:
                            required_count = int(discard_state.get("required", 0) or 0)
                            if discard_state.get("discarded", 0) >= required_count:
                                announce(f"Discard limit reached: confirm {required_count}")
                                return
                            if wiz.game.discard_cards(player, [card_id]):
                                discard_state["discarded"] += 1
                                add_notification(f"{player} discarded {card.get('name', card_id)}")
                        elif len(hand) <= 7:
                            popup("You cannot discard with 7 or fewer cards")
                        else:
                            if wiz.game.discard_cards(player, [card_id]):
                                add_notification(f"{player} discarded {card.get('name', card_id)}")
                    if card_id and action == "cast":
                        targeting = get_spell_targeting(card)
                        target_player = None
                        if targeting.get("needs_player"):
                            target_player = wiz.p2 if player == wiz.p1 else wiz.p1
                        discard_value = get_discard_value(card)
                        opponent = wiz.p2 if player == wiz.p1 else wiz.p1
                        opponent_hand = len(game_state.get(opponent, {}).get("hand", {}))
                        if wiz.cast_spell(card_id, target_player, player=player):
                            add_notification(f"{player} cast {card.get('name', 'a spell')}")
                            if discard_value and opponent_hand < discard_value:
                                add_notification(f"{opponent} discarded all cards")
                            activate_pending_discard(wiz.game.get_game_state())
                break
        context_menu["visible"] = False
        if clicked_option:
            return

    if discard_state.get("active") and discard_state.get("player") == player:
        required_count = int(discard_state.get("required", 0) or 0)
        discard_confirm = label_rects.get("discard_confirm")
        if discard_confirm and discard_confirm.collidepoint(pos):
            if discard_state.get("discarded", 0) != required_count:
                popup(f"You have to choose {required_count} cards to discard")
                return
            add_notification(f"{player} discarded {discard_state.get('discarded', 0)} card(s)")
            discard_state["active"] = False
            discard_state["discarded"] = 0
            wiz.priority_player = discard_state.get("return_player") or wiz.current_player()
            clear_pending_discard()
            popup_state["visible"] = False
            return
        return

    if combat_prompt_state.get("visible"):
        confirm_rect = combat_prompt_state.get("confirm_rect")
        cancel_rect = combat_prompt_state.get("cancel_rect")
        if confirm_rect and confirm_rect.collidepoint(pos):
            if combat_prompt_state.get("mode") == "attackers":
                confirm_attackers(game_state)
            elif combat_prompt_state.get("mode") == "blockers":
                confirm_blockers(game_state)
            combat_prompt_state["visible"] = False
            return
        if cancel_rect and cancel_rect.collidepoint(pos):
            if combat_prompt_state.get("mode") == "blockers":
                clear_blockers_ui()
            else:
                reset_combat_ui()
            combat_prompt_state["visible"] = False
            return
        rect = combat_prompt_state.get("rect")
        if rect and rect.collidepoint(pos):
            return
        combat_prompt_state["visible"] = False
        return

    if popup_state.get("visible"):
        close_rect = popup_state.get("close_rect")
        popup_rect = popup_state.get("rect")
        if close_rect and close_rect.collidepoint(pos):
            popup_state["visible"] = False
            return
        if popup_rect and popup_rect.collidepoint(pos):
            return

    action_mulligan = label_rects.get("mulligan")
    action_end_turn = label_rects.get("end_turn")
    combat_confirm = label_rects.get("combat_confirm")
    if action_mulligan and action_mulligan.collidepoint(pos):
        if player != wiz.current_player():
            popup("Only the active player can mulligan")
            return
        if wiz.card_played_this_turn > 0:
            popup("You cannot mulligan after playing a card")
            return
        if not wiz.mulligan():
            popup("You can only mulligan before playing a card")
        else:
            add_notification(f"{player} mulligans")
            draw_animation["active"] = False
            draw_animation["queue"] = []
            draw_animation["card_id"] = None
            draw_animation["card"] = None
            draw_animation["start"] = None
            draw_animation["end"] = None
            last_drawn_id[player] = None
            refreshed = wiz.game.get_game_state()
            prev_hand_ids[player] = set(refreshed.get(player, {}).get("hand", {}).keys())
        return
    if action_end_turn and action_end_turn.collidepoint(pos):
        if player != wiz.current_player():
            popup("Only the active player can end the turn")
            return
        if getattr(wiz, "combat_phase", None) == "attackers" and getattr(wiz, "pending_attackers", []):
            popup("You must confirm or cancel attackers first")
            return
        if len(game_state.get(player, {}).get("hand", {})) > 7:
            popup("You must discard down to 7 cards before ending your turn")
            return
        start_new_turn_ui()
        return
    if combat_confirm and combat_confirm.collidepoint(pos):
        if getattr(wiz, "combat_phase", None) == "attackers":
            lines = build_attackers_preview_lines(game_state, list(getattr(wiz, "pending_attackers", [])))
            show_combat_prompt("attackers", lines)
        elif getattr(wiz, "combat_phase", None) == "blockers":
            lines = build_blockers_preview_lines(game_state, getattr(wiz, "pending_blocks", {}))
            show_combat_prompt("blockers", lines)
        return

    if getattr(wiz, "combat_phase", None) == "blockers" and getattr(wiz, "priority_player", None) == player:
        if selected_blocker_id:
            for hit in reversed(active_creature_hitboxes):
                if hit["rect"].collidepoint(pos) and hit.get("owner") != player:
                    if assign_blocker(game_state, player, selected_blocker_id, hit["id"]):
                        selected_blocker_id = None
                    return

    # Click on label zones to move selected cards
    if selected_card_id:
        creatures_label = label_rects.get("creatures")
        lands_label = label_rects.get("lands")
        if creatures_label and creatures_label.collidepoint(pos):
            if move_selected_to_creatures(game_state, player):
                return
        if lands_label and lands_label.collidepoint(pos):
            if move_selected_to_lands(game_state, player):
                return
    tap_all_label = label_rects.get("tap_all_lands")
    if tap_all_label and tap_all_label.collidepoint(pos):
        if tap_all_lands(game_state, player):
            return

    # Click on hand card to select/deselect
    for hit in reversed(hand_hitboxes):
        if hit["rect"].collidepoint(pos):
            if selected_card_id == hit["id"]:
                selected_card_id = None
            else:
                selected_card_id = hit["id"]
                active_selected_card_id = None
            return

    if getattr(wiz, "combat_phase", None) == "attackers" and getattr(wiz, "priority_player", None) == player:
        for hit in reversed(creature_hitboxes):
            if hit["rect"].collidepoint(pos) and hit.get("owner") == player and hit.get("zone") == "creatures":
                toggle_attacker(game_state, player, hit["id"])
                return

    if getattr(wiz, "combat_phase", None) == "blockers" and getattr(wiz, "priority_player", None) == player:
        for hit in reversed(creature_hitboxes):
            if hit["rect"].collidepoint(pos) and hit.get("owner") == player and hit.get("zone") == "creatures":
                if selected_blocker_id == hit["id"]:
                    selected_blocker_id = None
                else:
                    selected_blocker_id = hit["id"]
                return

    if not selected_card_id:
        for hit in reversed(active_creature_hitboxes):
            if hit["rect"].collidepoint(pos) and hit.get("owner") == player:
                if active_selected_card_id == hit["id"]:
                    active_selected_card_id = None
                else:
                    active_selected_card_id = hit["id"]
                return

    # If a card is selected, allow targeting creatures/lands
    if selected_card_id:
        for hit in reversed(creature_hitboxes):
            if hit["rect"].collidepoint(pos):
                if handle_target_selection(selected_card_id, hit["id"]):
                    selected_card_id = None
                return
        for hit in reversed(land_hitboxes):
            if hit["rect"].collidepoint(pos):
                handle_target_selection(selected_card_id, hit["id"])
                return

    selected_card_id = None
    active_selected_card_id = None
    selected_blocker_id = None

def handle_right_click(game_state, player, pos):
    global context_menu
    if game_over_state.get("active"):
        return
    for hit in reversed(hand_hitboxes):
        if hit["rect"].collidepoint(pos):
            card_entry = hit.get("card", {})
            show_hand_context_menu({"id": hit["id"], **card_entry}, pos)
            return
    for hit in reversed(active_creature_hitboxes):
        if hit["rect"].collidepoint(pos) and hit.get("owner") == player:
            entry = game_state[player]["creatures"].get(hit["id"])
            if entry:
                entry = {**entry, "id": hit["id"]}
                show_creature_context_menu(entry, pos)
            return
    for hit in reversed(creature_hitboxes):
        if hit["rect"].collidepoint(pos) and hit.get("owner") == player:
            entry = game_state[player]["creatures"].get(hit["id"])
            if entry:
                entry = {**entry, "id": hit["id"]}
                show_creature_context_menu(entry, pos)
            return
    for hit in reversed(land_hitboxes):
        if hit["rect"].collidepoint(pos) and hit["owner"] == player:
            entry = game_state[player]["lands"].get(hit["id"])
            if entry:
                tapped = entry.get("tapped", entry.get("card", {}).get("tapped", False))
                if tapped:
                    return
                entry = {**entry, "id": hit["id"]}
                show_land_context_menu(entry, pos)
            return
    context_menu["visible"] = False

# Float when hovering over a card
def on_mouse_hover(game_state, player):
    global hovered_card_id, hover_state, hover_label_state
    mouse_pos = pygame.mouse.get_pos()
    hovered_card_id = None
    hover_hit = None

    for hit in reversed(hand_hitboxes):
        if hit["rect"].collidepoint(mouse_pos):
            hover_hit = hit
            break
    if not hover_hit:
        for hit in reversed(active_creature_hitboxes):
            if hit["rect"].collidepoint(mouse_pos):
                hover_hit = hit
                break
    if not hover_hit:
        for hit in reversed(creature_hitboxes):
            if hit["rect"].collidepoint(mouse_pos):
                hover_hit = hit
                break
    if not hover_hit:
        for hit in reversed(land_hitboxes):
            if hit["rect"].collidepoint(mouse_pos):
                hover_hit = hit
                break

    if hover_hit:
        hovered_card_id = hover_hit["id"]
        now = pygame.time.get_ticks()
        if hover_state.get("card_id") != hover_hit["id"]:
            hover_state = {
                "card_id": hover_hit["id"],
                "start_ms": now,
                "card": hover_hit.get("card"),
                "rect": hover_hit.get("rect"),
            }
            hover_label_state["visible"] = False
        else:
            hover_state["rect"] = hover_hit.get("rect")
            hover_state["card"] = hover_hit.get("card")
            if not hover_label_state.get("visible") and now - hover_state.get("start_ms", 0) >= 1500:
                card_dict = hover_state.get("card") or {}
                hover_label_state["lines"] = build_hover_label_lines(card_dict)
                hover_label_state["anchor_rect"] = hover_state.get("rect")
                hover_label_state["visible"] = True
            elif hover_label_state.get("visible"):
                hover_label_state["anchor_rect"] = hover_state.get("rect")
    else:
        hover_state = {"card_id": None, "start_ms": 0, "card": None, "rect": None}
        hover_label_state["visible"] = False
    return hovered_card_id

# Move the card upwards when clicked to signify it's selected
# Drop the card when released to signify it's not selected
def on_mouse_click(game_state, player):
    global selected_card_id
    return selected_card_id

wiz = Wizard("Player 1", "Player 2")
wiz.start()
view_player = wiz.current_player()

running = True
while running:
    state = wiz.game.get_game_state()
    view_player = wiz.priority_player or wiz.current_player()
    detect_creature_stat_changes(state)
    detect_draw_animation(state, view_player)
    activate_pending_discard(state)
    check_game_over(state)
    update_image_paths(state)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not game_over_state.get("active"):
                handle_left_click(state, view_player, event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if not game_over_state.get("active"):
                handle_right_click(state, view_player, event.pos)

    screen.fill(BACKGROUND_COLOR)
    on_mouse_hover(state, view_player)
    render_battlefield(state, view_player)
    _, _, _, _, hand_start_x = get_deck_layout()
    exclude_ids = []
    if draw_animation.get("active") and draw_animation.get("player") == view_player:
        exclude_ids = [draw_animation.get("card_id")]
    render_hand(state, view_player, start_x=hand_start_x, exclude_ids=exclude_ids)
    render_draw_animation()
    render_combat_lines(state)
    render_zone_labels()
    render_notifications()
    render_popup()
    render_context_menu()
    render_hover_label()
    render_combat_prompt()
    render_announce()
    if not popup_shown:
        popup("Welcome to Wizard!\n1. Click on a card to select it and click on the labels to move it around.\n2. You can only play one land per turn."
        "\n3. Right click on a land to tap it.\n4. Right click on a creature to attack.\n5. Click on spells to target creatures or players.")
        popup_shown = True
    if selected_card_id:
        current_hand = state.get(view_player, {}).get("hand", {})
        selected_card = current_hand.get(str(selected_card_id))
        draw_line = False
        if selected_card:
            if selected_card.get("type") == "Spell":
                targeting = get_spell_targeting(selected_card)
                draw_line = targeting.get("needs_creature")
        if draw_line:
            anchor = get_selected_anchor()
            if anchor:
                pygame.draw.line(screen, (255, 255, 255), anchor, pygame.mouse.get_pos(), 2)
    pygame.display.flip()

pygame.quit()