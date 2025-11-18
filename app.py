import streamlit as st
from model.recommender import FoodRecommender
from utils.gamification import (
    init_db, register_user, validate_user, reset_password,
    add_points, get_user_data, assign_badge, get_leaderboard
)
import pandas as pd
from database.db import has_tried, add_user_history, get_user_badges
from utils.map_utils import render_map_section
import base64
from pathlib import Path
import os
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

def render_logo_inline(path="assets/foodquest_logo.png", width=320):
    p = Path(path)
    if not p.exists():
        st.error(f"Logo not found: {path}")
        return
    data = p.read_bytes()
    data_url = "data:image/png;base64," + base64.b64encode(data).decode()
    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; margin-top:10px; margin-bottom:0px;">
            <img src="{data_url}" width="{width}" style="max-width:90%; height:auto; border-radius:8px;" />
        </div>
        """,
        unsafe_allow_html=True
    )

# ---- PAGE CONFIG ----
st.set_page_config(page_title="FoodQuest", layout="wide")
init_db()

@st.cache_resource
def load_recommender():
    return FoodRecommender("data/Dataset.csv")

recommender = load_recommender()

# ---- THEME TOGGLE STATE ----
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# ---- LOGIN / REGISTER / RESET ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
if "tried_restaurants" not in st.session_state:
    st.session_state.tried_restaurants = []
if "tried_set" not in st.session_state:
    st.session_state.tried_set = set()

# ---- PAGE STATE ----
if "page" not in st.session_state:
    st.session_state.page = "Home"


# ---- LOGIN PAGE ----
if not st.session_state.logged_in:
    # Hide sidebar
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="stSidebarNav"] {display: none;}
        [data-testid="stAppViewContainer"] {margin-left: 0 !important;}
        </style>
    """, unsafe_allow_html=True)

    # ---- LOGO (perfectly centered + hi-res) ----
    render_logo_inline("assets/foodquest_logo.png", width=300)

    # Tabs
    tab1, tab2, tab3 = st.tabs(["🔑 Login", "🆕 Register", "🔄 Reset Password"])

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = validate_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")

    with tab2:
        new_user = st.text_input("Choose Username")
        new_pass = st.text_input("Choose Password", type="password")
        if st.button("Register"):
            if register_user(new_user, new_pass):
                st.success("✅ Account created successfully! Please login now.")
            else:
                st.warning("Username already exists! Try another one.")

    with tab3:
        user_reset = st.text_input("Enter Username")
        new_pass_reset = st.text_input("Enter New Password", type="password")
        if st.button("Reset Password"):
            if reset_password(user_reset, new_pass_reset):
                st.success("Password reset successful! Login again.")
            else:
                st.error("Username not found!")

    st.stop()

# ---- SIDEBAR ----
with st.sidebar:
    # ---- THEME TOGGLE ABOVE USERNAME ----
    theme_choice = st.radio("🌓 Theme", ["🌞 Light", "🌙 Dark"],
                            index=0 if st.session_state.theme == "light" else 1,
                            key="theme_toggle")

    if (theme_choice == "🌙 Dark" and st.session_state.theme != "dark"):
        st.session_state.theme = "dark"
        st.rerun()
    elif (theme_choice == "🌞 Light" and st.session_state.theme != "light"):
        st.session_state.theme = "light"
        st.rerun()

    # USER CARD
    username = st.session_state.username
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#ffdde1 0%,#ee9ca7 100%);
                padding:15px;border-radius:20px;
                box-shadow:0 4px 8px rgba(0,0,0,0.15);text-align:center;'>
        <h3>👋 {username}</h3>
    </div>
    """, unsafe_allow_html=True)

# ---- THEME & UI STYLES (re-created from scratch; works for light & dark) ----
# ---- COMPLETE FIXED THEME STYLING (final version) ----
st.markdown(f"""
<style>
/* ================== GLOBAL RESET ================== */
* {{
    box-sizing: border-box !important;
}}
body, [data-testid="stAppViewContainer"] {{
    background: {"linear-gradient(135deg,#1e1e1e 0%,#2a2a2a 100%)" if st.session_state.theme=="dark" else "linear-gradient(135deg,#f8f9fa 0%,#ffe4ec 100%)"} !important;
    color: {"#f8f8f8" if st.session_state.theme=="dark" else "#222"} !important;
    font-family: "Inter", sans-serif !important;
}}

[data-testid="stSidebar"] {{
    background: {"linear-gradient(135deg,#232323 0%,#1b1b1b 100%)" if st.session_state.theme=="dark" else "linear-gradient(135deg,#fff3f6 0%,#ffe4ec 100%)"} !important;
    color: {"#f8f8f8" if st.session_state.theme=="dark" else "#222"} !important;
    border-radius: 10px;
}}

/* ================== TEXT ELEMENTS ================== */
h1,h2,h3,h4,h5,h6,p,span,label,div,li {{
    color: {"#f8f8f8" if st.session_state.theme=="dark" else "#222"} !important;
}}
label {{
    font-weight: 600 !important;
}}

/* ================== INPUTS & SELECTBOX ================== */
input, select, textarea, div[data-baseweb="select"] > div {{
    background-color: {"#2b2b2b" if st.session_state.theme=="dark" else "#fff"} !important;
    color: {"#f8f8f8" if st.session_state.theme=="dark" else "#222"} !important;
    border: 1px solid {"#555" if st.session_state.theme=="dark" else "#ccc"} !important;
    border-radius: 6px !important;
    padding: 10px 12px !important;
    font-size: 15px !important;
    line-height: 1.3 !important;
}}
div[data-baseweb="select"] > div {{
    min-height: 44px !important;
    display: flex;
    align-items: center;
}}

/* Placeholder fix */
input::placeholder, textarea::placeholder {{
    color: {"#aaa" if st.session_state.theme=="dark" else "#888"} !important;
}}

/* Selected text inside select */
div[data-baseweb="select"] span {{
    color: inherit !important;
    line-height: 1.4 !important;
}}

/* ================== DROPDOWN POPOVER ================== */
div[data-baseweb="popover"] {{
    background-color: {"#2b2b2b" if st.session_state.theme=="dark" else "#fff"} !important;
    border: 1px solid {"#555" if st.session_state.theme=="dark" else "#ccc"} !important;
    border-radius: 8px !important;
    box-shadow: 0 6px 18px rgba(0,0,0,0.25) !important;
    overflow: hidden !important;
}}
div[data-baseweb="popover"] [role="option"] {{
    background-color: transparent !important;
    color: {"#f8f8f8" if st.session_state.theme=="dark" else "#222"} !important;
    padding: 10px 14px !important;
    font-size: 15px !important;
    line-height: 1.4 !important;
}}
div[data-baseweb="popover"] [role="option"]:hover {{
    background-color: {"#3b3b3b" if st.session_state.theme=="dark" else "#ffe4ec"} !important;
    color: {"#ffffff" if st.session_state.theme=="dark" else "#000000"} !important;
}}
div[data-baseweb="popover"] [aria-selected="true"] {{
    background-color: {"#444" if st.session_state.theme=="dark" else "#ffd6e4"} !important;
    color: {"#fff" if st.session_state.theme=="dark" else "#000"} !important;
}}

/* Scrollbar styling */
div[data-baseweb="popover"]::-webkit-scrollbar {{
    width: 8px;
}}
div[data-baseweb="popover"]::-webkit-scrollbar-thumb {{
    background-color: {"#555" if st.session_state.theme=="dark" else "#bbb"} !important;
    border-radius: 10px;
}}
div[data-baseweb="popover"]::-webkit-scrollbar-thumb:hover {{
    background-color: {"#777" if st.session_state.theme=="dark" else "#999"} !important;
}}

/* ================== BUTTONS ================== */
div.stButton > button:first-child {{
    background-color:#ff4b4b !important;
    color:white !important;
    font-weight:600 !important;
    border-radius:10px !important;
    box-shadow:0 0 12px rgba(255,75,75,0.4) !important;
    padding:8px 16px !important;
    transition:all 0.2s ease !important;
}}
div.stButton > button:first-child:hover {{
    background-color:#ff1e1e !important;
    transform:scale(1.05);
}}

/* ================== RADIO / SIDEBAR ================== */
[data-testid="stSidebar"] [role="radiogroup"] > label:hover {{
    background: rgba(255,75,75,0.1) !important;
    border-radius: 8px;
}}
[data-testid="stSidebar"] [aria-checked="true"] {{
    background: linear-gradient(90deg,#ff4b4b,#ff9999) !important;
    color:white !important;
    font-weight:600 !important;
    border-radius:8px !important;
    box-shadow:0 0 10px rgba(255,75,75,0.5) !important;
}}

/* ================== FIXED ALIGNMENTS ================== */
div[data-baseweb="select"] input {{
    margin: 0 !important;
    padding: 6px 10px !important;
}}
div[data-baseweb="select"] div[role="combobox"] {{
    align-items: center !important;
    display: flex !important;
}}
</style>
""", unsafe_allow_html=True)

# ---- FORCE DROPDOWN POPOVER DARK IN DARK MODE (paste after main styles) ----
if st.session_state.theme == "dark":
    st.markdown("""
    <style>
    /* Make the entire popover (list) dark and readable */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] ul,
    div[data-baseweb="popover"] [role="listbox"] {
        background-color: #222428 !important;   /* dark blackish background */
        color: #f5f5f5 !important;               /* bright text */
        border: 1px solid #3a3a3a !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.6) !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }

    /* Ensure each option is full-opacity and visible */
    div[data-baseweb="popover"] [role="option"] {
        background-color: transparent !important;
        color: #f5f5f5 !important;
        opacity: 1 !important;                   /* make non-hovered items visible */
        font-weight: 500 !important;
        padding: 10px 14px !important;
        line-height: 1.45 !important;
    }

    /* Hover / selected highlight */
    div[data-baseweb="popover"] [role="option"]:hover,
    div[data-baseweb="popover"] [aria-selected="true"] {
        background-color: #3b3b3b !important;
        color: #ffffff !important;
    }

    /* Make the select control itself match dark theme */
    div[data-baseweb="select"] > div,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] input {
        background-color: #252525 !important;
        color: #f5f5f5 !important;
        border: 1px solid #3a3a3a !important;
    }

    /* Keep scrollbar visible on dark background */
    div[data-baseweb="popover"]::-webkit-scrollbar {
        width: 8px;
    }
    div[data-baseweb="popover"]::-webkit-scrollbar-thumb {
        background: #4a4a4a !important;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    # Optional: for light theme ensure popover remains light (no change needed usually)
    st.markdown("""
    <style>
    div[data-baseweb="popover"], div[data-baseweb="popover"] ul, div[data-baseweb="popover"] [role="listbox"] {
        background-color: #ffffff !important;
        color: #111 !important;
        border: 1px solid #ddd !important;
    }
    div[data-baseweb="popover"] [role="option"] {
        color: #111 !important;
        opacity: 1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ---- SIDEBAR ACTIVE PAGE & HOVER EFFECT ----
st.markdown("""
<style>
/* Smooth hover for sidebar items */
[data-testid="stSidebar"] [role="radiogroup"] > label:hover {
    background: rgba(255, 75, 75, 0.1) !important;
    border-radius: 8px;
    transition: all 0.2s ease-in-out;
    transform: scale(1.02);
}

/* Active page glow */
[data-testid="stSidebar"] [aria-checked="true"] {
    background: linear-gradient(90deg, #ff4b4b, #ff9999) !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 0 10px rgba(255, 75, 75, 0.6);
    border-radius: 8px;
    transform: scale(1.05);
    transition: all 0.2s ease;
}

/* Ensure radio label text stays readable */
[data-testid="stSidebar"] [role="radiogroup"] > label p {
    color: inherit !important;
}
</style>
""", unsafe_allow_html=True)


# ---- NAVIGATION ----
# ---- NAVIGATION (Optimized to remove double-click lag) ----
if "selected_page" not in st.session_state:
    st.session_state.selected_page = "Home"

def set_page(page):
    st.session_state.selected_page = page
    st.session_state.page = page

page = st.sidebar.radio(
    "Navigate",
    ["Home", "Recommend by Restaurant", "Recommend by Preferences", "Leaderboard", "Profile", "Dataset"],
    index=["Home", "Recommend by Restaurant", "Recommend by Preferences", "Leaderboard", "Profile", "Dataset"]
          .index(st.session_state.selected_page),
    key="page_radio",
    on_change=lambda: set_page(st.session_state.page_radio),
)

st.sidebar.write("---")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

page = st.session_state.selected_page

# ---- 🏠 HOME PAGE ----
if page == "Home":
    render_logo_inline(width=180)
    st.title("🍴 Welcome to FoodQuest!")
    st.markdown("""
    ### 🌍 Embark on your culinary adventure!
    **FoodQuest** helps you discover amazing restaurants, earn foodie badges, and climb the leaderboard as you explore cuisines across India.  
    Whether you're searching for a **local gem** or a **hidden flavor**, we've got you covered. 😋  
    """)

    st.markdown("#### ✨ What You Can Do Here:")
    st.markdown("""
    - 🍽️ **Get personalized restaurant recommendations** based on your favorites  
    - 🎯 **Recommendation based on preferences** like cuisine or location  
    - 🏅 **Earn points and unlock badges** every time you explore  
    - 🌐 **Visualize restaurants on an interactive map**  
    - 🧭 **Track your foodie journey** with your profile and leaderboard rank
    """)

    st.markdown("---")
    st.markdown("#### 🚀 Quick Start Guide:")
    st.markdown("""
    1. Go to **Recommend by Restaurant** or **Recommend by Preferences** from the sidebar  
    2. Choose a city and search your favorite restaurant or cuisine  
    3. Click **Try 🍽️** to earn points and level up your badge!  
    """)

    st.markdown("---")
    st.markdown("""
    #### ❤️ Powered by Data, Driven by Taste  
    *FoodQuest combines data science, intelligent recommendations, and community spirit to make dining fun and rewarding.*  
    """)

    st.info("Tip: Dark Mode looks delicious too 😎 — try switching it from the sidebar!")

if "selected_map_restaurant" not in st.session_state:
    st.session_state.selected_map_restaurant = None

# ---- RECOMMEND BY RESTAURANT ----
elif page == "Recommend by Restaurant":
    st.title("🤖 Recommend by Restaurant")

    try:
        df = pd.read_csv("data/Dataset.csv").fillna("")
    except FileNotFoundError:
        st.error("Dataset not found in 'data/Dataset.csv'")
        st.stop()

    city = st.selectbox("Select City:", sorted(df["City"].dropna().unique().tolist()))
    name = st.text_input("Enter restaurant name:")

    if st.button("Recommend"):
        if not name.strip():
            st.warning("Please enter a restaurant name first.")
        else:
            res = recommender.recommend(name, city)
            if res:
                st.session_state.recommendations = [
                    r for r in res if r[2].lower().strip() == city.lower().strip()
                ]
                if st.session_state.recommendations:
                    st.success(f"Showing similar restaurants to **{name.title()}** in **{city.title()}** 🍽️")
                else:
                    st.warning(f"No similar restaurants found for '{name.title()}' in {city.title()}.")
            else:
                st.warning("No matching restaurant found in dataset!")

    if st.session_state.recommendations:
        st.markdown("### 🍴 Recommended Restaurants:")
        for idx, (rname, cuisine, cty, score, lat, lon, addr) in enumerate(st.session_state.recommendations):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{rname}** — _{cuisine}_ ({cty}) | 🔹 {score}")
                if addr:
                    st.caption(f"📍 {addr}")
            with col2:
                show_key = f"showmap_{idx}_{rname}"
                try_key = f"try_{idx}_{rname}"

                if st.button("Show on Map 🗺️", key=show_key):
                    st.session_state.selected_map_restaurant = rname

                if st.button("Try 🍽️", key=try_key):
                    # precise Zomato/Google search using name + address + city
                    from urllib.parse import quote_plus
                    query = quote_plus(f"{rname} {addr} {cty} zomato")
                    zomato_link = f"https://www.google.com/search?q={query}&btnI=1"

                    if not has_tried(username, rname):
                        add_points(username, 5)
                        add_user_history(username, rname)
                        st.success(f"You tried {rname}! +5 points 🎉")
                        
                    else:
                        st.info(f"You already tried {rname} before 🍽️")
                    st.markdown(
                            f"<a href='{zomato_link}' target='_blank' style='font-size:16px;'>🔗 View on Zomato (precise)</a>",
                            unsafe_allow_html=True
                    )


        # ---- 📍 Map Visualization (All restaurants together) ----
        render_map_section()

# ---- RECOMMEND BY PREFERENCES ----
elif page == "Recommend by Preferences":
    st.title("🎯 Recommend by Preferences")

    cuisine = st.text_input("Cuisine:")
    city = st.text_input("City:")
    price = st.selectbox("💰 Price Range", [1, 2, 3, 4])
    rating = st.slider("⭐ Min Rating", 0.0, 5.0, 3.5, 0.1)

    if st.button("Find Restaurants"):
        results = recommender.recommend_by_preferences(cuisine, city, price, rating)
        st.session_state.recommendations = results

        if not results:
            st.warning("No results found.")

    # ---- SHOW RESULTS ----
    if st.session_state.recommendations:
        for i, (n, c, ci, sc, lat, lon, addr) in enumerate(st.session_state.recommendations[:10]):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{n}** — _{c}_ ({ci}) | ⭐ {sc}")
                if addr:
                    st.caption(f"📍 {addr}")
            with col2:
                show_key = f"pref_showmap_{i}_{n}"
                try_key = f"pref_try_{i}_{n}"

                if st.button("Show on Map 🗺️", key=show_key):
                    st.session_state.selected_map_restaurant = n

                if st.button("Try 🍽️", key=try_key):
                    from urllib.parse import quote_plus
                    query = quote_plus(f"{n} {addr} {ci} zomato")
                    zomato_link = f"https://www.google.com/search?q={query}&btnI=1"

                    if not has_tried(username, n):
                        add_points(username, 5)
                        add_user_history(username, n)
                        st.success(f"You tried {n}! +5 points 🎉")
                        
                    else:
                        st.info(f"You already tried {n} before 🍽️")
                    st.markdown(
                            f"<a href='{zomato_link}' target='_blank' style='font-size:16px;'>🔗 View on Zomato (precise)</a>",
                            unsafe_allow_html=True
                    )

        render_map_section()

# ---- LEADERBOARD ----
elif page == "Leaderboard":
    st.title("🏆 FoodQuest Leaderboard")
    st.markdown("See who's climbing the culinary ranks 🍴🔥")

    data = get_leaderboard()

    if data:
        leaderboard_df = pd.DataFrame(data, columns=["Username", "Points"])

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


        leaderboard_df["Badge"] = leaderboard_df["Points"].apply(assign_badge)
        leaderboard_df = leaderboard_df.sort_values(by="Points", ascending=False).reset_index(drop=True)

        # Theme adaptive leaderboard styling
        is_dark = st.session_state.theme == "dark"
        leaderboard_bg = (
            "linear-gradient(135deg, #2c2c2c, #3a3a3a)" if is_dark else "linear-gradient(135deg, #fff3f6, #ffe4ec)"
        )
        row_bg_self = (
            "background: linear-gradient(90deg, #3a3a3a, #2a2a2a);" if is_dark else "background: linear-gradient(90deg, #fff0f5, #ffe0e9);"
        )
        text_color = "#f8f8f8" if is_dark else "#1a1a1a"

        st.markdown(f"""
        <style>
        .leaderboard-container {{
            background: {leaderboard_bg};
            padding: 15px;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
            color: {text_color};
        }}
        .leaderboard-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 20px;
            border-radius: 12px;
            margin: 6px 0;
            transition: all 0.3s ease;
        }}
        .leaderboard-row:hover {{
            transform: scale(1.02);
            box-shadow: 0 0 12px rgba(255,75,75,0.3);
        }}
        .rank {{
            font-weight: bold;
            font-size: 1.1em;
            width: 35px;
        }}
        .username {{
            flex-grow: 1;
            font-weight: 600;
        }}
        .points {{
            font-weight: 600;
        }}
        .badge {{
            margin-right: 8px;
        }}
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="leaderboard-container">', unsafe_allow_html=True)

        for idx, row in leaderboard_df.iterrows():
            rank_emoji = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else f"{idx+1}."
            row_color = row_bg_self if row["Username"] == username else ""
            st.markdown(
                f"""
                <div class="leaderboard-row" style="{row_color}">
                    <span class="rank">{rank_emoji}</span>
                    <span class="username">{row['Username']}</span>
                    <span class="badge">{row['Badge']}</span>
                    <span class="points">⭐ {row['Points']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No users have earned points yet. Be the first to dine and shine 🌟!")

# ---- PROFILE ----
elif page == "Profile":
    st.title("👤 Your Profile")
    user_data = get_user_data(username)
    if user_data:
        points = user_data[2]
        badge = assign_badge(points)
        tiers = [
            ("🍴 Foodie Beginner", 0),
            ("🍕 Street Explorer", 20),
            ("🍔 Fast-Food Fanatic", 40),
            ("🍜 Local Foodie", 60),
            ("🍛 Flavor Chaser", 80),
            ("🌮 Taste Adventurer", 100),
            ("🍱 Gourmet Seeker", 130),
            ("🍣 Fine Dine Expert", 160),
            ("🥘 Culinary Hero", 190),
            ("🥇 Cuisine Legend", 220)
        ]

        for i, (name, req) in enumerate(tiers):
            if points < req:
                next_badge = name
                prev_req = tiers[i - 1][1] if i > 0 else 0
                next_req = req
                break
        else:
            next_badge, prev_req, next_req = "🏆 Maxed Out!", 200, 200
        progress = max(0, min((points - prev_req) / (next_req - prev_req) if next_req > prev_req else 1, 1))
        st.subheader(f"Username: {user_data[0]}")
        st.write(f"💰 Points: **{points}**")
        st.write(f"🏅 Current Badge: **{badge}**")
        st.markdown("---")
        st.subheader("🎯 Progress Toward Next Badge")
        st.markdown(f"""
        <div style="background:#ddd;border-radius:10px;height:20px;">
            <div style="width:{progress*100}%;
                height:100%;border-radius:10px;
                background:linear-gradient(90deg,#ff4b4b,#ff9b9b);
                transition:width 0.5s;"></div></div>
        <p>Next Badge: <b>{next_badge}</b> — {round(progress*100,1)}% complete</p>
        """, unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("🎖️ Badge History")
        badges = get_user_badges(username)
        if badges:
            for badge_name, date, score in badges:
                st.markdown(f"- {badge_name} — earned on **{date[:10]}**, score at that time: {score}")
        else:
            st.info("No badges earned yet. Start exploring to collect them! 🏅")
    else:
        st.warning("Profile not found!")

# ---- DATASET ----
elif page == "Dataset":
    st.title("📊 Restaurant Dataset Explorer")
    try:
        df = pd.read_csv("data/Dataset.csv").fillna("N/A")
    except FileNotFoundError:
        st.error("Dataset not found in 'data/Dataset.csv'")
        st.stop()

    st.markdown("### 🎛️ Choose a filter type to explore:")
    filter_type = st.radio("Select a filter type:", ["By Restaurant Name", "By City", "By Cuisine"], horizontal=True)

    with st.expander("🔍 Filter Dataset", expanded=True):
        col1, col2, col3 = st.columns(3)
        name_filter = city_filter = cuisine_filter = ""
        with col1:
            if filter_type == "By Restaurant Name":
                name_filter = st.text_input("Restaurant Name:")
            else:
                st.text_input("Restaurant Name:", disabled=True, placeholder="Disabled")
        with col2:
            if filter_type == "By City":
                city_filter = st.text_input("City:")
            else:
                st.text_input("City:", disabled=True, placeholder="Disabled")
        with col3:
            if filter_type == "By Cuisine":
                cuisine_filter = st.text_input("Cuisine:")
            else:
                st.text_input("Cuisine:", disabled=True, placeholder="Disabled")

    # Filter the data safely
    try:
        filtered_df = df[
            (df["Restaurant Name"].str.contains(name_filter, case=False, na=False) if name_filter else True)
            & (df["City"].str.contains(city_filter, case=False, na=False) if city_filter else True)
            & (df["Cuisines"].str.contains(cuisine_filter, case=False, na=False) if cuisine_filter else True)
        ]
    except Exception:
        filtered_df = df

    if not name_filter and not city_filter and not cuisine_filter:
        st.info("Enter a value in the selected filter above to explore the dataset 🔍")
        st.stop()

    if filtered_df.empty:
        st.warning("No results found for your filter.")
    else:
        st.dataframe(
            filtered_df[["Restaurant Name", "City", "Address", "Cuisines", "Aggregate rating", "Votes"]].head(100),
            use_container_width=True, height=400
        )
        st.markdown("---")
        with st.expander("🗺️ View Restaurant Locations on Map", expanded=False):
            try:
                import pydeck as pdk

                # ✅ Use only coordinates from the filtered_df (no re-tallying)
                map_df = filtered_df.copy()
                map_df["Latitude"] = pd.to_numeric(map_df["Latitude"], errors="coerce")
                map_df["Longitude"] = pd.to_numeric(map_df["Longitude"], errors="coerce")
                map_df = map_df.dropna(subset=["Latitude", "Longitude"])
                map_df = map_df.drop_duplicates(subset=["Restaurant Name", "City"])

                if not map_df.empty:
                    # Theme-based color scheme
                    point_color = [255, 100, 100] if st.session_state.theme == "dark" else [255, 50, 50]

                    # Create scatter layer (same config as recommendation pages)
                    layer = pdk.Layer(
                        "ScatterplotLayer",
                        data=map_df,
                        get_position='[Longitude, Latitude]',
                        get_fill_color=point_color,
                        get_radius=80,
                        radius_scale=10,
                        radius_min_pixels=4,
                        radius_max_pixels=12,
                        stroked=True,
                        filled=True,
                        line_width_min_pixels=1,
                        get_line_color=[0, 0, 0, 100],
                        opacity=0.45,
                        pickable=True
                    )

                    # Center the map based on this filtered data only
                    mean_lat = map_df["Latitude"].mean()
                    mean_lon = map_df["Longitude"].mean()
                    view_state = pdk.ViewState(latitude=mean_lat, longitude=mean_lon, zoom=10, pitch=0)

                    # Tooltip (same hover info as others)
                    tooltip = {
                        "html": "<b>🍽️ {Restaurant Name}</b><br/>{Cuisines}<br/>⭐ {Aggregate rating}<br/>🏙️ {City}",
                        "style": {
                            "backgroundColor": "rgba(30,30,30,0.85)" if st.session_state.theme == "dark" else "rgba(255,255,255,0.9)",
                            "color": "#fff" if st.session_state.theme == "dark" else "#000",
                            "borderRadius": "6px",
                            "padding": "6px"
                        }
                    }

                    st.pydeck_chart(
                        pdk.Deck(
                            layers=[layer],
                            initial_view_state=view_state,
                            tooltip=tooltip,
                            map_style=None
                        )
                    )
                else:
                    st.info("No valid location data found for these restaurants.")
            except Exception as e:
                st.warning(f"Could not load map data: {e}")