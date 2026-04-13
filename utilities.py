from flask import session, redirect, flash
from functools import wraps

# Const values to control lvl up logic

BASE = 80
MULTIPLIER = 1.20

def login_required(f):
    ''' Wrapper function that requires user to login '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            flash("You have to be logged in to continue!", "warning")
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def quest_earned_xp(diff):
    ''' Calculate the xp value for quest difficulty '''
    match diff:
        case "EASY": value = 10
        case "MEDIUM": value = 30
        case "HARD": value = 80
        case "BOSS": value = 200
        case _: value = 0
    return value


def calculate_xp_and_lvl(xp, lvl, earned_xp):
    ''' Calculate the new user xp and lvl '''
    
    # Calculate new xp
    new_xp = xp + earned_xp
    
    # Calculate xp required to lvl up
    lvl_up_xp = BASE * (MULTIPLIER ** (lvl - 1))
    
    # Check for level ups
    while True:
        
        if new_xp > lvl_up_xp:
            new_xp = new_xp - lvl_up_xp
            lvl += 1
            
            lvl_up_xp = BASE * (MULTIPLIER ** (lvl - 1))
            continue
        else:
            break
        
    return int(new_xp), lvl