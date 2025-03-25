import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import folium
from folium.plugins import MarkerCluster
from constants import us_states, us_states_coords
import json
from tsm_fn import get_election_data, get_politifact_data, get_selected_stance, get_politifact_categories
from streamlit_folium import st_folium

print('#######')
####### START: Header
st.set_page_config(
    layout="wide",
    page_icon="https://idir.uta.edu/stance_annotation/image/wildfire_wout_text.png",
    page_title="Truthfulness Stance Map",
)
st.markdown("<h1 style='text-align: center;'>Truthfulness Stance Map</h1>", unsafe_allow_html=True)
st.logo("https://idir.uta.edu/stance_annotation/image/wildfire_wout_text.png")
####### END: Header

####### START: Sidebar
stance_df = get_election_data()
politifact_df = get_politifact_data()
politifact_categories = get_politifact_categories()

categories = ["Election"] + politifact_categories
if "selected_category" in st.session_state:
    sidebar_selected_category = st.sidebar.multiselect(
        "Select categories/peoples/issues",
        categories,
        default=st.session_state.selected_category,
    )
    if sidebar_selected_category != st.session_state.selected_category:
        st.session_state.selected_category = sidebar_selected_category
else:
    sidebar_selected_category = st.sidebar.multiselect(
        "Select categories/peoples/issues",
        categories,
        default=["Election"],
    )
    st.session_state.selected_category = sidebar_selected_category


selected_category_str = ", ".join(st.session_state.selected_category)

election_factual_claims = [
    "Immigrants are helping Democrats steal the election",
    "Jews, Zionists and Israel control the election results",
    "Kamala Harris lied about her identity, credibility and eligibility to run for president",
    "The Trump assassination attempts were staged",
    "The government is weaponizing or creating hurricanes to interfere with the election",
    "Electronic voting machines are programmed to change votes ",
    "Michigan has more registered voters than citizens",
    "JD Vance admitted to an inappropriate sex act involving a couch in his memoir.",
    "The crowd at Kamala Harris’s rally was artificially inflated using AI technology.",
    "Taylor Swift and her fanbase endorse or are partial to Donald Trump for the 2024 Presidential Election.",
    "Kamala Harris and Tim Walz adopted the Nazi slogan “Strength through Joy” for their 2024 campaign.",
    "Kamala Harris was involved in a hit-and-run car accident in 2011.",
    "Kamala Harris wore an earpiece during the debate to receive answers.",
]
if "Election" in st.session_state.selected_category:
    selected_factual_claim = st.sidebar.multiselect(
        "A factual claim of interest to you",
        election_factual_claims,
        # default=["All"],
        # index=None,
        placeholder="Select factual claims",
    )
else:
    selected_factual_claim = st.sidebar.multiselect(
        "A factual claim of interest to you",
        politifact_df["Claim"].unique().tolist(),
        # default=["All"],
        # index=None,
        placeholder="Select a factual claim",
    )
# TODO:

if selected_factual_claim == []:
    # ask user to select a factual claim
    st.error("Please select a factual claim")
    st.stop()
else:
    stance_df = stance_df[stance_df["Claim"].isin(selected_factual_claim)]
        

# Customize the sidebar
markdown = """
Detecting the truthfulness stance of social media posts toward factual claims.
[Github](<https://github.com/opengeos/streamlit-map-template>)
"""
if 'selected_state' in st.session_state:
    print(f'has selected_state: {st.session_state.selected_state}')
    sidebar_selected_state = st.sidebar.selectbox("Select a state", us_states, index=us_states.index(st.session_state.selected_state))
    if sidebar_selected_state != st.session_state.selected_state:
        st.session_state.selected_state = sidebar_selected_state
else:
    print(f'no selected_state')
    sidebar_selected_state = st.sidebar.selectbox("Select a state", us_states)
    st.session_state.selected_state = sidebar_selected_state

    

# selected_score_range = st.sidebar.slider(f'Truthfulness Stance Score Range', min_value=0.0, max_value=1.0, value=(0.0, 1.0), step=0.01)
start_stance, end_stance = st.sidebar.select_slider(
    f"Truthfulness Stance Range",
    options=["Negative", "Neutral/No Stance", "Positive"],
    value=("Negative", "Positive"),
)
selected_stance = get_selected_stance(start_stance, end_stance)
selected_stance_str = ", ".join(selected_stance)

st.sidebar.info(markdown)
####### END: Sidebar

####### START: Main
# show selected options
st.write(f"Categories/People/Issues: **_{selected_category_str}_**")
if len(selected_factual_claim) == 1:
    selected_factual_claim_str = selected_factual_claim[0]
    st.write(f"Factual claim: **_{selected_factual_claim_str}_**")
else:
    selected_factual_claim_str = "; ".join(selected_factual_claim)
    st.write(f"Factual claims: **_{selected_factual_claim_str}_**")
st.write(f"State: **_{st.session_state.selected_state}_**")
st.write(f"Stance: **_{selected_stance_str}_**")


def create_map_folium(stance_df):
    # Center map
    # if st.session_state.selected_state != "All":
    #     print(f'Render map for {st.session_state.selected_state}')
    #     center_lat = us_states_coords[st.session_state.selected_state][0]
    #     center_lon = us_states_coords[st.session_state.selected_state][1]
    #     m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
    #     print(f'Finished rendering map for {st.session_state.selected_state}')
    # else:
    print(f'Render map for all states')
    # center_lat, center_lon = 40, -75
    center_lat, center_lon = 40, -100
    m = folium.Map(location=[center_lat, center_lon], zoom_start=4)
    print(f'Finished rendering map for all states')


    # Add state layer (GeoJSON)
    states_url = "https://raw.githubusercontent.com/giswqs/leafmap/master/examples/data/us_states.json"
    folium.GeoJson(
        states_url, 
        name="US States",
        zoom_on_click=True,
        highlight_function=lambda feature: {
        "fillColor": (
                "green" if "e" in feature["properties"]["name"].lower() else "#ffff00"
            ),
        },
        ).add_to(m)

    marker_cluster = MarkerCluster(
    ).add_to(m)
    # only first 10 rows
    # stance_df_on_map = stance_df.head(100)
    stance_df_on_map = stance_df
    # data = {
    #     "Tweet": ["Tweet A", "Tweet B", "Tweet C"],
    #     "City": ["Austin", "Dallas", "Houston"],
    #     "Stance": ["Positive", "Neutral", "Negative"],
    #     "Latitude": [30.2672, 32.7767, 29.7604],
    #     "Longitude": [-97.7431, -96.7970, -95.3698],
    # }
    # stance_df = pd.DataFrame(data)
    # print(stance_df.head())
    color_mp = {
        "Positive": "green",
        "Neutral": "orange",
        "Negative": "red"
    }
    print(f'len(stance_df_on_map): {len(stance_df_on_map)}')
    for idx, row in stance_df_on_map.iterrows():
        lat = row["Latitude"]
        lon = row["Longitude"]
        stance = row["Stance"]
        color = color_mp.get(stance, "gray")

        popup = f"<b>Tweet</b>: {row['Tweet']}<br><b>City:</b> {row['City']}<br><b>Stance:</b> {stance}"
        icons = {
            "Positive": "plus-circle",
            "Neutral": "dot-circle",
            "Negative": "minus-circle"
        }
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup, max_width=300),
            icon=folium.Icon(
            icon=icons.get(stance),
            prefix="fa",
            color=color
            )
        ).add_to(marker_cluster)

    return m

# m = create_map(stance_df)
# m.to_streamlit(height=500

print(f'len(stance_df): {len(stance_df)}')
m = create_map_folium(stance_df)
print(f'map created, {m}')
map_data = st_folium(m, height=500, width=1200)
print(f'map_data: {map_data}')
if map_data["last_active_drawing"] and (map_data["last_object_clicked_popup"]==None or map_data["last_object_clicked_popup"]!=st.session_state.clicked_popup):
    clicked_state = map_data["last_active_drawing"]['properties'].get('name')
    st.session_state.clicked_popup = map_data["last_object_clicked_popup"]
    if 'clicked_state' not in st.session_state:
        st.session_state.clicked_state = clicked_state
        st.session_state.selected_state = clicked_state
        st.rerun()
    elif clicked_state != st.session_state.clicked_state:
        if st.session_state.clicked_state!=None:
            st.session_state.clicked_state = clicked_state
            st.session_state.selected_state = clicked_state
            st.rerun()
    
        


tab1, tab2 = st.tabs(
    ["Stance distribution", "Stance timeline"]
)
with tab1:
    c1, _, c2 = st.columns((3.9, 0.2, 5.9))
    with c1:
        negative_count = stance_df[stance_df["Stance"] == "Negative"].shape[0]
        neutral_count = stance_df[stance_df["Stance"] == "Neutral"].shape[0]
        positive_count = stance_df[stance_df["Stance"] == "Positive"].shape[0]
        chart_data = pd.DataFrame(
            {
                "Stance": ["Negative", "Neutral", "Positive"],
                "Count": [negative_count, neutral_count, positive_count],
                # red  # orange  # green
                "col3": ["#C82820", "#FFA500", "#61A41D"],
            }
        )
        # set the bar chart title as "claim distribution"
        if st.session_state.selected_state == "All":
            st.write("United States level")
        else:
            st.write(f"{st.session_state.selected_state}'s city level")
        # a bar chart with the count of each stance
        c = (
            alt.Chart(chart_data)
            .mark_bar()
            .encode(
                x="Stance",
                y="Count",
                color=alt.Color(
                    "Stance",
                    scale=alt.Scale(
                        domain=chart_data["Stance"].tolist(),
                        range=chart_data["col3"].tolist(),
                    ),
                ),
                tooltip=["Stance", "Count"]
                # don't show ledgend
            )
            .properties(width=200, height=300)
            .configure_axis(labelFontSize=12, titleFontSize=12)
        )
        st.altair_chart(c, use_container_width=True)

    with c2:
        # set the bar chart title as "claim distribution"
        if st.session_state.selected_state == "All":
            st.write("United States level")
        else:
            st.write(f"{st.session_state.selected_state} level")
        # create a dataframe, first column is city, second column is negative count, third column is neutral count, fourth column is positive count
        city_stance_df = (
            stance_df.groupby(["City", "Stance"]).size().unstack().reset_index()
        )
        # print(city_stance_df.head())
        st.bar_chart(
            city_stance_df,
            x="City",
            y=["Positive", "Neutral", "Negative"],
            color=["#C82820", "#FFA500", "#61A41D"],
            width=600,
            height=300,
            horizontal=False,
            use_container_width=False,
        )
with tab2:
    # create a dataframe, first column is timestamp, second column is negative count, third column is neutral count, fourth column is positive count
    timeline_data = (
        stance_df.groupby(["Timestamp", "Stance"]).size().unstack().reset_index()
    )
    # sort the dataframe by timestamp
    timeline_data = timeline_data.sort_values(by="Timestamp")
    # format the timestamp column
    timeline_data["Timestamp"] = pd.to_datetime(timeline_data["Timestamp"])
    # set the bar chart title as "claim distribution"
    if st.session_state.selected_state == "All":
        st.write("Truthfulness stance distribution in United States")
    else:
        st.write(f"Truthfulness stance distribution in {st.session_state.selected_state}")
    # a bar chart with the count of each stance
    st.bar_chart(
        timeline_data,
        x="Timestamp",
        y=["Positive", "Neutral", "Negative"],
        color=["#C82820", "#FFA500", "#61A41D"],
    )
    # c3, _, c4 = st.columns((3.9, 0.2, 5.9))
    # with c3:
    #     # create a dataframe, first column is timestamp, second column is negative count, third column is neutral count, fourth column is positive count
    #     timeline_data = stance_df.groupby(["Timestamp", "Stance"]).size().unstack().reset_index()
    #     # sort the dataframe by timestamp
    #     timeline_data = timeline_data.sort_values(by="Timestamp")
    #     # format the timestamp column
    #     timeline_data["Timestamp"] = pd.to_datetime(timeline_data["Timestamp"])
    #     # set the bar chart title as "claim distribution"
    #     if selected_state == "All":
    #         st.write("Truthfulness stance distribution in United States")
    #     else:
    #         st.write(f"Truthfulness stance distribution in {selected_state}")
    #     # a bar chart with the count of each stance
    #     st.bar_chart(
    #         timeline_data,
    #         x="Timestamp",
    #         y=["Positive", "Neutral", "Negative"],
    #         color=["#C82820", "#2D96C8", "#61A41D"],
    #     )

    # with c4:
    #     # set the bar chart title as "claim distribution"
    #     st.write("Cummulative truthfulness stance count in United States")
    #     cumulative_timeline_data = timeline_data.copy()
    #     print(cumulative_timeline_data.head())
    #     # calculate the cummulative count for each stance at each timestamp
    #     cumulative_timeline_data["Positive"] = cumulative_timeline_data["Positive"].cumsum()
    #     cumulative_timeline_data["Neutral"] = cumulative_timeline_data["Neutral"].cumsum()
    #     cumulative_timeline_data["Negative"] = cumulative_timeline_data["Negative"].cumsum()
    #     # a bar chart with the count of each stance
    #     st.bar_chart(
    #         cumulative_timeline_data,
    #         x="Timestamp",
    #         y=["Positive", "Neutral", "Negative"],
    #         color=["#C82820", "#2D96C8", "#61A41D"],
    #     )


####### END: Main

####### START: Footer
st.markdown(
    """
    <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #f1f1f1;
            color: black;
            text-align: center;
        }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="footer">
        <p>© 2025 University of Texas at Arlington. All rights reserved. Contact: <a href="mailto:idir@uta.edu">idir@uta.edu</a></p>
        <p>Visit our lab: <a href="https://idir.uta.edu/home/">IDIR Lab</a>. Visit our project: <a href="https://idir.uta.edu/home/social_sensing/">IDIR Social Sensing</a></p>
    </div>
    """,
    unsafe_allow_html=True,
)
####### END: Footer