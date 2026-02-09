# The-Floor-Game
These are the classess required for the game engine
The Floor Game (demo)

This repository contains a minimal Python package that implements core classes
for a game based on the show "The Floor" and a very small Flask-based web UI
to demo registering players and categories and displaying the board.

How to run tests

1. Install pytest if needed:

```powershell
python -m pip install pytest
```

2. Run tests:

```powershell
python -m pytest -q
```

How to run the demo web UI

1. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

2. Start the web app:

```powershell
python -m the_floor_game.web
```

3. Open http://127.0.0.1:5000/ in your browser. The UI allows you to:
	- Create a board (rows x cols), which creates placeholder players.
	- Add categories.
	- Edit player names and set their expertise to a category.
	- (Demo) submit a challenge between two player IDs and resolve the duel by choosing the winner. The winner takes over the loser's board cells and the loser is eliminated. The game ends when a single player owns all cells.

Notes

This is an early prototype: duel resolution, persistence, authentication and
real game mechanics are intentionally minimal. Next steps could include a
question engine for duels, persistent storage, and a nicer UI.
