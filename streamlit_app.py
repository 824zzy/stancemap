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
    create_map_folium,
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
    broad_topic_options = list(broad2claim.keys())
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
            medium_topic_options = []
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
                detailed_topic_options = []
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
print("-------")
print(st.session_state.get("selected_detailed_topics"))
print(st.session_state.get("selected_medium_topics"))
print(st.session_state.get("selected_broad_topics"))
if (
    st.session_state.get("selected_detailed_topics") is not None
    and st.session_state.get("selected_medium_topics") is not None
    and st.session_state.get("selected_broad_topics") is not None
):
    for medium_topic in st.session_state.selected_medium_topics:
        for detailed_topic in st.session_state.selected_detailed_topics:
            claims_under_topics.extend(medium2detailed[medium_topic][detailed_topic])
elif (
    st.session_state.get("selected_medium_topics") is not None
    and st.session_state.get("selected_broad_topics") is not None
):
    for broad_topic in st.session_state.selected_broad_topics:
        for medium_topic in st.session_state.selected_medium_topics:
            claims_under_topics.extend(broad2medium[broad_topic][medium_topic])
elif st.session_state.get("selected_broad_topics") is not None:
    for broad_topic in st.session_state.selected_broad_topics:
        claims_under_topics.extend(broad2claim[broad_topic])

# use claims under topics when there are selected topics, otherwise use claims under categories
claims_under_categories = set(claims_under_categories)
claims_under_topics = set(claims_under_topics)
print("claims under categories: ", len(claims_under_categories))
print("claims under topics: ", len(claims_under_topics))
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
print("selected_factual_claims: ", selected_factual_claims)
print("claim_candidates: ", len(claim_candidates))
if "All" in selected_factual_claims:
    print("All selected, using all claims")
    # use the subset of the dataframe based on the selected category
    stance_df = stance_df[stance_df["Claim"].apply(lambda x: x in claim_candidates)]
else:
    # use the subset of the dataframe based on the selected category and selected factual claims
    stance_df = stance_df[
        stance_df["Claim"].apply(lambda x: x in selected_factual_claims)
    ]
print("qwer", stance_df.shape)

# Allow user to manually type a factual claim
typed_factual_claim = st.sidebar.text_area(
    "Or type a factual claim",
    placeholder="A video shows woman exiting her car during the 2025 Los Angeles protests, shouting, “I have babies in the car!",
    height=100,
)
if typed_factual_claim != st.session_state.get("typed_factual_claim", ""):
    st.session_state.typed_factual_claim = typed_factual_claim
    if st.session_state.typed_factual_claim == "":
        st.session_state.typed_factual_claim = None
        st.rerun()
    else:
        tweets = get_claim_related_tweets(st.session_state.typed_factual_claim)
        # tweets = TEST_TWEETS
        print("Found tweets related to the claim: ", len(tweets))
        online_stance_df = truthfulness_stance_detection(
            claim=st.session_state.typed_factual_claim,
            tweets=tweets,
        )
        st.session_state.online_stance_df = online_stance_df
        print("typed factual claim stance_df: ", online_stance_df)
        st.rerun()
print("Typed factual claim: ", st.session_state.get("typed_factual_claim", ""))

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


col_map, col_explaination = st.columns([3, 3])
# Apply custom CSS to adjust the width of the col_map

with col_map:
    # Render the map in the left column, filling the 3/4 width
    if has_typed_factual_claim:
        m = create_map_folium(st.session_state.online_stance_df)
    else:
        m = create_map_folium(stance_df)
    map_data = st_folium(m, height=420, width="100%")  # Let Streamlit fill the column

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

    if has_typed_factual_claim:
        table_html, table_dict = render_oneline_stance_table(
            regional_stance_df=regional_stance_df,
        )
    else:
        table_html, table_dict = render_stance_table(
            regional_stance_df=regional_stance_df
        )

    st.markdown(table_html, unsafe_allow_html=True)

    st.write("State level (Y-axis represents log10(tweet count))")
    if has_typed_factual_claim:
        # Use the online stance dataframe for the typed factual claim
        if "State" in st.session_state.online_stance_df.columns:
            state_stance_df = (
                st.session_state.online_stance_df.groupby(["State", "Stance"])
                .size()
                .unstack()
                .reset_index()
            )
        else:
            state_stance_df = pd.DataFrame(
                columns=["State", "Positive", "Neutral", "Negative"]
            )
    else:
        state_stance_df = (
            stance_df.groupby(["State", "Stance"]).size().unstack().reset_index()
        )
    # if Positive, Neutral, Negative columns are not present, fill them with 0
    if "Positive" not in state_stance_df.columns:
        state_stance_df["Positive"] = 0
    if "Neutral" not in state_stance_df.columns:
        state_stance_df["Neutral"] = 0
    if "Negative" not in state_stance_df.columns:
        state_stance_df["Negative"] = 0

    # Apply log10 transformation to the counts
    state_stance_df["Positive"] = state_stance_df["Positive"].apply(
        lambda x: math.log10(x + 1)
    )
    state_stance_df["Neutral"] = state_stance_df["Neutral"].apply(
        lambda x: math.log10(x + 1)
    )
    state_stance_df["Negative"] = state_stance_df["Negative"].apply(
        lambda x: math.log10(x + 1)
    )
    st.bar_chart(
        state_stance_df,
        x="State",
        y=["Positive", "Neutral", "Negative"],
        color=["#C82820", "#FFA500", "#61A41D"],
        use_container_width=True,  # Fit the chart to the column width
    )

with col_explaination:
    # Apply custom CSS for the expander width and scrolling
    st.markdown(
        """
        <style>
        .stExpander {
            max-height: 420px;
            overflow-y: auto;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

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

    with st.expander("Explain stance for the selected tweet", expanded=False):
        if map_data["last_object_clicked_popup"]:
            clicked_marker = map_data["last_object_clicked_popup"]
            # Extract the claim from the clicked marker
            claim = clicked_marker.split("Claim: ")[1].split("\n")[0]
            # Extract the tweet from the clicked marker
            tweet = clicked_marker.split("Tweet: ")[1].split("\n")[0]
            # Extract the stance from the clicked marker
            stance = clicked_marker.split("Stance: ")[1].split("\n")[0]
            if (
                st.session_state.get("explanation") != None
                and st.session_state.explanation[0] == tweet
            ):
                st.markdown(f"**Claim:** {claim}")
                st.markdown(f"***Tweet***: {tweet}")
                st.markdown(f"**Stance:** {stance}")
                st.markdown(f"**Stance Explanation:** {st.session_state.explanation}")
            elif st.button(f"Generate Explanation", key=f"explain_{clicked_marker}"):
                # use st.session_state to store the explanation
                tweet_explanation = generate_explanation(claim, tweet, stance)
                st.session_state.explanation = (tweet, tweet_explanation)
                st.markdown(f"**Claim:** {claim}")
                st.markdown(f"***Tweet***: {tweet}")
                st.markdown(f"**Stance:** {stance}")
                st.markdown(f"**Stance Explanation:** {st.session_state.explanation}")
        else:
            st.markdown("Please select a tweet on the map to view its explanation.")

    with st.expander("Generate a report for stance distribution", expanded=False):
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
        if st.button("Generate Report", key="generate_report"):
            with st.spinner("Generating report..."):
                report = generate_report(report_prompt)
                st.session_state.generated_report = report

        # Display the report if it exists in session state
        if "generated_report" in st.session_state:
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
