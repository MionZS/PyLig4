import Board
import Piece
import os

# Create a Board object to hold the pieces in place.
board = Board.Board("blue", 6, 7, style="default")

# Create a Piece object that holds the character styles for both players.
pieces = Piece.Piece(style="default")

piece_one = pieces.one
piece_two = pieces.two

print(f"\nPlayer 1 will use: '{piece_one}'")
print(f"Player 2 will use: '{piece_two}'")


input("Press enter to start")

current_player = 1
current_piece = pieces.one

game_is_on = True

while game_is_on:
    os.system('cls' if os.name == 'nt' else 'clear')
    board.print_board()

    print(f"\nPlayer {current_player}'s turn ({current_piece})")
    try:
        # User sees columns 1-7, but we use 0-6 internally.
        choice = int(input(f"Choose a column (1-{board.columns}): ")) - 1
    except ValueError:
        input("Invalid input. Please enter a number. Press Enter to continue...")
        continue

    # Attempt to drop the piece using the new Board method.
    if board.drop_piece(choice, current_piece):
        # --- A VICTORY CHECK WOULD GO HERE IN THE FUTURE ---

        # If successful, switch to the next player for the next turn.
        if current_player == 1:
            current_player = 2
            current_piece = pieces.two
        else:
            current_player = 1
            current_piece = pieces.one
    else:
        # If drop failed (e.g., column full or invalid), inform the user.
        input(
            f"Cannot place piece in column {choice + 1}. It may be full or invalid. "
            "Press Enter to try again..."
        )
