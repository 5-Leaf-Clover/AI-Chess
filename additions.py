# two player chess in python with Pygame!
# pawn double space checking
# castling
# en passant
# pawn promotion

import pygame
from constants import *

pygame.init()


# draw main game board
def draw_board():
    for i in range(32):
        column = i % 4
        row = i // 4
        if row % 2 == 0:
            pygame.draw.rect(screen, 'light gray', [px(600) - (column * px(200)), row * SQUARE, SQUARE, SQUARE])
        else:
            pygame.draw.rect(screen, 'light gray', [px(700) - (column * px(200)), row * SQUARE, SQUARE, SQUARE])
    pygame.draw.rect(screen, 'gold', [px(800), 0, px(200), HEIGHT], max(2, px(5)))
    for i in range(9):
        pygame.draw.line(screen, 'black', (0, SQUARE * i), (px(800), SQUARE * i), max(1, px(2)))
        pygame.draw.line(screen, 'black', (SQUARE * i, 0), (SQUARE * i, px(800)), max(1, px(2)))
    draw_forfeit_button()


# SECTION 6 UI refinement: the forfeit button now lives beside the board (the
# bottom of the right-hand sidebar), instead of in a strip underneath it.
def draw_forfeit_button():
    box = [px(800), px(700), px(200), px(100)]
    pygame.draw.rect(screen, 'gray', box)
    pygame.draw.rect(screen, 'gold', box, max(2, px(4)))
    text_surface = font.render('FORFEIT', True, 'black')
    text_rect = text_surface.get_rect(center=(box[0] + box[2] // 2, box[1] + box[3] // 2))
    screen.blit(text_surface, text_rect)


# trigger a pop-up message. kind is one of 'turn', 'illegal', 'check' -
# checkmate/stalemate use the dedicated "Grand Win" banner instead (see
# evaluate_game_end / draw_game_over) so we never stack two notifications.
def show_popup(message, color='gold', kind='turn'):
    global popup_message, popup_color, popup_timer, popup_type
    popup_message = message
    popup_color = color
    popup_type = kind
    popup_timer = POPUP_DURATION


# draw the active pop-up message (if any) over the top of the board.
# 'check' pop-ups get a red accent border plus a brief red screen-edge flash
# so they read as higher priority than an ordinary turn-change toast.
def draw_popup():
    global popup_timer
    if popup_timer > 0:
        box_width, box_height = px(460), px(70)
        box_x = (px(800) - box_width) // 2
        box_y = px(15)
        accent = 'red' if popup_type == 'check' else popup_color
        border_width = max(3, px(7)) if popup_type == 'check' else max(2, px(5))
        pygame.draw.rect(screen, 'black', [box_x, box_y, box_width, box_height])
        pygame.draw.rect(screen, accent, [box_x, box_y, box_width, box_height], border_width)
        text_surface = medium_font.render(popup_message, True, 'white')
        text_rect = text_surface.get_rect(center=(box_x + box_width // 2, box_y + box_height // 2))
        screen.blit(text_surface, text_rect)
        if popup_type == 'check' and counter < 15:
            pygame.draw.rect(screen, 'red', [0, 0, px(800), HEIGHT], max(2, px(6)))
        popup_timer -= 1


# draw pieces onto board
def draw_pieces():
    for i in range(len(white_pieces)):
        index = piece_list.index(white_pieces[i])
        if white_pieces[i] == 'pawn':
            screen.blit(white_pawn, (white_locations[i][0] * SQUARE + px(22), white_locations[i][1] * SQUARE + px(30)))
        else:
            screen.blit(white_images[index], (white_locations[i][0] * SQUARE + px(10), white_locations[i][1] * SQUARE + px(10)))
        if turn_step < 2:
            if selection == i:
                pygame.draw.rect(screen, 'red', [white_locations[i][0] * SQUARE + px(1), white_locations[i][1] * SQUARE + px(1),
                                                 SQUARE, SQUARE], max(1, px(2)))

    for i in range(len(black_pieces)):
        index = piece_list.index(black_pieces[i])
        if black_pieces[i] == 'pawn':
            screen.blit(black_pawn, (black_locations[i][0] * SQUARE + px(22), black_locations[i][1] * SQUARE + px(30)))
        else:
            screen.blit(black_images[index], (black_locations[i][0] * SQUARE + px(10), black_locations[i][1] * SQUARE + px(10)))
        if turn_step >= 2:
            if selection == i:
                pygame.draw.rect(screen, 'blue', [black_locations[i][0] * SQUARE + px(1), black_locations[i][1] * SQUARE + px(1),
                                                  SQUARE, SQUARE], max(1, px(2)))


# function to check all pieces valid options on board
# include_castling=False is used internally (see check_castling) to get a
# plain attack map without recursing back into castling legality checks.
def check_options(pieces, locations, turn, include_castling=True):
    global white_castle_moves, black_castle_moves
    moves_list = []
    all_moves_list = []
    for i in range((len(pieces))):
        location = locations[i]
        piece = pieces[i]
        if piece == 'pawn':
            moves_list = check_pawn(location, turn)
        elif piece == 'rook':
            moves_list = check_rook(location, turn)
        elif piece == 'knight':
            moves_list = check_knight(location, turn)
        elif piece == 'bishop':
            moves_list = check_bishop(location, turn)
        elif piece == 'queen':
            moves_list = check_queen(location, turn)
        elif piece == 'king':
            moves_list, castle_moves = check_king(location, turn, include_castling)
            if include_castling:
                # BUGFIX: this used to be stored in a single shared global
                # that white's computation (always run last each turn cycle)
                # unconditionally overwrote, so black's own castling options
                # were invisible to the click handler on black's turn. Each
                # color now keeps its own list.
                if turn == 'white':
                    white_castle_moves = castle_moves
                else:
                    black_castle_moves = castle_moves
        all_moves_list.append(moves_list)
    return all_moves_list


# check king valid moves
def check_king(position, color, include_castling=True):
    moves_list = []
    castle_moves = check_castling(color) if include_castling else []
    if color == 'white':
        enemies_list = black_locations
        friends_list = white_locations
    else:
        friends_list = black_locations
        enemies_list = white_locations
    # 8 squares to check for kings, they can go one square any direction
    targets = [(1, 0), (1, 1), (1, -1), (-1, 0), (-1, 1), (-1, -1), (0, 1), (0, -1)]
    for i in range(8):
        target = (position[0] + targets[i][0], position[1] + targets[i][1])
        if target not in friends_list and 0 <= target[0] <= 7 and 0 <= target[1] <= 7:
            moves_list.append(target)
    return moves_list, castle_moves


# check queen valid moves
def check_queen(position, color):
    moves_list = check_bishop(position, color)
    second_list = check_rook(position, color)
    for i in range(len(second_list)):
        moves_list.append(second_list[i])
    return moves_list


# check bishop moves
def check_bishop(position, color):
    moves_list = []
    if color == 'white':
        enemies_list = black_locations
        friends_list = white_locations
    else:
        friends_list = black_locations
        enemies_list = white_locations
    for i in range(4):  # up-right, up-left, down-right, down-left
        path = True
        chain = 1
        if i == 0:
            x = 1
            y = -1
        elif i == 1:
            x = -1
            y = -1
        elif i == 2:
            x = 1
            y = 1
        else:
            x = -1
            y = 1
        while path:
            if (position[0] + (chain * x), position[1] + (chain * y)) not in friends_list and \
                    0 <= position[0] + (chain * x) <= 7 and 0 <= position[1] + (chain * y) <= 7:
                moves_list.append((position[0] + (chain * x), position[1] + (chain * y)))
                if (position[0] + (chain * x), position[1] + (chain * y)) in enemies_list:
                    path = False
                chain += 1
            else:
                path = False
    return moves_list


# check rook moves
def check_rook(position, color):
    moves_list = []
    if color == 'white':
        enemies_list = black_locations
        friends_list = white_locations
    else:
        friends_list = black_locations
        enemies_list = white_locations
    for i in range(4):  # down, up, right, left
        path = True
        chain = 1
        if i == 0:
            x = 0
            y = 1
        elif i == 1:
            x = 0
            y = -1
        elif i == 2:
            x = 1
            y = 0
        else:
            x = -1
            y = 0
        while path:
            if (position[0] + (chain * x), position[1] + (chain * y)) not in friends_list and \
                    0 <= position[0] + (chain * x) <= 7 and 0 <= position[1] + (chain * y) <= 7:
                moves_list.append((position[0] + (chain * x), position[1] + (chain * y)))
                if (position[0] + (chain * x), position[1] + (chain * y)) in enemies_list:
                    path = False
                chain += 1
            else:
                path = False
    return moves_list


# check valid pawn moves
def check_pawn(position, color):
    moves_list = []
    if color == 'white':
        if (position[0], position[1] + 1) not in white_locations and \
                (position[0], position[1] + 1) not in black_locations and position[1] < 7:
            moves_list.append((position[0], position[1] + 1))
            # indent the check for two spaces ahead, so it is only checked if one space ahead is also open
            if (position[0], position[1] + 2) not in white_locations and \
                    (position[0], position[1] + 2) not in black_locations and position[1] == 1:
                moves_list.append((position[0], position[1] + 2))
        if (position[0] + 1, position[1] + 1) in black_locations:
            moves_list.append((position[0] + 1, position[1] + 1))
        if (position[0] - 1, position[1] + 1) in black_locations:
            moves_list.append((position[0] - 1, position[1] + 1))
        # add en passant move checker
        if (position[0] + 1, position[1] + 1) == black_ep:
            moves_list.append((position[0] + 1, position[1] + 1))
        if (position[0] - 1, position[1] + 1) == black_ep:
            moves_list.append((position[0] - 1, position[1] + 1))
    else:
        if (position[0], position[1] - 1) not in white_locations and \
                (position[0], position[1] - 1) not in black_locations and position[1] > 0:
            moves_list.append((position[0], position[1] - 1))
            # indent the check for two spaces ahead, so it is only checked if one space ahead is also open
            if (position[0], position[1] - 2) not in white_locations and \
                    (position[0], position[1] - 2) not in black_locations and position[1] == 6:
                moves_list.append((position[0], position[1] - 2))
        if (position[0] + 1, position[1] - 1) in white_locations:
            moves_list.append((position[0] + 1, position[1] - 1))
        if (position[0] - 1, position[1] - 1) in white_locations:
            moves_list.append((position[0] - 1, position[1] - 1))
        # add en passant move checker
        if (position[0] + 1, position[1] - 1) == white_ep:
            moves_list.append((position[0] + 1, position[1] - 1))
        if (position[0] - 1, position[1] - 1) == white_ep:
            moves_list.append((position[0] - 1, position[1] - 1))
    return moves_list


# check valid knight moves
def check_knight(position, color):
    moves_list = []
    if color == 'white':
        enemies_list = black_locations
        friends_list = white_locations
    else:
        friends_list = black_locations
        enemies_list = white_locations
    # 8 squares to check for knights, they can go two squares in one direction and one in another
    targets = [(1, 2), (1, -2), (2, 1), (2, -1), (-1, 2), (-1, -2), (-2, 1), (-2, -1)]
    for i in range(8):
        target = (position[0] + targets[i][0], position[1] + targets[i][1])
        if target not in friends_list and 0 <= target[0] <= 7 and 0 <= target[1] <= 7:
            moves_list.append(target)
    return moves_list




# --- SECTION 3: proper check / legal-move / checkmate / stalemate handling -
# A pseudo-legal move (from check_options) only obeys how a piece is allowed
# to travel. It says nothing about whether making that move would leave your
# own king under attack. The functions below simulate each candidate move on
# a scratch copy of the board and reject any that leave (or put) the mover's
# own king in check - this is what actually catches pins, and lets us detect
# checkmate/stalemate instead of only noticing a king has been captured.

def _king_square(pieces, locations):
    if 'king' in pieces:
        return locations[pieces.index('king')]
    return None


def move_leaves_king_in_check(mover_color, from_index, to_square):
    """Simulate one move and report whether the mover's own king would be
    left in check afterward (covers pins and en-passant discoveries).

    Note: the movement-checking functions below (check_bishop, check_rook,
    etc.) read the board off the module-level white_/black_ globals rather
    than any arguments passed to them, so a plain "pass in copies" approach
    wouldn't actually be evaluated against the simulated position. Instead,
    we build the simulated lists, temporarily swap them into those globals,
    ask check_options for the resulting attack map, then restore the real
    board - guaranteeing the simulation is evaluated correctly.
    """
    global white_pieces, white_locations, black_pieces, black_locations
    real_white_pieces, real_white_locations = white_pieces, white_locations
    real_black_pieces, real_black_locations = black_pieces, black_locations

    sim_white_pieces, sim_white_locations = white_pieces[:], white_locations[:]
    sim_black_pieces, sim_black_locations = black_pieces[:], black_locations[:]

    if mover_color == 'white':
        own_pieces, own_locations = sim_white_pieces, sim_white_locations
        enemy_pieces, enemy_locations = sim_black_pieces, sim_black_locations
        ep_square, ep_rank_step = black_ep, -1
    else:
        own_pieces, own_locations = sim_black_pieces, sim_black_locations
        enemy_pieces, enemy_locations = sim_white_pieces, sim_white_locations
        ep_square, ep_rank_step = white_ep, 1

    moving_piece = own_pieces[from_index]
    own_locations[from_index] = to_square
    if to_square in enemy_locations:
        captured = enemy_locations.index(to_square)
        enemy_pieces.pop(captured)
        enemy_locations.pop(captured)
    elif moving_piece == 'pawn' and to_square == ep_square:
        captured_square = (ep_square[0], ep_square[1] + ep_rank_step)
        if captured_square in enemy_locations:
            captured = enemy_locations.index(captured_square)
            enemy_pieces.pop(captured)
            enemy_locations.pop(captured)

    king_square = to_square if moving_piece == 'king' else _king_square(own_pieces, own_locations)

    white_pieces, white_locations = sim_white_pieces, sim_white_locations
    black_pieces, black_locations = sim_black_pieces, sim_black_locations
    try:
        if king_square is None:
            return False
        enemy_turn = 'black' if mover_color == 'white' else 'white'
        # include_castling=False: this is only an attack-map probe against a
        # throwaway simulated board. Without this, check_options would also
        # recompute (and overwrite) the real white_castle_moves/
        # black_castle_moves globals with values based on the simulated
        # board - and since this function runs on every candidate move for
        # every piece each frame, that would constantly corrupt real
        # castling state right after we restore the real piece lists below.
        attacked_squares = check_options(enemy_pieces, enemy_locations, enemy_turn, include_castling=False)
        return any(king_square in moves for moves in attacked_squares)
    finally:
        white_pieces, white_locations = real_white_pieces, real_white_locations
        black_pieces, black_locations = real_black_pieces, real_black_locations


def king_in_check(color):
    if color == 'white':
        king_square = _king_square(white_pieces, white_locations)
        attacker_options = black_options
    else:
        king_square = _king_square(black_pieces, black_locations)
        attacker_options = white_options
    if king_square is None:
        return False
    return any(king_square in moves for moves in attacker_options)


def has_any_legal_move(color):
    if color == 'white':
        pieces, options = white_pieces, white_options
    else:
        pieces, options = black_pieces, black_options
    for i in range(len(pieces)):
        for move in options[i]:
            if not move_leaves_king_in_check(color, i, move):
                return True
    return False


def evaluate_game_end(color_to_move):
    """Call right after black_options/white_options are refreshed for the
    side about to move - i.e. right after the attack map is generated, so
    the check pop-up can never lag behind or miss a discovered check.

    Authoritatively sets checkmate/stalemate (replacing any guess from
    king-capture alone) and, per Section 2's revision, fires a dedicated
    'check' pop-up that takes priority over (and merges with) the plain
    turn-change pop-up when the side to move is in check but not mated."""
    global game_over, winner, end_reason, check_flash_timer
    in_check = king_in_check(color_to_move)
    mover_label = color_to_move.capitalize()

    if has_any_legal_move(color_to_move):
        if in_check:
            # Check pop-up takes priority over / merges with the turn pop-up
            # that was already shown by the caller - this call supersedes it
            # rather than stacking a second notification.
            check_flash_timer = CHECK_FLASH_DURATION
            show_popup(f"Check! {mover_label}'s turn", 'red')
        return

    game_over = True
    if in_check:
        winner = 'black' if color_to_move == 'white' else 'white'
        end_reason = 'checkmate'
        show_popup(f"Checkmate! {winner.capitalize()} wins!", 'gold')
    else:
        winner = 'draw'
        end_reason = 'stalemate'
        # Distinct, neutral draw pop-up - must never share copy/styling with
        # the win banner (Section 3 revision).
        show_popup('Stalemate - Game Drawn', 'light gray')


# brief, distinct screen-edge flash that accompanies the check pop-up
def draw_check_flash():
    global check_flash_timer
    if check_flash_timer > 0:
        pygame.draw.rect(screen, 'red', [0, 0, px(800), px(800)], max(3, px(10)))
        check_flash_timer -= 1


# check for valid (and LEGAL - see above) moves for just the selected piece
def check_valid_moves():
    if turn_step < 2:
        options_list = white_options
        mover_color = 'white'
    else:
        options_list = black_options
        mover_color = 'black'
    pseudo_legal = options_list[selection]
    return [move for move in pseudo_legal if not move_leaves_king_in_check(mover_color, selection, move)]


# draw valid moves on screen
def draw_valid(moves):
    if turn_step < 2:
        color = 'red'
    else:
        color = 'blue'
    for i in range(len(moves)):
        pygame.draw.circle(screen, color, (moves[i][0] * SQUARE + SQUARE // 2, moves[i][1] * SQUARE + SQUARE // 2), max(2, px(5)))


# draw captured pieces on side of screen, in two clearly separated trays
def draw_captured():
    # FIX (Section 6 QA note): captured_pieces_white holds the pieces WHITE
    # has captured - i.e. pieces taken FROM black, so this tray is "Black
    # lost". captured_pieces_black holds pieces taken FROM white, so that
    # tray is "White lost". The headings were previously swapped.
    screen.blit(font.render('Black lost', True, 'black'), (px(805), px(650)))
    for i in range(len(captured_pieces_white)):
        captured_piece = captured_pieces_white[i]
        index = piece_list.index(captured_piece)
        screen.blit(small_black_images[index], (px(825), px(5) + px(50) * i))
    pygame.draw.line(screen, 'black', (px(900), 0), (px(900), px(690)), max(1, px(2)))
    screen.blit(font.render('White lost', True, 'black'), (px(905), px(650)))
    for i in range(len(captured_pieces_black)):
        captured_piece = captured_pieces_black[i]
        index = piece_list.index(captured_piece)
        screen.blit(small_white_images[index], (px(925), px(5) + px(50) * i))


# draw a flashing square around king if in check
def draw_check():
    global check
    check = False
    if turn_step < 2:
        if 'king' in white_pieces:
            king_index = white_pieces.index('king')
            king_location = white_locations[king_index]
            for i in range(len(black_options)):
                if king_location in black_options[i]:
                    check = True
                    if counter < 15:
                        pygame.draw.rect(screen, 'dark red', [white_locations[king_index][0] * SQUARE + px(1),
                                                              white_locations[king_index][1] * SQUARE + px(1), SQUARE, SQUARE], max(2, px(5)))
    else:
        if 'king' in black_pieces:
            king_index = black_pieces.index('king')
            king_location = black_locations[king_index]
            for i in range(len(white_options)):
                if king_location in white_options[i]:
                    check = True
                    if counter < 15:
                        pygame.draw.rect(screen, 'dark blue', [black_locations[king_index][0] * SQUARE + px(1),
                                                               black_locations[king_index][1] * SQUARE + px(1), SQUARE, SQUARE], max(2, px(5)))


def draw_game_over():
    # flashing full-board overlay flash for a "grand win" moment
    if counter < 15:
        flash = pygame.Surface((px(800), HEIGHT))
        flash.set_alpha(90)
        flash.fill('gold' if winner != 'draw' else 'light gray')
        screen.blit(flash, (0, 0))

    box_width, box_height = px(560), px(160)
    box_x = (px(800) - box_width) // 2
    box_y = (px(800) - box_height) // 2
    pygame.draw.rect(screen, 'black', [box_x, box_y, box_width, box_height])
    pygame.draw.rect(screen, 'gold', [box_x, box_y, box_width, box_height], max(2, px(5)))

    if winner == 'draw':
        headline = 'Stalemate - Game Drawn'
    elif end_reason == 'forfeit':
        headline = f'{winner.capitalize()} Wins by Forfeit!'
    else:
        headline = f'Checkmate - {winner.capitalize()} Wins!'
    headline_surface = medium_font.render(headline, True, 'white')
    headline_rect = headline_surface.get_rect(center=(box_x + box_width // 2, box_y + px(45)))
    screen.blit(headline_surface, headline_rect)

    option_surface = font.render('ENTER: Rematch     ESC: Exit', True, 'white')
    option_rect = option_surface.get_rect(center=(box_x + box_width // 2, box_y + px(100)))
    screen.blit(option_surface, option_rect)


# --- SECTION 3a: persistent winner tag ---------------------------------
# Unlike the transient turn/check toasts, this badge is driven by the same
# authoritative game_over/winner state as checkmate detection itself, and
# stays on screen for as long as game_over is True - through the celebratory
# flash fading, and through the Rematch/Exit choice - only clearing when a
# new game actually starts. It lives in the sidebar (not on top of the
# board) so it never obscures the mating position.
#
# Note: this codebase has no per-player name/clock panels yet (that's the
# Section 8 "live clocks" territory), so this is a single centered badge
# rather than a gold-badge-for-winner / greyed-out-panel-for-loser pair as
# described - the win/draw distinction itself is still fully honored.
def draw_winner_tag():
    if not game_over:
        return
    if winner == 'draw':
        text, badge_color, text_color = 'Draw', 'light gray', 'black'
    else:
        text, badge_color, text_color = f'Winner: {winner.capitalize()}', 'gold', 'black'
    badge_w, badge_h = px(190), px(50)
    badge_x = px(800) + (px(200) - badge_w) // 2
    badge_y = px(10)
    pygame.draw.rect(screen, 'black', [badge_x, badge_y, badge_w, badge_h])
    pygame.draw.rect(screen, badge_color, [badge_x, badge_y, badge_w, badge_h], max(2, px(4)))
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=(badge_x + badge_w // 2, badge_y + badge_h // 2))
    screen.blit(text_surface, text_rect)


# check en passant because people on the internet won't stop bugging me for it
def check_ep(old_coords, new_coords):
    if turn_step <= 1:
        index = white_locations.index(old_coords)
        ep_coords = (new_coords[0], new_coords[1] - 1)
        piece = white_pieces[index]
    else:
        index = black_locations.index(old_coords)
        ep_coords = (new_coords[0], new_coords[1] + 1)
        piece = black_pieces[index]
    if piece == 'pawn' and abs(old_coords[1] - new_coords[1]) > 1:
        # if piece was pawn and moved two spaces, return EP coords as defined above
        pass
    else:
        ep_coords = (100, 100)
    return ep_coords


# add castling
def check_castling(color):
    """Return valid castle moves as [(king_destination, rook_destination), ...]
    for the given color's king. A castle is only legal if:
      - neither the king nor that specific rook has moved before (even if
        either piece later moved back to its original square - the moved
        flags are one-way switches, never reset by returning "home"),
      - every square between the king and rook is empty,
      - the king is not currently in check,
      - the king does not pass through or land on a square under attack.

    The opponent's attack map is recomputed fresh right here, rather than
    trusting the ambient white_options/black_options globals - those can be
    one move stale depending on call order, which would let castling briefly
    ignore a check that was just delivered/revealed. include_castling=False
    on that inner call stops it from recursing back into this function for
    the opponent's own king (their castling options aren't attacks and are
    irrelevant to this check anyway).
    """
    castle_moves = []
    if color == 'white':
        pieces, locations, moved = white_pieces, white_locations, white_moved
        enemy_pieces, enemy_locations, enemy_color = black_pieces, black_locations, 'black'
    else:
        pieces, locations, moved = black_pieces, black_locations, black_moved
        enemy_pieces, enemy_locations, enemy_color = white_pieces, white_locations, 'white'

    if 'king' not in pieces:
        return castle_moves
    king_index = pieces.index('king')
    king_pos = locations[king_index]
    if moved[king_index]:
        return castle_moves

    enemy_attacks = check_options(enemy_pieces, enemy_locations, enemy_color, include_castling=False)

    def attacked(square):
        # BUGFIX: the old code tested `square in enemy_options`, but
        # enemy_options is a list of per-piece move lists, not a flat set of
        # attacked squares - a tuple can never equal one of those inner
        # lists, so that test was always False and never actually blocked
        # castling through/into check. This flattens it correctly.
        return any(square in moves for moves in enemy_attacks)

    if attacked(king_pos):
        return castle_moves  # king is currently in check

    for i in range(len(pieces)):
        if pieces[i] != 'rook' or moved[i]:
            continue
        rook_pos = locations[i]
        if rook_pos[1] != king_pos[1]:
            continue  # must be on the same rank as the king
        direction = 1 if rook_pos[0] > king_pos[0] else -1

        # every square strictly between king and rook must be empty
        between_squares = []
        step = king_pos[0] + direction
        while step != rook_pos[0]:
            between_squares.append((step, king_pos[1]))
            step += direction
        if any(sq in white_locations or sq in black_locations for sq in between_squares):
            continue

        # the two squares the king actually crosses/lands on must be safe
        king_path = [(king_pos[0] + direction, king_pos[1]), (king_pos[0] + 2 * direction, king_pos[1])]
        if any(attacked(sq) for sq in king_path):
            continue

        castle_moves.append((king_path[1], king_path[0]))  # (king_destination, rook_destination)
    return castle_moves


def draw_castling(moves):
    if turn_step < 2:
        color = 'red'
    else:
        color = 'blue'
    for i in range(len(moves)):
        pygame.draw.circle(screen, color, (moves[i][0][0] * SQUARE + SQUARE // 2, moves[i][0][1] * SQUARE + px(70)), max(2, px(8)))
        screen.blit(font.render('king', True, 'black'), (moves[i][0][0] * SQUARE + px(30), moves[i][0][1] * SQUARE + px(70)))
        pygame.draw.circle(screen, color, (moves[i][1][0] * SQUARE + SQUARE // 2, moves[i][1][1] * SQUARE + px(70)), max(2, px(8)))
        screen.blit(font.render('rook', True, 'black'),
                    (moves[i][1][0] * SQUARE + px(30), moves[i][1][1] * SQUARE + px(70)))
        pygame.draw.line(screen, color, (moves[i][0][0] * SQUARE + SQUARE // 2, moves[i][0][1] * SQUARE + px(70)),
                         (moves[i][1][0] * SQUARE + SQUARE // 2, moves[i][1][1] * SQUARE + px(70)), max(1, px(2)))


# add pawn promotion
def check_promotion():
    pawn_indexes = []
    white_promotion = False
    black_promotion = False
    promote_index = 100
    for i in range(len(white_pieces)):
        if white_pieces[i] == 'pawn':
            pawn_indexes.append(i)
    for i in range(len(pawn_indexes)):
        if white_locations[pawn_indexes[i]][1] == 7:
            white_promotion = True
            promote_index = pawn_indexes[i]
    pawn_indexes = []
    for i in range(len(black_pieces)):
        if black_pieces[i] == 'pawn':
            pawn_indexes.append(i)
    for i in range(len(pawn_indexes)):
        if black_locations[pawn_indexes[i]][1] == 0:
            black_promotion = True
            promote_index = pawn_indexes[i]
    return white_promotion, black_promotion, promote_index


def draw_promotion():
    pygame.draw.rect(screen, 'dark gray', [px(800), 0, px(200), px(420)])
    if white_promote:
        color = 'white'
        for i in range(len(white_promotions)):
            piece = white_promotions[i]
            index = piece_list.index(piece)
            screen.blit(white_images[index], (px(860), px(5) + SQUARE * i))
    elif black_promote:
        color = 'black'
        for i in range(len(black_promotions)):
            piece = black_promotions[i]
            index = piece_list.index(piece)
            screen.blit(black_images[index], (px(860), px(5) + SQUARE * i))
    pygame.draw.rect(screen, color, [px(800), 0, px(200), px(420)], max(2, px(8)))


def check_promo_select():
    mouse_pos = pygame.mouse.get_pos()
    left_click = pygame.mouse.get_pressed()[0]
    x_pos = mouse_pos[0] // SQUARE
    y_pos = mouse_pos[1] // SQUARE
    if white_promote and left_click and x_pos > 7 and y_pos < 4:
        white_pieces[promo_index] = white_promotions[y_pos]
    elif black_promote and left_click and x_pos > 7 and y_pos < 4:
        black_pieces[promo_index] = black_promotions[y_pos]


# main game loop
black_options = check_options(black_pieces, black_locations, 'black')
white_options = check_options(white_pieces, white_locations, 'white')
show_popup("White's Turn!", 'red')
run = True
while run:
    timer.tick(fps)
    if counter < 30:
        counter += 1
    else:
        counter = 0
    screen.fill('dark gray')
    draw_board()
    draw_pieces()
    draw_captured()
    draw_check()
    draw_check_flash()
    if not game_over:
        white_promote, black_promote, promo_index = check_promotion()
        if white_promote or black_promote:
            draw_promotion()
            show_popup('Select a piece to promote to!', 'gold')
            check_promo_select()
    if selection != 100:
        valid_moves = check_valid_moves()
        draw_valid(valid_moves)
        if selected_piece == 'king':
            current_castle_moves = white_castle_moves if turn_step < 2 else black_castle_moves
            draw_castling(current_castle_moves)
    draw_popup()
    # event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not game_over:
            x_coord = event.pos[0] // SQUARE
            y_coord = event.pos[1] // SQUARE
            click_coords = (x_coord, y_coord)
            if turn_step <= 1:
                previous_selection = selection
                move_made = False
                if click_coords == (8, 7) or click_coords == (9, 7):
                    winner = 'black'
                    end_reason = 'forfeit'
                if click_coords in white_locations:
                    selection = white_locations.index(click_coords)
                    # check what piece is selected, so you can only draw castling moves if king is selected
                    selected_piece = white_pieces[selection]
                    if turn_step == 0:
                        turn_step = 1
                if click_coords in valid_moves and selection != 100:
                    white_ep = check_ep(white_locations[selection], click_coords)
                    white_locations[selection] = click_coords
                    white_moved[selection] = True
                    if click_coords in black_locations:
                        black_piece = black_locations.index(click_coords)
                        captured_pieces_white.append(black_pieces[black_piece])
                        if black_pieces[black_piece] == 'king':
                            winner = 'white'
                            end_reason = 'checkmate'
                        black_pieces.pop(black_piece)
                        black_locations.pop(black_piece)
                        black_moved.pop(black_piece)
                    # adding check if en passant pawn was captured
                    if click_coords == black_ep:
                        black_piece = black_locations.index((black_ep[0], black_ep[1] - 1))
                        captured_pieces_white.append(black_pieces[black_piece])
                        black_pieces.pop(black_piece)
                        black_locations.pop(black_piece)
                        black_moved.pop(black_piece)
                    black_options = check_options(black_pieces, black_locations, 'black')
                    white_options = check_options(white_pieces, white_locations, 'white')
                    turn_step = 2
                    selection = 100
                    valid_moves = []
                    move_made = True
                    show_popup("Black's Turn!", 'blue')
                    evaluate_game_end('black')
                # add option to castle
                elif selection != 100 and selected_piece == 'king':
                    for q in range(len(white_castle_moves)):
                        if click_coords == white_castle_moves[q][0]:
                            white_locations[selection] = click_coords
                            white_moved[selection] = True
                            if click_coords == (1, 0):
                                rook_coords = (0, 0)
                            else:
                                rook_coords = (7, 0)
                            rook_index = white_locations.index(rook_coords)
                            white_locations[rook_index] = white_castle_moves[q][1]
                            white_moved[rook_index] = True
                            black_options = check_options(black_pieces, black_locations, 'black')
                            white_options = check_options(white_pieces, white_locations, 'white')
                            turn_step = 2
                            selection = 100
                            valid_moves = []
                            move_made = True
                            show_popup("Black's Turn!", 'blue')
                            evaluate_game_end('black')
                # warn the player if they clicked somewhere invalid while a piece was selected
                if not move_made and previous_selection != 100 and selection == previous_selection \
                        and click_coords not in white_locations \
                        and click_coords != (8, 7) and click_coords != (9, 7):
                    show_popup('Illegal Move!', 'orange')
            if turn_step > 1:
                previous_selection = selection
                move_made = False
                if click_coords == (8, 7) or click_coords == (9, 7):
                    winner = 'white'
                    end_reason = 'forfeit'
                if click_coords in black_locations:
                    selection = black_locations.index(click_coords)
                    # check what piece is selected, so you can only draw castling moves if king is selected
                    selected_piece = black_pieces[selection]
                    if turn_step == 2:
                        turn_step = 3
                if click_coords in valid_moves and selection != 100:
                    black_ep = check_ep(black_locations[selection], click_coords)
                    black_locations[selection] = click_coords
                    black_moved[selection] = True
                    if click_coords in white_locations:
                        white_piece = white_locations.index(click_coords)
                        captured_pieces_black.append(white_pieces[white_piece])
                        if white_pieces[white_piece] == 'king':
                            winner = 'black'
                            end_reason = 'checkmate'
                        white_pieces.pop(white_piece)
                        white_locations.pop(white_piece)
                        white_moved.pop(white_piece)
                    if click_coords == white_ep:
                        white_piece = white_locations.index((white_ep[0], white_ep[1] + 1))
                        captured_pieces_black.append(white_pieces[white_piece])
                        white_pieces.pop(white_piece)
                        white_locations.pop(white_piece)
                        white_moved.pop(white_piece)
                    black_options = check_options(black_pieces, black_locations, 'black')
                    white_options = check_options(white_pieces, white_locations, 'white')
                    turn_step = 0
                    selection = 100
                    valid_moves = []
                    move_made = True
                    show_popup("White's Turn!", 'red')
                    evaluate_game_end('white')
                # add option to castle
                elif selection != 100 and selected_piece == 'king':
                    for q in range(len(black_castle_moves)):
                        if click_coords == black_castle_moves[q][0]:
                            black_locations[selection] = click_coords
                            black_moved[selection] = True
                            if click_coords == (1, 7):
                                rook_coords = (0, 7)
                            else:
                                rook_coords = (7, 7)
                            rook_index = black_locations.index(rook_coords)
                            black_locations[rook_index] = black_castle_moves[q][1]
                            black_moved[rook_index] = True
                            black_options = check_options(black_pieces, black_locations, 'black')
                            white_options = check_options(white_pieces, white_locations, 'white')
                            turn_step = 0
                            selection = 100
                            valid_moves = []
                            move_made = True
                            show_popup("White's Turn!", 'red')
                            evaluate_game_end('white')
                # warn the player if they clicked somewhere invalid while a piece was selected
                if not move_made and previous_selection != 100 and selection == previous_selection \
                        and click_coords not in black_locations \
                        and click_coords != (8, 7) and click_coords != (9, 7):
                    show_popup('Illegal Move!', 'orange')
        if event.type == pygame.KEYDOWN and game_over:
            if event.key == pygame.K_ESCAPE:
                run = False
            if event.key == pygame.K_RETURN:
                game_over = False
                winner = ''
                end_reason = ''
                check_flash_timer = 0
                white_pieces = ['rook', 'knight', 'bishop', 'king', 'queen', 'bishop', 'knight', 'rook',
                                'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn']
                white_locations = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0),
                                   (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1)]
                white_moved = [False, False, False, False, False, False, False, False,
                               False, False, False, False, False, False, False, False]
                black_pieces = ['rook', 'knight', 'bishop', 'king', 'queen', 'bishop', 'knight', 'rook',
                                'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn', 'pawn']
                black_locations = [(0, 7), (1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7), (7, 7),
                                   (0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6), (7, 6)]
                black_moved = [False, False, False, False, False, False, False, False,
                               False, False, False, False, False, False, False, False]
                captured_pieces_white = []
                captured_pieces_black = []
                turn_step = 0
                selection = 100
                valid_moves = []
                black_options = check_options(black_pieces, black_locations, 'black')
                white_options = check_options(white_pieces, white_locations, 'white')
                show_popup("White's Turn!", 'red')

    if winner != '':
        game_over = True
        draw_game_over()
        draw_winner_tag()

    pygame.display.flip()
pygame.quit()
