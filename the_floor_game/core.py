from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import random


@dataclass
class Category:
    """A knowledge category or expertise area."""
    name: str
    description: Optional[str] = None


@dataclass
class Player:
    """Represents a player in the game.

    A player can own multiple board cells (positions) after winning duels.
    """
    id: int
    name: str
    expertise: Optional[Category] = None
    positions: List[Tuple[int, int]] = field(default_factory=list)
    eliminated: bool = False

    def choose_expertise(self, category: Category) -> None:
        """Set the player's expertise/category."""
        self.expertise = category

    def primary_position(self) -> Optional[Tuple[int, int]]:
        """Return one representative position (or None)."""
        return self.positions[0] if self.positions else None


@dataclass
class Duel:
    """Represents a duel between two players on a specific category.

    The challenger duels on the challenged player's category.
    """
    challenger: Player
    challenged: Player
    category: Category
    winner_id: Optional[int] = None

    def resolve(self, winner_id: int) -> None:
        """Record the winner's id. No game logic performed here.

        In a later iteration this might run questions/answers and compute a winner.
        """
        if winner_id not in (self.challenger.id, self.challenged.id):
            raise ValueError("winner_id must be one of the duel participants")
        self.winner_id = winner_id

    def loser(self) -> Player:
        return self.challenged if self.winner_id == self.challenger.id else self.challenger

    def winner(self) -> Optional[Player]:
        if self.winner_id is None:
            return None
        return self.challenger if self.winner_id == self.challenger.id else self.challenged


class Board:
    """Rectangular board that places players in a grid.

    The board's size must match the number of players placed on it.
    Positions are (row, col) with 0-based indices.
    """

    def __init__(self, nrows: int, ncols: int):
        if nrows <= 0 or ncols <= 0:
            raise ValueError("nrows and ncols must be positive")
        self.nrows = nrows
        self.ncols = ncols
        # map (row,col) -> player id
        self._grid: Dict[Tuple[int, int], Optional[int]] = {
            (r, c): None for r in range(nrows) for c in range(ncols)
        }

    @property
    def capacity(self) -> int:
        return self.nrows * self.ncols

    def place_players(self, players: List[Player]) -> None:
        """Place players on the board in row-major order.

        Raises if players list length doesn't match capacity.
        """
        if len(players) != self.capacity:
            raise ValueError("players list length must equal board capacity")

        it = iter(players)
        for r in range(self.nrows):
            for c in range(self.ncols):
                player = next(it)
                self._grid[(r, c)] = player.id
                player.positions = [(r, c)]

    def get_player_position(self, player: Player) -> Optional[Tuple[int, int]]:
        return player.primary_position()

    def get_player_at(self, row: int, col: int) -> Optional[int]:
        return self._grid.get((row, col))


class Game:
    """High-level game controller.

    Responsibilities implemented here are intentionally minimal: registering
    players, placing them on the board, setting expertise, and initiating duels.
    """

    def __init__(self, players: List[Player], nrows: int, ncols: int):
        if len(players) != nrows * ncols:
            raise ValueError("number of players must equal nrows*ncols")
        self.players: Dict[int, Player] = {p.id: p for p in players}
        self.board = Board(nrows, ncols)
        self.nrows = nrows
        self.ncols = ncols
        # place players
        self.board.place_players(players)
        self.duel_history = []
        self.over = False
        self.winner_id = None
        # id of player selected as the challenger for the current turn (if any)
        self.turn_challenger_id = None

    def set_player_expertise(self, player_id: int, category: Category) -> None:
        player = self.players.get(player_id)
        if not player:
            raise KeyError(f"player {player_id} not found")
        player.choose_expertise(category)

    def challenge(self, challenger_id: int, challenged_id: int) -> Duel:
        """Create a Duel where challenger duels on the challenged's category.

        Raises if players not found or challenged has no expertise.
        """
        if challenger_id == challenged_id:
            raise ValueError("player cannot challenge themself")

        challenger = self.players.get(challenger_id)
        challenged = self.players.get(challenged_id)
        if not challenger or not challenged:
            raise KeyError("both challenger and challenged must be registered players")
        if not challenged.expertise:
            raise ValueError("challenged player must have an expertise/category set")

        duel = Duel(challenger=challenger, challenged=challenged, category=challenged.expertise)
        self.duel_history.append(duel)
        return duel

    def resolve_duel(self, duel: Duel, winner_id: int) -> None:
        """Resolve the duel by selecting the winner and updating board/game state.

        Winner takes over all board cells owned by the loser. The loser is marked
        eliminated (their positions cleared). If one player ends up owning all
        cells, the game is marked as over.
        """
        if duel not in self.duel_history:
            raise ValueError("duel not found in game history")

        duel.resolve(winner_id=winner_id)

        # Determine winner and loser player objects
        if duel.winner_id == duel.challenger.id:
            winner = duel.challenger
            loser = duel.challenged
        else:
            winner = duel.challenged
            loser = duel.challenger

        # Transfer all loser positions to winner
        for pos in list(loser.positions):
            # update board grid
            self.board._grid[pos] = winner.id
            # add to winner positions
            winner.positions.append(pos)

        # Winner inherits the challenger's expertise/category
        winner.expertise = duel.challenger.expertise

        # clear loser
        loser.positions = []
        loser.eliminated = True

        # Check whether only one non-eliminated player remains and owns all cells
        alive_players = [p for p in self.players.values() if not p.eliminated]
        if len(alive_players) == 1 and len(alive_players[0].positions) == self.board.capacity:
            self.over = True
            self.winner_id = alive_players[0].id

    def start_turn(self) -> Optional[int]:
        """Start a new turn by selecting a challenger according to rules:

        - Prefer a random player who currently owns exactly one board cell.
        - If no such player exists, select a random alive player.

        Stores the selected player id in self.turn_challenger_id and returns it.
        """
        alive_players = [p for p in self.players.values() if not p.eliminated]
        if not alive_players:
            self.turn_challenger_id = None
            return None

        ones = [p for p in alive_players if len(p.positions) == 1]
        if ones:
            chosen = random.choice(ones)
        else:
            chosen = random.choice(alive_players)

        self.turn_challenger_id = chosen.id
        return self.turn_challenger_id
