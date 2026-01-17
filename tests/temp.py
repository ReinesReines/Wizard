#!/usr/bin/env python3
"""Interactive Wizard Card Game - Enhanced CLI Interface"""

import sys
import os
import random
from typing import List, Dict, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from game import GameEngine
from card_index import (
    # Creatures
    slime, bigger_slime, forest_bear, vine_elemental, alpha_wolf,
    skeleton, skeleton_army, phantom_warrior, sea_serpent, arcane_scholar, vergil,
    goblin_raider, fire_elemental, dragon_whelp, berserker,
    # Lands
    forest, island, mountain, tropical_grove, volcanic_peak, wild_highlands
)

class WizardCLI:
    """Enhanced CLI interface for Wizard card game."""
    
    def __init__(self):
        # Create diverse decks
        creature_pool = [
            slime, bigger_slime, forest_bear, vine_elemental, alpha_wolf,
            skeleton, phantom_warrior, arcane_scholar, goblin_raider, 
            fire_elemental, dragon_whelp, berserker
        ]
        
        land_pool = [
            forest, forest, forest, island, island, island,
            mountain, mountain, tropical_grove, volcanic_peak
        ]
        
        # Build balanced decks (20 cards each)
        deck = creature_pool * 2 + land_pool
        random.shuffle(deck)
        
        self.game = GameEngine('Player1', 'Player2', deck, deck.copy())
        self.current_turn_drawn = False
        
        # Track mulligan availability (only on first turn for each player)
        self.mulligan_available = {'Player1': True, 'Player2': True}
        
        # Initialize game state
        self.game.ready()
        
        # Deal opening hands (7 cards each)
        for _ in range(7):
            self.game.draw_card('Player1')
            self.game.draw_card('Player2')
        
        # Start the first turn properly
        self.game.start_turn('Player1')
        
        # Show initial game info
        self.show_game_info()
        
    def start_new_turn(self):
        """Start a new turn with all automatic processes."""
        state = self.game.get_game_state()
        player = state['active_player']
        
        print(f"\n{'='*60}")
        print(f"TURN {state['turn']} - {player}'s Turn")
        print(f"{'='*60}")
        
        # Untap step (except vigilant creatures)
        self.game.untap_step(player)
        print(f"Untap step: All permanents untapped")
        
        # Draw step (skip on turn 1 for starting player)
        if not (state['turn'] == 1 and player == 'Player1'):
            self.game.draw_step(player)
            print(f"Draw step: {player} draws a card")
        
        self.current_turn_drawn = False
        self.show_game_info()
        
    def show_game_info(self):
        """Display comprehensive game information."""
        state = self.game.get_game_state()
        player = state['active_player']
        
        # Find the other player
        all_players = [key for key in state.keys() if key not in ['active_player', 'turn', 'phase', 'turn_number', 'current_player', 'battlefield', 'lands_played_this_turn', 'combat']]
        opponent = next((p for p in all_players if p != player), None)
        
        print(f"\nGAME STATUS")
        print(f"Phase: {state.get('phase', 'main')}")  
        
        if opponent:
            print(f"{player}: {state[player]['health']} HP | {opponent}: {state[opponent]['health']} HP")
        else:
            print(f"{player}: {state[player]['health']} HP")
        
        # Mana pool
        mana_info = []
        for color in ['green', 'blue', 'red']:
            amt = state[player].get(f'{color}_mana', 0)
            if amt > 0:
                mana_info.append(f"{color[0].upper()}{amt}")
        mana_str = " ".join(mana_info) if mana_info else "No mana"
        print(f"Mana: {mana_str}")
        
        # Battlefield summary
        creatures = state[player].get('creatures', {})
        lands = state[player].get('lands', {})
        print(f"Battlefield: {len(creatures)} creatures, {len(lands)} lands")
        
        # Hand size
        hand_size = len(state[player].get('hand', {}))
        print(f"Hand: {hand_size} cards")
        
        # Show mulligan availability
        state = self.game.get_game_state()
        turn = state.get('turn', 1)
        if self.is_mulligan_available(player, turn):
            print("[MULLIGAN AVAILABLE] Use 'mulligan' to redraw your opening hand")
        
        print(f"\nAvailable commands: land, play, tap, attack, block, end, mulligan, hand, board, state, graveyard, deck")
        print(f"Admin commands: mana, admindraw")
        
    def is_mulligan_available(self, player: str, turn: int) -> bool:
        """Check if mulligan is available for the given player on the given turn."""
        if not self.mulligan_available.get(player, False):
            return False
        
        # Player1 can mulligan on turn 1, Player2 can mulligan on turn 2
        if player == 'Player1' and turn == 1:
            return True
        elif player == 'Player2' and turn == 2:
            return True
        
        return False
        
    def perform_mulligan(self, player: str):
        """Perform mulligan: shuffle hand back into deck and draw 7 new cards."""
        state = self.game.get_game_state()
        hand = state[player].get('hand', {})
        deck = state[player].get('deck', [])
        
        # Move all hand cards back to deck
        for card_id, card_data in hand.items():
            deck.append(card_data)
        
        # Clear hand
        state[player]['hand'] = {}
        
        # Shuffle deck
        random.shuffle(deck)
        state[player]['deck'] = deck
        
        # Draw 7 new cards
        for _ in range(7):
            if deck:
                card_id = str(max([int(k) for k in state[player].get('hand', {}).keys()] + [0]) + 1)
                state[player]['hand'][card_id] = deck.pop(0)
        
        # Mark mulligan as used for this player
        self.mulligan_available[player] = False
        
        # Save state
        self.game._save_state(state)
        
        print(f"{player} mulliganed and drew 7 new cards")
        
    def is_dual_land(self, player: str, land_id: str) -> bool:
        """Check if a land is a dual land that offers mana choice."""
        state = self.game.get_game_state()
        lands = state[player].get('lands', {})
        
        if land_id not in lands:
            return False
            
        land_card = lands[land_id]['card']
        effect = land_card.get('effect', '')
        
        # Check if effect contains dual mana generation
        return 'gen green/blue' in effect or 'gen red/blue' in effect or 'gen red/green' in effect
        
    def get_dual_land_colors(self, player: str, land_id: str) -> list:
        """Get the available color choices for a dual land."""
        state = self.game.get_game_state()
        lands = state[player].get('lands', {})
        
        if land_id not in lands:
            return []
            
        land_card = lands[land_id]['card']
        effect = land_card.get('effect', '')
        
        if 'gen green/blue' in effect:
            return ['green', 'blue']
        elif 'gen red/blue' in effect:
            return ['red', 'blue']
        elif 'gen red/green' in effect:
            return ['red', 'green']
        
        return []
        
    def tap_dual_land(self, player: str, land_id: str, chosen_color: str):
        """Tap a dual land for the chosen color of mana."""
        state = self.game.get_game_state()
        lands = state[player].get('lands', {})
        
        if land_id not in lands:
            raise Exception(f"Land {land_id} not found")
            
        land = lands[land_id]
        if land.get('tapped', 0) == 1:
            raise Exception(f"Land {land_id} is already tapped")
            
        # Validate color choice
        available_colors = self.get_dual_land_colors(player, land_id)
        if chosen_color not in available_colors:
            raise Exception(f"Invalid color '{chosen_color}' for this land. Choose from: {', '.join(available_colors)}")
            
        # Tap the land
        land['tapped'] = 1
        
        # Add the chosen mana
        state[player][f'{chosen_color}_mana'] += 1
        
        # Save state
        self.game._save_state(state)
        
    def show_hand(self):
        """Display player's hand with IDs."""
        state = self.game.get_game_state()
        player = state['active_player']
        hand = state[player].get('hand', {})
        
        if not hand:
            print("Your hand is empty")
            return
            
        print(f"\n{player}'s Hand:")
        print("-" * 50)
        for card_id, card_data in hand.items():
            # Use case-insensitive type check to correctly mark Lands
            card_type = "[L]" if str(card_data.get('type', '')).lower() == 'land' else "[C]"
            cost = self.format_mana_cost(card_data)
            stats = ""
            if card_data.get('attack') is not None:
                stats = f" [{card_data['attack']}/{card_data['defence']}]"
            print(f"{card_type} {card_id}: {card_data['name']}{stats} - {cost}")
            
    def show_board(self):
        """Display battlefield state."""
        state = self.game.get_game_state()
        
        # Get all player names dynamically
        all_players = [key for key in state.keys() if key not in ['active_player', 'turn', 'phase', 'turn_number', 'current_player', 'battlefield', 'lands_played_this_turn', 'combat']]
        
        for player_name in all_players:
            is_active = player_name == state['active_player']
            marker = "[ACTIVE]" if is_active else "        "
            print(f"\n{marker} {player_name}'s Battlefield:")
            print("-" * 40)
            
            # Mana pool
            mana_info = []
            for color in ['green', 'blue', 'red']:
                amt = state[player_name].get(f'{color}_mana', 0)
                if amt > 0:
                    mana_info.append(f"{color[0].upper()}{amt}")
            mana_str = " ".join(mana_info) if mana_info else "No mana"
            print(f"Mana: {mana_str}")
            
            # Creatures
            creatures = state[player_name].get('creatures', {})
            if creatures:
                print("Creatures:")
                for cid, creature in creatures.items():
                    card = creature['card']
                    status = []
                    if creature.get('tapped'): status.append("tapped")
                    if creature.get('summoning_sickness'): status.append("sick")
                    status_str = f" ({', '.join(status)})" if status else ""
                    print(f"   [C] {cid}: {card['name']} [{card['attack']}/{card['defence']}]{status_str}")
            
            # Lands  
            lands = state[player_name].get('lands', {})
            if lands:
                print("Lands:")
                for lid, land in lands.items():
                    card = land['card']
                    status = " (tapped)" if land.get('tapped') else ""
                    print(f"   [L] {lid}: {card['name']}{status}")
    
    def show_graveyard(self):
        """Display player's graveyard."""
        state = self.game.get_game_state()
        player = state['active_player']
        graveyard = state[player].get('graveyard', [])
        
        if not graveyard:
            print("Your graveyard is empty")
            return
            
        print(f"\n{player}'s Graveyard ({len(graveyard)} cards):")
        print("-" * 40)
        for i, card in enumerate(graveyard):
            # Case-insensitive type to correctly label Lands
            card_type = "[L]" if str(card.get('type', '')).lower() == 'land' else "[C]"
            print(f"{card_type} {card['name']}")
            
    def show_deck(self):
        """Display player's deck."""
        state = self.game.get_game_state()
        player = state['active_player']
        deck = state[player].get('deck', [])
        
        print(f"\n{player}'s Deck ({len(deck)} cards):")
        print("-" * 40)
        if deck:
            # Show top 3 cards for preview
            for i, card in enumerate(deck[:3]):
                # Case-insensitive type to correctly label Lands
                card_type = "[L]" if str(card.get('type', '')).lower() == 'land' else "[C]"
                print(f"{card_type} {card['name']}")
            if len(deck) > 3:
                print(f"   ... and {len(deck) - 3} more cards")
        else:
            print("   Empty deck!")
            
    def show_state(self):
        """Display full game state."""
        state = self.game.get_game_state()
        
        print(f"\nFULL GAME STATE")
        print("=" * 60)
        print(f"Turn: {state['turn']}")  
        print(f"Phase: {state.get('phase', 'main')}")
        print(f"Active Player: {state['active_player']}")
        
        # Get all player names dynamically
        all_players = [key for key in state.keys() if key not in ['active_player', 'turn', 'phase', 'turn_number', 'current_player', 'battlefield', 'lands_played_this_turn', 'combat']]
        
        for player in all_players:
            print(f"\n{player}:")
            pdata = state[player]
            print(f"   Health: {pdata['health']} HP")
            print(f"   Hand: {len(pdata.get('hand', {}))} cards")
            print(f"   Deck: {len(pdata.get('deck', []))} cards") 
            print(f"   Graveyard: {len(pdata.get('graveyard', []))} cards")
            print(f"   Creatures: {len(pdata.get('creatures', {}))}")
            print(f"   Lands: {len(pdata.get('lands', {}))}")
            
            mana = []
            for color in ['green', 'blue', 'red']:
                amt = pdata.get(f'{color}_mana', 0)
                if amt > 0: mana.append(f"{color}: {amt}")
            print(f"   Mana: {', '.join(mana) if mana else 'none'}")
    
    def format_mana_cost(self, card_data: Dict) -> str:
        """Format mana cost for display."""
        generic = card_data.get('generic_mana', 0)
        sp_mana = card_data.get('sp_mana', '')
        
        if generic == 0 and not sp_mana:
            return "Free"
        
        cost_parts = []
        if generic > 0:
            cost_parts.append(f"{generic}")
        if sp_mana:
            cost_parts.append(sp_mana[0].upper())  # First letter
            
        return f"({'+'.join(cost_parts)})"
        
    def end_turn(self):
        """End current turn and switch players."""
        state = self.game.get_game_state()
        current_player = state['active_player']
        
        # Clear mana pool
        self.game.clear_mana_pool(current_player)
        
        # End turn and switch - find the other player dynamically
        all_players = [key for key in state.keys() if key not in ['active_player', 'turn', 'phase', 'turn_number', 'current_player', 'battlefield', 'lands_played_this_turn', 'combat']]
        next_player = next((p for p in all_players if p != current_player), current_player)
        # Mark end of current player's turn in engine
        self.game.end_turn(current_player)
        
        # Start next player's turn in engine so state switches
        self.game.start_turn(next_player)
        
        # Check win condition
        winner = self.game.check_win_condition()
        if winner:
            print(f"\nGAME OVER! {winner} wins!")
            return True
            
        # Start next turn (untap/draw for next player)
        self.start_new_turn()
        return False
        
    def handle_command(self, cmd: str, args: List[str]) -> bool:
        """Handle a game command. Returns True if game should continue."""
        state = self.game.get_game_state()
        player = state['active_player']
        
        try:
            if cmd == 'land':
                if not args:
                    print("[!] Usage: land <id>")
                    return True
                self.game.play_land(player, args[0])
                print(f"Played land {args[0]}")
                
            elif cmd == 'play':
                if not args:
                    print("[!] Usage: play <id>")
                    return True
                self.game.play_creature(player, args[0])
                print(f"Played creature {args[0]}")
                
            elif cmd == 'tap':
                if not args:
                    print("Error: Usage: tap <id> [color]")
                    print("For dual lands, specify color: tap <id> red/blue/green")
                    return True
                    
                land_id = args[0]
                chosen_color = args[1] if len(args) > 1 else None
                
                try:
                    # Check if this is a dual land that needs color choice
                    if self.is_dual_land(player, land_id) and not chosen_color:
                        dual_colors = self.get_dual_land_colors(player, land_id)
                        print(f"Error: Dual land requires color choice. Use: tap {land_id} {'/'.join(dual_colors)}")
                        return True
                    
                    # Perform the tap
                    if chosen_color:
                        self.tap_dual_land(player, land_id, chosen_color)
                        print(f"Tapped {land_id} for {chosen_color} mana")
                    else:
                        self.game.tap_land(player, land_id)
                        print(f"Tapped land {land_id} for mana")
                        
                except Exception as e:
                    print(f"Error: {str(e)}")
                    
            elif cmd == 'attack':
                if not args:
                    print("[!] Usage: attack <id1> <id2> ...")
                    return True
                self.game.declare_attackers(player, args)
                print(f"Attacking with: {', '.join(args)}")
                print("Opponent can now declare blockers with 'block' command")
                
            elif cmd == 'block':
                # Parse blocking assignments
                if len(args) % 2 != 0:
                    print("[!] Usage: block <attacker_id> <blocker_id> <attacker_id> <blocker_id> ...")
                    return True
                    
                block_assignments = {}
                for i in range(0, len(args), 2):
                    attacker_id = args[i]
                    blocker_id = args[i + 1]
                    if attacker_id not in block_assignments:
                        block_assignments[attacker_id] = []
                    block_assignments[attacker_id].append(blocker_id)
                    
                # Find opponent dynamically
                state = self.game.get_game_state()
                all_players = [key for key in state.keys() if key not in ['active_player', 'turn', 'phase', 'turn_number', 'current_player', 'battlefield', 'lands_played_this_turn', 'combat']]
                opponent = next((p for p in all_players if p != player), player)
                self.game.declare_blockers(opponent, block_assignments)
                
                # Automatically resolve combat
                print("Resolving combat...")
                self.game.calculate_combat_damage()
                self.game.resolve_damage_queue()
                print("Combat resolved.")
                
                # Check for win condition
                winner = self.game.check_win_condition()
                if winner:
                    print(f"\nGAME OVER. {winner} wins.")
                    return False
                    
            elif cmd == 'end':
                return not self.end_turn()
                
            elif cmd == 'hand':
                self.show_hand()
                
            elif cmd == 'board':
                self.show_board()
                
            elif cmd == 'state':
                self.show_state()
                
            elif cmd == 'graveyard':
                self.show_graveyard()
                
            elif cmd == 'deck':
                self.show_deck()
                
            elif cmd == 'mulligan':
                state = self.game.get_game_state()
                turn = state.get('turn', 1)
                if self.is_mulligan_available(player, turn):
                    self.perform_mulligan(player)
                    self.show_game_info()  # Refresh display
                else:
                    if not self.mulligan_available.get(player, False):
                        print("Error: You have already used your mulligan")
                    else:
                        print("Error: Mulligan only available on your first turn")
                
            # Admin commands
            elif cmd == 'mana':
                if len(args) < 2:
                    print("[!] Usage: mana <color> <amount>")
                    return True
                color = args[0].lower()
                try:
                    amount = int(args[1])
                    if color in ['green', 'blue', 'red']:
                        state[player][f'{color}_mana'] += amount
                        self.game._save_state(state)
                        print(f"Added {amount} {color} mana")
                    else:
                        print("[!] Invalid color. Use: green, blue, red")
                except ValueError:
                    print("[!] Amount must be a number")
                    
            elif cmd == 'admindraw':
                deck = state[player].get('deck', [])
                if not deck:
                    print("[!] Deck is empty")
                    return True
                    
                if args:
                    # Draw specific card by ID (if it exists in deck)
                    target_name = ' '.join(args)
                    for i, card in enumerate(deck):
                        if card['name'].lower() == target_name.lower():
                            # Move card to hand
                            card_id = str(max([int(k) for k in state[player]['hand'].keys()] + [0]) + 1)
                            state[player]['hand'][card_id] = deck.pop(i)
                            self.game._save_state(state)
                            print(f"Drew {card['name']} (ID: {card_id})")
                            return True
                    print(f"[!] Card '{target_name}' not found in deck")
                else:
                    # Draw random card
                    self.game.draw_card(player)
                    print(f"Drew random card")
                    
            else:
                print(f"[!] Unknown command: {cmd}")
                print("Available: land, play, tap, attack, block, end, mulligan, hand, board, state, graveyard, deck")
                
        except Exception as e:
            print(f"Error: {str(e)}")
            
        return True
        
    def run(self):
        """Main game loop."""
        print("Welcome to Wizard")
        print("Type 'help' for commands")
        
        while True:
            try:
                # Get current player for prompt
                state = self.game.get_game_state()
                current_player = state['active_player']
                
                # Get input with player name in prompt
                user_input = input(f"\n{current_player}> ").strip()
                if not user_input:
                    continue
                    
                # Parse command
                parts = user_input.split()
                cmd = parts[0].lower()
                args = parts[1:]
                
                # Special commands
                if cmd in ['quit', 'exit']:
                    print("Thanks for playing!")
                    break
                elif cmd == 'help':
                    print("\nCOMMANDS:")
                    print("  land <id>     - Play land")
                    print("  play <id>     - Play creature")
                    print("  tap <id> [color] - Tap for mana (dual lands need color)")
                    print("  attack <ids>  - Declare attackers")
                    print("  block <pairs> - Declare blockers")
                    print("  end           - End turn")
                    print("  mulligan      - Redraw opening hand (first turn only)")
                    print("  hand          - Show your hand")
                    print("  board         - Show battlefield")
                    print("  state         - Show full game state")
                    print("  graveyard     - Show graveyard")
                    print("  deck          - Show deck")
                    print("  mana <c> <n>  - Add mana (admin)")
                    print("  admindraw [card] - Draw card (admin)")
                    continue
                    
                # Handle game command
                should_continue = self.handle_command(cmd, args)
                if not should_continue:
                    break
                    
            except KeyboardInterrupt:
                print("\nGame interrupted.")
                break
            except Exception as e:
                print(f"[!] Unexpected error: {e}")
                continue

if __name__ == "__main__":
    game = WizardCLI()
    game.run()