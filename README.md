# Move or Die

**Move or Die** is a simple 2D survival game built with Python using the Pygame library.  
Your objective is to survive as long as possible while enemies chase you across a randomly generated map.

The enemies use the **A\*** pathfinding algorithm to intelligently track the player, making the game progressively more challenging over time.

---

## Gameplay

- Control the player using the arrow keys
- Avoid enemies that chase you around the map
- Survive as long as possible to beat your best time
- Collect power-ups to gain temporary advantages

### The longer you survive

- Enemies become faster
- More enemies may appear
- The game becomes harder

---

## Features

- Grid-based movement system
- Intelligent enemy AI using A* pathfinding
- Randomly generated maps with obstacles
- Power-ups system:
  - Freeze – temporarily stops enemies
  - Teleport – instantly moves the player to a safe location
- Survival timer and best score tracking
- Increasing difficulty over time

---

## Requirements

- Python 3
- Pygame

### Install the dependency

```bash
pip install pygame
```

---

## Running the Game

```bash
python Move_or_die0.py
```

---

## Controls

| Key | Action |
|----|----|
| ↑ | Move Up |
| ↓ | Move Down |
| ← | Move Left |
| → | Move Right |
| ESC | Exit Game |

---

## Goal

Survive as long as possible without getting caught.  
If an enemy touches the player, the game resets and your **best survival time** is saved.

---

## License

This project is open source and free to use.
