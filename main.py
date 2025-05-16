# FLASK FRAMEWORK #

# MODULES/LIBRARIES #
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import random
import secrets
import csv
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import time
import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Global variable to store puzzles
puzzles = {
    'easy': [],
    'medium': [],
    'hard': []
}

def load_puzzles():
    # Load puzzles from CSV files based on difficulty
    for difficulty in puzzles.keys():
        try:
            with open(f'static/sudoku_{difficulty}.csv', 'r') as file:
                reader = csv.reader(file)
                puzzles[difficulty] = [row[0] for row in reader]  # Extract the first element of each line as a puzzle
                print(f"Loaded {len(puzzles[difficulty])} {difficulty} puzzles from CSV file")  # Debug log
        except FileNotFoundError:
            print(f"Puzzle file for {difficulty} not found.")

load_puzzles()  # Load puzzles at startup

### FLASK AND DATABASE SETUP
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.permanent_session_lifetime = timedelta(hours=6)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.sqlite3"
#app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

db = SQLAlchemy(app)
mail = Mail(app)

# Temporary storage for reset codes
reset_codes = {}

# Temporary storage for OTPs
otp_storage = {}

# Set up logging
logging.basicConfig(level=logging.INFO)

class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(10), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    generator_grid = db.Column(db.Text, default='')  # Store generated grid as a string
    user_grid = db.Column(db.Text, default='')  # Store user-modified grid as a string
    home_grid = db.Column(db.Text, default='')  # Store home grid as JSON string
    solver_grid = db.Column(db.Text, default='')  # Store solver grid as JSON string
    easy_solved = db.Column(db.Integer, default=0)  # Counter for easy puzzles solved
    medium_solved = db.Column(db.Integer, default=0)  # Counter for medium puzzles solved
    hard_solved = db.Column(db.Integer, default=0)  # Counter for hard puzzles solved
    current_puzzle_time = db.Column(db.Integer, default=0)  # Store elapsed time in seconds
    last_generation_time = db.Column(db.DateTime, nullable=True)  # Store last generation time

    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.password = generate_password_hash(password)  # Hash the password when creating a user

    def check_password(self, password):
        """Check if the provided password matches the stored hashed password."""
        return check_password_hash(self.password, password)

# push context manually to app
with app.app_context():
    db.create_all()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redirect to the login page if not logged in
        return f(*args, **kwargs)
    return decorated_function

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')

        if not all([email, username, password]):
            return render_template('register.html', error="All fields are required.")
        
        existing_user = users.query.filter_by(email=email).first()
        if existing_user:
            return render_template('register.html', error="Email already registered.")

        # Generate and store OTP
        otp = random.randint(100000, 999999)
        otp_storage[email] = {
            'otp': otp,
            'expires': time.time() + 300  # 5 minutes from now
        }

        # Send OTP via email
        try:
            msg = Message("Your OTP Code", recipients=[email])
            msg.body = f"Your OTP code is: {otp}. It will expire in 5 minutes."
            mail.send(msg)
            return jsonify({'message': 'OTP sent to your email. Please verify.'}), 200
        except Exception as e:
            return jsonify({'error': 'Failed to send OTP.'}), 500

    return render_template('register.html')

@app.route('/register_otp', methods=['GET', 'POST'])
def register_otp():
    if request.method == 'GET':
        email = request.args.get('email')
        username = request.args.get('username')
        password = request.args.get('password')
        return render_template('register_otp.html', email=email, username=username, password=password)

    data = request.get_json()
    email = data.get('email')
    entered_otp = data.get('otp')
    username = data.get('username')
    password = data.get('password')

    if email in otp_storage:
        stored_otp = otp_storage[email]['otp']
        expires = otp_storage[email]['expires']

        if time.time() < expires and int(entered_otp) == stored_otp:
            # Create the new user after successful OTP verification
            new_user = users(
                email=email,
                username=username,
                password=password  
            )
            db.session.add(new_user)
            db.session.commit()  # Commit the new user to the database
            
            del otp_storage[email]  # Remove the OTP after successful registration
            
            return jsonify({'message': 'Registration successful! Please log in.'}), 200
        else:
            return jsonify({'error': 'Invalid or expired OTP.'}), 400
    else:
        return jsonify({'error': 'No OTP request found for this email.'}), 400

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.query.filter_by(username=username).first()  # Fetch user from the database

        if user and user.check_password(password):  # Use the check_password method
            session['user_id'] = user.id  # Store user ID in session
            session['username'] = user.username  # Store username in session
            return redirect(url_for('home'))  # Redirect to home after login

        flash('Invalid username or password')  # Show error message if login fails

    return render_template('login.html')  # Render the login page

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    data = request.get_json()  # Get the JSON data from the request
    user = users.query.get(session['user_id'])
    if user:
        user.current_puzzle_time = data.get('time', 0)  # Save the current timer state
        db.session.commit()  # Commit the changes to the database
    session.pop('user_id', None)  # Clear the user ID from the session
    session.pop('username', None)  # Clear the username from the session
    return jsonify({'message': 'Logged out successfully.'}), 200  # Return a success message

### SOLVER/GENERATOR LOGIC
def is_valid_move(grid, row, col, number):
    """Check if placing a number in the specified cell is valid according to Sudoku rules."""
    # Ensure number is not repeated in the current row, column, or 3x3 subgrid
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
    """Recursively attempt to solve the Sudoku puzzle using backtracking."""
    # Move to the next row if end of row is reached
    if col == 9:
        if row == 8:  # If at last cell, puzzle is solved
            return True
        row += 1
        col = 0

    # Skip cells that are already filled and move to the next cell
    if grid[row][col] > 0:
        return solve(grid, row, col + 1)
    
    # Try placing numbers 1-9 in the current cell
    for num in range(1, 10):
        if is_valid_move(grid, row, col, num):
            grid[row][col] = num  # Place the number
            if solve(grid, row, col + 1):  # Recur to solve the next cell
                return True
        grid[row][col] = 0  # Reset the cell if no valid number can be placed

    return False  # Return False if no solution is found

def is_valid_board(grid):
    """Check if the current board configuration is valid (no duplicates in rows, columns, or subgrids)."""
    invalid_positions = []
    # Check each row for duplicates
    for row_idx, row in enumerate(grid):
        seen = set()
        for col_idx, value in enumerate(row):
            if value != 0:
                if value in seen:
                    invalid_positions.append((row_idx, col_idx))
                seen.add(value)

    # Check each column for duplicates
    for col in range(9):
        seen = set()
        for row in range(9):
            value = grid[row][col]
            if value != 0:
                if value in seen:
                    invalid_positions.append((row, col))
                seen.add(value)

    # Check each 3x3 subgrid for duplicates
    for box_row in range(3):
        for box_col in range(3):
            seen = set()
            for row in range(3):
                for col in range(3):
                    value = grid[box_row * 3 + row][box_col * 3 + col]
                    if value != 0:
                        if value in seen:
                            invalid_positions.append((box_row * 3 + row, box_col * 3 + col))
                        seen.add(value)

    if invalid_positions:
        return False, "Duplicate found in board.", invalid_positions
    return True, "", []

@app.route('/', methods=['GET', 'POST'])
@login_required  # Protect this route
def home():
    if 'user_id' not in session:
        return render_template('home.html')

    user = users.query.get(session['user_id'])
    if not user:
        return render_template('home.html')

    # Convert stored grid from JSON string to list
    try:
        grid = eval(user.home_grid) if user.home_grid else [['' for _ in range(9)] for _ in range(9)]
    except:
        grid = [['' for _ in range(9)] for _ in range(9)]

    if request.method == 'POST':
        # Save the current grid state before processing other requests
        user.home_grid = str(grid)  # Save current grid state
        db.session.commit()  # Commit changes to the database

        if 'clear' in request.form:
            # Clear the board
            grid = [['' for _ in range(9)] for _ in range(9)]
            return render_template('home.html', grid=grid)

        if 'generate' in request.form:
            try:
                difficulty = request.form.get('difficulty', 'easy')  # Get selected difficulty

                if not puzzles[difficulty]:
                    return jsonify({'error': 'No puzzles available for the selected difficulty.'}), 500
                # Generate a random puzzle from the CSV file
                random_puzzle = random.choice(puzzles[difficulty])  # Randomly select a puzzle
                grid = [[int(num) if num != '0' else '' for num in random_puzzle[i:i+9]] for i in range(0, 81, 9)]
                # Store the generated grid in database
                user.home_grid = str(grid)
                db.session.commit()
                return jsonify({'grid': grid, 'generation_time': user.last_generation_time}), 200  # Return the generated grid and time
            except Exception as e:
                print(f"Error generating puzzle: {e}")  # Log the error
                return jsonify({'error': 'Failed to generate puzzle'}), 500

        # Handle the Sudoku solving logic
        grid = []
        for i in range(9):
            row = []
            for j in range(9):
                value = request.form.get(f'cell-{i}-{j}', '')
                row.append(value if value.isdigit() and value != '' else '')  # Keep empty cells as empty strings
            grid.append(row)

        # Convert grid to integers for solving
        grid = [[int(cell) if cell != '' else 0 for cell in row] for row in grid]

        # Validate the board before attempting to solve
        is_valid, error_message, invalid_positions = is_valid_board(grid)
        if not is_valid:
            flash(error_message)  # Display an error message if the board is invalid
            return render_template('home.html', grid=grid, invalid_positions=invalid_positions)  # Render the same grid with the error message

        # Attempt to solve the Sudoku puzzle
        if solve(grid):
            # Store the solved grid in database
            user.home_grid = str(grid)
            db.session.commit()
            return render_template('home.html', grid=grid)  # Render the solved grid
        else:
            flash("No solution exists for the given Sudoku puzzle.")
            return render_template('home.html', grid=grid, invalid_positions=[])  # Render the same grid with the error message

    return render_template('home.html', grid=grid)

@app.route('/solver', methods=['GET', 'POST'])
@login_required
def solver():
    """Render the Sudoku Solver page and handle form submissions."""
    if 'user_id' not in session:
        return render_template('solver.html')

    user = users.query.get(session['user_id'])
    if not user:
        return render_template('solver.html')

    # Convert stored grid from JSON string to list
    try:
        grid = eval(user.solver_grid) if user.solver_grid else [['' for _ in range(9)] for _ in range(9)]
    except:
        grid = [['' for _ in range(9)] for _ in range(9)]

    if request.method == 'POST':
        # Capture user inputs from the form
        for i in range(9):
            for j in range(9):
                value = request.form.get(f'cell-{i}-{j}', '')
                grid[i][j] = value if value.isdigit() and value != '' else ''  # Keep empty cells as empty strings

        # Save the current grid state before processing other requests
        user.solver_grid = str(grid)  # Save current grid state
        db.session.commit()  # Commit changes to the database

        if 'clear' in request.form:
            # Clear the board
            grid = [['' for _ in range(9)] for _ in range(9)]
            return render_template('solver.html', grid=grid)

        grid = []
        # Build the grid from the form input
        for i in range(9):
            row = []
            for j in range(9):
                value = request.form.get(f'cell-{i}-{j}', '')
                row.append(value if value.isdigit() and value != '' else '')  # Keep empty cells as empty strings
            grid.append(row)

        # Convert grid to integers for solving
        grid = [[int(cell) if cell != '' else 0 for cell in row] for row in grid]

        # Validate the board before attempting to solve
        is_valid, error_message, invalid_positions = is_valid_board(grid)
        if not is_valid:
            return render_template('solver.html', grid=[[str(cell) if cell != 0 else '' for cell in row] for row in grid], invalid_positions=invalid_positions)  # Render the same grid with the error message

        # Attempt to solve the Sudoku puzzle
        if solve(grid):
            # Store the solved grid in database
            user.solver_grid = str(grid)
            db.session.commit()
            return render_template('solver.html', grid=grid)  # Render the solved grid
        else:
            return render_template('solver.html', grid=[[str(cell) if cell != 0 else '' for cell in row] for row in grid], invalid_positions=[])  # Render the same grid with the error message

    return render_template('solver.html', grid=grid)

hints_used = 0

@app.route('/generator', methods=['GET', 'POST'])
@login_required
def generator():
    user = users.query.get(session['user_id'])  # Get the current user
    if user is None:
        return redirect(url_for('login'))  # Redirect to login if user is not found

    db.session.commit()
    
    # Initialize grid, user inputs, colors, and read-only status
    grid = [['' for _ in range(9)] for _ in range(9)]  # Default empty grid
    user_inputs = [['' for _ in range(9)] for _ in range(9)]  # Default empty user inputs
    colors = [['' for _ in range(9)] for _ in range(9)]  # Initialize colors
    read_only = [[False for _ in range(9)] for _ in range(9)]  # Initialize read-only status
    
    # Load the saved generator grid if the user is logged in
    if user and user.generator_grid:
        grid = eval(user.generator_grid)  # Load the saved grid from the database

    # Load the user-modified grid if available
    if user and user.user_grid:
        user_inputs = eval(user.user_grid)  # Load user inputs from the database

    if request.method == 'POST':
        # Capture user inputs from the form
        for i in range(9):
            for j in range(9):
                value = request.form.get(f'cell-{i}-{j}', '')
                if value.isdigit() and value != '':
                    user_inputs[i][j] = value  # Save user input
                else:
                    user_inputs[i][j] = ''  # Clear user input if not valid

        # Save user inputs to the database
        if user:
            user.user_grid = str(user_inputs)  # Save user inputs
            db.session.commit()  # Commit changes to the database

        if 'clear' in request.form:
            # Reset hints used when clearing the board
            hints_used = 0
            # Clear only the user inputs (empty cells)
            user_inputs = [['' for _ in range(9)] for _ in range(9)]
            return render_template('generator.html', grid=grid, user_inputs=user_inputs, colors=colors, read_only=read_only)

        if 'generate' in request.form:
            difficulty = request.form.get('difficulty', 'easy')  # Get selected difficulty
            user.current_puzzle_time = 0

            if not puzzles[difficulty]:
                return jsonify({'error': 'No puzzles available for the selected difficulty.'}), 500
            
            # Generate a random puzzle from the selected difficulty
            random_puzzle = random.choice(puzzles[difficulty])  # Randomly select a puzzle
            grid = [[int(num) if num != '0' else '' for num in random_puzzle[i:i+9]] for i in range(0, 81, 9)]
            
            # Save the generated grid to the database
            if user:
                user.generator_grid = str(grid)
                db.session.commit()

            # Prepare colors for the grid
            colors = [['black' if cell != '' else 'blue' for cell in row] for row in grid]

            # Prepare read-only status for the grid
            read_only = [[(cell != '') for cell in row] for row in grid]  # Set read-only status

            # Return the generated grid as JSON
            return jsonify({
                'grid': grid,
                'user_inputs': user_inputs,
                'colors': colors,
                'read_only': read_only,  # Set read-only status
                'generation_time': user.last_generation_time  # Return generation time
            })

    return render_template('generator.html', grid=grid, user_inputs=user_inputs, colors=colors, read_only=read_only)

@app.route('/get_hint', methods=['POST'])
def get_hint():
    """Handle hint requests separately from the generator route."""
    global hints_used

    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in to use hints.'})

    user = users.query.get(session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'})

    try:
        grid = eval(user.generator_grid) if user.generator_grid else [['' for _ in range(9)] for _ in range(9)]
    except:
        return jsonify({'success': False, 'message': 'Invalid grid state.'})

    if hints_used >= 3:
        return jsonify({'success': False, 'message': 'Hint limit reached. You can only use 3 hints per puzzle.'})

    # Create a copy of the grid for solving
    grid_copy = [[0 if cell == '' else cell for cell in row] for row in grid]
    
    # Solve the puzzle
    if solve(grid_copy):
        # Get all empty cells
        empty_cells = [(i, j) for i in range(9) for j in range(9) if grid[i][j] == '']
        
        if empty_cells:
            # Pick a random empty cell
            row, col = random.choice(empty_cells)
            # Fill in the selected cell with the solved value
            grid[row][col] = grid_copy[row][col]
            hints_used += 1  # Increment hints used
            
            # Update the grid in database
            user.generator_grid = str(grid)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'row': row,
                'col': col,
                'value': grid[row][col],
                'color': 'blue'  # Add color information
            })
        else:
            return jsonify({'success': False, 'message': 'No empty cells available for hints.'})
    else:
        return jsonify({'success': False, 'message': 'No solution exists for the current puzzle.'})

@app.route('/solve', methods=['POST'])
def solve_puzzle():
    grid = []
    for i in range(9):
        row = []
        for j in range(9):
            value = request.form.get(f'cell-{i}-{j}', '')
            row.append(int(value) if value.isdigit() and value != '' else 0)  # Convert to int or 0
        grid.append(row)

    if solve(grid):
        return jsonify({'solved': True, 'grid': grid})
    else:
        return jsonify({'solved': False})

@app.route('/clear', methods=['POST'])
def clear_puzzle():
    # Return an empty grid
    empty_grid = [['' for _ in range(9)] for _ in range(9)]
    return jsonify({'grid': empty_grid})

@app.route('/user/<string:username>')
@login_required
def user_page(username):
    """Render the user page for the logged-in user."""
    user = users.query.filter_by(username=username).first()  # Fetch user by username

    if not user or session['user_id'] != user.id:  # Check if user exists and matches logged-in user
        return "Access denied: You can only view your own user page.", 403  # Return a 403 Forbidden error

    return render_template('user_page.html', user=user)

@app.route('/save_user_input', methods=['POST'])
def save_user_input():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 403  # Return error if user is not logged in

    user = users.query.get(session['user_id'])
    if user:
        data = request.get_json()  # Get the JSON data from the request
        user_inputs = eval(user.user_grid) if user.user_grid else [['' for _ in range(9)] for _ in range(9)]

        # Update the user inputs based on the received data
        for cell_name, value in data.items():
            row, col = map(int, cell_name.split('-')[1:])  # Extract row and column from cell name
            user_inputs[row][col] = value  # Update the user input

        user.user_grid = str(user_inputs)  # Save updated user inputs to the database
        db.session.commit()  # Commit changes to the database

        print(f"Updated user inputs for user {user.id}: {user_inputs}")  # Log the updated inputs
    else:
        return jsonify({'error': 'User not found'}), 404  # Return error if user is not found

    return jsonify({'success': True})

@app.route('/update_solved_count', methods=['POST'])
def update_solved_count():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 403  # Return error if user is not logged in

    user = users.query.get(session['user_id'])
    if user:
        data = request.get_json()
        difficulty = data.get('difficulty')

        if difficulty == 'easy':
            user.easy_solved += 1
        elif difficulty == 'medium':
            user.medium_solved += 1
        elif difficulty == 'hard':
            user.hard_solved += 1

        db.session.commit()  # Commit changes to the database
        return jsonify({'success': True})
    return jsonify({'error': 'User not found'}), 404  # Return error if user is not found

@app.route('/api/send_email', methods=['POST'])
def send_email():
    data = request.get_json()  # Get the JSON data from the request

    # Validate the input data
    if not data or 'recipient' not in data or 'subject' not in data or 'body' not in data:
        return jsonify({'error': 'Missing required fields: recipient, subject, body'}), 400

    recipient = data['recipient']
    subject = data['subject']
    body = data['body']

    # Create and send the email
    try:
        msg = Message(subject, recipients=[recipient])
        msg.body = body
        mail.send(msg)
        return jsonify({'message': 'Email sent successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/forgot_password')
def forgot_password_page():
    return render_template('forgot_password.html')

@app.route('/api/request_otp', methods=['POST'])
def request_otp():
    data = request.get_json()
    email = data.get('email')

    # Check if the user exists
    user = users.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'If an account exists with that email, an OTP will be sent.'}), 200

    # Generate a random 6-digit OTP
    otp = random.randint(100000, 999999)
    otp_storage[email] = {
        'otp': otp,
        'expires': time.time() + 300  # 5 minutes from now
    }

    # Send the OTP via email
    try:
        msg = Message("Your OTP Code", recipients=[email])
        msg.body = f"Your OTP code is: {otp}. It will expire in 5 minutes."
        mail.send(msg)
        return jsonify({'message': 'OTP sent to your email address.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    if email in otp_storage:
        stored_otp = otp_storage[email]['otp']
        expires = otp_storage[email]['expires']

        try:
            entered_otp = int(otp)  # Convert the entered OTP to an integer
        except ValueError:
            return jsonify({'error': 'OTP must be a number.'}), 400

        if time.time() < expires and entered_otp == stored_otp:
            return jsonify({'message': 'OTP verified. You can now reset your password.'}), 200
        else:
            return jsonify({'error': 'Invalid or expired OTP.'}), 400
    else:
        return jsonify({'error': 'No OTP request found for this email.'}), 400

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('new_password')

    user = users.query.filter_by(email=email).first()
    if user:
        user.password = generate_password_hash(new_password)  # Hash the new password
        db.session.commit()
        del otp_storage[email]  # Remove the OTP after successful reset
        return jsonify({'message': 'Your password has been reset successfully.'}), 200
    else:
        return jsonify({'error': 'User not found.'}), 404

@app.route('/save_puzzle_time', methods=['POST'])
@login_required
def save_puzzle_time():
    data = request.get_json()
    user = users.query.get(session['user_id'])
    user.current_puzzle_time = data['time']  # Update the user's current puzzle time
    db.session.commit()
    return jsonify({'message': 'Puzzle time saved successfully.'}), 200

@app.route('/get_puzzle_time', methods=['GET'])
@login_required
def get_puzzle_time():
    user = users.query.get(session['user_id'])
    return jsonify({'time': user.current_puzzle_time}), 200

@app.route('/change_password/<string:username>', methods=['GET', 'POST'])
@login_required
def change_password(username):
    user = users.query.filter_by(username=username).first()

    if not user or session['user_id'] != user.id:
        return "Access denied: You can only reset your own password.", 403

    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')

        if not user.check_password(old_password):
            flash("Old password is incorrect.", "error")
            return render_template('change_password.html', user=user)

        # Update the password with the new hashed one
        user.password = generate_password_hash(new_password)
        db.session.commit()

        flash("Password updated successfully. Please log in again.", "success")
        session.clear()  # Log out the user after password change
        return redirect(url_for('login'))

    return render_template('change_password.html', user=user)

@app.route('/display_data')
def display_data():
    # Render the generator page
    return render_template('display_data.html')

if __name__ == '__main__':
    app.run(debug=True)
