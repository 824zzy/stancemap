# Truthfulness Stance Map Functions
import streamlit as st
import pandas as pd
import json
import numpy as np
from collections import Counter
from constants import US_STATES_COORDS
import spacy
from credentials import (
    CONSUMER_KEY,
    CONSUMER_SECRET,
    ACCESS_TOKEN,
    ACCESS_SECRET,
    BEARER_TOKEN,
)
import tweepy
from geopy.geocoders import Nominatim
import datetime

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
    print(taxonomy_df.head())
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
    for token in doc:
        if token.pos_ == "NOUN" or token.pos_ == "PROPN" or token.pos_ == "VERB":
            keywords.add(token.text)
    keywords = list(keywords)
    query = " ".join(keywords) + " is:verified"
    # Load the Twitter client using tweepy
    client = tweepy.Client(
        bearer_token=BEARER_TOKEN,
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_SECRET,
    )
    print(f"Searching for tweets related to the claim: {claim}")
    # Search for tweets related to the claim
    tweets = client.search_recent_tweets(
        query=query,
        max_results=10,
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
        }
        # Add user profile info
        user_profile = users.get(tweet.author_id)
        print(f"User Profile: {user_profile}")
        if user_profile:
            tweet_info["user_profile"] = {
                "username": user_profile.username,
                "name": user_profile.name,
                "location": getattr(user_profile, "location", None),
                "profile_image_url": getattr(user_profile, "profile_image_url", None),
                "description": getattr(user_profile, "description", None),
            }
            if tweet_info["user_profile"]["location"]:
                # Infer user location if available
                city, county, state, latitude, longitude = infer_user_location(
                    tweet_info["user_profile"]["location"]
                )
                tweet_info["user_profile"]["inferred_location"] = {
                    "city": city,
                    "county": county,
                    "state": state,
                    "latitude": latitude,
                    "longitude": longitude,
                }
        # Add place info if available
        if tweet.geo and hasattr(tweet.geo, "place_id"):
            place = client.get_place(place_id=tweet.geo.place_id)
            if place.data:
                tweet_info["place"] = place.data
        tweet_data.append(tweet_info)
    return tweet_data


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

    # tweets = get_claim_related_tweets("Biden is the best president in US history")
    tweets = [
        {
            "id": 1933701786055196888,
            "text": "RT @WesternDecline_: @SenAdamSchiff Biden pardoned the most amount of people out of any President in all of US history.\n\nLet that sink in.",
            "created_at": datetime.datetime(
                2025, 6, 14, 1, 43, 26, tzinfo=datetime.timezone.utc
            ),
            "author_id": 1599215772274159616,
            "geo": None,
            "user_profile": {
                "username": "Bev_Wasson",
                "name": "Beverly Wasson",
                "location": None,
                "profile_image_url": "https://pbs.twimg.com/profile_images/1629314117906628608/FGMvjcZi_normal.jpg",
                "description": "",
            },
        },
        {
            "id": 1933680090363080709,
            "text": "@AesPolitics1 Biden was THE worst president in US history.",
            "created_at": datetime.datetime(
                2025, 6, 14, 0, 17, 14, tzinfo=datetime.timezone.utc
            ),
            "author_id": 1312197301,
            "geo": None,
            "user_profile": {
                "username": "504CNM",
                "name": "504girl ⚜️",
                "location": "United States",
                "profile_image_url": "https://pbs.twimg.com/profile_images/1906011010520989696/6xNdwPIb_normal.jpg",
                "description": "🇺🇸❤️🇺🇸Love God ,my country, pro-life, 🇺🇸❤️🇺🇸 #MAGA Happily married💍 TS-@504girl🚫DM",
            },
        },
        {
            "id": 1933670187670384760,
            "text": "@cb_doge Fun Fact: Donald Trump will be the oldest President in all of US history by the end of his 2nd term, a few hundred days older than Joe Biden when he finished his term in 2025.",
            "created_at": datetime.datetime(
                2025, 6, 13, 23, 37, 53, tzinfo=datetime.timezone.utc
            ),
            "author_id": 1359631662636806146,
            "geo": None,
            "user_profile": {
                "username": "WesternDecline_",
                "name": "Western Decline",
                "location": None,
                "profile_image_url": "https://pbs.twimg.com/profile_images/1913161359958667264/DtTEkbO7_normal.jpg",
                "description": "Documenting the decline of Western civilization.",
            },
        },
        {
            "id": 1933668591661957210,
            "text": "@NotaRINO2025 @GavinNewsom Give me a break. You’d rather have a Manchurian candidate than an actual President. Joe Biden was the worst President in US history.",
            "created_at": datetime.datetime(
                2025, 6, 13, 23, 31, 32, tzinfo=datetime.timezone.utc
            ),
            "author_id": 1586083916967968768,
            "geo": None,
            "user_profile": {
                "username": "MichaelKeveryn",
                "name": "Storm Tracker",
                "location": "Florida ",
                "profile_image_url": "https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png",
                "description": "I'm a patriot. Maga, Husband, Father, Grandfather, and golfer. Trump must win this election or we will all be in a dystopian nightmare.",
            },
        },
        {
            "id": 1933659064732422495,
            "text": "@DisavowTrump20 Nope.  Biden will go down in history as the most corrupt president. The only president in US history to give out half a dozen pardons to family members. Preemptive pardons were issued to 6 family members. From January 1, 2014, through 01/20/25\n- Hunter Biden - his son, pardoned",
            "created_at": datetime.datetime(
                2025, 6, 13, 22, 53, 41, tzinfo=datetime.timezone.utc
            ),
            "author_id": 1380677392520376323,
            "geo": None,
            "user_profile": {
                "username": "WTFpeople2022",
                "name": "WTFPeople",
                "location": "Washington, DC",
                "profile_image_url": "https://pbs.twimg.com/profile_images/1531010046217404417/dxoOhYQf_normal.jpg",
                "description": "",
            },
        },
        {
            "id": 1933654971968610568,
            "text": "RT @WesternDecline_: @SenAdamSchiff Biden pardoned the most amount of people out of any President in all of US history.\n\nLet that sink in.",
            "created_at": datetime.datetime(
                2025, 6, 13, 22, 37, 25, tzinfo=datetime.timezone.utc
            ),
            "author_id": 1585931231316918273,
            "geo": None,
            "user_profile": {
                "username": "vobitaka",
                "name": "man in town",
                "location": "Cleveland, OH",
                "profile_image_url": "https://pbs.twimg.com/profile_images/1802107370606100480/2aeW3zyi_normal.jpg",
                "description": "",
            },
        },
        {
            "id": 1933654276108399021,
            "text": "@ChrisDJackson @JoeBiden So, lots of crooks and thieves take the train. Biden will go down in history as the most corrupt president. The only president in US history to give out half a dozen pardons to family members. Preemptive pardons were issued to 6 family members. From January 1, 2014, through",
            "created_at": datetime.datetime(
                2025, 6, 13, 22, 34, 39, tzinfo=datetime.timezone.utc
            ),
            "author_id": 1380677392520376323,
            "geo": None,
            "user_profile": {
                "username": "WTFpeople2022",
                "name": "WTFPeople",
                "location": "Washington, DC",
                "profile_image_url": "https://pbs.twimg.com/profile_images/1531010046217404417/dxoOhYQf_normal.jpg",
                "description": "",
            },
        },
        {
            "id": 1933653886021095682,
            "text": "@SenAdamSchiff Biden pardoned the most amount of people out of any President in all of US history.\n\nLet that sink in.",
            "created_at": datetime.datetime(
                2025, 6, 13, 22, 33, 6, tzinfo=datetime.timezone.utc
            ),
            "author_id": 1359631662636806146,
            "geo": None,
            "user_profile": {
                "username": "WesternDecline_",
                "name": "Western Decline",
                "location": None,
                "profile_image_url": "https://pbs.twimg.com/profile_images/1913161359958667264/DtTEkbO7_normal.jpg",
                "description": "Documenting the decline of Western civilization.",
            },
        },
        {
            "id": 1933644342884798871,
            "text": "@ttccai1 @_SmokeyGirl25 @PAYthe_PIPER @PaulMer53 @Hawkesbay69 @RockyMtMama1 @DragonSword778 @45johnmac @GilbertWanda @ArmandKleinX @DoraDallas6 @Zegdie @janninereid1 @PecanC8 @m86742 @ToniLL22 @PriamtheB @Lindaprentice16 @Ilegvm @NancyMar2022 @sxdoc @Donald_Army @emma6USA Biden’s presidency was the biggest scam in US history! I’m grateful for President Trump. \nThank you @ttccai1 ❤️❤️👑👑❤️❤️ https://t.co/EV5ZCXcaqB",
            "created_at": datetime.datetime(
                2025, 6, 13, 21, 55, 11, tzinfo=datetime.timezone.utc
            ),
            "author_id": 1392962413255970817,
            "geo": None,
            "user_profile": {
                "username": "x4Eileen",
                "name": "Eileen Bridget🌸",
                "location": None,
                "profile_image_url": "https://pbs.twimg.com/profile_images/1832473649720258560/YJDnhh9o_normal.jpg",
                "description": "RN BSN🌟Daughter of a Marine🌟 Veteran advocate 🌟Dont call it gun control, it’s civilian disarmament 2A 🌟ProLife🌟",
            },
        },
        {
            "id": 1933633786828439676,
            "text": "RT @Suzierizzo1: President Barack Obama is one of the Greatest Presidents in History and he warned us all along with President Biden what T…",
            "created_at": datetime.datetime(
                2025, 6, 13, 21, 13, 14, tzinfo=datetime.timezone.utc
            ),
            "author_id": 777349670179774464,
            "geo": None,
            "user_profile": {
                "username": "Trib3zz",
                "name": "Brian Falagan",
                "location": "San Diego, CA",
                "profile_image_url": "https://pbs.twimg.com/profile_images/1615645346427961344/uCDnZJWB_normal.jpg",
                "description": "Apparently I sound like @GstaAsim",
            },
        },
    ]
    for tweet in tweets:
        user_geo = None
        if tweet["user_profile"]["location"]:
            user_geo = infer_user_location(tweet["user_profile"]["location"])
        print("User Geo:", user_geo)
