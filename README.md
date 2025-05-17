![🔢Sudoku_2-in-1 (1)](https://github.com/user-attachments/assets/c1684da3-e752-4338-b8bc-7a862dec6f06)

# SudoGuru - Sudoku Solver and Generator

## Overview

SudoGuru is a 2-in-1 Sudoku Solver and Generator built with Python and Tkinter. This application allows users to generate and solve Sudoku puzzles offline, providing a user-friendly interface and various features to enhance the solving experience.

## Features

- **Puzzle Generation**: Generate Sudoku puzzles of varying difficulty levels (Easy, Medium, Hard).
- **Puzzle Solving**: Solve puzzles with a single click using a backtracking algorithm.
- **Pencil Mode**: A feature that allows users to jot down candidate numbers for each cell.
- **User-Friendly Interface**: Built with Tkinter and ttkbootstrap for a modern look and feel, with dark and light theme.

## Installation

To install and run the SudoGuru application, follow these steps, either **run the installer** which can be found in the `dist` folder, or:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/sudoguru.git
   cd sudoguru
   ```

2. **Install Dependencies**:
   Make sure you have Python installed on your machine. Then, install the required packages using pip:
   ```bash
   pip install ttkbootstrap
   ```

3. **Download Puzzle Files**:
   Ensure you have the CSV files for Sudoku puzzles in the `static` directory:
   - `sudoku_easy.csv`
   - `sudoku_medium.csv`
   - `sudoku_hard.csv`

4. **Run the Application**:
   Execute the main script to start the application:
   ```bash
   python main.py
   ```

## Usage

- Launch the application, and you will see the Sudoku grid.
- Select the difficulty level from the dropdown menu.
- Click on "Generate" to create a new puzzle.
- Use the "Solve" button to find the solution for the current puzzle.
- Toggle "Pencil Mode" to enter candidate numbers for cells.


Enjoy solving Sudoku puzzles with ease!
