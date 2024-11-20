import tkinter as tk
from tkinter import messagebox
import random
import time

def is_valid_move(grid, row, col, number):
    for x in range(9):
        if grid[row][x] == number:
            return False
        
    for x in range(9):
        if grid[x][col] == number:
            return False
    
    corner_row = row - row % 3
    corner_col = col - col % 3 
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

def solve_sudoku():
    clear_all_candidates()  # Clear all candidates
    grid = [[0]*9 for _ in range(9)]
    for i in range(9):
        for j in range(9):
            try:
                value = int(entries[i][j].get())
                grid[i][j] = value
            except ValueError:
                grid[i][j] = 0

    if solve(grid, 0, 0):
        display_solution(grid)
    else:
        messagebox.showinfo("No Solution", "No solution exists for the given Sudoku puzzle.")

def clear_grid():
    clear_all_candidates()
    for i in range(9):
        for j in range(9):
            pencil_candidates[i][j] = ""
            display_candidates(i, j)
    for i in range(9):
        for j in range(9):
            entries[i][j].config(state=tk.NORMAL)
            entries[i][j].delete(0, tk.END)

def generate_sudoku():
    clear_all_candidates()  
    # Create an empty grid
    grid = [[0]*9 for _ in range(9)]

    # Fill the diagonal 3x3 sub-grids
    for i in range(0, 9, 3):
        fill_diagonal_sub_grid(grid, i, i)

    # Fill remaining blocks
    solve(grid)

    # Remove some numbers to create a puzzle
    remove_numbers_from_grid(grid)
    
    # Display the generated puzzle
    display_solution(grid)

def fill_diagonal_sub_grid(grid, row, col):
    nums = list(range(1, 10))
    random.shuffle(nums)
    for i in range(3):
        for j in range(3):
            grid[row + i][col + j] = nums.pop()

def remove_numbers_from_grid(grid, removal_count=65):
    #List of picked cells
    picked = set()

    while removal_count > 0:
        row = random.randint(0, 8)
        col = random.randint(0, 8)

        if (row, col) in picked:
            continue

        if grid[row][col] != 0 or grid[row][col] != '' or grid[row][col] != ' ':
            grid[row][col] = ''
            picked.add((row,col))
            removal_count -= 1

#Candidates
def toggle_pencil_mode():
    global pencil_mode
    pencil_mode = not pencil_mode
    pencil_button.config(relief=tk.SUNKEN if pencil_mode else tk.RAISED)

def enter_value(event, row, col):
    value = entries[row][col].get().strip()
    if pencil_mode:
        current_text = pencil_candidates[row][col]
        if value.isdigit() and 1 <= int(value) <= 9:
            if value in current_text:
                current_text = current_text.replace(value, "")
            else:
                current_text += value
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
        if value in pencil_candidates[row][i]:
            pencil_candidates[row][i] = pencil_candidates[row][i].replace(value, "")
            display_candidates(row, i)
        if value in pencil_candidates[i][col]:
            pencil_candidates[i][col] = pencil_candidates[i][col].replace(value, "")
            display_candidates(i, col)
    
    corner_row = (row // 3) * 3
    corner_col = (col // 3) * 3
    for i in range(3):
        for j in range(3):
            if value in pencil_candidates[corner_row + i][corner_col + j]:
                pencil_candidates[corner_row + i][corner_col + j] = pencil_candidates[corner_row + i][corner_col + j].replace(value, "")
                display_candidates(corner_row + i, corner_col + j)

def display_candidates(row, col):
    text = pencil_candidates[row][col]
    for widget in entries[row][col].winfo_children():
        widget.destroy()
    for char in text:
        candidate_label = tk.Label(entries[row][col], text=char, font=('Arial', 9), fg='grey')
        index = int(char) - 1
        r, c = divmod(index, 3)
        candidate_label.place(relx=c*0.32, rely=r*0.32, relwidth=0.32, relheight=0.32)

def clear_all_candidates():
    for i in range(9):
        for j in range(9):
            pencil_candidates[i][j] = ""
            display_candidates(i, j)
    
# Create the GUI window
root = tk.Tk()
root.title("Sudoku Solver")

pencil_mode = False
pencil_candidates = [["" for _ in range(9)] for _ in range(9)]

# Create a main frame to hold everything
main_frame = tk.Frame(root)
main_frame.pack(padx=10, pady=10)

entries = [[None for _ in range(9)] for _ in range(9)]

cell_size = 50

# Create 3x3 sub-grids
for i in range(3):
    for j in range(3):
        sub_grid = tk.Frame(main_frame, bd=2, relief="solid")
        sub_grid.grid(row=i, column=j, padx=(0, 0), pady=(0, 0))
        for x in range(3):
            for y in range(3):
                row = i * 3 + x
                col = j * 3 + y
                entries[row][col] = tk.Entry(sub_grid, width=2, font=('Times New Roman', 18), justify='center')
                entries[row][col].grid(row=x, column=y, padx=1, pady=1)
                entries[row][col].config(width=2)
                entries[row][col].bind("<KeyRelease>", lambda event, r=row, c=col: enter_value(event, r, c))
                entries[row][col].grid_propagate(False)

# Create buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

gen_button = tk.Button(button_frame, text="Generate", command=generate_sudoku)
gen_button.pack(side=tk.LEFT, padx=5)

solve_button = tk.Button(button_frame, text="Solve", command=solve_sudoku)
solve_button.pack(side=tk.LEFT, padx=5)

clear_button = tk.Button(button_frame, text="Clear", command=clear_grid)
clear_button.pack(side=tk.LEFT, padx=5)

pencil_button = tk.Button(button_frame, text="Pencil Mode", command=toggle_pencil_mode, relief=tk.RAISED)
pencil_button.pack(side=tk.LEFT, padx=10)

# Set window size to be square
root.update()
root.geometry(f"{main_frame.winfo_width() + 40}x{main_frame.winfo_height() + 100}")

root.mainloop()
