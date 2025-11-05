import sqlite3, os, datetime

# ---- INITIALIZE DATABASE ----
def init_db():
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect("database/foodquest.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            points INTEGER DEFAULT 0,
            level TEXT DEFAULT 'Foodie Beginner',
            badges TEXT DEFAULT '',
            join_date TEXT DEFAULT '',
            tried_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# ---- USER MANAGEMENT ----
def register_user(username, password):
    conn = sqlite3.connect("database/foodquest.db")
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE username=?", (username,))
    if cur.fetchone():
        conn.close()
        return False
    join_date = datetime.date.today().strftime("%d-%b-%Y")
    cur.execute("INSERT INTO users (username, password, join_date) VALUES (?, ?, ?)", (username, password, join_date))
    conn.commit()
    conn.close()
    return True

def validate_user(username, password):
    conn = sqlite3.connect("database/foodquest.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cur.fetchone()
    conn.close()
    return user

def reset_password(username, new_password):
    conn = sqlite3.connect("database/foodquest.db")
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE username=?", (username,))
    if not cur.fetchone():
        conn.close()
        return False
    cur.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))
    conn.commit()
    conn.close()
    return True

# ---- POINTS SYSTEM ----
def add_points(username, points):
    conn = sqlite3.connect("database/foodquest.db")
    cur = conn.cursor()
    cur.execute("SELECT points, tried_count FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    if row:
        new_points = row[0] + points
        new_tried = row[1] + 1
        cur.execute("UPDATE users SET points=?, tried_count=? WHERE username=?", (new_points, new_tried, username))
    conn.commit()
    conn.close()

# ---- USER DATA ----
def get_user_data(username):
    conn = sqlite3.connect("database/foodquest.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cur.fetchone()
    conn.close()
    return user

def assign_badge(points):
    if points >= 200:
        return "Cuisine Master"
    elif points >= 100:
        return "Spice Explorer"
    elif points >= 50:
        return "Local Foodie"
    else:
        return "Foodie Beginner"

def get_leaderboard():
    conn = sqlite3.connect("database/foodquest.db")
    cur = conn.cursor()
    cur.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 10")
    data = cur.fetchall()
    conn.close()
    return data
