import pytest

from the_floor_game.core import Category, Player, Game


def test_board_and_positions_and_challenge():
    # Prepare two categories
    cat_a = Category(name="History")
    cat_b = Category(name="Science")

    # Two players; board will be 1x2
    p1 = Player(id=1, name="Alice")
    p2 = Player(id=2, name="Bob")

    game = Game(players=[p1, p2], nrows=1, ncols=2)

    # positions assigned
    assert p1.positions == [(0, 0)]
    assert p2.positions == [(0, 1)]

    # set expertise
    game.set_player_expertise(player_id=2, category=cat_b)
    assert p2.expertise is cat_b

    # challenger (p1) challenges p2 and must duel on p2's category
    duel = game.challenge(challenger_id=1, challenged_id=2)
    assert duel.category is cat_b
    assert duel.challenger is p1
    assert duel.challenged is p2

    # resolve duel via game so state (positions/elimination) is updated
    game.resolve_duel(duel, winner_id=2)
    assert duel.winner_id == 2

    # winner (p2) should now own both cells and loser (p1) eliminated
    assert set(p2.positions) == {(0, 1), (0, 0)}
    assert p1.eliminated is True
    # winner inherits challenger's expertise
    assert p2.expertise is p1.expertise


def test_invalid_board_size_raises():
    p1 = Player(id=1, name="One")
    p2 = Player(id=2, name="Two")
    with pytest.raises(ValueError):
        Game(players=[p1, p2], nrows=2, ncols=2)  # capacity 4 != 2


def test_challenge_without_expertise_raises():
    p1 = Player(id=1, name="One")
    p2 = Player(id=2, name="Two")
    game = Game(players=[p1, p2], nrows=1, ncols=2)
    with pytest.raises(ValueError):
        game.challenge(challenger_id=1, challenged_id=2)
