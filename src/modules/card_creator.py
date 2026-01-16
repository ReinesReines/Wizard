from PIL import Image, ImageDraw, ImageFont
import os
import random

# Card dimensions (2x for clarity)
CARD_WIDTH = 264
CARD_HEIGHT = 448

# Mana icon dimensions (2x)
MANA_ICON_SIZE = 32
PLACEHOLDER_WIDTH = 64
PLACEHOLDER_HEIGHT = 32

# Asset dimensions (2x)
CREATURE_IMAGE_WIDTH = 256
CREATURE_IMAGE_HEIGHT = 128

# Paths
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")
FONTS_PATH = os.path.join(ASSETS_PATH, "fonts")
FONT_FILE = os.path.join(FONTS_PATH, "Silkscreen-Regular.ttf")


def load_font(size):
    """Load the aseprite font at the specified size."""
    try:
        font = ImageFont.truetype(FONT_FILE, size)
        return font
    except Exception as e:
        print(f"Warning: Could not load font: {e}")
        return ImageFont.load_default()


def draw_crisp_text(base_img, position, text, font, color=(0, 0, 0, 255), mode="antialiased"):
    """
    Render text onto the base image.

    mode:
      - "antialiased": use PIL's default antialiased rendering (smooth)
      - "crisp": 1-bit mask paste (blocky pixel-perfect)
    """
    if mode == "antialiased":
        # Just draw directly with PIL's built-in antialiasing
        draw = ImageDraw.Draw(base_img)
        draw.text(position, text, fill=color, font=font)
        return
    
    # Crisp pixel mode (original 1-bit approach)
    dummy = Image.new("L", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy)
    bbox = dummy_draw.textbbox((0, 0), text, font=font)
    w0, h0 = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    mask = Image.new("1", (w0, h0), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.text((0, 0), text, font=font, fill=1)

    text_img = Image.new("RGBA", (w0, h0), color)
    base_img.paste(text_img, position, mask.convert("L"))

def create_card(card_data, output_path="card_output.png"):
    """
    Create a card image based on card data.
    
    Args:
        card_data: Card object (SummonCard, SpellCard, or LandCards)
        output_path: Path where to save the generated card
    """
    # Load random card base (card1-card6.png) and scale 2x with nearest neighbor
    card_num = random.randint(1, 6)
    card_base_path = os.path.join(ASSETS_PATH, f"card{card_num}.png")
    if os.path.exists(card_base_path):
        card_original = Image.open(card_base_path).convert('RGBA')
        # Scale 2x using nearest neighbor for pixel-perfect scaling
        card = card_original.resize((CARD_WIDTH, CARD_HEIGHT), Image.NEAREST)
    else:
        # Fallback to blank card if not found
        card = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), color=(255, 255, 255, 255))
    
    draw = ImageDraw.Draw(card)
    
    # Load fonts - exact multiples of 8 for crisp pixel rendering
    name_font = load_font(24)
    mana_font = load_font(32)
    text_font = load_font(16)
    stats_font = load_font(32)
    
    # Position trackers (2x)
    current_y = 8
    
    # 1. Draw card name (top left) - abbreviate if needed
    card_name = card_data.name
    # Abbreviate long names (keep first word + initial of second)
    words = card_name.split()
    if len(words) > 1 and len(card_name) > 8:
        card_name = f"{words[0]} {words[1][0]}."
    draw_crisp_text(card, (8, current_y), card_name, name_font, (0, 0, 0, 255))
    
    # 2. Draw mana cost (top right with placeholder background)
    placeholder_path = os.path.join(ASSETS_PATH, "placeholder.png")
    if os.path.exists(placeholder_path):
        placeholder_original = Image.open(placeholder_path).convert("RGBA")
        # Scale 2x with nearest neighbor
        placeholder = placeholder_original.resize((PLACEHOLDER_WIDTH, PLACEHOLDER_HEIGHT), Image.NEAREST)
        placeholder_x = CARD_WIDTH - PLACEHOLDER_WIDTH - 4
        placeholder_y = current_y
        card.paste(placeholder, (placeholder_x, placeholder_y), placeholder)
        
        # Generic mana number
        generic_mana = str(card_data.generic_mana)
        mana_text_x = placeholder_x + 6
        mana_text_y = placeholder_y - 6
        draw_crisp_text(card, (mana_text_x, mana_text_y), generic_mana, mana_font, (0, 0, 0, 255))
        
        # Colored mana icon
        if card_data.sp_mana:
            mana_color = card_data.sp_mana.lower()
            mana_icon_path = os.path.join(ASSETS_PATH, f"{mana_color}_mana.png")
            if os.path.exists(mana_icon_path):
                mana_icon_original = Image.open(mana_icon_path).convert("RGBA")
                # Scale 2x with nearest neighbor
                mana_icon = mana_icon_original.resize((MANA_ICON_SIZE, MANA_ICON_SIZE), Image.NEAREST)
                mana_icon_x = placeholder_x + 32
                mana_icon_y = placeholder_y
                card.paste(mana_icon, (mana_icon_x, mana_icon_y), mana_icon)
    
    current_y += 40
    
    # 3. Creature/Land image (centered, scaled 2x)
    creature_image_name = card_data.name.lower().replace(" ", "_") + ".png"
    
    # Check if it's a land card by looking in the lands folder first
    land_image_path = os.path.join(ASSETS_PATH, "lands", creature_image_name)
    creature_image_path = os.path.join(ASSETS_PATH, creature_image_name)
    
    # Prioritize land folder for land images
    if os.path.exists(land_image_path):
        image_path = land_image_path
    elif os.path.exists(creature_image_path):
        image_path = creature_image_path
    else:
        image_path = None
    
    if image_path:
        creature_img_original = Image.open(image_path).convert("RGBA")
        # Scale 2x with nearest neighbor for pixel-perfect scaling
        creature_img = creature_img_original.resize((CREATURE_IMAGE_WIDTH, CREATURE_IMAGE_HEIGHT), Image.NEAREST)
        creature_x = (CARD_WIDTH - CREATURE_IMAGE_WIDTH) // 2
        creature_y = current_y
        card.paste(creature_img, (creature_x, creature_y), creature_img)
        current_y += CREATURE_IMAGE_HEIGHT + 8
    else:
        draw.rectangle([4, current_y, CARD_WIDTH - 4, current_y + CREATURE_IMAGE_HEIGHT], 
                       outline='gray', fill='lightgray')
        current_y += CREATURE_IMAGE_HEIGHT + 8
    
    # 4. Description text
    description = card_data.description
    parts = description.split("|")
    
    if parts:
        abilities_text = parts[0].strip()
        wrapped_lines = wrap_text(abilities_text, text_font, CARD_WIDTH - 16)
        for line in wrapped_lines:
            draw_crisp_text(card, (8, current_y), line, text_font, (0, 0, 0, 255))
            current_y += 20
    
    if len(parts) > 1 and parts[1].strip():
        current_y += 4
        draw.line([(8, current_y), (CARD_WIDTH - 8, current_y)], fill='black', width=2)
        current_y += 8
        
        flavor_text = parts[1].strip()
        wrapped_flavor = wrap_text(flavor_text, text_font, CARD_WIDTH - 16)
        for line in wrapped_flavor:
            draw_crisp_text(card, (8, current_y), line, text_font, (0, 0, 0, 255))
            current_y += 20
    
    # 5. Stats (bottom right)
    if hasattr(card_data, 'attack') and hasattr(card_data, 'defence'):
        stats_text = f"{card_data.attack}/{card_data.defence}"
        stats_x = CARD_WIDTH - 70
        stats_y = CARD_HEIGHT - 40
        draw_crisp_text(card, (stats_x, stats_y), stats_text, stats_font, (0, 0, 0, 255))
    
    card.save(output_path)
    print(f"Card created: {output_path}")
    return card

def wrap_text(text, font, max_width):
    """
    Wrap text to fit within max_width.
    
    Args:
        text: Text to wrap
        font: Font to use for measuring
        max_width: Maximum width in pixels
    
    Returns:
        List of wrapped lines
    """
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        # Use a dummy image to measure text
        dummy_img = Image.new('RGB', (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)
        
        # Get bounding box of text
        bbox = dummy_draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


# Example usage
if __name__ == "__main__":
    # Import card data
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    
    from card_index import _universal_cards, _land_cards
    
    # Create cards folder if it doesn't exist
    cards_output_path = os.path.join(ASSETS_PATH, "cards")
    os.makedirs(cards_output_path, exist_ok=True)
    
    # Get all creature images in assets folder
    all_assets = [f for f in os.listdir(ASSETS_PATH) if f.endswith('.png')]
    
    # Get all land images in lands folder
    lands_path = os.path.join(ASSETS_PATH, "lands")
    if os.path.exists(lands_path):
        land_assets = [f for f in os.listdir(lands_path) if f.endswith('.png')]
    else:
        land_assets = []
    
    # Filter out card bases and mana icons
    skip_files = {'placeholder.png', 'red_mana.png', 'blue_mana.png', 'green_mana.png'}
    skip_files.update([f'card{i}.png' for i in range(1, 8)])
    
    creature_images = [f for f in all_assets if f not in skip_files]
    
    # Combine creature and land images
    all_images = creature_images + land_assets
    
    # Create a map of card names to card objects
    all_cards = _universal_cards + _land_cards
    card_map = {card.name.lower().replace(" ", "_") + ".png": card for card in all_cards}
    
    # Generate cards for each image
    generated_count = 0
    for img_file in all_images:
        output_file = os.path.join(cards_output_path, img_file)
        
        # Skip if card already exists
        if os.path.exists(output_file):
            continue
        
        # Find corresponding card data
        if img_file in card_map:
            card_data = card_map[img_file]
            create_card(card_data, output_file)
            generated_count += 1
            print(f"Generated: {img_file}")
        else:
            print(f"Warning: No card data found for {img_file}")
    
    print(f"\nTotal cards generated: {generated_count}")