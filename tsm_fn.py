# Truthfulness Stance Map Functions
import streamlit as st
import pandas as pd
import json
import numpy as np


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
    stance_df["Latitude"] = stance_df["Latitude"] + np.random.normal(0, 0.2, len(stance_df))
    stance_df["Longitude"] = stance_df["Longitude"] + np.random.normal(0, 0.2, len(stance_df))
    return stance_df


@st.cache_data(ttl=3 * 60 * 60)
def get_politifact_data():
    # Load the data
    politifact_csv = "./data/stancemap_eval.csv"
    politifact_df = pd.read_csv(politifact_csv)
    # drop the rows with 'None' in the 'State' column
    politifact_df = politifact_df[politifact_df["State"] != "None"]
    # update Stance column, 0 to Positive, 1 to Neutral, 2 to Negative
    politifact_df["Stance"] = politifact_df["Stance"].replace({0: "Positive", 1: "Neutral", 2: "Negative"})
    # add jitter to the latitude and longitude
    politifact_df["Latitude"] = politifact_df["Latitude"] + np.random.normal(0, 0.2, len(politifact_df))
    politifact_df["Longitude"] = politifact_df["Longitude"] + np.random.normal(0, 0.2, len(politifact_df))
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
    categories = set()
    for i in range(len(category_col)):
        category_row = eval(category_col[i])
        for c in category_row:
            if c:
                categories.add(c)        
    return list(categories)


def get_selected_stance(start_stance, end_stance):
    if start_stance == "Negative" and end_stance == "Positive":
        selected_stance = ["Negative", "Neutral/No Stance", "Positive"]
    elif start_stance == "Neutral/No Stance" and end_stance == "Positive":
        selected_stance = ["Neutral/No Stance", "Positive"]
    elif start_stance == "Negative" and end_stance == "Neutral/No Stance":
        selected_stance = ["Negative", "Neutral/No Stance"]
    elif start_stance == "Negative" and end_stance == "Negative":
        selected_stance = ["Negative"]
    elif start_stance == "Neutral/No Stance" and end_stance == "Neutral/No Stance":
        selected_stance = ["Neutral/No Stance"]
    elif start_stance == "Positive" and end_stance == "Positive":
        selected_stance = ["Positive"]
    else:
        selected_stance = ["Negative", "Neutral/No Stance", "Positive"]
    return selected_stance