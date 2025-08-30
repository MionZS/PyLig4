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
        self.color: str = color

        try:
            self._parts = _STYLE_MAP[style]          # {'top': '...', 'mid': '...', ...}
        except KeyError as exc:
            raise ValueError(
                f"Unknown style '{style}'. "
                f"Available: {', '.join(sorted(_STYLE_MAP))}"
            ) from exc

        # The logical board (None until you start dropping tokens, etc.)
        self.board: List[List[Optional[str]]] = [
            [None for _ in range(columns)] for _ in range(rows)
        ]

    # ────────────────────────────────────────────────────────────────
    # Rendering – prints each board row as three text lines
    # ────────────────────────────────────────────────────────────────
    def print_board(self) -> None:
        """
        Prints the current board state to the console.

        Each logical row of the board is rendered as three lines of text,
        forming cells from the chosen style. Tokens are placed in the
        center of the middle line of each cell.
        """
        top_part = self._parts["top"]
        mid_part = self._parts["mid"]
        bot_part = self._parts["bottom"]

        # Pre-calculate the center index for token placement. This assumes
        # the mid_part string has a center character to be replaced.
        center_idx = len(mid_part) // 2

        for logical_row in self.board:
            # 1. Top line of a row of cells (all identical)
            print(" ".join(top_part for _ in logical_row))

            # 2. Middle line, with tokens substituted in.
            rendered_mids = [
                mid_part[:center_idx] + (str(c) if c is not None else " ") + mid_part[center_idx + 1:]
                for c in logical_row
            ]
            print(" ".join(rendered_mids))

            # 3. Bottom line of a row of cells (all identical)
            print(" ".join(bot_part for _ in logical_row))
            # optional spacer line between board rows:
            # print()

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
            return False  # Column index is out of bounds

        # Iterate from the bottom row (e.g., 5) up to the top row (0)
        for r in range(self.rows - 1, -1, -1):
            if self.board[r][column] is None:
                self.board[r][column] = piece
                return True

        return False  # If the loop completes, the column is full

    def check_for_win(self, piece: str):
        for row in range(self.rows):
            for col in range(self.columns):
                if self.board[row][col] == piece:



# ──────────────────────────────────────────────────────────────────────
# Hot-reload helper – call while program is running to pick up new JSON
# ──────────────────────────────────────────────────────────────────────
def reload_styles() -> None:
    """Re-scan styles/cells/*.json and refresh the shared style map in memory."""
    global _STYLE_MAP
    _STYLE_MAP = _load_cell_styles()
