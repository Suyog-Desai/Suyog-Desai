"""Fetch Chess.com rapid rating and update README.md between marker tags."""

import os
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import quote

USERNAME = os.environ.get("CHESS_USERNAME", "kaata-laga")
README_PATH = os.environ.get("README_PATH", "README.md")
API_URL = f"https://api.chess.com/pub/player/{quote(USERNAME)}/stats"
PROFILE_URL = f"https://www.chess.com/member/{USERNAME}"

START_MARKER = "<!-- CHESS-RATING:START -->"
END_MARKER = "<!-- CHESS-RATING:END -->"


def fetch_rapid_rating() -> int:
    """Return the current rapid rating. Chess.com requires a User-Agent header."""
    req = urllib.request.Request(
        API_URL,
        headers={
            "User-Agent": "github-readme-updater (contact: suyogdesai1105@gmail.com)",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        import json
        data = json.loads(resp.read().decode("utf-8"))

    rapid = data.get("chess_rapid")
    if not rapid or "last" not in rapid or "rating" not in rapid["last"]:
        raise RuntimeError(
            f"No rapid rating found for '{USERNAME}'. "
            "Play at least one rated rapid game on Chess.com, then retry."
        )
    return int(rapid["last"]["rating"])


def build_badge(rating: int) -> str:
    """Build a shields.io badge matching the README's existing flat style."""
    # shields.io dynamic label: "Chess.com Rapid" + rating value
    badge_url = (
        f"https://img.shields.io/badge/Chess.com_Rapid-{rating}-81B64C"
        "?style=flat&logo=chessdotcom&logoColor=white"
    )
    return f"[![Chess.com Rapid]({badge_url})]({PROFILE_URL})"


def update_readme(rating: int) -> bool:
    """Replace content between markers. Returns True if file changed."""
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    badge = build_badge(rating)
    new_block = f"{START_MARKER}\n{badge}\n{END_MARKER}"

    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )

    if not pattern.search(content):
        raise RuntimeError(
            f"Markers not found in {README_PATH}. "
            f"Add {START_MARKER} and {END_MARKER} where the badge should appear."
        )

    updated = pattern.sub(new_block, content)
    if updated == content:
        return False

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)
    return True


def main() -> int:
    try:
        rating = fetch_rapid_rating()
    except urllib.error.HTTPError as e:
        print(f"Chess.com API returned HTTP {e.code}: {e.reason}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Failed to fetch rating: {e}", file=sys.stderr)
        return 1

    try:
        changed = update_readme(rating)
    except Exception as e:
        print(f"Failed to update README: {e}", file=sys.stderr)
        return 1

    print(f"Rapid rating: {rating} ({'updated' if changed else 'unchanged'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
