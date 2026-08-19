# 🧭 AI Maze Navigation

> **A maze game where finding the shortest path isn't necessarily the best path.**

AI Maze Navigation is an algorithmic maze game that explores **multi-objective pathfinding**.

Instead of simply asking:

> *"What is the shortest path from A to B?"*

the game asks:

> **"What is the best path when distance, energy, terrain, and time all matter?"**

Players navigate through procedurally generated mazes containing different terrain types, movement costs, slopes, and energy consumption.

To win, a player's route must achieve a sufficiently high score compared with the **AI-computed optimal solution**.

---

## 🎯 The Idea

Traditional maze games usually evaluate a path using a single objective:

```text
Shortest Path
      ↓
Reach the Goal
      ↓
Win
```

AI Maze Navigation introduces multiple competing objectives:

```text
                 ┌── Distance
                 │
                 ├── Energy
Player Path ─────┼── Time
                 │
                 └── Terrain Cost
                         │
                         ▼
                  Overall Score
```

A shorter path may consume significantly more energy.

A longer path may be slower but much more energy-efficient.

A path through steep terrain may be shorter but more expensive than taking a flatter route.

Therefore:

> **The shortest path is not always the optimal path.**

---

## 🎮 Gameplay

The player starts at an **origin** and must reach a **destination** inside a procedurally generated maze.

Each cell can have different properties:

* 🟩 Walkable terrain
* 🪨 Difficult terrain
* ⛰️ Different elevation / slope
* ⚡ Different energy costs
* ⏱️ Different movement costs

The player must choose a route that balances multiple objectives.

### Example

Consider two possible routes:

```text
Route A
Distance:  80
Energy:    140
Time:       60

Route B
Distance:  95
Energy:     90
Time:       55
```

If the game prioritizes energy efficiency, **Route B may be considered better despite being longer**.

This creates a strategic decision:

> **Do you take the shortest route, or the route that is actually more efficient?**

---

## 🧠 Multi-Objective Pathfinding

The core of the project is treating pathfinding as an **optimization problem with multiple objectives**.

Instead of minimizing only:

```text
Distance
```

the system considers a weighted objective:

```text
Overall Cost =
    w₁ × Distance
  + w₂ × Energy
  + w₃ × Time
  + w₄ × Terrain Cost
```

where:

```text
w₁ + w₂ + w₃ + w₄ = 1
```

The weights determine the priorities of the current game.

For example:

```text
Energy-focused:

Distance   = 0.20
Energy     = 0.50
Time       = 0.20
Terrain    = 0.10
```

This means the AI considers **energy consumption more important than distance**.

---

## 🏆 How Do You Win?

The game does not require the player to find the exact same path as the AI.

Instead, the player's route is evaluated against the AI's optimal solution.

```text
              Maze
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
   Player Route    AI Solver
        │             │
        ▼             ▼
   Path Metrics    Optimal Metrics
        │             │
        └──────┬──────┘
               ▼
          Score / Ratio
               │
               ▼
         Win / Continue
```

A player can therefore discover a **different route** and still win, as long as its overall performance is sufficiently close to the optimal solution.

For example:

```text
AI Optimal Score:       100
Player Score:            94

Performance:
94 / 100 = 94%

Required threshold:
≥ 90%

Result:
🏆 WIN
```

This makes the game less about reproducing an AI's exact path and more about **making a good decision under multiple constraints**.

---

## 🤖 AI Solver

The project provides pathfinding algorithms that can search the maze and compare possible routes.

Current algorithmic components include:

* **BFS** — baseline pathfinding
* **DFS** — exploration baseline
* **Dijkstra** — weighted shortest-path search
* **A*** — heuristic-guided search

These algorithms provide different ways to reason about the maze.

### Why not just use BFS?

Because once movement has different costs:

```text
1 step ≠ 1 cost
```

A path with fewer cells may not have the lowest total cost.

This makes algorithms such as **Dijkstra and A*** much more interesting in the weighted environment.

---

## 🗺️ Maze Generation

The maze is procedurally generated rather than manually designed.

This allows the system to create different environments for each game.

The generation layer is separated from the solving layer:

```text
Maze Generation
       │
       ▼
Maze Representation
       │
       ▼
Terrain / Movement Costs
       │
       ▼
Pathfinding Algorithms
       │
       ▼
Path Evaluation
```

This separation makes it possible to experiment with different maze generators and AI strategies independently.

---

## 🌍 Terrain & Environment

A major part of the project is moving beyond a binary maze:

```text
Walkable / Blocked
```

and towards a richer environment where each location can have different characteristics.

Conceptually:

```text
Cell
├── Position
├── Terrain
├── Elevation
├── Movement Cost
├── Energy Cost
└── Time Cost
```

This allows the same maze layout to produce different optimal routes depending on the objective weights.

---

## ⚡ Energy Model

Movement can consume different amounts of energy depending on the environment.

For example:

```text
Flat terrain
    ↓
Low energy cost

Steep terrain
    ↓
Higher energy cost

Difficult terrain
    ↓
Higher movement cost
```

This introduces another constraint into pathfinding:

> A path that reaches the goal quickly may leave the player with significantly less energy.

Future versions can make energy a **hard constraint**, where a route becomes invalid if the player cannot complete it with the available energy.

---

## ⏱️ Time Model

The game can also associate different movement times with terrain and movement conditions.

A route can therefore be evaluated using:

```text
Total Time
= Σ movement time of each step
```

This allows the player to trade:

```text
Distance ↔ Energy ↔ Time
```

instead of optimizing a single metric.

---

## 📊 Path Evaluation

Every completed route can be represented as a set of measurable metrics:

```text
Path
├── Distance
├── Energy Consumption
├── Time
├── Terrain Cost
└── Overall Score
```

These metrics are combined using the current objective weights.

This makes the project not only a pathfinding problem, but also a **path evaluation and optimization problem**.

---

## 🏗️ Project Architecture

The project is organized into several independent components:

```text
ai_maze_navigation/
│
├── algorithms/
│   ├── bfs.py
│   ├── dfs.py
│   ├── dijkstra.py
│   └── astar.py
│
├── core/
│   ├── cell.py
│   ├── maze.py
│   ├── path.py
│   └── terrain.py
│
├── generation/
│   └── recursive_backtracking.py
│
├── simulation/
│
├── ui/
│
├── tests/
│
├── experiments/
│
├── config.py
├── main.py
├── requirements.txt
└── README.md
```

The separation between **core data structures, maze generation, algorithms, simulation, UI, and tests** is intended to make the project easier to extend.

---

## 🛠️ Tech Stack

| Component       | Technology                          |
| --------------- | ----------------------------------- |
| Language        | Python                              |
| Algorithms      | BFS, DFS, Dijkstra, A*              |
| Data Structures | Custom grid / graph representations |
| Maze Generation | Recursive Backtracking              |
| Testing         | Python test suite                   |
| Visualization   | Python-based UI                     |
| Version Control | Git / GitHub                        |

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/nguyenquangtrunghieu2k7-coder/ai_maze_navigation.git
cd ai_maze_navigation
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the project

```bash
python main.py
```

---

## 🧪 Current Status

**Status: Active Development**

### Implemented

* [x] Maze representation
* [x] Cell and terrain models
* [x] Procedural maze generation
* [x] BFS pathfinding
* [x] DFS pathfinding
* [x] Dijkstra pathfinding
* [x] A* pathfinding
* [x] Path representation
* [x] Algorithm testing
* [ ] Multi-objective scoring system
* [ ] Energy simulation
* [ ] Time-based movement model
* [ ] Full terrain cost model
* [ ] Player-vs-AI evaluation
* [ ] Complete game UI

---

## 🔬 Experiments

The `experiments/` directory is used to investigate algorithm behavior and compare different pathfinding strategies.

Potential experiments include:

* Algorithm runtime comparison
* Path length comparison
* Energy consumption
* Search efficiency
* Weighted objective changes
* Different terrain distributions
* Different maze sizes

The long-term goal is to move from:

> **"Which algorithm finds a path?"**

towards:

> **"Which strategy finds the best path under different objectives?"**

---

## 🔭 Future Directions

### Multi-objective Optimization

Instead of combining objectives immediately into a single weighted score, future versions could explore **Pareto-optimal paths**.

For example:

```text
          Lower Energy
               ↑
               │    ● A
               │
               │         ● B
               │
               │               ● C
               └────────────────────→
                    Shorter Distance
```

A path may be optimal for one objective while another path is better for a different objective.

This opens the possibility of comparing:

* Weighted-sum optimization
* Pareto fronts
* Different player preferences
* Dynamic objective weights

---

### Dynamic Environments

Future versions could introduce:

* Moving obstacles
* Changing terrain costs
* Limited energy
* Time-dependent paths
* Random environmental events

This would turn the problem into a more dynamic navigation environment rather than a static maze.

---

### AI vs Human Analysis

Another possible direction is comparing:

```text
Human Player
     vs
AI Solver
```

using:

* Path efficiency
* Energy efficiency
* Decision time
* Objective trade-offs

The goal would be to analyze **how humans and algorithms make navigation decisions under competing objectives**.

---

## 💭 Project Motivation

This project started from a simple idea:

> **What if a maze game wasn't really about finding the exit?**

A player might know several ways to reach the goal.

The interesting question becomes:

> **Which route should you choose?**

The project explores that question through algorithms, optimization, and game mechanics.

---

## 👨‍💻 Author

**Nguyễn Quang Trung Hiếu — Bánh mì kẹp bèo 🥖**

Data Science & AI @ HUST

Interested in **AI × Algorithms × Systems**.

---

> **Don't just find a path. Find a better one.**
