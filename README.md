# LevelUp - Gamified Life Tracking App
## Version v1.0

> Change your everyday boring tasks into quests just like in RPG games. This app lets you track your tasks and earn EXP for completing them. Earn EXP to Level Up your account and track your life improvement!

## About Project

LevelUp is my first Full-Stack project built with Flask from scratch. I decided to begin this project to gather all my Real Life tracking needs into one gamified platform. Jumping between different apps, where not every app is available on different devices, was frustrating. So, instead of a boring check-list, users can earn experience and level up their "character" by working. This visualizes the progress and consistency of your daily efforts!

This product is currently a Minimum Viable Product (MVP). The main purpose was to learn Full-Stack development, database management, and web security.

## Features

* **Secure Authentication:** User registration, login, and session management (Flask-Session). Routes are protected against unauthorized access. Passwords are securely hashed using the Werkzeug library.
* **Quest Management (CRUD):** Add, view, and complete tasks. Each quest has a specific difficulty level (EASY, MEDIUM, HARD, BOSS) which determines the reward.
* **RPG Engine (Leveling System):** Custom algorithm calculating Experience Points (EXP) required for character progression, based on a logarithmic scale (each level requires exponentially more EXP).
* **Commander's Dashboard:** Main hub displaying the user's current level, gathered EXP, and a real-time animated Progress Bar built with Bootstrap.
* **Dynamic Frontend:** User interface built with Bootstrap 5 and Jinja2, featuring a Dark Mode aesthetic and dynamic element coloring based on task status and difficulty.

## Tech Stack

* **Backend:** Python 3, Flask
* **Database:** SQLite3 (SQL)
* **Frontend:** HTML5, CSS3, Bootstrap 5, Jinja2
* **Architecture:** MVC Pattern (Model-View-Controller), Pure Functions

## Local Setup

If you want to run this project on your local machine, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/akamanyara/LevelUp.git
   ```

2. Navigate to the project directory:
   ```bash
   cd LevelUp
   ```

3. Install required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Create your database:
    ```bash
    sqlite3 tracker.db < schema.sql
    ```
    
5. Run the development server:
    ```bash
    flask run
    ```

## Roadmap

The app is continuously being improved. Upcoming features include:

* [x] Adding Deadlines to Quests.
* [x] Adding Habit Tracker.
* [ ] "Quick Notes" module for sudden ideas.
* [ ] Specialized tracking modules (Budget Tracker, Fit Tracker (Gym split and Diet shopping list))

---

Created for learning purposes and skill development after completing the CS50 course.
