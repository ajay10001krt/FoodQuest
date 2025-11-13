from database.db import (
    init_db, register_user, validate_user, reset_password,
    add_points, get_user_data, get_leaderboard,
    add_user_badge, get_user_badges
)

# ---- BADGE ASSIGNMENT (current live badge) ----
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


# ---- AUTOMATIC BADGE AWARD SYSTEM ----
def check_and_award_badge(username):
    """
    Awards a new badge automatically when user's points
    cross a defined threshold.
    """
    user = get_user_data(username)
    if not user:
        return

    points = user[2]  # points column

    # Same thresholds as assign_badge()
    badge_levels = [
        (0, "🍴 Foodie Beginner"),
        (20, "🍕 Street Explorer"),
        (40, "🍔 Fast-Food Fanatic"),
        (60, "🍜 Local Foodie"),
        (80, "🍛 Flavor Chaser"),
        (100, "🌮 Taste Adventurer"),
        (130, "🍱 Gourmet Seeker"),
        (160, "🍣 Fine Dine Expert"),
        (190, "🥘 Culinary Hero"),
        (220, "🥇 Cuisine Legend"),
    ]

    # Get badges already earned (first column in get_user_badges)
    existing_badges = [b[0] for b in get_user_badges(username)]

    # Award missing badges the user qualifies for
    for threshold, badge_name in badge_levels:
        if points >= threshold and badge_name not in existing_badges:
            add_user_badge(username, badge_name, points)