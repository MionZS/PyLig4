import json
from pathlib import Path
from typing import Dict, List, Optional

STYLES_DIR = Path(__file__).parent / "styles"
PIECES_DIR = STYLES_DIR / "pieces"


def _load_piece_styles(directory: Path = PIECES_DIR) -> Dict[str, Dict[str, str]]:
    """
    Build a mapping of piece_style_name → {'one': str, 'two': str}.

    This function scans a directory for *.json files to load piece styles,
    allowing player tokens (e.g., 'X' and 'O') to be easily customized.
    It works just like the cell style loader.

    Each JSON file in *directory* may be a single-style file or a
    multi-style bundle, similar to the cell style loader.

    Requirements
    ------------
    * Every style dict must contain exactly the keys 'one', 'two'.
    * After scanning all files there must be a style named 'default'.
    """
    if not directory.is_dir():
        raise FileNotFoundError(f"Styles folder not found: {directory}")

    required = {"one", "two"}
    style_map: Dict[str, Dict[str, str]] = {}

    for fp in directory.glob("*.json"):
        with fp.open(encoding="UTF-8") as f:
            data = json.load(f)

        # ---- Case A: file defines ONE style (root has one/two) ----
        if required.issubset(data):
            style_name = fp.stem
            if style_name in style_map:
                raise ValueError(
                    f"Duplicate piece style name '{style_name}' found again in {fp.name}"
                )
            style_map[style_name] = {k: data[k] for k in required}
            continue

        # ---- Case B: file bundles MANY styles ---------------------------
        for style_name, parts in data.items():
            if style_name in style_map:
                raise ValueError(
                    f"Duplicate piece style name '{style_name}' (also in {fp.name})"
                )
            missing = required - parts.keys()
            if missing:
                raise ValueError(
                    f"Piece style '{style_name}' in {fp.name} missing keys: {', '.join(missing)}"
                )
            style_map[style_name] = {k: parts[k] for k in required}

    if "default" not in style_map:
        raise ValueError(
            'At least one JSON in styles/pieces/ must provide a style named "default".'
        )

    return style_map


# Parsed exactly once at import time
_PIECE_STYLE_MAP: Dict[str, Dict[str, str]] = _load_piece_styles()


# ──────────────────────────────────────────────────────────────────────
# Piece class
# ──────────────────────────────────────────────────────────────────────
class Piece:
    """
    A simple container for a pair of player piece styles (e.g., 'X' and 'O').

    Parameters
    ----------
    style : str
        The name of the piece style to use, corresponding to a key in the
        loaded piece styles. Defaults to 'default'.
    """

    def __init__(
        self,
        style: str = "default",
    ) -> None:
        try:
            # Find the requested style definition from the globally loaded map.
            style_def = _PIECE_STYLE_MAP[style]
        except KeyError as exc:
            raise ValueError(
                f"Unknown piece style '{style}'. "
                f"Available: {', '.join(sorted(_PIECE_STYLE_MAP))}"
            ) from exc

        # Assign the specific characters for player one and player two.
        self.one: str = style_def["one"]
        self.two: str = style_def["two"]

    def __repr__(self) -> str:
        """Provides a developer-friendly representation of the Piece object."""
        return f"{self.__class__.__name__}(one='{self.one}', two='{self.two}')"


# ──────────────────────────────────────────────────────────────────────
# Hot-reload helper – call while program is running to pick up new JSON
# ──────────────────────────────────────────────────────────────────────
def reload_piece_styles() -> None:
    """
    Re-scans styles/pieces/*.json and refreshes the shared style map in memory.

    This is a development utility. It allows you to change the piece style JSON
    files and see the changes in a running application without restarting it,
    for example by calling this function from a special debug input.
    """
    global _PIECE_STYLE_MAP
    _PIECE_STYLE_MAP = _load_piece_styles()