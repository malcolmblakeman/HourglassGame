# ⏳ Hourglass Puzzle Game

An interactive puzzle engine built with **Python** and **Streamlit** for solving and playing hourglass timing puzzles.

Unlike traditional hourglass games that present only a fixed solution, this project contains a complete simulation engine capable of evaluating the current board state, computing optimal moves in real time, and supporting both single-target and sequential multi-target timing puzzles.

---

## Overview

The objective is to measure an exact amount of time using a collection of hourglasses of different durations.

Players may flip any combination of hourglasses whenever sand finishes flowing, attempting to reach the target time using as few flips as possible.

The engine includes an optimal solver that can determine the mathematically shortest sequence of flips from **any current game state**, allowing hints to remain accurate even after mistakes or experimentation.

---

## Features

### 🎮 Interactive Gameplay

* Dynamic hourglass simulation
* Stage multiple flips before advancing time
* Event-driven time progression
* Undo previous moves
* Reset puzzles instantly
* Chronological event log

---

### 🧩 Multiple Game Modes

#### Single-Target Mode

Reach one exact target time.

Example:

```text
Hourglasses:
4m, 7m

Goal:
9 minutes
```

---

#### Sequential Multi-Target Mode

Reach multiple checkpoints in order without restarting.

Example:

```text
Hourglasses:
21m, 24m, 29m

Goals:
30 → 33 → 38 minutes
```

---
#### Convergence Mode

Manage N isolated groups of hourglasses (channels) simultaneously. All channels must maintain continuous sand flow and finish running at the exact same final timestamp.

Example:

```text
Hourglasses:
Channel A: 3m, 4m | Channel B: 5m, 7m

Target:
8 minutes
```

---
### 💡 Optimal Hint System

Hints are not pre-recorded.

Whenever the player requests help, the engine performs a fresh search beginning from the **current board configuration** and returns the optimal immediate action required to stay on the shortest solution path.

If no solution exists from the current state, the engine reports that the puzzle has become mathematically impossible.

---

### 📚 Puzzle Library

The application loads puzzles dynamically from external JSON datasets.

Features include:

* Rank-based difficulty filtering
* Random puzzle selection
* Automatic level loading
* Support for both standard, sequential, and convergence puzzles

---

### 🏆 Difficulty Ranking

Puzzles are organized into progressively more complex categories.

Single-target ranks include:

* Rank 1 – Linear Tutorial
* Rank 2 – One Midflip
* Rank 3 – Two Midflips
* Rank 4 – One Midflip, Three Glasses
* Rank 5 – Two Midflips, Three Glasses
* Rank 6 – Three Midflips, Three Glasses
* Rank 7 – Synergistic Two Midflips
* Rank 8 – Synergistic Three Midflips

Sequential puzzles contain their own ranking system based on checkpoint complexity.

---

## Solver

The project contains a complete **Breadth-First Search (BFS)** solver.

Each search state stores:

* Remaining sand in every hourglass
* Current elapsed time
* (Sequential mode) active checkpoint index

From every state, the solver explores every possible combination of simultaneous flips, advancing time only to the next event boundary.

The search guarantees:

* shortest-flip solution
* exact timing
* valid simultaneous flip handling
* support for arbitrary mid-game positions

Because hints search from the live board state, they remain optimal even after incorrect player moves.

---

## Technologies

* Python
* Streamlit
* Breadth-First Search (BFS)
* JSON puzzle datasets

---

## Running the Project

Install the dependencies:

```bash
pip install streamlit
```

Run the application:

```bash
streamlit run app.py
```

---

## Project Structure

```text
.
├── app.py
├── generate_ranked_puzzles.py
├── generate_multitarget_puzzles.py
├── generate_converg_2ch_puzzles.py
├── generate_converg_3ch_puzzles.py
├── all_hourglass_puzzles.txt
├── multitarget_puzzles.txt
├── convergence_puzzles.txt
└── README.md
```

---

## Gameplay

Each turn follows the same sequence:

1. Stage any number of hourglass flips.
2. Submit the turn.
3. Time advances automatically to the next hourglass event.
4. Sand levels update.
5. The engine checks whether the target has been reached or exceeded.

Players cannot advance arbitrary amounts of time—the simulation always moves to the next meaningful event.

---

## Current Features

* ✅ Single-target puzzles
* ✅ Sequential checkpoint puzzles
* ✅ Convergence puzzles
* ✅ Optimal BFS solver
* ✅ Live hint generation
* ✅ Undo system
* ✅ Dynamic puzzle loading
* ✅ Difficulty ranking
* ✅ Random puzzle selection
* ✅ Event history
* ✅ Simultaneous flip support
---

## Why This Project?

This project began as an exploration of classic hourglass timing puzzles and evolved into a general-purpose puzzle engine.

Rather than hard-coding solutions, every puzzle is treated as a search problem. The engine simulates the complete state space, allowing it to verify solvability, compute optimal solutions, and generate hints dynamically from any position.

The result is both an educational tool for exploring search algorithms and a fully playable puzzle game. 

Honestly its a chill way to relax and take a fun math break from whatever you're doing as well ;)

---

## License

This project is open source. Feel free to fork, modify, and expand upon it.
