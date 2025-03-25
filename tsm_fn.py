# Truthfulness Stance Map Functions
import streamlit as st
import pandas as pd
import json
import numpy as np


@st.cache_data(ttl=3 * 60 * 60)
def get_election_data():
    # Load the data
    stance_csv = "./data/2024_election_stance.csv"
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
    politifact_csv = "./data/politifact.csv"
    politifact_df = pd.read_csv(politifact_csv)
    # select first 100 rows
    # stance_df = stance_df.head(100)

    return politifact_df


@st.cache_data(ttl=3 * 60 * 60)
def get_politifact_categories():
    politifact_categories = json.load(open("data/politifact_categories.json"))
    return politifact_categories


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