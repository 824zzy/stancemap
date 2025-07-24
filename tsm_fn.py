# Truthfulness Stance Map Functions
import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
from constants import US_STATES_COORDS, VERDICT_MAPPING, VERDICT_FORMATTER
import spacy
import tweepy
from geopy.geocoders import Nominatim
import datetime
from LLM_fn import stance_analysis
import math
from collections import defaultdict
import folium
from folium.plugins import MarkerCluster

nlp = spacy.load("en_core_web_sm")


@st.cache_data(ttl=3 * 60 * 60)
def get_election_data():
    # Load the data
    stance_csv = "./data/2024_election_stance_v2_cleaned.csv"
    stance_df = pd.read_csv(stance_csv)
    # select first 100 rows
    # stance_df = stance_df.head(100)

    # drop first index column
    stance_df = stance_df.drop(stance_df.columns[0], axis=1)
    # add jitter to the latitude and longitude
    stance_df["Latitude"] = stance_df["Latitude"] + np.random.normal(
        0, 0.2, len(stance_df)
    )
    stance_df["Longitude"] = stance_df["Longitude"] + np.random.normal(
        0, 0.2, len(stance_df)
    )
    return stance_df


@st.cache_data(ttl=3 * 60 * 60)
def get_politifact_data():
    # Load the data
    politifact_csv = "./data/stancemap_eval.csv"
    politifact_df = pd.read_csv(politifact_csv)
    # only select the rows that State is in US_STATES_COORDS
    politifact_df = politifact_df[politifact_df["State"].isin(US_STATES_COORDS)]
    # update Stance column, 0 to Positive, 1 to Neutral, 2 to Negative
    politifact_df["Stance"] = politifact_df["Stance"].replace(
        {0: "Positive", 1: "Neutral", 2: "Negative"}
    )
    # add jitter to the latitude and longitude
    politifact_df["Latitude"] = politifact_df["Latitude"] + np.random.normal(
        0, 0.2, len(politifact_df)
    )
    politifact_df["Longitude"] = politifact_df["Longitude"] + np.random.normal(
        0, 0.2, len(politifact_df)
    )
    # select first 100 rows
    # stance_df = stance_df.head(100)

    return politifact_df


@st.cache_data(ttl=3 * 60 * 60)
def get_category2claim(stance_df):
    category2claim = {}
    for i in range(len(stance_df)):
        category = stance_df["Category"][i]
        category = eval(category)
        for c in category:
            c = c.strip()
            claim = stance_df["Claim"][i]
            if c in category2claim:
                category2claim[c].add(claim)
            else:
                category2claim[c] = {claim}
    # sort the claims
    for category in category2claim:
        category2claim[category] = sorted(category2claim[category])
    return category2claim


@st.cache_data(ttl=3 * 60 * 60)
def get_politifact_categories():
    politifact_csv = "./data/stancemap_eval.csv"
    politifact_df = pd.read_csv(politifact_csv)
    category_col = politifact_df["Category"]
    categories = Counter()
    for i in range(len(category_col)):
        category_row = eval(category_col[i])
        for c in category_row:
            if c:
                categories[c] += 1
    # sort the categories by frequency
    categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    # get the category names
    category_names = [c[0] for c in categories]
    return category_names


@st.cache_data(ttl=3 * 60 * 60)
def get_taxonomy():
    taxonomy_csv = "./data/coronavirus_taxonomy.csv"
    taxonomy_df = pd.read_csv(taxonomy_csv)
    # Convert the DataFrame to a dictionary
    broad2claim = {}
    broad2medium = {}
    medium2detailed = {}
    for _, row in taxonomy_df.iterrows():
        claim = row["claim"]
        broad = row["broad_topic"]
        medium = row["medium_topic"]
        detailed = row["detailed_topic"]

        # broad2claim
        if broad not in broad2claim:
            broad2claim[broad] = []
        broad2claim[broad].append(claim)

        # broad2medium
        if not pd.isna(medium):
            if broad not in broad2medium:
                broad2medium[broad] = {}
            if medium not in broad2medium[broad]:
                broad2medium[broad][medium] = []
            broad2medium[broad][medium].append(claim)

        # medium2detailed
        if not pd.isna(detailed):
            if medium not in medium2detailed:
                medium2detailed[medium] = {}
            if detailed not in medium2detailed[medium]:
                medium2detailed[medium][detailed] = []
            medium2detailed[medium][detailed].append(claim)

    # print("Broad to Claim Mapping:", broad2claim)
    # print("Broad to Medium Mapping:", broad2medium)
    # print("Medium to Detailed Mapping:", medium2detailed)
    return broad2claim, broad2medium, medium2detailed


def get_selected_stance(start_stance, end_stance):
    if start_stance == "Negative" and end_stance == "Positive":
        selected_stance = ["Negative", "Neutral", "Positive"]
    elif start_stance == "Neutral/No Stance" and end_stance == "Positive":
        selected_stance = ["Neutral", "Positive"]
    elif start_stance == "Negative" and end_stance == "Neutral/No Stance":
        selected_stance = ["Negative", "Neutral"]
    elif start_stance == "Negative" and end_stance == "Negative":
        selected_stance = ["Negative"]
    elif start_stance == "Neutral/No Stance" and end_stance == "Neutral/No Stance":
        selected_stance = ["Neutral/No Stance"]
    elif start_stance == "Positive" and end_stance == "Positive":
        selected_stance = ["Positive"]
    else:
        selected_stance = ["Negative", "Neutral", "Positive"]
    return selected_stance


def infer_user_location(place):
    """
    Infer the user's location based on their profile location.
    This function can be extended to use more sophisticated methods.

    Args:
        place (str): The location string from the user's profile.
    Returns:
        tuple: A tuple containing the address, latitude, and longitude of the inferred location.
               If the location cannot be found, returns (None, None, None).
    """
    geolocator = Nominatim(user_agent="geoapi")
    location = geolocator.geocode(place, addressdetails=True, timeout=5)
    if not location:
        return None, None, None, None, None
    address, latitude, longitude = (
        location.address,
        location.latitude,
        location.longitude,
    )
    addresses = address.split(",")
    country, state, county, city = None, None, None, None
    for x in addresses[::-1]:
        # if x is a number, skip
        if x.strip().isdigit():
            continue
        if country == None:
            country = x.strip()
        elif state == None:
            state = x.strip()
        elif county == None:
            county = x.strip()
        elif city == None:
            city = x.strip()
    if country in ("United States", "USA", "US", "United States of America"):
        return city, county, state, latitude, longitude
    return None, None, None, None, None


def get_claim_related_tweets(claim):
    doc = nlp(claim)
    keywords = set()
    # Stepwise keyword extraction: NOUN -> NOUN+PROPN -> NOUN+PROPN+VERB
    pos_priority = [["NOUN"], ["NOUN", "PROPN"], ["NOUN", "PROPN", "VERB"]]
    idx = 0
    while idx < len(pos_priority):
        keywords.clear()
        for token in doc:
            if token.pos_ in pos_priority[idx]:
                keywords.add(token.text)
        if len(keywords) > 3 or idx == len(pos_priority) - 1:
            break
        idx += 1
    keywords = list(keywords)
    if len(keywords) == 0:
        print("No keywords found in the claim.")
        return []
    # exclude grok using operators
    query = " ".join(keywords) + " -from:grok"
    # Load the Twitter client using tweepy
    client = tweepy.Client(
        bearer_token=st.secrets["BEARER_TOKEN"],
        consumer_key=st.secrets["CONSUMER_KEY"],
        consumer_secret=st.secrets["CONSUMER_SECRET"],
        access_token=st.secrets["ACCESS_TOKEN"],
        access_token_secret=st.secrets["ACCESS_SECRET"],
    )
    print(f"Searching for tweets related to the claim: {claim}\nquery: {query}")
    # Search for tweets related to the claim
    tweets = client.search_recent_tweets(
        query=query,
        max_results=30,
        tweet_fields=["created_at", "geo", "author_id"],
        expansions=["author_id", "geo.place_id"],
        user_fields=[
            "location",
            "username",
            "name",
            "profile_image_url",
            "description",
        ],
    )
    if not tweets.data:
        print("No tweets found for the given claim.")
        return []
    print(f"Found {len(tweets.data)} tweets related to the claim.")

    # Build a mapping from user id to user profile
    users = (
        {u.id: u for u in tweets.includes["users"]}
        if "users" in tweets.includes
        else {}
    )
    tweet_data = []
    for tweet in tweets.data:
        tweet_info = {
            "id": tweet.id,
            "text": tweet.text,
            "created_at": tweet.created_at,
            "author_id": tweet.author_id,
            "geo": tweet.geo,
            "user_profile": {
                "username": None,
                "name": None,
                "location": None,
                "profile_image_url": None,
                "description": None,
                "inferred_location": {
                    "city": None,
                    "county": None,
                    "state": None,
                    "latitude": None,
                    "longitude": None,
                },
            },
            "place": None,
        }
        # Add user profile info
        user_profile = users.get(tweet.author_id)
        if user_profile:
            tweet_info["user_profile"]["username"] = user_profile.username
            tweet_info["user_profile"]["name"] = user_profile.name
            tweet_info["user_profile"]["location"] = getattr(
                user_profile, "location", None
            )
            tweet_info["user_profile"]["profile_image_url"] = getattr(
                user_profile, "profile_image_url", None
            )
            tweet_info["user_profile"]["description"] = getattr(
                user_profile, "description", None
            )
            if tweet_info["user_profile"]["location"]:
                # Infer user location if available
                city, county, state, latitude, longitude = infer_user_location(
                    tweet_info["user_profile"]["location"]
                )
                tweet_info["user_profile"]["inferred_location"]["city"] = city
                tweet_info["user_profile"]["inferred_location"]["county"] = county
                tweet_info["user_profile"]["inferred_location"]["state"] = state
                tweet_info["user_profile"]["inferred_location"]["latitude"] = latitude
                tweet_info["user_profile"]["inferred_location"]["longitude"] = longitude
        # Add place info if available
        if tweet.geo and hasattr(tweet.geo, "place_id"):
            place = client.get_place(place_id=tweet.geo.place_id)
            if place.data:
                tweet_info["place"] = place.data
        # last check the latitude and longitude
        if (
            tweet_info["user_profile"]["inferred_location"]["latitude"] is not None
            and tweet_info["user_profile"]["inferred_location"]["longitude"] is not None
        ):
            tweet_info["user_profile"]["inferred_location"][
                "latitude"
            ] += np.random.normal(0, 0.2)
            tweet_info["user_profile"]["inferred_location"][
                "longitude"
            ] += np.random.normal(0, 0.2)
        else:
            # use lat=39.8333, lon=–98.5855 at the placeholder for missing locations
            tweet_info["user_profile"]["inferred_location"] = {
                "city": "Unknown",
                "county": "Unknown",
                "state": "Unknown",
                "latitude": 39.8333 + np.random.normal(0, 0.2),
                "longitude": -98.5855 + np.random.normal(0, 0.2),
            }
        tweet_data.append(tweet_info)
    return tweet_data


def truthfulness_stance_detection(claim, tweets):
    # use GPT for now, replace with our RATSD later
    for tweet in tweets:
        stance = stance_analysis(claim, tweet["text"], st.secrets["OPENAI_API_KEY"])
        tweet["stance"] = stance
    # return as a DataFrame: City,Claim,Tweet,Latitude,Longitude,User,Timestamp,Stance,Category,State,Verdict
    stance_df = pd.DataFrame(
        [
            {
                "City": tweet["user_profile"]["inferred_location"]["city"],
                "Claim": claim,
                "Tweet": tweet["text"],
                "Latitude": tweet["user_profile"]["inferred_location"]["latitude"],
                "Longitude": tweet["user_profile"]["inferred_location"]["longitude"],
                "User": tweet["user_profile"]["username"],
                "Timestamp": tweet["created_at"],
                "Stance": tweet["stance"],
                "Category": None,  # Placeholder for category
                "State": tweet["user_profile"]["inferred_location"]["state"],
                "Verdict": None,  # Placeholder for verdict
            }
            for tweet in tweets
        ]
    )
    return stance_df


def render_stance_table(regional_stance_df):
    """
    Render the stance DataFrame as a table in Streamlit.
    """
    table_dict = defaultdict(int)
    for _, row in regional_stance_df.iterrows():
        if pd.isna(row["Verdict"]):
            row["Verdict"] = "unknown"
        elif row["Verdict"] == False:
            row["Verdict"] = "false"
        verdict = VERDICT_MAPPING.get(row["Verdict"].lower(), "Unknown")
        stance = row["Stance"]
        table_dict[(stance, verdict)] += 1
    table_dict[("Positive", "Precision")] = (
        table_dict[("Positive", "Truth")]
        / max(
            table_dict[("Positive", "Truth")]
            + table_dict[("Positive", "Mixed")]
            + table_dict[("Positive", "Misinfo")],
            1,
        )
        * 100
    )
    table_dict[("Neutral", "Precision")] = (
        table_dict[("Neutral", "Truth")]
        / max(
            table_dict[("Neutral", "Truth")]
            + table_dict[("Neutral", "Mixed")]
            + table_dict[("Neutral", "Misinfo")],
            1,
        )
        * 100
    )
    table_dict[("Negative", "Precision")] = (
        table_dict[("Negative", "Truth")]
        / max(
            table_dict[("Negative", "Truth")]
            + table_dict[("Negative", "Mixed")]
            + table_dict[("Negative", "Misinfo")],
            1,
        )
        * 100
    )
    table_dict[("Truth", "Recall")] = (
        table_dict[("Positive", "Truth")]
        / max(
            table_dict[("Positive", "Truth")]
            + table_dict[("Neutral", "Truth")]
            + table_dict[("Negative", "Truth")],
            1,
        )
        * 100
    )
    table_dict[("Mixed", "Recall")] = (
        table_dict[("Positive", "Mixed")]
        / max(
            table_dict[("Positive", "Mixed")]
            + table_dict[("Neutral", "Mixed")]
            + table_dict[("Negative", "Mixed")],
            1,
        )
        * 100
    )
    table_dict[("Misinfo", "Recall")] = (
        table_dict[("Positive", "Misinfo")]
        / max(
            table_dict[("Positive", "Misinfo")]
            + table_dict[("Neutral", "Misinfo")]
            + table_dict[("Negative", "Misinfo")],
            1,
        )
        * 100
    )
    # Add F1 scores
    table_dict[("Positive", "F1")] = (
        2
        * (table_dict[("Positive", "Precision")] * table_dict[("Truth", "Recall")])
        / max(
            table_dict[("Positive", "Precision")] + table_dict[("Truth", "Recall")],
            1,
        )
    )
    table_dict[("Neutral", "F1")] = (
        2
        * (table_dict[("Neutral", "Precision")] * table_dict[("Mixed", "Recall")])
        / max(
            table_dict[("Neutral", "Precision")] + table_dict[("Mixed", "Recall")],
            1,
        )
    )
    table_dict[("Negative", "F1")] = (
        2
        * (table_dict[("Negative", "Precision")] * table_dict[("Misinfo", "Recall")])
        / max(
            table_dict[("Negative", "Precision")] + table_dict[("Misinfo", "Recall")],
            1,
        )
    )

    rows = [
        [
            "<b>⊕</b>",
            table_dict.get(("Positive", "Truth"), 0),
            table_dict.get(("Positive", "Mixed"), 0),
            table_dict.get(("Positive", "Misinfo"), 0),
            table_dict.get(("Positive", "Precision"), None),
            table_dict.get(("Positive", "F1"), None),
        ],
        [
            "<b>⊙</b>",
            table_dict.get(("Neutral", "Truth"), 0),
            table_dict.get(("Neutral", "Mixed"), 0),
            table_dict.get(("Neutral", "Misinfo"), 0),
            table_dict.get(("Neutral", "Precision"), None),
            table_dict.get(("Neutral", "F1"), None),
        ],
        [
            "<b>⊖</b>",
            table_dict.get(("Negative", "Truth"), 0),
            table_dict.get(("Negative", "Mixed"), 0),
            table_dict.get(("Negative", "Misinfo"), 0),
            table_dict.get(("Negative", "Precision"), None),
            table_dict.get(("Negative", "F1"), None),
        ],
        [
            "<b>Recall</b>",
            table_dict.get(("Truth", "Recall"), None),
            table_dict.get(("Mixed", "Recall"), None),
            table_dict.get(("Misinfo", "Recall"), None),
            None,
            None,
        ],
    ]

    # Max values for bar scaling
    max_truth = max(r[1] for r in rows[:3])
    max_mixed = max(r[2] for r in rows[:3])
    max_misinfo = max(r[3] for r in rows[:3])
    max_value = max(
        max_truth, max_mixed, max_misinfo, 1
    )  # Ensure max_value is at least 1

    # Color per row index
    row_colors = ["#28a745", "#fd7e14", "#dc3545"]  # green, orange, red

    # Helper to create bar cell with label inside
    def bar_cell(value, max_value, color):
        if value is None:
            return ""
        max_value = max(
            max_value, 1
        )  # Ensure max_value is at least 1 to avoid division by zero
        width_pct = (math.log2(value + 1) / math.log2(max_value + 1)) * 100
        return f"""
        <div style='width: 100%; background: #e9ecef; height: 24px; border-radius: 4px; position: relative; overflow: hidden;'>
            <div style='width: {width_pct:.1f}%; background: {color}; height: 100%; border-radius: 4px; text-align: right; padding-right: 4px; color: white; font-size: 12px; line-height: 24px;'>
                {value:.1f}
            </div>
        </div>
        """

    # Build HTML table
    html = """
    <style>
        table.custom-table {
            border-collapse: collapse;
            width: 100%;
            font-family: sans-serif;
        }
        table.custom-table th, table.custom-table td {
            border: 1px solid #ddd;
            padding: 6px;
            vertical-align: middle;
        }
    </style>
    <table class="custom-table">
        <tr>
            <th>Stance</th>
            <th>Truth</th>
            <th>Mixed</th>
            <th>Misinfo</th>
            <th>Prec</th>
            <th>F1</th>
        </tr>
    """

    for i, row in enumerate(rows):
        stance, truth, mixed, misinfo, precision, f1 = row
        html += "<tr>"
        html += f"<td>{stance}</td>"

        # Bar or number for each cell
        if i < 3:
            color = row_colors[i]
            html += f"<td>{bar_cell(truth, max_value, color)}</td>"
            html += f"<td>{bar_cell(mixed, max_value, color)}</td>"
            html += f"<td>{bar_cell(misinfo, max_value, color)}</td>"
        else:
            html += f"<td>{truth:.1f}</td>"
            html += f"<td>{mixed:.1f}</td>"
            html += f"<td>{misinfo:.1f}</td>"

        html += f"<td>{'' if precision is None else f'{precision:.1f}'}</td>"
        html += f"<td>{'' if f1 is None else f'{f1:.1f}'}</td>"
        html += "</tr>"

    html += "</table><hr>Note: Precision, Recall, and F1 measure the accuracy of tweet stance alignment with the claim’s verdict."
    ""
    return html, table_dict


def render_oneline_stance_table(regional_stance_df):
    """
    Render the stance DataFrame as a one-line table in Streamlit as there is no verdict in online stance.
    """
    table_dict = defaultdict(int)
    for _, row in regional_stance_df.iterrows():
        stance = row["Stance"]
        table_dict[stance] += 1

    rows = [
        ["⊕", table_dict.get("Positive", 0)],
        ["⊙", table_dict.get("Neutral", 0)],
        ["⊖", table_dict.get("Negative", 0)],
    ]

    # Build HTML table
    html = """
    <style>
        table.custom-table {
            border-collapse: collapse;
            width: 100%;
            font-family: sans-serif;
        }
        table.custom-table th, table.custom-table td {
            border: 1px solid #ddd;
            padding: 6px;
            vertical-align: middle;
        }
    </style>
    <table class="custom-table">
        <tr>
            <th>Stance</th>
            <th>Count</th>
        </tr>
    """

    # Max value for scaling
    max_count = max(row[1] for row in rows)

    # Helper to create bar cell with label inside
    def bar_cell(value, max_value):
        if value is None:
            return ""
        width_pct = (value / (max_value + 1)) * 100
        return f"""
        <div style='width: 100%; background: #e9ecef; height: 24px; border-radius: 4px; position: relative; overflow: hidden;'>
            <div style='width: {width_pct:.1f}%; background: #007bff; height: 100%; border-radius: 4px; text-align: right; padding-right: 4px; color: white; font-size: 12px; line-height: 24px;'>
                {value}
            </div>
        </div>
        """

    for row in rows:
        stance, count = row
        html += "<tr>"
        html += f"<td>{stance}</td>"
        html += f"<td>{bar_cell(count, max_count)}</td>"
        html += "</tr>"

    html += "</table>"
    return html, table_dict


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
            {"<b>State:</b> " + row['State'] + "<br>" if row['State'] is not None and not pd.isna(row['State']) else ""}
            {"<b>City:</b> " + row['City'] + "<br>" if row['City'] is not None and not pd.isna(row['City']) else ""}
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


if __name__ == "__main__":
    # Example usage
    # stance_df = get_election_data()
    # print(stance_df.head())
    # politifact_df = get_politifact_data()
    # print(politifact_df.head())
    # category2claim = get_category2claim(stance_df)
    # print(category2claim)
    # categories = get_politifact_categories()
    # print(categories)

    # taxonomy = get_taxonomy()
    # print(taxonomy)

    tweets = get_claim_related_tweets(
        "A video shows woman exiting her car during the 2025 Los Angeles protests, shouting, “I have babies in the car!”"
    )
    print(tweets)

    # for tweet in tweets:
    #     user_geo = None
    #     if tweet["user_profile"]["location"]:
    #         user_geo = infer_user_location(tweet["user_profile"]["location"])
    #     print("User Geo:", user_geo)
