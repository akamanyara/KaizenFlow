util:

1. 

index:

# Deadlines penalty for user 
    penalty = calculate_and_apply_penalty(session["user_id"])
    if penalty:
        flash(f"You lost {penalty} XP due to not completing Quests on deadline!", "danger")

 # Calculate xp required to level up and XP %
    req_xp = int(BASE * (MULTIPLIER ** (user_level - 1)))
    
    xp_percent = int((user_xp / req_xp) * 100)
    
    return render_template("index.html", nickname=user_nickname, level=user_level, curr_xp=user_xp, req_xp=req_xp, xp_percent=xp_percent)



habits:

# Update streak and penalties
        if late_habits:
            total_penalty = 0
            penalty = 20 # base * 2 
            
            for habit in late_habits:      
                # update streak status
                db.execute("UPDATE habits SET streak = 0 WHERE user_id = ? AND id = ?", (session["user_id"], habit["id"]))
                total_penalty += penalty
                
            # update users level and xp
            db.execute("SELECT level, current_xp FROM users WHERE id = ?", (session["user_id"],))
            user_data = db.fetchone()
            
            if user_data:
                level = user_data["level"]
                xp = user_data["current_xp"]
                xp -= total_penalty
    
                # if the new xp value is negative, we drop the level
                while xp < 0 and level > 1:
                    level -= 1    
                    
                    # calculate how much xp we needed for this level, and add it to the current xp
                    xp_to_lvl_up = int(BASE * (MULTIPLIER ** (level - 1)))
                    xp += xp_to_lvl_up
                    
                # if there's still negative xp after that, at level 1 just set xp to 0
                if xp < 0:
                    xp = 0

                db.execute("UPDATE users SET level = ?, current_xp = ? WHERE id = ?", (level, xp, session["user_id"]))
                flash(f"You lost your streak at {len(late_habits)}! You lost {total_penalty} XP.", "danger")
            conn.commit()