import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import folium
from folium.plugins import MarkerCluster
from constants import us_states, us_states_coords
import json
from tsm_fn import get_election_data, get_politifact_data, get_selected_stance, get_politifact_categories, get_category2claim
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
categories = get_politifact_categories()
# concatenate the two dataframes
stance_df = pd.concat([stance_df, politifact_df], ignore_index=True)
category2claims = get_category2claim(stance_df)

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
        default=["Climate Change",],
    )
    st.session_state.selected_category = sidebar_selected_category


selected_category_str = ", ".join(st.session_state.selected_category)



category_claims = []
for c in st.session_state.selected_category:
    category_claims.extend(category2claims[c])
category_claims = ['All']+category_claims
            
selected_factual_claims= st.sidebar.multiselect(
    "Factual claims of interest to you",
    category_claims,
    placeholder="Select factual claims",
    default=["All"]
)

# TODO:

if selected_factual_claims == ['All']:
    # use the subset of the dataframe based on the selected category
    stance_df = stance_df[stance_df["Category"].apply(lambda x: any([c in x for c in st.session_state.selected_category]))]
else:
    # use the subset of the dataframe based on the selected category and selected factual claims
    stance_df = stance_df[stance_df["Claim"].apply(lambda x: x in selected_factual_claims)]
print(f'len(stance_df): {len(stance_df)}')

# Customize the sidebar
markdown = """
Detecting the truthfulness stance of social media posts toward factual claims.
[Github](<https://github.com/opengeos/streamlit-map-template>)
"""
if 'selected_state' in st.session_state:
    sidebar_selected_state = st.sidebar.selectbox("Select a state", us_states, index=us_states.index(st.session_state.selected_state))
    print(f'has selected_state: {st.session_state.selected_state}, new selected_state: {sidebar_selected_state}')
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
stance_df = stance_df[stance_df["Stance"].isin(selected_stance)]
selected_stance_str = ", ".join(selected_stance)

st.sidebar.info(markdown)
####### END: Sidebar

####### START: Main
# show selected options
st.write(f"Categories/People/Issues: **_{selected_category_str}_**")
if len(selected_factual_claims) == 1:
    selected_factual_claim_str = selected_factual_claims[0]
    st.write(f"Factual claim: **_{selected_factual_claim_str}_**")
else:
    selected_factual_claim_str = "; ".join(selected_factual_claims)
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
    stance_df_on_map = stance_df.head(200)
    if len(stance_df) > 400:
        # select 400 rows with interval of 3
        stance_df_on_map = stance_df[::3].head(400)
    else:
        stance_df_on_map = stance_df
    color_mp = {
        "Positive": "green",
        "Neutral": "orange",
        "Negative": "red"
    }
    print(f'len(stance_df_on_map): {len(stance_df_on_map)}')
    for idx, row in stance_df_on_map.iterrows():
        lat = row["Latitude"]
        lon = row["Longitude"]
        if np.isnan(lat) or np.isnan(lon):
            if row["State"] not in us_states_coords:
                continue
            else:
                lat = us_states_coords[row["State"]][0]
                lon = us_states_coords[row["State"]][1]
        stance = row["Stance"]
        color = color_mp.get(stance, "gray")
        verdict = {
            'true': 'True',
            'mostly-true': "Mostly True", 
            'half-true': 'Half True',
            'barely-true': 'Barely True',
            'false': 'False',
            'pants-fire': 'Pants on Fire',
            'full-flop': 'Full Flop',
            'half-flip': 'Half Flip',
        }
        if row['Verdict']==False:
            row['Verdict'] = 'false'
        popup = f"""
            <b>Tweet</b>: {row['Tweet']}<br>
            <b>Claim:</b> {row['Claim']}<br>
            <b>Claim verdict:</b> {verdict[row['Verdict'].lower()]}<br>
            <hr style="margin: 4px 0; border: none; height: 1px; background-color: #ccc;">
            <b>Stance:</b> {stance}"""
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

m = create_map_folium(stance_df)
map_data = st_folium(m, height=500, width=1200)
if map_data["last_active_drawing"] and 'name' in map_data["last_active_drawing"]["properties"]:
    clicked_state = map_data["last_active_drawing"]['properties'].get('name')
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
    c1, c2 = st.columns([2,3])
    with c1:
        # set the bar chart title as "claim distribution"
        if st.session_state.selected_state == "All":
            c1_df = stance_df
            st.write("United States level")
        else:
            c1_df = stance_df[stance_df["State"]==st.session_state.selected_state]
            st.write(f"{st.session_state.selected_state}'s state level")
    
        negative_count = c1_df[c1_df["Stance"] == "Negative"].shape[0]
        neutral_count = c1_df[c1_df["Stance"] == "Neutral"].shape[0]
        positive_count = c1_df[c1_df["Stance"] == "Positive"].shape[0]
        chart_data = pd.DataFrame(
            {
                "Stance": ["Negative", "Neutral", "Positive"],
                "Count": [negative_count, neutral_count, positive_count],
                # red  # orange  # green
                "col3": ["#C82820", "#FFA500", "#61A41D"],
            }
        )
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
                legend=None,
            ),
            tooltip=["Stance", "Count"]
            )
            .properties(width=400, height=300)
            .configure_axis(labelFontSize=12, titleFontSize=12)
        )
        st.altair_chart(c, use_container_width=False)

    with c2:
        # set the bar chart title as "claim distribution"
        if st.session_state.selected_state == "All":
            st.write("United States city level")
            c2_df = stance_df
        else:
            st.write(f"{st.session_state.selected_state} city level")
            c2_df = stance_df[stance_df["State"]==st.session_state.selected_state]

        # create a dataframe, first column is city, second column is negative count, third column is neutral count, fourth column is positive count
        city_stance_df = (
            c2_df.groupby(["City", "Stance"]).size().unstack().reset_index()
        )
        # if Positive, Neutral, Negative columns are not present, fill them with 0
        if "Positive" not in city_stance_df.columns:
            city_stance_df["Positive"] = 0
        if "Neutral" not in city_stance_df.columns:
            city_stance_df["Neutral"] = 0
        if "Negative" not in city_stance_df.columns:
            city_stance_df["Negative"] = 0
        # row City="None" is not useful, so remove it
        city_stance_df = city_stance_df[city_stance_df["City"] != "None"]

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
    if st.session_state.selected_state == "All":
        timeline_data = (
            stance_df.groupby(["Timestamp", "Stance"]).size().unstack().reset_index()
        )
    else:
        timeline_data = (
            stance_df[stance_df["State"]==st.session_state.selected_state].groupby(["Timestamp", "Stance"]).size().unstack().reset_index()
        )
    # sort the dataframe by timestamp
    timeline_data = timeline_data.sort_values(by="Timestamp")
    # format the timestamp column
    timeline_data["Timestamp"] = pd.to_datetime(timeline_data["Timestamp"])
    if "Positive" not in timeline_data.columns:
        timeline_data["Positive"] = 0
    if "Neutral" not in timeline_data.columns:
        timeline_data["Neutral"] = 0
    if "Negative" not in timeline_data.columns:
        timeline_data["Negative"] = 0
    print(timeline_data.columns)

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