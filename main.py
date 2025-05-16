import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
import tkinter as tk
import csv
import random
from tkinter import messagebox
import os

# Get the directory of the current script
base_dir = os.path.dirname(os.path.abspath(__file__))

# Paths to the CSV files
easy_puzzles_path = os.path.join(base_dir, 'static', 'sudoku_easy.csv')
medium_puzzles_path = os.path.join(base_dir, 'static', 'sudoku_medium.csv')
hard_puzzles_path = os.path.join(base_dir, 'static', 'sudoku_hard.csv')

# Load puzzles into memory once
difficulty_paths = {
    "Easy": easy_puzzles_path,
    "Medium": medium_puzzles_path,
    "Hard": hard_puzzles_path
}

loaded_puzzles = {
    "Easy": [],
    "Medium": [],
    "Hard": []
}

for level, path in difficulty_paths.items():
    try:
        with open(path, 'r') as file:
            reader = csv.reader(file)
            loaded_puzzles[level] = [row[0] for row in reader if row]
    except Exception as e:
        print(f"Could not load {level} puzzles: {e}")

# Initialize the GUI window
root = ttkb.Window(themename="litera")
root.title("SudoGuru")

style = ttkb.Style()
current_theme = {"name": "litera"}

def toggle_theme():
    new_theme = "cyborg" if current_theme["name"] == "litera" else "litera"
    style.theme_use(new_theme)
    current_theme["name"] = new_theme
    theme_button.config(text=f"{'Light' if new_theme == 'cyborg' else 'Dark'} mode")

### FUNCTIONS

def clear_grid():
    clear_all_candidates()
    for i in range(9):
        for j in range(9):
            entries[i][j].config(state=tk.NORMAL)
            entries[i][j].delete(0, tk.END)

def is_valid_move(grid, row, col, number):
    for x in range(9):
        if grid[row][x] == number or grid[x][col] == number:
            return False
    corner_row, corner_col = 3 * (row // 3), 3 * (col // 3)
    for x in range(3):
        for y in range(3):
            if grid[corner_row + x][corner_col + y] == number:
                return False
    return True

def solve(grid, row=0, col=0):
    if col == 9:
        if row == 8:
            return True
        row += 1
        col = 0
    if grid[row][col] > 0:
        return solve(grid, row, col + 1)
    for num in range(1, 10):
        if is_valid_move(grid, row, col, num):
            grid[row][col] = num
            if solve(grid, row, col + 1):
                return True
        grid[row][col] = 0
    return False

def display_solution(grid):
    for i in range(9):
        for j in range(9):
            entries[i][j].config(state=tk.NORMAL)
            entries[i][j].delete(0, tk.END)
            entries[i][j].insert(0, str(grid[i][j]))

def is_valid_puzzle(grid):
    # Check for duplicates in rows, columns, or subgrids
    for i in range(9):
        row = [grid[i][j] for j in range(9) if grid[i][j] != 0]
        if len(row) != len(set(row)):  # Check for duplicates in the row
            return False
        col = [grid[j][i] for j in range(9) if grid[j][i] != 0]
        if len(col) != len(set(col)):  # Check for duplicates in the column
            return False
    # Check subgrids
    for i in range(3):
        for j in range(3):
            subgrid = [grid[i*3+k][j*3+l] for k in range(3) for l in range(3) if grid[i*3+k][j*3+l] != 0]
            if len(subgrid) != len(set(subgrid)):  # Check for duplicates in the subgrid
                return False
    return True

def solve_sudoku():
    clear_all_candidates()
    grid = [[0]*9 for _ in range(9)]
    for i in range(9):
        for j in range(9):
            try:
                value = int(entries[i][j].get())
                grid[i][j] = value
            except ValueError:
                grid[i][j] = 0
    # Check if the puzzle is valid before attempting to solve
    if not is_valid_puzzle(grid):
        messagebox.showinfo("Invalid Puzzle", "The puzzle contains duplicates in rows, columns, or subgrids.", icon="error")
        return
    if solve(grid):
        display_solution(grid)
    else:
        messagebox.showinfo("Unsolvable Puzzle", "Sorry, this puzzle cannot be solved.", icon="error")
        
def generate_sudoku():
    difficulty = difficulty_var.get()
    if difficulty not in loaded_puzzles or not loaded_puzzles[difficulty]:
        messagebox.showinfo("Error", f"No puzzles loaded for difficulty: {difficulty}")
        return
    random_puzzle = random.choice(loaded_puzzles[difficulty])
    grid = [[int(num) if num != '0' else '' for num in random_puzzle[i:i+9]] for i in range(0, 81, 9)]
    display_solution(grid)

pencil_mode = False
pencil_candidates = [["" for _ in range(9)] for _ in range(9)]

def toggle_pencil_mode():
    global pencil_mode
    pencil_mode = not pencil_mode
    pencil_button.config(bootstyle="success" if pencil_mode else "secondary-outline")

def clear_all_candidates():
    for i in range(9):
        for j in range(9):
            pencil_candidates[i][j] = ""
            display_candidates(i, j)

def enter_value(event, row, col):
    value = entries[row][col].get().strip()
    if pencil_mode:
        current_text = pencil_candidates[row][col]
        if value.isdigit() and 1 <= int(value) <= 9:
            current_text = current_text.replace(value, "") if value in current_text else current_text + value
            pencil_candidates[row][col] = current_text
            display_candidates(row, col)
        entries[row][col].delete(0, tk.END)
    else:
        try:
            int_value = int(value)
            if 1 <= int_value <= 9:
                entries[row][col].delete(0, tk.END)
                entries[row][col].insert(0, value)
                clear_pencil_candidates(row, col, value)
                pencil_candidates[row][col] = ""
                display_candidates(row, col)
        except ValueError:
            entries[row][col].delete(0, tk.END)

def clear_pencil_candidates(row, col, value):
    value = str(value)
    for i in range(9):
        for coord in [(row, i), (i, col)]:
            r, c = coord
            pencil_candidates[r][c] = pencil_candidates[r][c].replace(value, "")
            display_candidates(r, c)
    start_r, start_c = 3 * (row // 3), 3 * (col // 3)
    for i in range(3):
        for j in range(3):
            r, c = start_r + i, start_c + j
            pencil_candidates[r][c] = pencil_candidates[r][c].replace(value, "")
            display_candidates(r, c)

def display_candidates(row, col):
    text = pencil_candidates[row][col]
    for widget in entries[row][col].winfo_children():
        widget.destroy()
    for char in text:
        label = tk.Label(entries[row][col], text=char, font=('Arial', 9), fg='grey')
        r, c = divmod(int(char) - 1, 3)
        label.place(relx=c*0.32, rely=r*0.32, relwidth=0.32, relheight=0.32)

### GUI LAYOUT ###
main_frame = ttkb.Frame(root)
main_frame.pack(padx=10, pady=10)

entries = [[None for _ in range(9)] for _ in range(9)]

for i in range(3):
    for j in range(3):
        sub_grid = ttkb.Frame(main_frame, bootstyle="dark")
        sub_grid.grid(row=i, column=j, padx=2, pady=2)
        for x in range(3):
            for y in range(3):
                row, col = i*3 + x, j*3 + y
                entries[row][col] = ttkb.Entry(sub_grid, width=2, font=('Segoe UI', 16), justify='center', bootstyle='secondary')
                entries[row][col].grid(row=x, column=y, padx=1, pady=1)
                entries[row][col].bind("<KeyRelease>", lambda e, r=row, c=col: enter_value(e, r, c))

button_frame = ttkb.Frame(root)
button_frame.pack(pady=10)

difficulty_var = tk.StringVar()
difficulty_var.set("Easy")

difficulty_menu = ttkb.OptionMenu(button_frame, difficulty_var, "Easy", "Easy", "Medium", "Hard", bootstyle="primary")
difficulty_menu.pack(side=LEFT, padx=5)

gen_button = ttkb.Button(button_frame, text="Generate", command=generate_sudoku, bootstyle="success-outline")
gen_button.pack(side=LEFT, padx=5)

solve_button = ttkb.Button(button_frame, text="Solve", command=solve_sudoku, bootstyle="info-outline")
solve_button.pack(side=LEFT, padx=5)

clear_button = ttkb.Button(button_frame, text="Clear", command=clear_grid, bootstyle="warning-outline")
clear_button.pack(side=LEFT, padx=5)

pencil_button = ttkb.Button(button_frame, text="Pencil Mode", command=toggle_pencil_mode, bootstyle="secondary-outline")
pencil_button.pack(side=LEFT, padx=5)

theme_button = ttkb.Button(root, text="Dark mode", command=toggle_theme, bootstyle="info")
theme_button.pack(pady=5)

description_text = (
    "Welcome to the SudoGuru App!\n\n"
    "This application allows you to generate and solve Sudoku puzzles offline.\n"
    "Key Features:\n"
    "- Generate puzzles of varying difficulty (Easy, Medium, Hard)\n"
    "- Solve puzzles with a single click\n"
    "- Pencil feature for jotting down candidate numbers\n"
    "Enjoy solving Sudoku puzzles with ease!"
)

description_label = ttkb.Label(root, text=description_text, justify='left', padding=10, font=('Segoe UI', 10))
description_label.pack(pady=10)

root.mainloop()
