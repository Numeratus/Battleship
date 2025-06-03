import colorama
import os
import random
import string
import sys
from colorama import Fore, Style

# Initialize Colorama
colorama.init(autoreset=True)

class BoardPreset:
    """
    Represents predefined board configurations for different game difficulties.

    Attributes:
        grid_size (int): Dimensions of the game board (grid_size x grid_size)
        ship_sizes (list[int]): List of ship lengths for this configuration
    """
    _presets = {
        'small':  {'grid_size': 5, 'ship_sizes': [2, 2, 3]},
        'medium': {'grid_size': 6, 'ship_sizes': [2, 2, 2, 3]},
        'big':    {'grid_size': 8, 'ship_sizes': [2, 2, 2, 3, 4]},
    }

    def __init__(self, grid_size: int, ship_sizes: list[int]):
        """
        Initialize a board configuration instance.

        Args:
            grid_size: Size of the game board (N x N grid)
            ship_sizes: List of ship lengths to be placed on the board
        """
        self.grid_size = grid_size
        self.ship_sizes = ship_sizes

    @classmethod
    def select(cls) -> 'BoardPreset':
        """
        Interactive selection of board configuration from available presets.

        Returns:
            BoardPreset: Chosen configuration instance

        Exits:
            If user chooses to quit, terminates the program
        """
        choices = [f"{name.capitalize()} ({p['grid_size']}x{p['grid_size']})"
                  for name, p in cls._presets.items()]
        prompt = ' / '.join(choices)
        while True:
            choice = input(f"Select board size: {prompt} or 'q' to quit: ").strip().lower()
            if choice == 'q':
                print("\nQuitting game. Goodbye!")
                sys.exit()
            if choice in cls._presets:
                p = cls._presets[choice]
                return cls(p['grid_size'], p['ship_sizes'])
            print(f"Please type one of: {', '.join(cls._presets.keys())}, or 'q'.")

class AIStrategy:
    """
    Abstract base class defining the interface for AI targeting strategies.

    Subclasses must implement choose_target() for concrete targeting behavior.

    Attributes:
        grid_size (int): Size of the game board for boundary checking
    """
    def __init__(self, grid_size: int):
        """
        Initialize common AI strategy components.

        Args:
            grid_size: Size of the game board for coordinate validation
        """
        self.grid_size = grid_size

    def choose_target(self) -> tuple[int, int]:
        """
        Select next coordinate to attack.

        Returns:
            tuple[int, int]: (row, column) tuple representing target position

        Raises:
            NotImplementedError: If concrete subclass doesn't implement
        """
        raise NotImplementedError

    def process_result(self, coord: tuple[int, int], hit: bool) -> None:
        """
        Update AI internal state based on attack outcome.

        Args:
            coord: (row, column) of previous attack
            hit: True if attack was successful, False otherwise
        """
        pass

class RandomShooter(AIStrategy):
    """
    Easy AI strategy that selects targets completely at random.

    Maintains memory of previous shots to avoid repetition.
    """
    def __init__(self, grid_size: int):
        """
        Initialize random shooter state.

        Args:
            grid_size: Board dimensions for coordinate generation
        """
        super().__init__(grid_size)
        self.shots = set()

    def choose_target(self) -> tuple[int, int]:
        """
        Generate random coordinates until finding an unexplored position.

        Returns:
            tuple[int, int]: Valid target coordinates not previously attacked
        """
        choices = [(r, c) for r in range(self.grid_size)
                   for c in range(self.grid_size) if (r, c) not in self.shots]
        coord = random.choice(choices)
        self.shots.add(coord)
        return coord

class SeekAndDestroy(AIStrategy):
    """
    Intermediate AI strategy that prioritizes neighboring cells after hits.

    Uses queue system to continue attacking around successful hits.
    """
    def __init__(self, grid_size: int):
        """
        Initialize hunting state.

        Args:
            grid_size: Board dimensions for coordinate validation
        """
        super().__init__(grid_size)
        self.targets = []
        self.shots = set()

    def choose_target(self) -> tuple[int, int]:
        """
        Select target from queued positions or fall back to random selection.

        Returns:
            tuple[int, int]: Highest priority available target coordinates
        """
        while self.targets:
            coord = self.targets.pop()
            if coord not in self.shots:
                self.shots.add(coord)
                return coord

        # Fallback to random selection when queue is empty
        choices = [(r, c) for r in range(self.grid_size)
                   for c in range(self.grid_size) if (r, c) not in self.shots]
        coord = random.choice(choices)
        self.shots.add(coord)
        return coord

    def process_result(self, coord: tuple[int, int], hit: bool) -> None:
        """
        Update target queue based on hit success.

        Args:
            coord: Position of previous attack
            hit: Whether the attack revealed a ship segment
        """
        if hit:
            r, c = coord
            neighbors = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
            valid = [(nr, nc) for nr, nc in neighbors
                     if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size]
            random.shuffle(valid)
            self.targets.extend(valid)

class StrategicGenius(AIStrategy):
    """
    Advanced AI using probability targeting with two-phase strategy:
    1. Checkerboard pattern hunting for efficient ship discovery
    2. Systematic exploration of adjacent cells after hit detection
    """
    def __init__(self, grid_size: int):
        """
        Initialize strategic state.

        Args:
            grid_size: Board dimensions for coordinate generation
        """
        super().__init__(grid_size)
        self.hunt_mode = True
        self.shots = set()
        self.targets = []

    def choose_target(self) -> tuple[int, int]:
        """
        Select target based on current strategy phase.

        Returns:
            tuple[int, int]: Calculated target coordinates
        """
        if self.hunt_mode:
            # Checkerboard pattern targets (even sum coordinates)
            choices = [(r, c) for r in range(self.grid_size)
                       for c in range(self.grid_size)
                       if (r + c) % 2 == 0 and (r, c) not in self.shots]
            if not choices:  # Fallback if checkerboard exhausted
                choices = [(r, c) for r in range(self.grid_size)
                           for c in range(self.grid_size) if (r, c) not in self.shots]
            coord = random.choice(choices)
            self.shots.add(coord)
            return coord

        # Target mode - process queued positions
        while self.targets:
            coord = self.targets.pop(0)
            if coord not in self.shots:
                self.shots.add(coord)
                return coord
        # Return to hunting if queue empties
        self.hunt_mode = True
        return self.choose_target()

    def process_result(self, coord: tuple[int, int], hit: bool) -> None:
        """
        Update strategy phase based on attack outcome.

        Args:
            coord: Position of previous attack
            hit: Whether the attack was successful
        """
        if hit:
            self.hunt_mode = False
            r, c = coord
            # Queue adjacent cells in cross pattern
            for nr, nc in [(r, c+1), (r, c-1), (r+1, c), (r-1, c)]:
                if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size:
                    if (nr, nc) not in self.shots:
                        self.targets.append((nr, nc))

class Ship:
    """
    Represents a naval vessel with position tracking and damage state.

    Attributes:
        size (int): Length of the ship in grid cells
        positions (list[tuple[int, int]]): Grid coordinates occupied by ship
        hits (set[tuple[int, int]]): Coordinates where ship has been struck
    """
    def __init__(self, size: int, positions: list[tuple[int, int]]):
        """
        Initialize ship instance.

        Args:
            size: Length of the ship
            positions: List of (row, column) coordinates occupied by ship
        """
        self.size = size
        self.positions = positions
        self.hits = set()

    def check_hit(self, target: tuple[int, int]) -> bool:
        """
        Register attack on ship position.

        Args:
            target: (row, column) coordinates being attacked

        Returns:
            bool: True if target hits ship, False otherwise
        """
        if target in self.positions:
            self.hits.add(target)
            return True
        return False

    def is_sunk(self) -> bool:
        """
        Determine if ship has been completely destroyed.

        Returns:
            bool: True if all positions have been hit, False otherwise
        """
        return len(self.hits) == self.size

class Grid:
    """
    Manages game board state and visualization.

    Attributes:
        grid_size (int): Dimensions of the board
        cells (dict): Dictionary tracking cell states with (row, col) keys
    """
    def __init__(self, grid_size: int):
        """
        Initialize empty game board.

        Args:
            grid_size: Dimensions of the board (N x N)
        """
        self.grid_size = grid_size
        self.cells = {(r, c): ' ' for r in range(grid_size) for c in range(grid_size)}

    def update(self, target: tuple[int, int], hit: bool) -> None:
        """
        Update cell state based on attack result.

        Args:
            target: (row, column) of attacked cell
            hit: True for successful hit, False for miss
        """
        self.cells[target] = 'X' if hit else 'O'

    def render(self, show_ships: bool = False, ships: list[Ship] = None) -> list[str]:
        """
        Generate visual representation of board state, with ANSI color codes.

        Args:
            show_ships: Whether to reveal undamaged ship positions
            ships: List of Ship objects for position checking

        Returns:
            list[str]: Formatted lines representing the game board
        """
        lines = []
        header = '  ' + ' '.join(str(i+1) for i in range(self.grid_size))
        lines.append(header)
        for r in range(self.grid_size):
            row_label = string.ascii_uppercase[r]
            row_cells = []
            for c in range(self.grid_size):
                cell = self.cells[(r, c)]
                # Choose color based on state:
                if cell == 'X':
                    sym = Fore.RED + 'X'
                elif cell == 'O':
                    sym = Fore.CYAN + 'O'
                elif cell == ' ' and show_ships and ships and any((r, c) in s.positions for s in ships):
                    sym = Fore.GREEN + 'S'
                else:
                    sym = ' '
                row_cells.append(sym + Style.RESET_ALL)
            lines.append(f"{row_label} {' '.join(row_cells)}")
        return lines

class Player:
    """
    Represents a game participant with ships and board state.

    Attributes:
        grid (Grid): Player's game board
        ships (list[Ship]): Fleet of ships placed on the board
    """
    def __init__(self, grid_size: int, ship_sizes: list[int]):
        """
        Interactive ship placement constructor.

        Args:
            grid_size: Dimensions of the game board
            ship_sizes: List of ship lengths to place on board
        """
        self.grid = Grid(grid_size)
        self.ships: list[Ship] = []
        occupied = set()
        for size in ship_sizes:
            placed = False
            while not placed:
                # Display current placement progress
                for line in self.grid.render(show_ships=True, ships=self.ships):
                    print(line)
                # Get placement parameters from user
                coord = input(f"Enter start coord for ship of size {size} (e.g. A1): ").strip().upper()
                orient = input("Orientation horizontal [h] or vertical [v]: ").strip().lower()
                start = self._parse(coord)
                if orient in ('h','v') and start:
                    positions = self._calc_positions(start, size, orient)
                    if positions and not any(p in occupied for p in positions):
                        for p in positions:
                            occupied.add(p)
                        self.ships.append(Ship(size, positions))
                        placed = True
                        os.system('cls' if os.name=='nt' else 'clear')
                        continue
                print("Invalid placement, try again.")
                os.system('cls' if os.name=='nt' else 'clear')

    def _parse(self, coord: str) -> tuple[int, int] | None:
        """
        Convert alphanumeric coordinate to grid indices.

        Args:
            coord: String in format 'A1' to 'Z99'

        Returns:
            tuple[int, int] | None: (row, column) indices or None if invalid
        """
        if len(coord)<2 or coord[0] not in string.ascii_uppercase[:self.grid.grid_size]:
            return None
        r = ord(coord[0])-ord('A')
        try:
            c=int(coord[1:])-1
        except ValueError:
            return None
        return (r, c) if 0 <= c < self.grid.grid_size else None

    def _calc_positions(self, start: tuple[int, int], size: int, orient: str) -> list[tuple[int, int]] | None:
        """
        Calculate ship positions from placement parameters.

        Args:
            start: (row, column) of ship's starting position
            size: Length of the ship
            orient: 'h' for horizontal, 'v' for vertical placement

        Returns:
            list[tuple[int, int]] | None: List of occupied coordinates or None if invalid
        """
        r, c = start
        if orient == 'h':
            if c + size > self.grid.grid_size:
                return None
            return [(r, c+i) for i in range(size)]
        else:
            if r + size > self.grid.grid_size:
                return None
            return [(r+i, c) for i in range(size)]

    def all_sunk(self) -> bool:
        """
        Check if all ships have been destroyed.

        Returns:
            bool: True if entire fleet is sunk, False otherwise
        """
        return all(s.is_sunk() for s in self.ships)

    @classmethod
    def random_placement(cls, grid_size: int, ship_sizes: list[int]) -> "Player":
        """
        Create Player instance with randomly placed ships.

        Args:
            grid_size: Board dimensions
            ship_sizes: List of ship lengths to place

        Returns:
            Player: Instance with randomly arranged fleet
        """
        self = cls.__new__(cls)
        self.grid = Grid(grid_size)
        self.ships = []
        occupied = set()

        for size in ship_sizes:
            placed = False
            while not placed:
                orient = random.choice(['h','v'])
                start = (random.randrange(grid_size), random.randrange(grid_size))
                positions = cls._calc_positions(self, start, size, orient)
                if positions and not any(p in occupied for p in positions):
                    occupied.update(positions)
                    self.ships.append(Ship(size, positions))
                    placed = True
        return self

class Game:
    """
    Manages game flow and player/AI interactions.

    Attributes:
        player (Player): Human player instance
        computer (Player): AI-controlled opponent
        pc_ctrl (AIStrategy): AI targeting strategy implementation
        grid_size (int): Board dimensions
        reports (list[str]): Turn result messages for display
    """
    def __init__(self):
        """
        Initialize game state with user-configured settings.
        """
        # Configure AI strategy
        ai_choice = input("Select AI difficulty: Easy, Medium or Hard: ").strip().lower()
        strategies = {'easy': RandomShooter, 'medium': SeekAndDestroy, 'hard': StrategicGenius}
        while ai_choice not in strategies:
            ai_choice = input("Choose one of: Easy, Medium or Hard: ").strip().lower()

        # Set up board configuration
        preset = BoardPreset.select()
        self.player = Player(preset.grid_size, preset.ship_sizes)
        self.computer = Player.random_placement(preset.grid_size, preset.ship_sizes)
        self.pc_ctrl = strategies[ai_choice](preset.grid_size)
        self.grid_size = preset.grid_size
        self.reports = []

    def clear(self) -> None:
        """Clear terminal screen based on operating system."""
        os.system('cls' if os.name=='nt' else 'clear')

    def play(self) -> None:
        """
        Execute main game loop until victory condition is met.

        Alternates between player and AI turns, updating game state
        and displaying results after each round.
        """
        while True:
            self.clear()

            label_width = self.grid_size * 2 + 3
            print(f"{'Your Fleet':<{label_width}}    {'Enemy Waters'}")
            # Render dual board display
            own = self.player.grid.render(show_ships=True, ships=self.player.ships)
            opp = self.computer.grid.render()
            for l1, l2 in zip(own, opp):
                print(f"{l1:<{label_width}}    {l2.lstrip()}")


            # Display turn reports
            for r in self.reports:
                print(r)
            self.reports = []

            # Player turn
            move = input("Enter target (e.g. B3) or 'q' to quit: ").strip().lower()
            if move == 'q':
                sys.exit()
            tgt = self.player._parse(move.upper())
            if not tgt:
                self.reports.append("Invalid coordinate!")
                continue

            # Check if coordinate was already targeted
            if self.computer.grid.cells[tgt] != ' ':
                self.reports.append(f"You already fired at {move.upper()}!")
                continue

            # Process player attack
            hit = any(s.check_hit(tgt) for s in self.computer.ships)
            self.computer.grid.update(tgt, hit)
            self.reports.append(f"You fire at {move.upper()}: {'Hit' if hit else 'Miss'}")
            if self.computer.all_sunk():
                self.reports.append("🏆 You win! 🏆")
                self.display_and_exit()

            # AI turn
            pc_tgt = self.pc_ctrl.choose_target()
            hit_pc = any(s.check_hit(pc_tgt) for s in self.player.ships)
            self.player.grid.update(pc_tgt, hit_pc)
            self.pc_ctrl.process_result(pc_tgt, hit_pc)
            coord = f"{string.ascii_uppercase[pc_tgt[0]]}{pc_tgt[1]+1}"
            self.reports.append(f"Computer fires at {coord}: {'Hit' if hit_pc else 'Miss'}")
            if self.player.all_sunk():
                self.reports.append("💥 You lose! 💥")
                self.display_and_exit()

    def display_and_exit(self) -> None:
        """
        Final game state display and program termination.

        Shows complete board states with revealed ships and exits.
        """
        self.clear()
        # Render boards first
        own = self.player.grid.render(show_ships=True, ships=self.player.ships)
        opp = self.computer.grid.render()
        for l1, l2 in zip(own, opp):
            print(f"{l1:<{self.grid_size*2+3}}    {l2}")
        # Then show victory message
        for r in self.reports:
            print(r)
        sys.exit()

if __name__ == '__main__':
    Game().play()
