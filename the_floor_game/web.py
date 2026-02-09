import os
from typing import Dict, Optional
from flask import Flask, render_template, request, redirect, url_for

from .core import Player, Category, Game


APP_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, ".."))
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates")


app = Flask(__name__, template_folder=TEMPLATES_DIR)

# In-memory data store for this simple demo
categories: Dict[int, Category] = {}
next_category_id = 1
current_game: Optional[Game] = None


def _get_next_category_id() -> int:
    global next_category_id
    cid = next_category_id
    next_category_id += 1
    return cid


def _color_for_id(pid: int) -> str:
    """Return a color dict for the player id with background, border and text.

    - background: pastel color
    - border: slightly darker for contrast
    - text: black or dark depending on background lightness
    """
    hue = (pid * 73) % 360
    # pastel background
    bg = f"hsl({hue},70%,85%)"
    # darker border by reducing lightness
    border = f"hsl({hue},70%,60%)"
    # compute text color: for pastel backgrounds we'll use dark text
    text = "#111"
    return {"bg": bg, "border": border, "text": text}


@app.route("/", methods=["GET"])
def index():
    """Setup page: collect board size and optional initial categories."""
    cats = list(categories.items())
    return render_template("setup.html", categories=cats, game=current_game)


@app.route("/board", methods=["GET"])
def board():
    global categories, current_game
    cats = list(categories.items())
    player_colors = {}
    if current_game:
        for pid in current_game.players.keys():
            player_colors[pid] = _color_for_id(pid)
    # compute owner counts for badges
    owner_counts = {}
    if current_game:
        for pid, p in current_game.players.items():
            owner_counts[pid] = len(p.positions)
    return render_template("index.html", game=current_game, categories=cats, player_colors=player_colors, owner_counts=owner_counts)


@app.route("/start_turn", methods=["POST"])
def start_turn():
    """Select a challenger for the next turn using game rules and redirect to board."""
    global current_game
    if not current_game:
        return "No game created", 400
    cid = current_game.start_turn()
    if cid is None:
        return "No players alive", 400
    return redirect(url_for("board"))


@app.route("/create_game", methods=["POST"])
def create_game():
    global current_game
    try:
        nrows = int(request.form.get("nrows", "1"))
        ncols = int(request.form.get("ncols", "1"))
    except ValueError:
        return "Invalid nrows/ncols", 400

    capacity = nrows * ncols
    # create placeholder players with sequential ids
    players = [Player(id=i + 1, name=f"Player {i + 1}") for i in range(capacity)]
    current_game = Game(players=players, nrows=nrows, ncols=ncols)

    # optional initial categories (comma separated)
    cats_raw = request.form.get("categories", "").strip()
    if cats_raw:
        for name in [c.strip() for c in cats_raw.split(",") if c.strip()]:
            cid = _get_next_category_id()
            categories[cid] = Category(name=name)

    # optional initial player names (comma separated)
    names_raw = request.form.get("player_names", "").strip()
    if names_raw:
        names = [n.strip() for n in names_raw.split(",") if n.strip()]
    else:
        names = []

    # assign provided names to players where available
    for i, player in enumerate(players):
        if i < len(names):
            player.name = names[i]

    return redirect(url_for("board"))


@app.route("/add_category", methods=["POST"])
def add_category():
    global categories
    name = request.form.get("name", "").strip()
    desc = request.form.get("description", "").strip()
    if not name:
        return "Category name required", 400
    cid = _get_next_category_id()
    categories[cid] = Category(name=name, description=desc)
    # If a game exists, show board; otherwise return to setup so user can
    # continue adding categories before creating the board.
    if current_game:
        return redirect(url_for("board"))
    return redirect(url_for("index"))


@app.route("/set_player", methods=["POST"])
def set_player():
    global current_game, categories
    if not current_game:
        return "No game created", 400
    try:
        pid = int(request.form.get("player_id"))
    except (TypeError, ValueError):
        return "Invalid player id", 400
    player = current_game.players.get(pid)
    if not player:
        return "Player not found", 404
    name = request.form.get("name", "").strip()
    if name:
        player.name = name
    cat_id = request.form.get("category_id")
    if cat_id:
        try:
            cid = int(cat_id)
            if cid in categories:
                player.expertise = categories[cid]
        except ValueError:
            pass
    # Allow forms to request returning to setup page
    next_page = request.form.get("next")
    if next_page == "setup":
        return redirect(url_for("index"))
    return redirect(url_for("board"))


@app.route("/challenge", methods=["POST"])
def challenge():
    global current_game
    if not current_game:
        return "No game created", 400
    try:
        challenger_id = int(request.form.get("challenger_id"))
        challenged_id = int(request.form.get("challenged_id"))
    except (TypeError, ValueError):
        return "Invalid player id(s)", 400
    try:
        duel = current_game.challenge(challenger_id=challenger_id, challenged_id=challenged_id)
    except Exception as e:
        return str(e), 400
    # For the demo, we won't run a real duel — just record the duel and return success.
    return redirect(url_for("board"))


@app.route("/resolve_duel", methods=["POST"])
def resolve_duel():
    global current_game
    if not current_game:
        return "No game created", 400
    if not current_game.duel_history:
        return "No duel to resolve", 400
    try:
        winner_id = int(request.form.get("winner_id"))
    except (TypeError, ValueError):
        return "Invalid winner id", 400

    duel = current_game.duel_history[-1]
    try:
        current_game.resolve_duel(duel, winner_id=winner_id)
    except Exception as e:
        return str(e), 400
    return redirect(url_for("board"))


if __name__ == "__main__":
    # Run on 127.0.0.1:5000
    app.run(debug=True)