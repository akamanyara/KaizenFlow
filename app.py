from flask import Flask, session, render_template, request, redirect, flash
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime, timedelta

from utilities import login_required, calculate_xp_and_lvl, quest_earned_xp, calculate_and_apply_penalty, BASE, MULTIPLIER

# App initialization
app = Flask(__name__)

# Auto reload config
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Session config
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#! -- LOGIN, SETTINGS, DASHBOARD SECTION -- 
@app.route("/register", methods=["GET", "POST"])
def register():
    ''' Register user '''
    if request.method == "POST":
        
        # Get data
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        nickname = request.form.get("nickname")

        # Data validation
        if not email or "@" not in email:
            flash("Enter email correctly", "danger")
            return redirect("/register")
        
        if not password:
            flash("Enter the password", "danger")
            return redirect("/register")
        
        if not confirmation:
            flash("Enter the confirmation password", "danger")
            return redirect("/register")
        
        if not nickname:
            flash("Enter the nickname", "danger")
            return redirect("/register")
        
        if password != confirmation:
            flash("Confirmation does not match the password", "danger")
            return redirect("/register")
        
        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create user in data base
        try:
            connection = sqlite3.connect("tracker.db")
            cursor = connection.cursor()
        
            cursor.execute(
                "INSERT INTO users (email, password_hash, nickname) VALUES (?, ?, ?)", 
                (email, hashed_password, nickname)
            )
        
            connection.commit()
        
        except sqlite3.IntegrityError:
            flash("Account with this email already exist", "warning")
            return redirect("/register")
        
        finally:
            if connection:
                connection.close()
        
        flash("Account created successfuly", "success")
        return redirect("/login") 
    
    else:
        return render_template("register.html")
    

@app.route("/login", methods=["GET", "POST"])
def login():
    ''' Login user '''
    
    if request.method == "POST":
        
        # Clear the current session
        session.clear()
        
        email = request.form.get("email")
        password = request.form.get("password")

        # Validation
        if not email or "@" not in email:
            flash("Incorrect email", "danger")
            return redirect("/login")

        if not password:
            flash("Incorrect password", "danger")
            return redirect("/login")

        # Check for data in user data base
        try:
            connection = sqlite3.connect("tracker.db")
            connection.row_factory = sqlite3.Row # For objects 
            
            cursor = connection.cursor()
            
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            
            user_data = cursor.fetchone()
        
        finally:
            connection.close()   
        
        # Check for the password correctness
        if user_data is None or not check_password_hash(user_data["password_hash"], password):
            flash("Incorrect email or password", "danger")
            return redirect("/login")
        
        # Create a session
        session["user_id"] = user_data["id"]
        
        flash("Logged in", "success")
        return redirect("/")
    
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    ''' Logout user '''
    
    # clear the users session
    session.clear()
    return redirect("/login")


@app.route("/")
@login_required
def index():
    
    # Deadlines penalty for user 
    penalty = calculate_and_apply_penalty(session["user_id"])
    if penalty:
        flash(f"You lost {penalty} XP due to not completing Quests on deadline!", "danger")
        
    # Get user's data: nickname, level, current_xp
    try: 
        conn = sqlite3.connect("tracker.db")
        conn.row_factory = sqlite3.Row
        db = conn.cursor()
        
        db.execute("SELECT nickname, level, current_xp FROM users WHERE id = ?", (session["user_id"],))
        data = db.fetchone()
        
        if data:
            user_nickname = data["nickname"]
            user_level = data["level"]
            user_xp = data["current_xp"]
    
    finally:
        if conn:
            conn.close()
    
    # Calculate xp required to level up and XP %
    req_xp = int(BASE * (MULTIPLIER ** (user_level - 1)))
    
    xp_percent = int((user_xp / req_xp) * 100)
    
    return render_template("index.html", nickname=user_nickname, level=user_level, curr_xp=user_xp, req_xp=req_xp, xp_percent=xp_percent)


#!-- QUESTS SECTION -- 
@app.route("/quests", methods=["GET", "POST"])
@login_required
def quests():
    ''' Active quests '''
    
    try:
        conn = sqlite3.connect("tracker.db")
        conn.row_factory = sqlite3.Row
        db = conn.cursor()
        
        # Get all user's quests
        db.execute("SELECT * FROM quests WHERE user_id = ? AND status = 'PENDING'", (session["user_id"],))
        
        quests = db.fetchall()
    
    finally:
        if conn:
            conn.close()
    
    return render_template("quest_base.html", quests=quests)


@app.route("/complete_quest", methods=["POST"])
@login_required
def complete_quest():
    
    quest_id = request.form.get("quest_id")
    if not quest_id:
        flash("Invalid quest", "danger")
        return redirect("/quests")
    
    try:
        conn = sqlite3.connect("tracker.db")
        conn.row_factory = sqlite3.Row
        db = conn.cursor()
        
        # Update quest status
        db.execute("UPDATE quests SET status = 'COMPLETED' WHERE id = ? AND user_id = ?", (quest_id, session["user_id"]))
        conn.commit()
        
        # Get the difficulty
        db.execute("SELECT difficulty FROM quests WHERE id = ? AND user_id = ?", (quest_id, session["user_id"]))
        diff = db.fetchone()
        
        # Get xp and level of user
        db.execute("SELECT current_xp, level FROM users WHERE id = ?", (session["user_id"], ))
        data = db.fetchone()
        
        if data:
            curr_xp = data["current_xp"]
            curr_lvl = data["level"]
        
        # Calculate new xp and level values
        earned_xp = quest_earned_xp(diff["difficulty"])
        new_xp, new_lvl = calculate_xp_and_lvl(curr_xp, curr_lvl, earned_xp)
        
        # Update the user database with new values
        db.execute("UPDATE users SET current_xp = ?, level = ? WHERE id = ?", 
                   (new_xp, new_lvl, session["user_id"]))
        conn.commit()
        
    except sqlite3.Error:
        flash("Error while updating quest status", "danger")
        return redirect("/quests")
    
    finally:
        if conn:
            conn.close()

    flash(f"Quest completed! You earned {earned_xp}xp!", "success")
    return redirect("/quests")


@app.route("/delete_quest", methods=["POST"])
@login_required
def delete_quest():
    ''' Completly remove quest from data base '''
    
    quest_id = request.form.get("quest_id")
    if not quest_id:
        flash("Couldn't find the quest", "warning")
        return redirect("/quests")
    
    # Delete quest from database
    conn = sqlite3.connect("tracker.db")
    db = conn.cursor()
    
    db.execute("DELETE FROM quests WHERE id = ? AND user_id = ?", (quest_id, session["user_id"]))
    
    conn.commit()
    conn.close()
    
    flash("Successfully removed quest", "success")
    return redirect("/quests")
    

@app.route("/add_quest", methods=["GET", "POST"])
@login_required
def add_quest():
    ''' Adding quests '''
    if request.method == "POST":
        
        # Get data
        title = request.form.get("title")
        description = request.form.get("description")
        deadline = request.form.get("deadline")
        difficulty = request.form.get("difficulty")
        
        # Validate data 
        if not title:
            flash("Invalid title", "danger")
            return redirect("/add_quest")
        
        if not deadline:
            deadline = None
        
        if not difficulty or difficulty not in ('EASY', 'MEDIUM', 'HARD', 'BOSS'):
            flash("Invalid difficulty", "danger")
            return redirect("/add_quest")
        
        # Save the data into database
        try:
            conn = sqlite3.connect("tracker.db")
            db = conn.cursor()
            
            db.execute("INSERT INTO quests (user_id, title, description, difficulty, deadline) VALUES (?, ?, ?, ?, ?)",
                       (session["user_id"], title, description, difficulty, deadline))
            conn.commit()
            
        except sqlite3.IntegrityError:
            flash("There was a problem creating a task", "danger")
            return redirect("/add_quest")
        
        finally:
            if conn:
                conn.close()
        
        flash("Created the task successfully", "success")
        return redirect("/quests")
    else:
        return render_template("quest_add.html")


@app.route("/deadlines")
@login_required
def deadlines():
    ''' Show the deadlines for the user '''
    
    # Todays date
    date = datetime.now()
    
    # Get data
    try:
        conn = sqlite3.connect("tracker.db")
        conn.row_factory = sqlite3.Row
        db = conn.cursor()
        
        db.execute("SELECT title, deadline FROM quests WHERE user_id = ? AND status = 'PENDING' AND deadline IS NOT NULL ORDER BY deadline ASC",
                   (session["user_id"],))
        
        quests = db.fetchall()
        formatted_quests = []
        
        if quests:
            for quest in quests:
                # calculate days left
                deadline = datetime.strptime(quest["deadline"], "%Y-%m-%d")
                days_left = deadline.date() - date.date()
                
                formatted_quests.append({
                    "title": quest["title"],
                    "deadline": quest["deadline"],
                    "days_left": days_left.days
                })
                
    finally:
        if conn:
            conn.close()
    
    today_date = date.strftime("%d %B %Y")
    
    return render_template("deadlines.html", quests=formatted_quests, today_date=today_date)


#!-- HABITS SECTION -- 
@app.route("/habits")
@login_required
def habit_tracker():
    '''Track the users daily habits'''
    todays_date = datetime.now().date().isoformat()
    
    conn = sqlite3.connect("tracker.db")
    conn.row_factory = sqlite3.Row
    db = conn.cursor()
    
    # Get the habits data
    db.execute(""" SELECT ha.id, ha.title, ha.streak, history.completion_date 
                   FROM habits ha
                   LEFT JOIN habits_history history
                   ON ha.id = history.habit_id AND history.completion_date = ?
                   WHERE ha.user_id = ?
               """, (todays_date, session["user_id"]))

    habits = db.fetchall()
    
    conn.close()
    
    return render_template("habits.html", habits=habits)


@app.route("/add_habit", methods=["POST"])
@login_required
def add_habit():
    
    title = request.form.get("title")
    if not title:
        flash("Invalid habit name.", "danger")
        return redirect("/habits")
    
    # add the habit into the database
    conn = sqlite3.connect("tracker.db")
    db = conn.cursor()
    
    db.execute("INSERT INTO habits (user_id, title) VALUES (?, ?)", (session["user_id"], title))
    
    conn.commit()
    conn.close()
        
    flash("Added habit successfully", "success")
    return redirect("/habits")


@app.route("/delete_habit", methods=["POST"])
@login_required
def delete_habit():
    pass


@app.route("/complete_habit", methods=["POST"])
@login_required
def complete_habit():
    '''Complete the habit task, reward the user and update database'''
    
    # get habit id
    habit_id = request.form.get("habit_id")
    if not habit_id:
        flash("Invalid habid id", "danger")
        return redirect("/habits")

    # get todays and yesterdays date
    todays_date = datetime.now().date().isoformat()
    yesterdays_date = (datetime.now() - timedelta(days=1)).date().isoformat()
    
    try: 
        # check for the streak and it's continuation
        conn = sqlite3.connect("tracker.db")
        conn.row_factory = sqlite3.Row
        db = conn.cursor()
        
        db.execute("SELECT streak FROM habits WHERE user_id = ? AND id = ?", (session["user_id"], habit_id))
        habit_data = db.fetchone()
        if habit_data:
            users_streak = habit_data["streak"]
        else:
            users_streak = 0
        
        db.execute("SELECT completion_date FROM habits_history WHERE habit_id = ? AND completion_date = ?", (habit_id, yesterdays_date))
        yesterdays_data = db.fetchone()
        if yesterdays_data:
            users_streak += 1
        else:
            users_streak = 1

        # update the database
        db.execute("INSERT INTO habits_history (habit_id, completion_date) VALUES (?, ?)", (habit_id, todays_date))
        db.execute("UPDATE habits SET streak = ? WHERE user_id = ? AND id = ?", (users_streak, session["user_id"], habit_id))
        
        # get users data for rewards
        db.execute("SELECT level, current_xp FROM users WHERE id = ?", (session["user_id"],))
        user_data = db.fetchone()
        if user_data:
            level = user_data["level"]
            xp = user_data["current_xp"]
                  
            # reward the player with streak bonus
            base_xp = 10
            
            if users_streak >= 21:
                bonus_multiplier = 2.0
            elif users_streak >= 14:
                bonus_multiplier = 1.75
            elif users_streak >= 7:
                bonus_multiplier = 1.5
            elif users_streak >= 3:
                bonus_multiplier = 1.1
            else: 
                bonus_multiplier = 1.0
                
            earned_xp = int(base_xp * bonus_multiplier)
            new_xp, new_lvl = calculate_xp_and_lvl(xp, level, earned_xp)

            # update the users stats
            db.execute("UPDATE users SET level = ?, current_xp = ? WHERE id = ?", (new_lvl, new_xp, session["user_id"]))
        
        conn.commit()
        flash(f"Habit completed, you earned {earned_xp} XP! Streak: {users_streak}", "success")
    
    except sqlite3.IntegrityError:
        flash("You already completed this habit today!", "warning")
        
    finally:
        if conn:
            conn.close()
    
    return redirect("/habits")
    
    
# Server starter
if __name__ == "__main__":
    app.run(debug=True)