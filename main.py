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

try:
    card_font = pygame.font.Font(SILK_PATH, 18)
    menu_font = pygame.font.Font(SILK_PATH, 16)
except Exception:
    card_font = pygame.font.Font(None, 18)
    menu_font = pygame.font.Font(None, 16)

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
  # use aseprite font from assets/fonts/Silkscreen-Regular.ttf
    font = pygame.font.Font(None, 36)
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

    if creature_deck_rect:
        x = creature_deck_rect.right + CARD_SPACING

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


def render_creature_row(game_state, player, y, align_right=False):
    global creature_hitboxes
    creatures = list(game_state[player]["creatures"].items())
    if not creatures:
        return

    placeholder = load_pil_image(PLACEHOLDER_PATH)
    card_width = max(1, int(placeholder.width * CARD_SCALE))
    total_width = (card_width * len(creatures)) + CARD_SPACING * (len(creatures) - 1)

    if align_right:
        x = max(HAND_MARGIN, WIDTH - HAND_MARGIN - total_width)
    else:
        x = HAND_MARGIN

    for card_id, creature_entry in creatures:
        card_dict = creature_entry.get("card", {})
        rect = render_image(card_dict, x, y)
        creature_hitboxes.append({"id": card_id, "rect": rect, "owner": player})
        x += rect.width + CARD_SPACING


def render_land_row(game_state, player, y, align_right=False):
    global land_hitboxes
    lands = list(game_state[player]["lands"].items())
    if not lands:
        return

    placeholder = load_pil_image(PLACEHOLDER_PATH)
    card_width = max(1, int(placeholder.width * CARD_SCALE))
    total_width = (card_width * len(lands)) + CARD_SPACING * (len(lands) - 1)

    if align_right:
        x = max(HAND_MARGIN, WIDTH - HAND_MARGIN - total_width)
    else:
        x = HAND_MARGIN

    for card_id, land_entry in lands:
        card_dict = land_entry.get("card", {})
        tapped = land_entry.get("tapped", card_dict.get("tapped", False))
        rect = render_land_image(card_dict, x, y, tapped=bool(tapped))
        land_hitboxes.append({"id": card_id, "rect": rect, "owner": player, "card": card_dict})
        x += rect.width + CARD_SPACING


def render_battlefield(game_state, player):
    global land_hitboxes, creature_hitboxes
    land_hitboxes = []
    creature_hitboxes = []

    enemy = wiz.p2 if player == wiz.p1 else wiz.p1
    placeholder = load_pil_image(PLACEHOLDER_PATH)
    card_height = max(1, int(placeholder.height * CARD_SCALE))
    row_gap = max(12, int(card_height * 0.2))

    top_creatures_y = HAND_MARGIN + card_height
    top_lands_y = top_creatures_y + card_height + row_gap

    bottom_hand_y = HEIGHT - HAND_MARGIN
    bottom_lands_y = bottom_hand_y - card_height - row_gap
    bottom_creatures_y = bottom_lands_y - card_height - row_gap

    render_creature_row(game_state, enemy, top_creatures_y, align_right=False)
    render_land_row(game_state, enemy, top_lands_y, align_right=False)
    render_land_row(game_state, player, bottom_lands_y, align_right=False)
    render_creature_row(game_state, player, bottom_creatures_y, align_right=True)

def render_creature_deck(game_state, player):
    global creature_deck_rect
    creatures = game_state[player]["creatures"]

    placeholder = load_pil_image(PLACEHOLDER_PATH)
    card_width = max(1, int(placeholder.width * CARD_SCALE))
    card_height = max(1, int(placeholder.height * CARD_SCALE))

    x = HAND_MARGIN
    y = HEIGHT - HAND_MARGIN
    deck_path = os.path.join(CARDS_PATH, "deck.png")
    deck_dict = {"image_path": deck_path, "name": "deck"}
    creature_deck_rect = render_image(deck_dict, x, y)

    pygame.draw.rect(screen, (245, 245, 245), creature_deck_rect, 2)

    label = "Creatures"
    count = len(creatures)
    label_surface = card_font.render(f"{label}: {count}", True, (235, 235, 235))
    label_rect = label_surface.get_rect()
    label_rect.midtop = (creature_deck_rect.centerx, creature_deck_rect.top + 6)
    screen.blit(label_surface, label_rect)

    return creature_deck_rect

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
        announce("Insufficient mana")
        return False
    if not wiz.game.pay_mana(player, generic_cost, color_cost):
        announce("Insufficient mana")
        return False
    if not wiz.game.play_creature(player, selected_card_id):
        return False
    selected_card_id = None
    return True

def handle_target_selection(selected_id, target_id):
    print(f"Selected card {selected_id} → target {target_id}")

# Handle left-click interactions
def handle_left_click(game_state, player, pos):
    global selected_card_id, context_menu

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

    # Click on creature deck to move selected card
    if selected_card_id and creature_deck_rect and creature_deck_rect.collidepoint(pos):
        if move_selected_to_creatures(game_state, player):
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
    render_creature_deck(state, wiz.current_player())
    render_hand(state, wiz.current_player())
    render_context_menu()
    if selected_card_id:
        anchor = get_selected_anchor()
        if anchor:
            pygame.draw.line(screen, (255, 255, 255), anchor, pygame.mouse.get_pos(), 2)
    pygame.display.flip()

pygame.quit()