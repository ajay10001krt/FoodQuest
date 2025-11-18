import sqlite3, os, datetime

BASE_DIR = os.path.dirname(__file__)    # directory where app.py exist
db_path = os.path.join(BASE_DIR, "database", "foodquest.db")

def get_connection():
    os.makedirs("database", exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # ---- USERS TABLE ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            points INTEGER DEFAULT 0,
            join_date TEXT DEFAULT '',
            tried_count INTEGER DEFAULT 0
        )
    """)

    # ---- RESTAURANT HISTORY ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_restaurant_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            restaurant_name TEXT,
            tried_on TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)

    # ---- BADGES TABLE ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            badge_name TEXT,
            score_at_time INTEGER,
            earned_on TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)

    conn.commit()
    conn.close()

# ---------- USER MANAGEMENT ----------
def register_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE username=?", (username,))
    if cur.fetchone():
        conn.close()
        return False

    join_date = datetime.date.today().strftime("%d-%b-%Y")
    cur.execute(
        "INSERT INTO users (username, password, join_date, points, tried_count) VALUES (?, ?, ?, 0, 0)",
        (username, password, join_date)
    )

    # ✅ Give default badge "Foodie Beginner" at registration
    cur.execute(
        "INSERT INTO user_badges (username, badge_name, score_at_time) VALUES (?, ?, ?)",
        (username, "🍴 Foodie Beginner", 0)
    )

    conn.commit()
    conn.close()
    return True


def validate_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cur.fetchone()
    conn.close()
    return user

def reset_password(username, new_password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE username=?", (username,))
    if not cur.fetchone():
        conn.close()
        return False
    cur.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))
    conn.commit()
    conn.close()
    return True

# ---------- POINTS & USER DATA ----------
def add_points(username, points):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT points, tried_count FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    if row:
        new_points = row[0] + points
        new_tried = row[1] + 1
        cur.execute("UPDATE users SET points=?, tried_count=? WHERE username=?", (new_points, new_tried, username))
    conn.commit()
    conn.close()

    # ---- After updating points, check for badge upgrade ----
    try:
        from utils.gamification import check_and_award_badge
        check_and_award_badge(username)
    except Exception as e:
        print("Badge awarding failed:", e)

def get_user_data(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cur.fetchone()
    conn.close()
    return user

def get_leaderboard():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 10")
    data = cur.fetchall()
    conn.close()
    return data

# ---------- RESTAURANT HISTORY ----------
def add_user_history(username, restaurant_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO user_restaurant_history (username, restaurant_name) VALUES (?, ?)", (username, restaurant_name))
    conn.commit()
    conn.close()

def has_tried(username, restaurant_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM user_restaurant_history WHERE username=? AND restaurant_name=?", (username, restaurant_name))
    result = cur.fetchone()
    conn.close()
    return result is not None

# ---------- BADGES ----------
def add_user_badge(username, badge_name, score):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO user_badges (username, badge_name, score_at_time) VALUES (?, ?, ?)", (username, badge_name, score))
    conn.commit()
    conn.close()

def get_user_badges(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT badge_name, earned_on, score_at_time FROM user_badges WHERE username=? ORDER BY earned_on DESC", (username,))
    badges = cur.fetchall()
    conn.close()

    return badges
