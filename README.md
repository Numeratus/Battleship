# Battleship

Battleship is a console-based implementation of the classic naval strategy game “Battleship”, developed in Python and built as my Final Project for CS50 Python. This project features a fully interactive experience for a human player, who competes against an AI-controlled opponent. Three levels of AI difficulty (Easy, Medium, Hard) provide progressively challenging strategies, from random shooting to advanced probability-based targeting, ensuring both casual and seasoned players find an engaging experience.

---

## Project Structure

```
~/Battleship
├── battleship.py          # Main application logic and game loop
├── test_battleship.py     # Pytest suite covering core functionality
├── requirements.txt       # List of dependencies
└── README.md              # Project documentation (this file)
```

### battleship.py

All game logic resides in `battleship.py`. Key components include:

* **BoardPreset**: Predefined board sizes and ship configurations (small, medium, big).
* **AIStrategy** and its subclasses:

  * *RandomShooter* (Easy): Fires at random unexplored cells.
  * *SeekAndDestroy* (Medium): Switches to targeted neighboring attacks after a hit.
  * *StrategicGenius* (Hard): Implements a checkerboard hunting pattern followed by systematic adjacent probing.
* **Ship**: Tracks position and hit status of individual ships.
* **Grid**: Maintains cell states, renders board for both own and opponent view.
* **Player**: Handles ship placement (interactive and random), coordinate parsing, and fleet status checks.
* **Game**: Coordinates turn-based play, processes user input, updates both player and AI boards, and handles victory conditions.

### test\_battleship.py

The test suite uses pytest to verify:

* Board preset definitions and interactive selection flows.
* Correct behavior of all three AI strategies, including target selection and result processing.
* Ship hit detection and sinking logic.
* Grid initialization, updates, and rendering with and without ships.
* Player coordinate parsing, placement validation, random placement, and fleet sinking checks.
* Game initialization mapping difficulties to AI strategies, and terminal clear function.

---

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/Numeratus/battleship.git
   cd battleship/battleship
   ```

2. **Create a virtual environment** (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate      # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies** (none external required beyond standard library; add extras if extended):

   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

From the project root, run:

```bash
python battleship.py
```

1. **Select AI difficulty**: Easy, Medium, or Hard.
2. **Choose board preset**: small (5×5), medium (6×6), or big (8×8).
3. **Place your ships**:

   * Enter start coordinate (e.g., `A1`).
   * Specify orientation: horizontal `[h]` or vertical `[v]`.
4. **Gameplay loop**:

   * Your turn: enter target cell (e.g., `B3`) to fire.
   * AI turn: observe incoming fire results.
   * Boards and hit/miss reports are displayed side-by-side each turn.
5. **Victory condition**: All of one side’s ships are sunk.

---

## Testing

Run the test suite with pytest:

```bash
pytest
```

All core classes and functions are covered by tests, ensuring robust game logic and reliable AI behavior.

---

## Design Decisions and Reflections

1. **Strategy Pattern for AI**: To cleanly separate AI behaviors, an abstract `AIStrategy` class provides a common interface. Each difficulty subclass implements its own `choose_target` and `process_result` methods, to facilitate modifications.

2. **Grid Rendering**: Using a simple text-based grid allows for cross-platform compatibility without external graphics libraries. Revealing and hiding ship positions is controlled by a flag, simplifying display logic.

3. **Ship Placement**: Interactive placement in the console guides players visually by re-rendering the board after each placement, providing immediate feedback on valid and invalid placements.

---

Thank you for exploring my Project Battleship! Feel free to dive into the code, suggest improvements, or extend the game with new features. Good luck, and happy sinking!
