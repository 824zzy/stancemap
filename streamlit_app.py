import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import folium
from folium.plugins import MarkerCluster
from constants import (
    US_STATES,
    US_STATES_COORDS,
    VERDICT_FORMATTER,
    VERDICT_MAPPING,
    TEST_TWEETS,
)
from tsm_fn import (
    get_election_data,
    get_politifact_data,
    get_selected_stance,
    get_politifact_categories,
    get_category2claim,
    get_taxonomy,
)
from streamlit_folium import st_folium
from LLM_fn import generate_report
from tsm_fn import (
    get_claim_related_tweets,
    truthfulness_stance_detection,
    render_stance_table,
    render_oneline_stance_table,
)
import datetime

from collections import defaultdict
import math

####### START: Header
st.set_page_config(
    layout="wide",
    page_icon="https://idir.uta.edu/stance_annotation/image/wildfire_wout_text.png",
    page_title="Truthfulness Stance Map",
)
st.logo("https://idir.uta.edu/stance_annotation/image/wildfire_wout_text.png")
####### END: Header

####### START: Sidebar
stance_df = get_election_data()
politifact_df = get_politifact_data()
categories = get_politifact_categories()
# set up taxonomy
broad2claim, broad2medium, medium2detailed = get_taxonomy()
# concatenate the two dataframes
stance_df = pd.concat([stance_df, politifact_df], ignore_index=True)

# Check if there is a typed factual claim
has_typed_factual_claim = st.session_state.get("typed_factual_claim", "") != ""
# Select categories
selected_categories = st.sidebar.multiselect(
    "Select categories",
    categories,
    default=st.session_state.get("selected_categories", ["Coronavirus"]),
    disabled=has_typed_factual_claim,
)
if selected_categories != st.session_state.get("selected_categories", []):
    st.session_state.selected_categories = selected_categories
    st.rerun()  # Force a rerun to ensure the session state is updated

selected_categories_str = ", ".join(st.session_state.selected_categories)


if st.session_state.get("selected_categories") == ["Coronavirus"]:
    broad_topic_options = ["All"] + list(broad2claim.keys())

    # Create columns for indentation
    col1, col2 = st.sidebar.columns(
        [1, 14]
    )  # Adjust the ratio to control the indentation

    with col2:  # Place the select boxes in the second column
        sidebar_selected_broad_topics = st.multiselect(
            f"Select broad topics under {selected_categories_str}",
            broad_topic_options,
            default=st.session_state.get("selected_broad_topics", None),
            disabled=has_typed_factual_claim,
        )
        if sidebar_selected_broad_topics != st.session_state.get(
            "selected_broad_topics", []
        ):
            st.session_state.selected_broad_topics = sidebar_selected_broad_topics
            st.rerun()
        if st.session_state.get("selected_broad_topics", []) != []:
            medium_topic_options = ["All"]
            for broad_topic in st.session_state.get("selected_broad_topics"):
                if broad_topic in broad2medium:
                    medium_topic_options.extend(broad2medium[broad_topic])
            selected_broad_topics_str = ", ".join(
                st.session_state.selected_broad_topics
            )

            sidebar_selected_medium_topics = st.multiselect(
                f"Select medium topics under {selected_broad_topics_str}",
                medium_topic_options,
                default=st.session_state.get("selected_medium_topic", []),
                disabled=has_typed_factual_claim,
            )
            if sidebar_selected_medium_topics != st.session_state.get(
                "selected_medium_topics", []
            ):
                st.session_state.selected_medium_topics = sidebar_selected_medium_topics
                st.rerun()

            detailed_topic_options = medium2detailed.get(medium_topic_options[0], [])
            if (
                st.session_state.get("selected_medium_topics", []) != []
                and len(st.session_state.get("selected_medium_topics")) > 0
            ):
                detailed_topic_options = ["All"]
                for medium_topic in st.session_state.get("selected_medium_topics"):
                    if medium_topic in medium2detailed:
                        detailed_topic_options.extend(medium2detailed[medium_topic])
                selected_medium_topics_str = ", ".join(
                    st.session_state.selected_medium_topics
                )

                sidebar_selected_detailed_topics = st.multiselect(
                    f"Select detailed topics under {selected_medium_topics_str}",
                    detailed_topic_options,
                    default=st.session_state.get("selected_detailed_topic", None),
                    disabled=has_typed_factual_claim,
                )
                if sidebar_selected_detailed_topics != st.session_state.get(
                    "selected_detailed_topics", []
                ):
                    st.session_state.selected_detailed_topics = (
                        sidebar_selected_detailed_topics
                    )
                    st.rerun()


claims_under_categories = []
category2claims = get_category2claim(stance_df)
for c in st.session_state.selected_categories:
    claims_under_categories.extend(category2claims[c])
claims_under_topics = []
if (
    st.session_state.get("selected_detailed_topics") is not None
    and st.session_state.get("selected_medium_topics") is not None
    and st.session_state.get("selected_broad_topics") is not None
):
    for broad_topic in st.session_state.selected_broad_topics:
        if broad_topic in broad2claim:
            claims_under_topics.extend(broad2claim[broad_topic])
    for medium_topic in st.session_state.selected_medium_topics:
        if medium_topic in broad2medium:
            claims_under_topics.extend(broad2medium[medium_topic])
    for detailed_topic in st.session_state.selected_detailed_topics:
        if detailed_topic in medium2detailed:
            claims_under_topics.extend(medium2detailed[detailed_topic])
elif (
    st.session_state.get("selected_medium_topics") is not None
    and st.session_state.get("selected_broad_topics") is not None
):
    for broad_topic in st.session_state.selected_broad_topics:
        if broad_topic in broad2claim:
            claims_under_topics.extend(broad2claim[broad_topic])
    for medium_topic in st.session_state.selected_medium_topics:
        if medium_topic in broad2medium:
            claims_under_topics.extend(broad2medium[medium_topic])
elif st.session_state.get("selected_broad_topics") is not None:
    for broad_topic in st.session_state.selected_broad_topics:
        if broad_topic in broad2claim:
            claims_under_topics.extend(broad2claim[broad_topic])

# use claims under topics when there are selected topics, otherwise use claims under categories
claims_under_categories = set(claims_under_categories)
claims_under_topics = set(claims_under_topics)
if len(claims_under_topics) == 0:
    claim_candidates = claims_under_categories
else:
    claim_candidates = claims_under_topics


claim_candidates = ["All"] + list(claim_candidates)
selected_factual_claims = st.sidebar.multiselect(
    "Choose factual claims of interest to you",
    claim_candidates,
    placeholder="Select factual claims",
    default=["All"],
    disabled=has_typed_factual_claim,
)
if selected_factual_claims == ["All"]:
    # use the subset of the dataframe based on the selected category
    stance_df = stance_df[
        stance_df["Category"].apply(
            lambda x: any([c in x for c in st.session_state.selected_categories])
        )
    ]
else:
    # use the subset of the dataframe based on the selected category and selected factual claims
    stance_df = stance_df[
        stance_df["Claim"].apply(lambda x: x in selected_factual_claims)
    ]


# Allow user to manually type a factual claim
typed_factual_claim = st.sidebar.text_area(
    "Or type a factual claim",
    value=st.session_state.get("typed_factual_claim", ""),
    height=100,
)
if typed_factual_claim != st.session_state.get("typed_factual_claim", ""):
    st.session_state.typed_factual_claim = typed_factual_claim
    # tweets = get_claim_related_tweets(st.session_state.typed_factual_claim)
    tweets = TEST_TWEETS
    print("Found tweets related to the claim: ", len(tweets))
    online_stance_df = truthfulness_stance_detection(
        claim=st.session_state.typed_factual_claim,
        tweets=tweets,
    )
    st.session_state.online_stance_df = online_stance_df
    print("typed factual claim stance_df: ", online_stance_df)
    st.rerun()


# Customize the sidebar
markdown = """
Detecting the truthfulness stance of social media posts toward factual claims.
[Github](<https://github.com/idirlab/trustmap>)
"""
if "selected_state" in st.session_state:
    sidebar_selected_state = st.sidebar.selectbox(
        "Select a state",
        US_STATES,
        index=US_STATES.index(st.session_state.selected_state),
    )
    if sidebar_selected_state != st.session_state.selected_state:
        st.session_state.selected_state = sidebar_selected_state
else:
    sidebar_selected_state = st.sidebar.selectbox("Select a state", US_STATES)
    st.session_state.selected_state = sidebar_selected_state


# Filter stance_df based on the selected stance
start_stance, end_stance = st.sidebar.select_slider(
    f"Truthfulness Stance Range",
    options=["Negative", "Neutral/No Stance", "Positive"],
    value=("Negative", "Positive"),
)
selected_stance = get_selected_stance(start_stance, end_stance)
stance_df = stance_df[stance_df["Stance"].isin(selected_stance)]
selected_stance_str = ", ".join(selected_stance)
# GitHub link at the bottom of the sidebar
st.sidebar.info(markdown)
####### END: Sidebar


####### START: Main
# Show current display options in a compact summary box
with st.expander("Current Display Settings", expanded=True):
    # Use columns for compact display
    cols = st.columns(4)
    col_idx = 0

    def next_col():
        nonlocal_col_idx = next_col.col_idx
        col = cols[nonlocal_col_idx]
        next_col.col_idx = (nonlocal_col_idx + 1) % len(cols)
        return col

    next_col.col_idx = 0

    if not has_typed_factual_claim:
        next_col().markdown(f"**Categories:** _{selected_categories_str}_")
        if st.session_state.get("selected_broad_topics"):
            selected_broad_topics_str = ", ".join(
                st.session_state.get("selected_broad_topics", [])
            )
            next_col().markdown(f"**Broad topics:** _{selected_broad_topics_str}_")
        if st.session_state.get("selected_medium_topics"):
            selected_medium_topics_str = ", ".join(
                st.session_state.get("selected_medium_topics", [])
            )
            next_col().markdown(f"**Medium topics:** _{selected_medium_topics_str}_")
        if st.session_state.get("selected_detailed_topics"):
            selected_detailed_topics_str = ", ".join(
                st.session_state.get("selected_detailed_topics", [])
            )
            next_col().markdown(
                f"**Detailed topics:** _{selected_detailed_topics_str}_"
            )
        # Show selected factual claims
        if len(selected_factual_claims) == 1:
            selected_factual_claim_str = selected_factual_claims[0]
            next_col().markdown(f"**Factual claim:** _{selected_factual_claim_str}_")
        else:
            selected_factual_claim_str = "; ".join(selected_factual_claims)
            next_col().markdown(f"**Factual claims:** _{selected_factual_claim_str}_")
    else:
        next_col().markdown(
            f"**Typed factual claim:** _{st.session_state.typed_factual_claim}_"
        )
    next_col().markdown(f"**State:** _{st.session_state.selected_state}_")
    next_col().markdown(f"**Stance:** _{selected_stance_str}_")


def create_map_folium(stance_df):
    center_lat, center_lon = 40, -100
    m = folium.Map(location=[center_lat, center_lon], zoom_start=4)

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

    marker_cluster = MarkerCluster().add_to(m)
    # only first 10 rows
    stance_df_on_map = stance_df.head(200)
    if len(stance_df) > 400:
        # select 400 rows with interval of 3
        stance_df_on_map = stance_df[::3].head(400)
    else:
        stance_df_on_map = stance_df
    color_mp = {"Positive": "green", "Neutral": "orange", "Negative": "red"}
    for idx, row in stance_df_on_map.iterrows():
        lat = row["Latitude"]
        lon = row["Longitude"]
        if np.isnan(lat) or np.isnan(lon):
            if row["State"] not in US_STATES_COORDS:
                continue
            else:
                lat = US_STATES_COORDS[row["State"]][0]
                lon = US_STATES_COORDS[row["State"]][1]
        stance = row["Stance"]
        color = color_mp.get(stance, "gray")
        verdict = row["Verdict"]
        if pd.isna(verdict):
            row["Verdict"] = "unknown"
        elif row["Verdict"] == False:
            row["Verdict"] = "false"
        popup = f"""
            <b>Tweet</b>: {row['Tweet']}<br>
            <b>Claim:</b> {row['Claim']}<br>
            <b>Claim verdict:</b> {VERDICT_FORMATTER[row['Verdict'].lower()]}<br>
            <hr style="margin: 4px 0; border: none; height: 1px; background-color: #ccc;">
            <b>Stance:</b> {stance}
            """
        icons = {
            "Positive": "plus-circle",
            "Neutral": "dot-circle",
            "Negative": "minus-circle",
        }
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup, max_width=400),
            icon=folium.Icon(icon=icons.get(stance), prefix="fa", color=color),
        ).add_to(marker_cluster)
    return m


col_map, col_explanation = st.columns([3, 2])
with col_map:
    # Render the map in the left column, filling the 3/4 width
    if has_typed_factual_claim:
        m = create_map_folium(st.session_state.online_stance_df)
    else:
        m = create_map_folium(stance_df)
    map_data = st_folium(m, height=420, width="100%")  # Let Streamlit fill the column

with col_explanation:
    # Check if a marker was clicked
    def generate_explanation(claim, tweet, stance):
        # Function to call LLM for explanation
        explanation_prompt = f"""
        Provide an explanation for the truthfulness stance (whether the tweet believe the claim is true ) result:
        - Claim: {claim}
        - Tweet: {tweet}
        - Stance: {stance}
        """
        explanation = generate_report(
            explanation_prompt
        )  # Assuming `generate_report` interacts with the LLM
        return explanation

    if map_data["last_object_clicked_popup"]:
        clicked_marker = map_data["last_object_clicked_popup"]
        # Extract the claim from the clicked marker
        claim = clicked_marker.split("Claim: ")[1].split("\n")[0]
        # Extract the tweet from the clicked marker
        tweet = clicked_marker.split("Tweet: ")[1].split("\n")[0]
        # Extract the stance from the clicked marker
        stance = clicked_marker.split("Stance: ")[1].split("\n")[0]
        with st.expander("Explain stance for the selected tweet", expanded=False):
            if st.button(f"Generate Explanation", key=f"explain_{clicked_marker}"):
                explanation = generate_explanation(claim, tweet, stance)
                st.markdown(f"**Claim:** {claim}")
                st.markdown(f"***Tweet***: {tweet}")
                st.markdown(f"**Stance:** {stance}")
                st.markdown(f"**Stance Explanation:** {explanation}")


if (
    map_data["last_active_drawing"]
    and "name" in map_data["last_active_drawing"]["properties"]
):
    clicked_state = map_data["last_active_drawing"]["properties"].get("name")
    if "clicked_state" not in st.session_state:
        st.session_state.clicked_state = clicked_state
        st.session_state.selected_state = clicked_state
        st.rerun()
    elif clicked_state != st.session_state.clicked_state:
        if st.session_state.clicked_state != None:
            st.session_state.clicked_state = clicked_state
            st.session_state.selected_state = clicked_state
            st.rerun()

# Draw a table that shows the Distribution of X users’ truthfulness stances toward true, mixed, and false claims
# st.markdown(
#     """
#     <h4 style='text-align: center;'>Distribution of Truthfulness Stances</h2>
# """,
#     unsafe_allow_html=True,
# )
# top example: header is Stance, Truth, Mixed, Misinfor, Precision, Recal F1; First raw is \oplus, 6,754 5,094 64,643 9.0 15.6; Second row is \ominus, 1,398 1,350 9,677 10.9 11.7; Third row is \ominus, 3,494 4,453 39,177 83.1 48.8; Fourth row is Recall, 58.0 12.4 34.6, -, -


# Curate data for rendering the table
# limit the stance_df to the selected state
if has_typed_factual_claim:
    _df = st.session_state.online_stance_df
else:
    _df = stance_df

if st.session_state.selected_state == "All":
    regional_stance_df = _df
else:
    regional_stance_df = _df[_df["State"] == st.session_state.selected_state]

for _, row in regional_stance_df.iterrows():
    print(row)

if has_typed_factual_claim:
    table_html, table_dict = render_oneline_stance_table(
        regional_stance_df=regional_stance_df,
    )
else:
    table_html, table_dict = render_stance_table(regional_stance_df=regional_stance_df)
# Display the table using 3 out of 5 column space
col_table, col_empty = st.columns([3, 2])
with col_table:
    st.markdown(table_html, unsafe_allow_html=True)

# tab1, tab2 = st.tabs(
#     ["Stance distribution", "Stance timeline"]
# )
# with tab1:
#     c1, c2 = st.columns([2,3])
#     with c1:
#         # set the bar chart title as "claim distribution"
#         if st.session_state.selected_state == "All":
#             c1_df = stance_df
#             st.write("United States level")
#         else:
#             c1_df = stance_df[stance_df["State"]==st.session_state.selected_state]
#             st.write(f"{st.session_state.selected_state}'s state level")

#         negative_count = c1_df[c1_df["Stance"] == "Negative"].shape[0]
#         neutral_count = c1_df[c1_df["Stance"] == "Neutral"].shape[0]
#         positive_count = c1_df[c1_df["Stance"] == "Positive"].shape[0]
#         chart_data = pd.DataFrame(
#             {
#                 "Stance": ["Negative", "Neutral", "Positive"],
#                 "Count": [negative_count, neutral_count, positive_count],
#                 # red  # orange  # green
#                 "col3": ["#C82820", "#FFA500", "#61A41D"],
#             }
#         )
#         # a bar chart with the count of each stance
#         c = (
#             alt.Chart(chart_data)
#             .mark_bar()
#             .encode(
#             x="Stance",
#             y="Count",
#             color=alt.Color(
#                 "Stance",
#                 scale=alt.Scale(
#                 domain=chart_data["Stance"].tolist(),
#                 range=chart_data["col3"].tolist(),
#                 ),
#                 legend=None,
#             ),
#             tooltip=["Stance", "Count"]
#             )
#             .properties(width=400, height=300)
#             .configure_axis(labelFontSize=12, titleFontSize=12)
#         )
#         st.altair_chart(c, use_container_width=False)

#     with c2:
#         # set the bar chart title as "claim distribution"
#         if st.session_state.selected_state == "All":
#             st.write("United States city level")
#             c2_df = stance_df
#         else:
#             st.write(f"{st.session_state.selected_state} city level")
#             c2_df = stance_df[stance_df["State"]==st.session_state.selected_state]

#         # create a dataframe, first column is city, second column is negative count, third column is neutral count, fourth column is positive count
#         city_stance_df = (
#             c2_df.groupby(["City", "Stance"]).size().unstack().reset_index()
#         )
#         # if Positive, Neutral, Negative columns are not present, fill them with 0
#         if "Positive" not in city_stance_df.columns:
#             city_stance_df["Positive"] = 0
#         if "Neutral" not in city_stance_df.columns:
#             city_stance_df["Neutral"] = 0
#         if "Negative" not in city_stance_df.columns:
#             city_stance_df["Negative"] = 0
#         # row City="None" is not useful, so remove it
#         city_stance_df = city_stance_df[city_stance_df["City"] != "None"]

#         st.bar_chart(
#             city_stance_df,
#             x="City",
#             y=["Positive", "Neutral", "Negative"],
#             color=["#C82820", "#FFA500", "#61A41D"],
#             width=600,
#             height=300,
#             horizontal=False,
#             use_container_width=False,
#         )
# with tab2:
# # create a dataframe, first column is timestamp, second column is negative count, third column is neutral count, fourth column is positive count
# if st.session_state.selected_state == "All":
#     timeline_data = (
#         stance_df.groupby(["Timestamp", "Stance"]).size().unstack().reset_index()
#     )
# else:
#     timeline_data = (
#         stance_df[stance_df["State"]==st.session_state.selected_state].groupby(["Timestamp", "Stance"]).size().unstack().reset_index()
#     )
# # sort the dataframe by timestamp
# timeline_data = timeline_data.sort_values(by="Timestamp")
# # format the timestamp column
# timeline_data["Timestamp"] = pd.to_datetime(timeline_data["Timestamp"])
# if "Positive" not in timeline_data.columns:
#     timeline_data["Positive"] = 0
# if "Neutral" not in timeline_data.columns:
#     timeline_data["Neutral"] = 0
# if "Negative" not in timeline_data.columns:
#     timeline_data["Negative"] = 0
# print(timeline_data.columns)

# # set the bar chart title as "claim distribution"
# if st.session_state.selected_state == "All":
#     st.write("Truthfulness stance distribution in United States")
# else:
#     st.write(f"Truthfulness stance distribution in {st.session_state.selected_state}")
# # a bar chart with the count of each stance
# st.bar_chart(
#     timeline_data,
#     x="Timestamp",
#     y=["Positive", "Neutral", "Negative"],
#     color=["#C82820", "#FFA500", "#61A41D"],
# )


# Add a section for report generation
st.markdown(
    """
    <p style='text-align: center;'>
        You can generate a report based on the current selections.
        This report will summarize the truthfulness stance distribution and other relevant information (precision, recall and F1 score).
    </p>
""",
    unsafe_allow_html=True,
)
if not has_typed_factual_claim:
    report_prompt = f"""
    Generate a report based on the following selections:
    - Categories/People/Issues: {selected_categories_str}
    - Factual claims: {selected_factual_claim_str}
    - State: {st.session_state.selected_state}
    - Stance: {selected_stance_str}
    - Distribution statistics:
    {table_dict}
    The report should include an overview of the truthfulness stance distribution, key findings, and any notable trends or insights.
    """
else:
    report_prompt = f"""
    Generate a report based on the following typed factual claim:
    - Factual claim: {st.session_state.typed_factual_claim}
    - State: {st.session_state.selected_state}
    - Stance: {selected_stance_str}
    The report should include an overview of the truthfulness stance distribution, key findings, and any notable trends or insights.
    """
if st.button("Generate Report"):
    with st.spinner("Generating report..."):
        report = generate_report(report_prompt)
        st.session_state.generated_report = report

# Display the report if it exists in session state
if "generated_report" in st.session_state:
    st.markdown(f"### Generated Report")
    st.write(st.session_state.generated_report)


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
