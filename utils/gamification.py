from database.db import (
    init_db, register_user, validate_user, reset_password,
    add_points, get_user_data, get_leaderboard,
    add_user_badge, get_user_badges
)

# ---- BADGE ASSIGNMENT ----
def assign_badge(points):
    if points >= 220:
        return "🥇 Cuisine Legend"
    elif points >= 190:
        return "🥘 Culinary Hero"
    elif points >= 160:
        return "🍣 Fine Dine Expert"
    elif points >= 130:
        return "🍱 Gourmet Seeker"
    elif points >= 100:
        return "🌮 Taste Adventurer"
    elif points >= 80:
        return "🍛 Flavor Chaser"
    elif points >= 60:
        return "🍜 Local Foodie"
    elif points >= 40:
        return "🍔 Fast-Food Fanatic"
    elif points >= 20:
        return "🍕 Street Explorer"
    else:
        return "🍴 Foodie Beginner"