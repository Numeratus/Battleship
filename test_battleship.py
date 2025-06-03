"""
pytest suite for battleship.py
Tests cover:
    BoardPreset configuration and selection
    AI strategies: RandomShooter, SeekAndDestroy, StrategicGenius
    Ship behavior: hit registration and sinking
    Grid rendering and updates
    Player parsing, position calculation, random placement, sinking
    Game helpers: AI strategy mapping, screen clear
"""

import os
import pytest
import battleship
from battleship import (
    BoardPreset, RandomShooter, SeekAndDestroy, StrategicGenius,
    Ship, Grid, Player, Game
)

# --- 1. BoardPreset tests ---------------------------------------------------

def test_presets_exist():
    """
    Ensure default presets include small, medium, big with correct grid sizes and ship configurations.
    """
    keys = set(BoardPreset._presets.keys())
    assert keys == {'small', 'medium', 'big'}
    assert BoardPreset._presets['small']['grid_size'] == 5
    assert BoardPreset._presets['small']['ship_sizes'] == [2, 2, 3]

@pytest.mark.parametrize("size,ships", [
    (5, [2, 2]),
    (6, [2, 2, 3]),
    (8, [2, 2, 3, 4])
])
def test_constructor(size, ships):
    """"
    Verify BoardPreset constructor assigns grid_size and ship_sizes correctly.
    """
    p = BoardPreset(size, ships)
    assert p.grid_size == size
    assert p.ship_sizes == ships


def test_select_valid(monkeypatch):
    """
    Simulate valid user input for preset selection returns expected BoardPreset.
    """
    monkeypatch.setattr('builtins.input', lambda _: 'medium')
    p = BoardPreset.select()
    assert p.grid_size == 6
    assert p.ship_sizes == [2, 2, 2, 3]


def test_select_invalid_then_valid(monkeypatch, capsys):
    """
    Simulate two invalid inputs followed by valid 'big', ensure prompt repeats and returns correct preset.
    """
    inputs = iter(['foo', 'bar', 'big'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    p = BoardPreset.select()
    captured = capsys.readouterr()
    assert 'Please type one of:' in captured.out
    assert p.grid_size == 8
    assert p.ship_sizes == [2, 2, 2, 3, 4]


def test_select_quit(monkeypatch):
    """
    Typing 'q' at selection should exit the program.
    """
    monkeypatch.setattr('builtins.input', lambda _: 'q')
    with pytest.raises(SystemExit):
        BoardPreset.select()


# --- 2. AI Strategy tests ---------------------------------------------------

def test_random_shooter_no_repeats_and_bounds():
    """
    RandomShooter should produce exactly N*N unique targets within bounds.
    """
    rs = RandomShooter(3)
    coords = {rs.choose_target() for _ in range(9)}
    assert len(coords) == 9
    for r, c in coords:
        assert 0 <= r < 3 and 0 <= c < 3


def test_seek_and_destroy_fallback():
    """
    SeekAndDestroy without queued targets behaves like random shooter.
    """
    sd = SeekAndDestroy(2)
    coords = {sd.choose_target() for _ in range(4)}
    assert len(coords) == 4


def test_seek_and_destroy_process_result():
    """
    After a hit, SeekAndDestroy should enqueue all valid neighboring coordinates.
    """
    sd = SeekAndDestroy(3)
    sd.process_result((1, 1), hit=True)
    expected = {(0, 1), (2, 1), (1, 0), (1, 2)}
    assert set(sd.targets) == expected


def test_strategic_genius_hunt_mode():
    """
    StrategicGenius in hunt_mode picks only checkerboard cells first.
    """
    sg = StrategicGenius(4)
    coords = {sg.choose_target() for _ in range(8)}
    assert all((r + c) % 2 == 0 for r, c in coords)


def test_strategic_genius_switch_and_target_mode():
    """
    StrategicGenius switches out of hunt_mode on hit, drains targets, then returns to hunt_mode.
    """
    sg = StrategicGenius(4)
    sg.process_result((1, 1), hit=True)
    assert not sg.hunt_mode
    expected = {(1, 2), (1, 0), (2, 1), (0, 1)}
    assert set(sg.targets) == expected

    # Consume all queued target-mode picks
    out = {sg.choose_target() for _ in range(len(expected))}
    assert out == expected
    assert not sg.hunt_mode  # still targeting until fallback

    # Next choose_target triggers fallback and re-enters hunt_mode
    _ = sg.choose_target()
    assert sg.hunt_mode


# --- 3. Ship tests ----------------------------------------------------------

def test_ship_check_and_sunk():
    """
    Ship.check_hit should record hits and is_sunk should reflect when all positions hit.
    """
    ship = Ship(2, [(0, 0), (0, 1)])
    assert ship.check_hit((0, 0))
    assert ship.hits == {(0, 0)}
    assert not ship.is_sunk()
    ship.check_hit((0, 1))
    assert ship.is_sunk()
    assert not ship.check_hit((1, 1))  # miss does not count


# --- 4. Grid tests ----------------------------------------------------------

def test_grid_init_and_update_and_render():
    """
    Grid.cells initialize to blank, update marks 'X' and 'O', render shows correct symbols and header.
    """
    g = Grid(3)
    for coord, val in g.cells.items():
        assert val == ' '
    g.update((0, 1), hit=True)
    g.update((2, 2), hit=False)
    lines = g.render(show_ships=False)
    assert lines[0] == '  1 2 3'
    assert lines[1].startswith('A ')
    assert 'X' in lines[1]
    assert 'O' in lines[3]


def test_render_with_ships():
    """
    When show_ships=True, ship positions are revealed as 'S'.
    """
    ship = Ship(1, [(1, 1)])
    g = Grid(3)
    lines = g.render(show_ships=True, ships=[ship])
    tokens = lines[2].split()
    assert any('S' in tok for tok in tokens), f"No 'S' found in {tokens}"

# --- 5. Player tests --------------------------------------------------------

def test_parse_and_calc_positions():
    """
    Player._parse converts coordinates, _calc_positions enforces orientation and bounds.
    """
    p = Player.__new__(Player)
    p.grid = Grid(4)
    assert p._parse('A1') == (0, 0)
    assert p._parse('D4') == (3, 3)
    assert p._parse('E1') is None
    assert p._parse('A0') is None
    assert p._calc_positions((0, 0), 2, 'h') == [(0, 0), (0, 1)]
    assert p._calc_positions((3, 3), 2, 'h') is None
    assert p._calc_positions((0, 0), 3, 'v') == [(0, 0), (1, 0), (2, 0)]


def test_random_placement_and_all_sunk():
    """
    Player.random_placement should place correct number of ships without overlap and all_sunk signals when ships are hit.
    """
    sizes = [1, 2]
    p = Player.random_placement(4, sizes)
    assert len(p.ships) == len(sizes)
    positions = [pos for s in p.ships for pos in s.positions]
    assert len(positions) == len(set(positions))
    for r, c in positions:
        assert 0 <= r < 4 and 0 <= c < 4
    for s in p.ships:
        for coord in s.positions:
            s.check_hit(coord)
    assert p.all_sunk()


# --- 6. Game helper tests --------------------------------------------------

def test_game_strategy_mapping(monkeypatch):
    """
    Ensure Game.__init__ maps input difficulty to correct AIStrategy subclass.
    """
    # stub out interactive components
    monkeypatch.setattr(battleship.BoardPreset, 'select', lambda: BoardPreset(5, [1]))
    class DummyPlayer:
        def __init__(self, *args, **kwargs): pass
        @classmethod
        def random_placement(cls, grid_size, ship_sizes): return cls()
    monkeypatch.setattr(battleship, 'Player', DummyPlayer)
    for diff, cls in [('easy', RandomShooter), ('medium', SeekAndDestroy), ('hard', StrategicGenius)]:
        inputs = iter([diff])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        g = Game()
        assert isinstance(g.pc_ctrl, cls)


def test_clear(monkeypatch):
    """
    Game.clear should invoke os.system without error.
    """
    called = {}
    monkeypatch.setattr(os, 'system', lambda cmd: called.setdefault('cmd', cmd))
    g = Game.__new__(Game)
    g.clear()
    assert 'cmd' in called
