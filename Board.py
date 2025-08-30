# board.py ── loads cell-art styles from every JSON file in styles/cells/
# ----------------------------------------------------------------------
import json
from pathlib import Path
from typing import Dict, List, Optional

# ──────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────
STYLES_DIR   = Path(__file__).parent / "styles"
CELLS_DIR    = STYLES_DIR / "cells"          # each *.json may hold one or many styles
SKELETON_DIR = STYLES_DIR / "skeletons"      # reserved for future use


# ──────────────────────────────────────────────────────────────────────
# Helper – load all cell styles once
# ──────────────────────────────────────────────────────────────────────
def _load_cell_styles(directory: Path = CELLS_DIR) -> Dict[str, Dict[str, str]]:
    """
    Build a mapping of style_name → {'top': str, 'mid': str, 'bottom': str}.

    This function is the engine for making the board's appearance customizable.
    It aggregates all style definitions from all JSON files in the target
    directory into a single dictionary, which is then used by the Board class
    to render itself.

    Each JSON file in *directory* may be:
      • a **single-style** file:
            {"top": "...", "mid": "...", "bottom": "..."}
        (the style name becomes the file's stem)
      • OR a **multi-style** bundle:
            {
              "default": {"top": "...", "mid": "...", "bottom": "..."},
              "style2":  {"top": "...", "mid": "...", "bottom": "..."}
            }

    Requirements
    ------------
    * Every style dict must contain exactly the keys 'top', 'mid', 'bottom'.
    * After scanning all files there must be a style named 'default'.
    """
    if not directory.is_dir():
        raise FileNotFoundError(f"Styles folder not found: {directory}")

    required = {"top", "mid", "bottom"}
    style_map: Dict[str, Dict[str, str]] = {}

    for fp in directory.glob("*.json"):
        with fp.open(encoding="utf-8") as f:
            data = json.load(f)

        # ---- Case A: file defines ONE style (root has top/mid/bottom) ----
        if required.issubset(data):
            style_name = fp.stem
            if style_name in style_map:
                raise ValueError(
                    f"Duplicate style name '{style_name}' found again in {fp.name}"
                )
            style_map[style_name] = {k: data[k] for k in required}
            continue

        # ---- Case B: file bundles MANY styles ---------------------------
        for style_name, parts in data.items():
            if style_name in style_map:
                raise ValueError(
                    f"Duplicate style name '{style_name}' (also in {fp.name})"
                )
            missing = required - parts.keys()
            if missing:
                raise ValueError(
                    f"Style '{style_name}' in {fp.name} missing keys: {', '.join(missing)}"
                )
            style_map[style_name] = {k: parts[k] for k in required}

    if "default" not in style_map:
        raise ValueError(
            'At least one JSON in styles/cells/ must provide a style named "default".'
        )

    return style_map


# Parsed exactly once at import time
_STYLE_MAP: Dict[str, Dict[str, str]] = _load_cell_styles()


# ──────────────────────────────────────────────────────────────────────
# Board class
# ──────────────────────────────────────────────────────────────────────
class Board:
    """
    Simple Connect-Four board that can print itself with ASCII/Unicode cell art.

    Parameters
    ----------
    rows, columns : int
    size          : int      (placeholder for future GUI scaling)
    color         : str      (arbitrary metadata)
    style         : str      key into the loaded style map; default='default'
    """

    _CELL_LINE_ORDER = ("top", "mid", "bottom")

    def __init__(
        self,
        color: str,
        rows: int = 6,
        columns: int = 7,
        style: str = "default",
    ) -> None:
        self.rows: int = rows
        self.columns: int = columns
        self.color: str = color  # Metadata, not currently used for rendering.

        try:
            # _parts holds the ASCII/Unicode strings for the chosen cell style.
            self._parts = _STYLE_MAP[style]
        except KeyError as exc:
            raise ValueError(
                f"Unknown style '{style}'. "
                f"Available: {', '.join(sorted(_STYLE_MAP))}"
            ) from exc

        # The logical board is a 2D list (list of lists).
        # `None` represents an empty cell. It will be filled with piece strings ('X', 'O').
        self.board: List[List[Optional[str]]] = [
            [None for _ in range(columns)] for _ in range(rows)
        ]

    # ────────────────────────────────────────────────────────────────
    # Rendering – prints each board row as three text lines
    # ────────────────────────────────────────────────────────────────
    def print_board(self) -> None:
        """
        Prints the current board state to the console, with row and column indexes.

        Each logical row of the board is rendered as three lines of text,
        forming cells from the chosen style. Tokens are placed in the
        center of the middle line of each cell.
        """
        top_part = self._parts["top"]
        mid_part = self._parts["mid"]
        bot_part = self._parts["bottom"]

        center_idx = len(mid_part) // 2

        # To ensure the board aligns nicely, we calculate the width of the row
        # labels (e.g., "5: ") and add padding to lines that don't have a label.
        row_label_width = len(str(self.rows - 1))
        row_prefix_padding = " " * (row_label_width + 2)  # e.g., for "5: "

        for r, logical_row in enumerate(self.board):
            # Row label for the middle line, e.g., "0: ", "1: ", ...
            row_label = f"{r:>{row_label_width}}: "

            # 1. Top line of a row of cells (with padding for row label)
            print(row_prefix_padding + " ".join(top_part for _ in logical_row))

            # 2. Middle line, with tokens and row label.
            rendered_mids = [
                mid_part[:center_idx] + (str(c) if c is not None else " ") + mid_part[center_idx + 1:]
                for c in logical_row
            ]
            print(row_label + " ".join(rendered_mids))

            # 3. Bottom line of a row of cells (with padding for row label)
            print(row_prefix_padding + " ".join(bot_part for _ in logical_row))
            # optional spacer line between board rows:
            # print()

        # --- Column Index Footer ---
        print()  # Add a blank line for spacing before the footer.
        cell_width = len(mid_part)
        # Center each column index within the width of a single cell.
        col_labels = [str(c).center(cell_width) for c in range(self.columns)]
        print(row_prefix_padding + " ".join(col_labels))

    def drop_piece(self, column: int, piece: str) -> bool:
        """
        Drops a piece into the specified column, obeying gravity.

        Checks from the bottom row up for the first empty slot.

        Parameters
        ----------
        column : int
            The column index (0-based) to drop the piece into.
        piece : str
            The player's token ('X', 'O', etc.).

        Returns
        -------
        bool
            True if the piece was successfully placed, False if the column
            was full or the index was invalid.
        """
        if not 0 <= column < self.columns:
            return False  # Column index is out of bounds, drop is invalid.

        # To simulate gravity, we check from the bottom row upwards.
        # `range(self.rows - 1, -1, -1)` iterates from 5 down to 0 for a 6-row board.
        for r in range(self.rows - 1, -1, -1):
            if self.board[r][column] is None:
                self.board[r][column] = piece
                return True  # Piece successfully placed.

        return False  # If the loop completes, no empty slot was found.

    def check_for_win(self, piece: str) -> bool:
        """
        Checks the entire board for a winning sequence of 4 for the given piece.

        Iterates through each cell. If a cell contains the target piece, it checks
        for a win starting from that cell in all four primary directions
        (horizontal, vertical, and both diagonals).
        """
        # Directions to check: (row_change, col_change)
        directions = [
            (0, 1),  # Horizontal
            (1, 0),  # Vertical
            (1, 1),  # Diagonal down-right
            (1, -1),  # Diagonal down-left
        ]

        for r in range(self.rows):
            for c in range(self.columns):
                # We only need to start a check if the cell contains the piece
                if self.board[r][c] == piece:
                    for dr, dc in directions:
                        # Check if a line of 4 would fit on the board from here
                        end_r, end_c = r + 3 * dr, c + 3 * dc
                        if not (0 <= end_r < self.rows and 0 <= end_c < self.columns):
                            continue  # This line won't fit, try next direction

                        # Check the 4 cells (start + 3 more) in the current direction.
                        # `all()` is efficient: it stops checking as soon as one
                        # element is not the piece (short-circuiting).
                        if all(self.board[r + i * dr][c + i * dc] == piece for i in range(4)):
                            return True  # Found a win

        return False  # No win found after checking all possibilities

    def reset_board(self):
        """
        Resets the board to its initial empty state.

        This is done by creating a new 2D list filled with `None`.
        """
        self.board = [
            [None for _ in range(self.columns)] for _ in range(self.rows)
        ]

# ──────────────────────────────────────────────────────────────────────
# Hot-reload helper – call while program is running to pick up new JSON
# ──────────────────────────────────────────────────────────────────────
def reload_styles() -> None:
    """
    Re-scans styles/cells/*.json and refreshes the shared style map in memory.

    This is a development utility. It allows you to change the cell style JSON
    files and see the changes in a running application without restarting it,
    for example by calling this function from a special debug input.
    """
    global _STYLE_MAP
    _STYLE_MAP = _load_cell_styles()
