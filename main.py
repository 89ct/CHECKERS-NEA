# from numpy import square
import pygame
from pygame import K_ESCAPE, KEYDOWN, MOUSEBUTTONDOWN, mixer
from copy import deepcopy
import time
import random
import sys

mixer.init() # initialise pygame mixer module
pygame.font.init() # initialise pygame font


# arial_large = pygame.font.SysFont("Sans", 80)
# arial = pygame.font.SysFont("Sans", 30)
# arial_med = pygame.font.SysFont("Sans", 20)

# Fonts to render text
arial_large = pygame.font.Font('Merchant.ttf', 80) 
arial = pygame.font.Font('Merchant.ttf', 30)
arial_med = pygame.font.Font('Merchant.ttf', 40)

WIDTH, HEIGHT = 800, 800 # Define width and height of display (in pixel)
ROWS, COLUMNS = 8, 8 # number of rows and columns on board
SQUARE_SIZE = WIDTH / COLUMNS # size of one tile
WIN = pygame.display.set_mode((WIDTH, HEIGHT)) # initialise display

# colours
BROWN_MOVE = (163, 122, 89) # brown tile
WHITE_MOVE = (216, 195, 163) # white tile

RED_SELECTED = (255, 150, 150) # selected

# basic colours
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

MOVE_SOUND = mixer.Sound("sound/move_sound.mp3") # sound which is going to be player when you move a piece
brown_tiles = [] # list of brown tiles

player = "ai" # second player: either "ai" or "human"

ai_dif = "easy" # ai difficulty: "easy"/"medium"/"hard"

# window name
pygame.display.set_caption("Checkers")


# def drawText(screen, pos, text, colour, size):  # draw text
#     font = pygame.font.Font('Merchant.ttf', size)
#     text = font.render(text, True, colour)
#     screen.blit(text, (pos.x, pos.y))

# Main Board Object
class Board:
    """
    Board Logic
    """
    def __init__(self):
        self.board = [] # board list that stores every row and piece in the row
        self.selected_piece = None # currently selected piece
        self.white_left = self.black_left = 12 # number of pieces left for white and black
        self.white_kings = self.black_kings = 0 # number of kings for white and black
        self.selected_tile = None # currently selected tile tuple of (row, col)
        self.take_valid = {} # valid takes {}
        self.create_board() # create the board
        self.white_turns = 0 # number of turns made by white
        self.black_turns = 0 # number of turns made by black
        self.turns = 0 # number of total turns

    def draw_squares(self):
        """
        Displays the black and white squares
        """
        WIN.fill(BLACK) # fill background
        for row in range(ROWS): # iterate through rows
            for col in range(row % 2, ROWS, 2): # iterate through every second column
                pygame.draw.rect(WIN, RED, (row * SQUARE_SIZE, col * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)) # draw tile of right colour
                brown_tiles.append((row, col)) # add tile to list

    def create_board(self):
        """
        Creates the board
        """
        for row in range(ROWS): # iterate through every row
            self.board.append([]) # add row to list
            for col in range(COLUMNS): # iterate through every column
                if col % 2 == (row + 1) % 2: # check if column is valid for a piece
                    if row < 3: # if top three rows
                        self.board[row].append(Piece(row, col, RED)) # add red piece
                    elif row > 4: # if bottom rows
                        self.board[row].append(Piece(row, col, WHITE)) # add white piece
                    else:
                        self.board[row].append(0) # add blank spot
                else:
                    self.board[row].append(0) # add blank spot

    def draw(self):
        """
        Display the entire GUI
        """
        self.draw_squares() # draw squares to background
        if self.selected_tile != None: # if there is a selected tile
            if self.selected_tile in brown_tiles: # if selected tile is brown tile
                # draw selected tile in right colour
                pygame.draw.rect(WIN, RED_SELECTED, (
                self.selected_tile[1] * SQUARE_SIZE, self.selected_tile[0] * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
            else:
                # draw selected tile in right colour
                pygame.draw.rect(WIN, RED_SELECTED, (
                self.selected_tile[1] * SQUARE_SIZE, self.selected_tile[0] * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        for row in range(ROWS): # for every row
            for col in range(COLUMNS): # for every col
                piece = self.board[row][col] # get piece on pos (row, col)
                if piece != 0: # if piece is not blank
                    piece.draw() # draw the piece

    def select(self, row, col):
        """
        Select pos
        """
        self.selected_tile = (row, col) # save selected pos

    def move(self, piece, row, col):
        """
        Move piece to destination
        """
        self.board[piece.row][piece.col], self.board[row][col] = self.board[row][col], self.board[piece.row][piece.col] # set current piece pos to blank, move piece to next pos
        piece.move(row, col) # move piece
        self.select(row, col) # select new pos
        self.turns += 1 # increment turns
        if piece.colour == WHITE: # if piece colour is white
            self.white_turns += 1 # incement white turns
        elif piece.colour == RED: # if piece colour is red
            self.black_turns += 1 # increment red turns

        if row == 7 and piece.colour == RED and piece.king == False: # check if piece got into last row and is not already a king
            piece.king = True # make piece to king
            self.black_kings += 1 # increment king counter
        elif row == 0 and piece.colour == WHITE and piece.king == False: # check same thing for white
            piece.king = True
            self.white_kings += 1

    def check_no_moves(self, colour):
        """
        Checks if there are no moves available for colour
        """
        for piece in self.get_all_pieces(colour): # iterate through every piece of player
            valid_moves = self.get_valid_moves(piece) # get every valid move for piece

            if len(valid_moves.keys()) != 0: # if there are valid moves
                return False # return False

        return True # return True if there are no valid moves for any piece

    def evaluate(self):
        """
        Evaluate a board position
        """
        # evaluate board by subtracting white left pieces from black left pieces, then add number of white kings multiplied by 0.5 and subtracted by black kings
        return self.white_left - self.black_left + (self.white_kings * 0.5 - self.black_kings * 0.5) + round(
            random.uniform(0.1, 0.3), 2) # in the end, add a small number to randomise the moves that have the same evaluation

    # def winner(self):
    #     if self.black_left <= 0:
    #         return WHITE
    #     elif self.white_left <= 0:
    #         return RED
    #
    #     return None

    def get_all_pieces(self, colour):
        """
        Get all pieces of certain colour that are on the board
        """
        pieces = [] # init pieces list
        for row in self.board: # iterate through every row
            for piece in row: # iterate through every piece in row
                if piece != 0 and piece.colour == colour: # if piece is not blank and is of right colour
                    pieces.append(piece) # add piece to pieces

        return pieces # return pieces list

    def get_piece(self, row, col):
        """
        Gets piece on specific position on baord
        """
        return self.board[row][col] # returns board on position (row, col)

    def remove(self, pieces):
        """
        Remove pieces from board
        """
        for piece in pieces: # iterate through pieces
            self.board[piece.row][piece.col] = 0 # set board piece pos to black (0)
            if piece != 0: # if piece is not blank
                if piece.colour == WHITE: # if piece is white
                    self.white_left -= 1 # subtract white pieces left
                else:
                    self.black_left -= 1 # subtract black pieces left

    def winner(self):
        """
        Check if player won
        """
        if self.white_left <= 0: # if no white pieces left
            return WHITE # return white as winner
        if self.black_left <= 0: # if no black pieces left
            return RED # return red as winner

        return None # return None for no winner

    def get_takes(self, colour):
        """
        Get all takes that are possible to make for a player
        """
        moves = {} # initialise moves dictionary
        for piece in self.get_all_pieces(colour): # get every piece of colour
            valid_moves = self.get_valid_moves(piece) # get every valid move for piece

            valid_copy = valid_moves.copy() # copy valid moves
            for k in valid_moves.keys(): # go through every key in valid moves dictionary
                if valid_moves[k] == []: # remove every key that has an empty list (no takes) as value
                    valid_copy.pop(k)
            valid_moves = valid_copy # set valid moves
            if valid_moves != {}: # if valid moves is not empty
                moves.update({piece: valid_moves}) # update moves

        return moves # else: return moves

    def get_valid_moves(self, piece):
        """
        Get all valid moves for a piece
        """
        moves = {} # initialise moves dictionary 
        pops = [] # initialise pops list
        left = piece.col - 1 # left of piece
        right = piece.col + 1 # right of piece
        row = piece.row # piece row

        if piece.colour == WHITE or piece.king: # if piece is white or king
            moves.update(self.go_left(row - 1, max(row - 3, -1), -1, piece.colour, left)) # update moves to left
            moves.update(self.go_right(row - 1, max(row - 3, -1), -1, piece.colour, right)) # update moves to right
        if piece.colour == RED or piece.king: # if piece if red or king
            moves.update(self.go_left(row + 1, min(row + 3, ROWS), 1, piece.colour, left)) # update moves to left
            moves.update(self.go_right(row + 1, min(row + 3, ROWS), 1, piece.colour, right)) # update moves to right

        valid_copy = moves.copy() # copy moves
        for k in moves.keys(): # iterate through every key in moves
            if valid_copy[k] == []: # if move has no takes
                pops.append(k) # add moves to pops
        for k in pops: # iterate through pops
            valid_copy.pop(k) # remove key from valid moves copy
        if valid_copy != {}: # if valid moves copy is not empty
            moves = valid_copy # set moves to valid moves copy

        return moves

    def go_left(self, start, stop, step, colour, left, skipped=[]):
        """
        Traverse every move to the left of a piece
        """
        moves = {} # initialise moves
        last = [] # initialise last
        for r in range(start, stop, step): # iterate through every step to left
            if left < 0: # if out of board
                break # break loop

            current = self.board[r][left] # get board piece on current pos
            if current == 0: # if current is blank
                if skipped and not last: # if there are skipped pieces and no last skipped pieces
                    break # break loop
                elif skipped: # if there are skipped pieces
                    moves[(r, left)] = last + skipped # update moves and add skipped pieces to move
                else:
                    moves[(r, left)] = last # update moves and add skipped pieces to move

                if last: # if last skipped pieces
                    if step == -1: # if stepp is up
                        row = max(r - 3, -1) # get new row
                    else:
                        row = min(r + 3, ROWS) # get new row
                    # piece can make another move from its current pos
                    moves.update(self.go_left(r + step, row, step, colour, left - 1, skipped=last)) # update moves again (recursively)
                    moves.update(self.go_right(r + step, row, step, colour, left + 1, skipped=last)) # update moves again
                break # break loop
            elif current.colour == colour: # if current piece colour is equal to traversed piece colour
                break # break loop
            else:
                last = [current] # add piece to skipped pieces

            left -= 1 # go further left

        return moves # return moves

    def go_right(self, start, stop, step, colour, right, skipped=[]):
        """
        Traverse every move to the left of a piece
        """
        #! Same structure as "go_left"
        moves = {}
        last = []
        for r in range(start, stop, step):
            if right >= COLUMNS:
                break

            current = self.board[r][right]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, right)] = last + skipped
                else:
                    moves[(r, right)] = last

                if last:
                    if step == -1:
                        row = max(r - 3, -1)
                    else:
                        row = min(r + 3, ROWS)
                    moves.update(self.go_left(r + step, row, step, colour, right - 1, skipped=last))
                    moves.update(self.go_right(r + step, row, step, colour, right + 1, skipped=last))
                break
            elif current.colour == colour:
                break
            else:
                last = [current]

            right += 1

        return moves


class Piece:
    """
    Piece Object
    """
    # drawing attributes
    PADDING = 20
    INLINE = 5
    INLINE_BORDER = 2

    def __init__(self, row, col, colour):
        # piece pos
        self.row = row
        self.col = col
        # colour
        self.colour = colour

        # is king
        self.king = False
        # is selected
        self.selected = False

        # calculate piece pos on screen
        self.calc_pos()

    def calc_pos(self):
        """
        Calculate the position on screen with help of current board pos
        """
        self.x = SQUARE_SIZE * self.col + SQUARE_SIZE / 2 # x-pos
        self.y = SQUARE_SIZE * self.row + SQUARE_SIZE / 2 # y-pos

    def draw(self):
        """
        Display the piece on screen
        """
        # get piece radius
        radius = SQUARE_SIZE // 2 - self.PADDING
        # draw piece circle
        pygame.draw.circle(WIN, self.colour, (self.x, self.y), radius)
        # add golden lines if piece is king
        if self.king:
            pygame.draw.circle(WIN, (210, 210, 0), (self.x, self.y), 20, width=5)
            pygame.draw.circle(WIN, (210, 210, 0), (self.x, self.y), 5)

    def move(self, row, col):
        """
        Move piece to another position
        """
        # update the piece pos
        self.row = row
        self.col = col
        # calculate new pos
        self.calc_pos()


class Play:
    """
    Main Game Class
    """
    def __init__(self):
        # currently selected piece
        self.selected = None
        # game board
        self.board = Board()
        # current turn
        self.turn = WHITE
        # current valid moves
        self.valid_moves = {}

    def update(self):
        """
        Update Board
        """
        try:
            self.board.draw() # try drawing the board
        except:
            AttributeError # except AttributeError
            if self.board.check_no_moves(WHITE) == True or self.board.check_no_moves(BLACK) == True: # if Board has no moves
                pass
        self.draw_valid_moves(self.valid_moves) # display valid moves

    def reset(self):
        """
        Reset the Object for new Game
        """
        self.selected = None
        self.board = Board()
        self.turn = WHITE
        self.valid_moves = {}

    def select(self, row, col):
        """
        Select position on board
        """
        if self.selected: # if already selected piece
            result = self.move(row, col) # move piece
            if result == False: # if moving was not successful
                self.selected = None # deselect
                self.select(row, col) # select pos for first time

        piece = self.board.get_piece(row, col) # get piece on position
        if piece != 0 and piece.colour == self.turn: # if piece is not blank and piece colour equals current turn
            self.selected = piece # set selected to piece
            vm = self.board.get_takes(piece.colour) # get piece takes
            if vm != {}: # if piece can take
                if piece in vm.keys(): # add take to valid moves
                    self.valid_moves = self.board.get_valid_moves(piece)
            else:
                # udpate valid moves
                self.valid_moves = self.board.get_valid_moves(piece)
            return True 
        return False

    def move(self, row, col):
        """
        Move piece
        """
        piece = self.board.get_piece(row, col) # get piece on pos
        if self.selected and piece == 0 and (row, col) in self.valid_moves: # if already selected and destination in valid moves
            mixer.Sound.play(MOVE_SOUND) # play move sound
            self.board.move(self.selected, row, col) # move piece
            skipped = self.valid_moves[(row, col)] # get skipped pieces
            if skipped: # if there are skipped pieces
                self.board.remove(skipped) # remove skipped pieces
            self.valid_moves = {} # reset valid moves
            if self.turn == WHITE: # if current turn is white
                self.turn = RED # change turn to red
            else:
                self.turn = WHITE # else: change turn to white
        else:
            return False # return false

        return True # return success

    def stalemate(self):
        """
        Check for a stalemate
        """
        if self.board.white_left == 1 and self.board.black_left == 1: # if only one piece left of both players
            return True
        if self.board.turns >= 100: # over 100 turns made
            return True
        return False # else: no stalemate

    def change_turn(self):
        """
        Change turn
        """
        self.valid_moves = {} # reset valid moves
        # change current turn
        if self.turn == WHITE:
            self.turn = RED
        else:
            self.turn = WHITE

    def draw_valid_moves(self, moves):
        """
        Display every valid move
        """
        for move in moves: # iterate through moves
            row, col = move # unpack move
            if (row, col) in brown_tiles: # check if pos in brown tiles
                # draw corresponding circle
                pygame.draw.circle(WIN, BROWN_MOVE,
                                   (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), 15)
            else:
                # else: draw correcponding circle to red tile
                pygame.draw.circle(WIN, WHITE_MOVE,
                                   (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), 15)

    def get_board(self):
        """
        Get the game board
        """
        return self.board

    def ai_move(self, board):
        """
        Make ai move
        """
        self.board = board # update board
        self.change_turn() # change turn


def get_mouse_pos(pos):
    """
    Get mouse pos on board
    """
    x, y = pos # unpack pos
    row = y // SQUARE_SIZE # get row from y-value
    col = x // SQUARE_SIZE # get col from x-value

    return int(row), int(col) # return (row, col)


def minimax(pos, depth, max_player, game, alpha=float("-inf"), beta=float("inf")):
    """
    Minimax AI function
    """
    # game ending
    if depth == 0 or pos.winner() != None:
        # white wins
        if pos.winner() == WHITE:
            return 20, pos
        # red wins
        elif pos.winner() == RED:
            return -20, pos
        # depth exceeded
        return pos.evaluate(), pos
    # maximising player
    if max_player:
        maxEval = float("-inf") # initialise evaluation
        best_move = None # initialise best move
        for move in get_all_moves(pos, WHITE, game): # iterate through all possible moves
            evaluation = minimax(move, depth - 1, False, game, alpha, beta)[0] # get evaluation by calling function recursively
            maxEval = max(maxEval, evaluation) # get new max evaluation
            alpha = max(alpha, evaluation) # alpha beta pruning
            if maxEval == evaluation: # if max eval is equal to current evaluation
                best_move = move # set new best move
            if pos.turns <= 30: # if turn count is smaller than 30
                if alpha > beta: # use alpha-beta pruning
                    break

        return maxEval, best_move # return evaluation and best move
    else: #! same structure as above
        minEval = float("inf")
        best_move = None
        for move in get_all_moves(pos, RED, game):
            evaluation = minimax(move, depth - 1, True, game, alpha, beta)[0]
            minEval = min(minEval, evaluation)
            if minEval == evaluation:
                best_move = move
            beta = min(beta, evaluation)
            if minEval == evaluation:
                best_move = move
            if pos.turns <= 30:
                if alpha > beta:
                    break

        return minEval, best_move


def get_all_moves(board, colour, game):
    """
    Get all possible moves of player
    """
    moves = [] # initialise moves
    vm = board.get_takes(colour) # get takes for current player
    if vm != {}: # if there are takes
        for piece in vm.keys(): # iterate through every piece
            valid_moves = vm[piece] # get valid moves for piece
            for move, skip in valid_moves.items(): # get move and skipped pieces for move
                temp_board = deepcopy(board) # copy board class
                temp_piece = temp_board.get_piece(piece.row, piece.col) # get piece on copied board
                new_board = simulate_move(temp_piece, move, temp_board, game, skip) # simulate move on board
                moves.append(new_board) # add new board to moves
    else:
        for piece in board.get_all_pieces(colour): # iterate through every piece
            valid_moves = board.get_valid_moves(piece) # get every valid move for piece
            for move, skip in valid_moves.items(): # get move and skipped pieces for move
                temp_board = deepcopy(board) # copy board class
                temp_piece = temp_board.get_piece(piece.row, piece.col) # get piece on copied board
                new_board = simulate_move(temp_piece, move, temp_board, game, skip) # simulate move on board
                moves.append(new_board) # add new board to moves

    return moves # return moves list


def simulate_move(piece, move, board, game, skip):
    """
    Simulate move on board
    """
    board.move(piece, move[0], move[1]) # move
    if skip: # if there are skipped pieces
        board.remove(skip) # remove skipped pieces from board
    return board # return new board


def draw_text(text, colour, x, y,size = 30):
    """
    Draw Text on screen
    """
    textRender = arial.render(text, False, colour) # render string

    if size != 30: # if size is less than 30
        font = pygame.font.Font('Merchant.ttf', size) # set font size to 30
        textRender = font.render(text, False, colour) # render text

    text_rect = textRender.get_rect() # get text rect
    text_rect.topleft = (x, y) # set text rect to pos
    WIN.blit(textRender, text_rect) # display rendered text at pos


def main():
    """
    Main Game function
    """
    global ai_dif, player # get global variables
    run = True # loop boolean
    clock = pygame.time.Clock() # clock
    FPS = 60 # frames per second
    play = Play() # initialise game
    # winning texts
    winner_white = arial_large.render("RED WON", False, WHITE) 
    winner_black = arial_large.render("WHITE WON", False, WHITE)
    stalemate = arial_large.render("DRAW", False, WHITE)
    # set depth based on ai difficulty
    if ai_dif == "easy":
        depth = 3
    else:
        depth = 5

    # init counter
    counter = 0

    def draw_score():
        """
        Draw current score and turn count
        """
        # render text
        score = arial_med.render(str(int(play.board.evaluate())), False, BLACK)
        turn_count = arial_med.render("|" + str(play.board.turns), False, BLACK)
        # draw background
        pygame.draw.rect(WIN, WHITE,
                         (0, 0, score.get_width() * 2 + turn_count.get_width() + score.get_width() // 4 + 5 + 30, 40))
        # draw texts
        WIN.blit(score, (0 + score.get_width() // 4, 0))
        WIN.blit(turn_count, (10 + score.get_width() + turn_count.get_width(), 0))
        pygame.display.update() # update display

    while run: # mainloop
        clock.tick(FPS) # tick at frames per second
        # check if game over
        black_lost = play.board.check_no_moves(RED)
        white_lost = play.board.check_no_moves(WHITE)
        if play.board.winner() != None or white_lost or black_lost: # if winner
            # if white won
            if play.board.winner() == WHITE or white_lost:
                # draw winning text
                WIN.blit(winner_white,
                         (WIDTH / 2 - winner_white.get_width() / 2, HEIGHT / 2 - winner_white.get_height() / 2))
            else: # else: draw black winning text
                WIN.blit(winner_black,
                         (WIDTH / 2 - winner_black.get_width() / 2, HEIGHT / 2 - winner_black.get_height() / 2))
            # update display
            pygame.display.update()
            # wait for 3 seconds
            pygame.time.wait(3000)
            # go back to main menu
            main_menu()
            return

        if play.stalemate(): # if stalemate
            # draw text
            WIN.blit(stalemate, (WIDTH / 2 - stalemate.get_width() / 2, HEIGHT / 2 - stalemate.get_height() / 2))
            # update display
            pygame.display.update()
            # wait for 3 seconds
            pygame.time.wait(3000)
            # go back to main menu
            main_menu()
            return

        # if second player is ai
        elif player == "ai":
            if play.turn == RED: # if current turn is red
                value, new_board = minimax(play.board, depth, False, play) # get ai move
                play.ai_move(new_board) # make ai move
                if depth < 5: # wait time
                    pygame.time.delay(400)

        # event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT: # quit event
                run = False # stop running
            if event.type == pygame.MOUSEBUTTONDOWN: # click event
                pos = pygame.mouse.get_pos() # get mouse pos
                row, col = get_mouse_pos(pos) # get mouse pos on board
                play.select(row, col) # select board pos
                play.board.select(row, col)
            elif event.type == KEYDOWN: # if pressed key
                if event.key == pygame.K_m: # if key is m
                    return main_menu() # back to main menu
                if event.key == pygame.K_p: # if key is p
                    pause() # pause game

        play.update() # upate display
        draw_score() # draw score
        if counter == 0: # if counter is equal to zero
            pygame.time.wait(1000) # wait for 1 second
            counter = 1 # set counter to 1

    pygame.quit() # quit after loop is finished


class Button(pygame.Rect):
    """
    Button Helper Class
    """
    def __init__(self, x, y, width, height, colour, text, outline=None, outline_width=3, rect_width=0, font_colour=BLACK,
                 font=arial, shadow=None, shadow_size=5, show_rect=True):
        super().__init__(x, y, width, height)
        # basic variables
        self.colour = colour
        self.outline = outline
        self.outline_width = outline_width
        self.rect_width = rect_width
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.text = font.render(text, 1, font_colour)
        self.real_text = text
        self.shadow = shadow
        self.shadow_size = shadow_size
        self.show_rect = show_rect

    def draw(self):
        """
        Draw Button on screen
        """
        # check for setting variables and draw button accordingly
        if self.shadow:
            pygame.draw.rect(WIN, self.shadow, (
            self.rect.x + self.shadow_size, self.y + self.shadow_size, self.rect.width, self.rect.height),
                             border_radius=self.rect_width)
        if self.show_rect:
            pygame.draw.rect(WIN, self.colour, self.rect, 0, self.rect_width)
        WIN.blit(self.text, (self.rect.x + self.width / 2 - self.text.get_width() / 2,
                             self.rect.y + self.height / 2 - self.text.get_height() / 2))
        if self.outline:
            pygame.draw.rect(WIN, self.outline, self.rect, self.outline_width, self.rect_width)

    def click(self):
        """
        Check if Button has been clicked
        """
        # get current mouse pos
        m = pygame.mouse.get_pos()
        if self.rect.collidepoint(m): # if mouse pos collides with button rect
            return True
        return False


def main_menu():
    """
    Main Menu
    """
    WIN.fill((135, 135, 135)) # fill window
    draw_text("CHECKERS",(255,255,255),180,300,145) # draw text
    pygame.display.update() # update display
    pygame.time.wait(3000) # wait time

    global ai_dif, player # get global variables
    clock = pygame.time.Clock() # clock

    # create clickable buttons
    human_ai = Button(WIDTH / 2 - 150, 250, 300, 50, WHITE, "Human vs. AI")
    human_human = Button(WIDTH / 2 - 150, 400, 300, 50, WHITE, "Human vs. Human")
    controls = Button(WIDTH / 2 - 150, 550, 300, 50, WHITE, "Game Controls")
    back = Button(WIDTH / 2 - 150, 500, 300, 50, RED, "Back")

    mode = False  # mode boolean
    game_controls = False # game controls booleaan

    # buttons for easy or hard mode
    easy = Button(WIDTH / 2 - 150, 300, 300, 50, WHITE, "Easy")
    hard = Button(WIDTH / 2 - 150, 500, 300, 50, WHITE, "Hard")

    # render text
    pause_text = arial.render("Press P to open the Pause Menu.", 1, WHITE)
    menu_text = arial.render("Press M to go back to the Main Menu", 1, WHITE)

    while 1: # mainloop
        clock.tick(30) # tick at 30 FPS

        WIN.fill((180, 180, 180)) # fill window with grey

        if not mode and not game_controls: # main menu
            # draw buttons
            controls.draw()
            human_ai.draw()
            human_human.draw()
            draw_text("Main Menu", (255, 0, 0), 260, 110, 85)
        elif mode and not game_controls: # choose mode menu
            # draw buttons and text
            draw_text("Game Difficulty", (244, 244, 23), 190, 100, 85)
            easy.draw()
            hard.draw()
        elif game_controls and not mode: # game controls menu
            # draw buttons and text
            draw_text("Game Controls", (244, 244, 23), 210, 100, 85)
            WIN.blit(pause_text, (WIDTH / 2 - pause_text.get_width() / 2, 250))
            WIN.blit(menu_text, (WIDTH / 2 - menu_text.get_width() / 2, 400))
            back.draw()

        # eventloop
        for event in pygame.event.get():
            # quit event
            if event.type == pygame.QUIT:
                pygame.quit()
            # click event
            if event.type == pygame.MOUSEBUTTONDOWN:
                # check for button clicks and perform actions
                if not mode:
                    if human_ai.click():
                        player = "ai"
                        mode = True
                    if controls.click():
                        game_controls = True
                    if back.click() and game_controls:
                        game_controls = False
                    if human_human.click():
                        player = "human"
                        return main()
                else:
                    if hard.click():
                        ai_dif = "hard"
                        return main()
                    elif easy.click():
                        ai_dif = "easy"
                        return main()

        pygame.display.update() # update display


def pause():
    """
    Pause Menu
    """

    # Buttons
    resume = Button(WIDTH / 4 - 150, HEIGHT / 2, 200, 50, (0, 255, 0), "Resume")
    restart = Button(WIDTH / 2 - 100, HEIGHT / 2, 200, 50, (255, 0, 0), "Restart")
    menu = Button(WIDTH * 0.75 - 50, HEIGHT / 2, 200, 50, (100, 100, 100), "Main Menu")

    # background
    bg = pygame.Rect(0, HEIGHT / 2 - 200, WIDTH, 400)

    while 1: # mainloop
        # draw background and buttons
        pygame.draw.rect(WIN, WHITE, bg)
        resume.draw()
        restart.draw()
        menu.draw()
        pygame.display.update() # update display

        # eventloop
        for event in pygame.event.get():
            # quit event
            if event.type == pygame.QUIT:
                pygame.quit()

            # click event
            if event.type == pygame.MOUSEBUTTONDOWN:
                # click resume
                if resume.click():
                    return
                # click restart
                elif restart.click():
                    return main()
                # back to main menu
                else:
                    return main_menu()


main_menu() # run code


