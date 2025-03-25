import json
import pandas as pd
from random import random
from geopy.geocoders import Nominatim


def create_us_stance():
    # read the json file
    with open("./data/tweets_latest.json", "r") as f:
        data = json.load(f)
        tweet_list = data["San Bernardino"]
        tweet_text_list = [tweet[1] for tweet in tweet_list]
        print(tweet_list)

    # read the us_cities.csv file
    cities = pd.read_csv("./data/us_cities.csv")
    # assign tweet with random tweet in the tweet_list
    cities["tweet"] = [
        tweet_text_list[int(random() * len(tweet_text_list))]
        for i in range(len(cities))
    ]
    cities["time created"] = [
        tweet_list[i % len(tweet_list)][2] for i in range(len(cities))
    ]

    cities.to_csv("./data/us_stance.csv", index=False)


def clean_us_stance():
    # read the us_stance.csv file
    df = pd.read_csv("./data/2024_election_stance.csv")
    pass


def update_stance_value():
    # read the us_stance.csv file
    df = pd.read_csv("./data/_2024_election_stance.csv")
    # ensure the 'Stance' column contains integers
    df["Stance"] = df["Stance"].astype(str)
    # mapping the stance value from 0 to positive, from 1 to neutral and 2 to negative
    for i, row in df.iterrows():
        if row["Stance"] == "0":
            df.at[i, "Stance"] = "Positive"
        elif row["Stance"] == "1":
            df.at[i, "Stance"] = "Neutral"
        else:
            df.at[i, "Stance"] = "Negative"

    df.to_csv("./data/2024_election_stance.csv", index=False)


def get_politifact_categories():
    # read the politifact.csv file
    df = pd.read_csv("./data/politifact.csv")
    # get the unique categories
    category_column = df["Tags"].unique()
    categories = set()
    for category in category_column:
        if pd.isna(category):
            continue
        for c in category.split(","):
            c = c.strip()
            categories.add(c)

    print(categories)
    print(len(categories))
    # save the categories as json
    with open("./data/politifact_categories.json", "w") as f:
        json.dump(list(categories), f, indent=4)


def get_politifact_categories_first_only():
    # read the politifact.csv file
    df = pd.read_csv("./data/politifact.csv")
    # get the unique categories
    category_column = df["Tags"].unique()
    categories = set()
    for category in category_column:
        if pd.isna(category):
            continue
        for c in category.split(","):
            c = c.strip()
            categories.add(c)
            break

    print(categories)
    print(len(categories))
    # save the categories as json
    with open("./data/politifact_categories_first_only.json", "w") as f:
        json.dump(list(categories), f, indent=4)


def test_geo():
    geolocator = Nominatim(user_agent="geoapi")
    location = geolocator.geocode("USA")
    if location:
        print((location.latitude, location.longitude))
    else:
        print("Location not found")


if __name__ == "__main__":
    # create_us_stance()
    # update_stance_value()
    # clean_us_stance()
    # get_politifact_categories_first_only()
    test_geo()
