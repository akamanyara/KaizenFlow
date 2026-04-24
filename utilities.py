from flask import session, redirect, flash
from functools import wraps
import sqlite3
from datetime import datetime

# Const values to control lvl up logic
BASE = 80
MULTIPLIER = 1.20

PENALTY_MULTIPLIER = 2

def alert(message, type, redirect_url):
    ''' Flash an alert message and redirect to a page '''
    flash(message, type)
    return redirect(redirect_url)


def login_required(f):
    ''' Wrapper function that requires user to login '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return alert("You have to be logged in to continue!", "warning", "/login")
        return f(*args, **kwargs)
    return decorated_function


def quest_earned_xp(diff):
    ''' Calculate the xp value for quest difficulty '''
    match diff:
        case "EASY": value = 20
        case "MEDIUM": value = 40
        case "HARD": value = 80
        case "BOSS": value = 200
        case _: value = 0
    return value


def calculate_xp_and_lvl(xp, lvl, earned_xp):
    ''' Calculate the new user xp and lvl '''
    
    # Calculate new users xp
    new_xp = xp + earned_xp
    # Calculate xp required to lvl up
    xp_to_lvl_up = BASE * (MULTIPLIER ** (lvl - 1))
    
    # Check for level ups
    while True:  
        
        if new_xp > xp_to_lvl_up:
            new_xp = new_xp - xp_to_lvl_up
            lvl += 1
            xp_to_lvl_up = BASE * (MULTIPLIER ** (lvl - 1))
            continue
        else:
            break
        
    return int(new_xp), lvl


def calculate_and_update_deadlines_penalties(user_id):
    ''' Calculate and apply penalties for players '''
    conn = sqlite3.connect("tracker.db")
    conn.row_factory = sqlite3.Row
    db = conn.cursor()
    
    # get user's data
    db.execute("SELECT level, current_xp FROM users WHERE id = ?", (user_id,))
    user = db.fetchone()
    if user:
        curr_lvl = user["level"]
        curr_xp = user["current_xp"]
    
    date = datetime.now().date().isoformat()
    
    # get quests where: deadline < date, status = "PENDING", penalty_applied = 0
    db.execute("""SELECT * FROM quests 
               WHERE user_id = ? AND deadline < ? AND status = 'PENDING' AND penalty_applied = 0""", 
               (user_id, date))
    late_quests = db.fetchall()
    
    # if there's no late quests return None
    if not late_quests:
        conn.close()
        return None
    
    total_penalty = 0

    # apply penalties
    for quest in late_quests:
        total_penalty += quest_earned_xp(quest["difficulty"]) * PENALTY_MULTIPLIER
        # mark quest as punished
        db.execute("UPDATE quests SET penalty_applied = 1 WHERE id = ?", (quest["id"],))
        
    # Calculate lvl and xp after penalty
    curr_xp -= total_penalty
    
    # if the new xp value is negative, we drop the level
    while curr_xp < 0 and curr_lvl > 1:
        curr_lvl -= 1    
        
        # calculate how much xp we needed for this level, and add it to the current xp
        xp_to_lvl_up = int(BASE * (MULTIPLIER ** (curr_lvl - 1)))
        curr_xp += xp_to_lvl_up
        
    # if there's still negative xp after that, at level 1 just set xp to 0
    if curr_xp < 0:
        curr_xp = 0
        
    # update the user's new data
    db.execute("UPDATE users SET level = ?, current_xp = ? WHERE id = ?", (curr_lvl, curr_xp, user_id))
    conn.commit()
    conn.close()
    
    # inform the user
    return total_penalty