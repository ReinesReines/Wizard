import os
import pygame
from PIL import Image

from src.modules.card_creator import create_card
from src.modules.utils import get_land_colors
from src.wizard import Wizard

WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (75, 82, 99)
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

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Wizard")

image_cache = {}
pil_cache = {}
hand_hitboxes = []
land_hitboxes = []
creature_hitboxes = []
hovered_card_id = None
selected_card_id = None
creature_deck_rect = None
label_rects = {}
label_draw_queue = []
popup_state = {
    "visible": False,
    "message": "",
    "rect": None,
    "close_rect": None,
    "lines": [],
    "font_size": 16,
}
popup_shown = False

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
    base_attack = creature_entry.get("base_attack")
    base_defence = creature_entry.get("base_defence")
    if base_attack is None or base_defence is None:
        return False
    return card_dict.get("attack") != base_attack or card_dict.get("defence") != base_defence


def build_temp_image(card_id, card_dict):
    card_obj = wiz.game._reconstruct_card(card_dict)
    if not card_obj:
        return None
    temp_name = f"{card_id}_{card_dict.get('attack')}_{card_dict.get('defence')}.png"
    temp_path = os.path.join(TEMP_PATH, temp_name)
    if not os.path.exists(temp_path):
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

def announce(message):
    # use silkscreen font from assets/fonts/Silkscreen-Regular.ttf
    font = pygame.font.Font(SILK_PATH, 36)
    text = font.render(message, True, (255, 255, 255))
    text_rect = text.get_rect()
    text_rect.center = (WIDTH // 2, HEIGHT // 2)
    screen.blit(text, text_rect)
    pygame.display.flip()

    # remove the text after 2 seconds
    pygame.time.wait(2000)
    font.render("", True, (255, 255, 255))
    text_rect = text.get_rect()
    text_rect.center = (WIDTH // 2, HEIGHT // 2)
    screen.blit(text, text_rect)
    pygame.display.flip()

def render_hand(game_state, player):
    global hand_hitboxes
    hand_hitboxes = []

    hand = game_state[player]["hand"]
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

    x = HAND_MARGIN
    base_y = HEIGHT - HAND_MARGIN

    draw_queue = []
    for gi, group_name in enumerate(ordered_groups):
        for card_id, card_dict in grouped[group_name]:
            draw_queue.append((card_id, card_dict, x))
            x += hand_step
        if gi < len(ordered_groups) - 1:
            x += group_gap

    # draw order: normal cards first, then hovered, then selected (on top)
    for card_id, card_dict, card_x in draw_queue:
        if card_id in (hovered_card_id, selected_card_id):
            continue
        rect = render_image(card_dict, card_x, base_y)
        hand_hitboxes.append({"id": card_id, "rect": rect})

    for card_id, card_dict, card_x in draw_queue:
        if card_id != hovered_card_id or card_id == selected_card_id:
            continue
        rect = render_image(card_dict, card_x, base_y - max(12, card_height // 8))
        hand_hitboxes.append({"id": card_id, "rect": rect})

    for card_id, card_dict, card_x in draw_queue:
        if card_id != selected_card_id:
            continue
        rect = render_image(card_dict, card_x, base_y - max(20, card_height // 6))
        hand_hitboxes.append({"id": card_id, "rect": rect})


def render_creature_row(game_state, player, y, align="left", filter_fn=None):
    global creature_hitboxes
    creatures = list(game_state[player]["creatures"].items())
    if filter_fn:
        creatures = [(cid, cdata) for cid, cdata in creatures if filter_fn(cdata)]
    if not creatures:
        return

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
        rect = render_image(card_dict, x, y)
        creature_hitboxes.append({"id": card_id, "rect": rect, "owner": player})
        x += rect.width + CARD_SPACING


def render_land_row(game_state, player, y, align="left"):
    global land_hitboxes
    lands = list(game_state[player]["lands"].items())
    if not lands:
        return

    placeholder = load_pil_image(PLACEHOLDER_PATH)
    card_width = max(1, int(placeholder.width * CARD_SCALE))
    total_width = (card_width * len(lands)) + CARD_SPACING * (len(lands) - 1)

    if align == "right":
        x = max(HAND_MARGIN, WIDTH - HAND_MARGIN - total_width)
    elif align == "center":
        x = max(HAND_MARGIN, (WIDTH - total_width) // 2)
    else:
        x = HAND_MARGIN

    for card_id, land_entry in lands:
        card_dict = land_entry.get("card", {})
        tapped = land_entry.get("tapped", card_dict.get("tapped", False))
        rect = render_land_image(card_dict, x, y, tapped=bool(tapped))
        land_hitboxes.append({"id": card_id, "rect": rect, "owner": player, "card": card_dict})
        x += rect.width + CARD_SPACING


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
    graveyard = list(game_state[player].get("graveyard", []))
    if not graveyard:
        return

    placeholder = load_pil_image(PLACEHOLDER_PATH)
    card_width = max(1, int(placeholder.width * CARD_SCALE))
    total_width = (card_width * len(graveyard)) + CARD_SPACING * (len(graveyard) - 1)

    if align == "right":
        x = max(HAND_MARGIN, WIDTH - HAND_MARGIN - total_width)
    elif align == "center":
        x = max(HAND_MARGIN, (WIDTH - total_width) // 2)
    else:
        x = HAND_MARGIN

    for card_dict in graveyard:
        rect = render_image(card_dict, x, y)
        x += rect.width + CARD_SPACING


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


def render_battlefield(game_state, player):
    global land_hitboxes, creature_hitboxes, label_rects, label_draw_queue
    land_hitboxes = []
    creature_hitboxes = []
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

    enemy_active_count = sum(
        1
        for cdata in game_state[enemy]["creatures"].values()
        if is_active_creature(cdata)
    )

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

    if enemy_active_count:
        queue_zone_label("Enemy active creatures", WIDTH // 2, top_label_y, align="center", key="enemy_active")
        render_creature_row(
            game_state,
            enemy,
            top_creatures_y,
            align="center",
            filter_fn=is_active_creature,
        )

    creatures_label_y = middle_creatures_y - label_height - label_gap
    queue_zone_label("Creatures", HAND_MARGIN, creatures_label_y, align="left", key="creatures")
    render_creature_row(game_state, player, middle_creatures_y, align="left")

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
    queue_zone_label("Lands", WIDTH // 2, lands_label_y, align="center", key="lands")
    queue_zone_label("Graveyard", WIDTH - HAND_MARGIN, graveyard_label_y, align="right", key="graveyard")

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
        "land_id": land_entry.get("id")
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
        rect.right - close_size - pad,
        rect.top + pad,
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
    else:
      announce("You can only play one land per turn")
      return False
    selected_card_id = None
    return True

def handle_target_selection(selected_id, target_id):
    print(f"Selected card {selected_id} → target {target_id}")

# Handle left-click interactions
def handle_left_click(game_state, player, pos):
    global selected_card_id, context_menu, popup_state

    if context_menu.get("visible"):
        clicked_option = False
        for idx, (rect, _) in enumerate(context_menu.get("rects", [])):
            if rect.collidepoint(pos):
                clicked_option = True
                land_id = context_menu.get("land_id")
                color = context_menu.get("actions", [None])[idx]
                if land_id:
                    wiz.tap_land(land_id, color, player=player)
                break
        context_menu["visible"] = False
        if clicked_option:
            return

    if popup_state.get("visible"):
        close_rect = popup_state.get("close_rect")
        popup_rect = popup_state.get("rect")
        if close_rect and close_rect.collidepoint(pos):
            popup_state["visible"] = False
            return
        if popup_rect and popup_rect.collidepoint(pos):
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

    # Click on hand card to select/deselect
    for hit in reversed(hand_hitboxes):
        if hit["rect"].collidepoint(pos):
            if selected_card_id == hit["id"]:
                selected_card_id = None
            else:
                selected_card_id = hit["id"]
            return

    # If a card is selected, allow targeting creatures/lands
    if selected_card_id:
        for hit in reversed(creature_hitboxes):
            if hit["rect"].collidepoint(pos):
                handle_target_selection(selected_card_id, hit["id"])
                return
        for hit in reversed(land_hitboxes):
            if hit["rect"].collidepoint(pos):
                handle_target_selection(selected_card_id, hit["id"])
                return

    selected_card_id = None

def handle_right_click(game_state, player, pos):
    global context_menu
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
    global hovered_card_id
    mouse_pos = pygame.mouse.get_pos()
    hovered_card_id = None
    for hit in reversed(hand_hitboxes):
        if hit["rect"].collidepoint(mouse_pos):
            hovered_card_id = hit["id"]
            break
    return hovered_card_id

# Move the card upwards when clicked to signify it's selected
# Drop the card when released to signify it's not selected
def on_mouse_click(game_state, player):
    global selected_card_id
    return selected_card_id

wiz = Wizard("Player 1", "Player 2")
wiz.start()

running = True
while running:
    state = wiz.game.get_game_state()
    update_image_paths(state)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle_left_click(state, wiz.current_player(), event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            handle_right_click(state, wiz.current_player(), event.pos)

    screen.fill(BACKGROUND_COLOR)
    on_mouse_hover(state, wiz.current_player())
    render_battlefield(state, wiz.current_player())
    render_hand(state, wiz.current_player())
    render_zone_labels()
    render_popup()
    render_context_menu()
    if not popup_shown:
        popup("Welcome to Wizard!\n1. Click on a creature card to select it and click on the labels to move them around.\n2. Click on a land card to select it and click on the labels to move it around."
        "\n3. Click on a spell card to select it and click on the desired target.\n4. Click off to deselect a card.")
        popup_shown = True
    if selected_card_id:
        anchor = get_selected_anchor()
        if anchor:
            pygame.draw.line(screen, (255, 255, 255), anchor, pygame.mouse.get_pos(), 2)
    pygame.display.flip()

pygame.quit()