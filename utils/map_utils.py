import pandas as pd
import pydeck as pdk
import streamlit as st


def build_map(recommendations, selected_restaurant, theme):
    if not recommendations:
        return None

    # Recommendations ALREADY contain coordinates now
    map_df = pd.DataFrame(
    recommendations,
    columns=["Restaurant Name", "Cuisine", "City", "Score", "Latitude", "Longitude", "Address"]
    )

    # Clean names
    map_df["Restaurant Name Clean"] = map_df["Restaurant Name"].str.strip().str.lower()

    # Drop duplicates
    map_df = map_df.drop_duplicates(subset=["Restaurant Name Clean"])

    # Highlight selected restaurant
    selected_clean = selected_restaurant.strip().lower() if selected_restaurant else None
    map_df["is_selected"] = map_df["Restaurant Name Clean"] == selected_clean

    # Colors
    def get_color(row):
        if row["is_selected"]:
            return [255, 255, 0]   # Yellow
        return [255, 50, 50]      # Red

    map_df["color"] = map_df.apply(get_color, axis=1)

    # Center map
    if selected_clean in map_df["Restaurant Name Clean"].values:
        row = map_df[map_df["Restaurant Name Clean"] == selected_clean].iloc[0]
        mean_lat = float(row["Latitude"])
        mean_lon = float(row["Longitude"])
    else:
        mean_lat = map_df["Latitude"].mean()
        mean_lon = map_df["Longitude"].mean()

    tooltip = {
    "html": "<b>{Restaurant Name}</b><br/>Cuisine: {Cuisine}<br/>City: {City}<br/>Similarity: {Score}<br/>Address: {Address}",
    "style": {"backgroundColor": "white", "color": "black"}
    }

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position='[Longitude, Latitude]',
        get_fill_color='color',
        radiusScale=6,
        radiusMinPixels=8,
        radiusMaxPixels=30,
        pickable=True
    )

    view_state = pdk.ViewState(latitude=mean_lat, longitude=mean_lon, zoom=12)

    return pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="light"
    )


def render_map_section():
    st.markdown("---")
    st.subheader("📍 Restaurant Locations on Map")

    chart = build_map(
        st.session_state.get("recommendations", []),
        st.session_state.get("selected_map_restaurant"),
        st.session_state.get("theme", "light")
    )

    if chart:
        st.pydeck_chart(chart)
    else:
        st.info("No restaurants to display on the map.")