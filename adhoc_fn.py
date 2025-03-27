import json
import pandas as pd
from random import random
from geopy.geocoders import Nominatim
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from time import sleep
from collections import *
from matplotlib import pyplot as plt
import plotly.express as px
from constants import MANUAL_CLAIM_KEYWORDS

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
    df = pd.read_csv("./data/2024_election_stance_v2.csv")
    for i, row in tqdm(df.iterrows(), total=len(df)):
        keywords = MANUAL_CLAIM_KEYWORDS[row["Claim"]]
        # if the keywords are not all in the tweet, remove the row
        if not all([keyword.lower() in row["Tweet"].lower() for keyword in keywords.split()]):
            df.drop(i, inplace=True)
    # update the Category column from Election to ['Elections']
    df["Category"] = "['Elections']"
    # add a verdict column, set to FALSE
    df["Verdict"] = "FALSE"
    print('final df:', len(df))
    df.to_csv("./data/2024_election_stance_v2_cleaned.csv", index=False)
    


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


def get_geo(place):
    geolocator = Nominatim(user_agent="geoapi")
    location = geolocator.geocode(place, addressdetails=True, timeout=5)
    if location:
        return location.address, location.latitude, location.longitude
    return None, None, None

def add_state_geo():
    # read the us_cities.csv file
    df = pd.read_csv("./data/2024_election_stance.csv")
    print(df.columns) # Index(['Unnamed: 0', 'City', 'Claim', 'Tweet', 'Latitude', 'Longitude', 'User', 'Timestamp', 'Stance', 'Category'],
    # add a new column for state using the city and get_geo
    # get unique value of city
    cities = {'San Bernardino': ('San Bernardino County, California, United States', 34.8253019, -116.0833144), 'Bridgeport': ('Bridgeport, Greater Bridgeport Planning Region, Connecticut, United States', 41.1792695, -73.1887863), 'Rochester': ('City of Rochester, Monroe County, New York, United States', 43.157285, -77.615214), 'St. Paul': ('Saint Paul, Ramsey County, Minnesota, United States', 44.9497487, -93.0931028), 'Billings': ('Billings, Yellowstone County, Montana, United States', 45.7874957, -108.49607), 'Great Falls': ('Great Falls, Cascade County, Montana, United States', 47.5048851, -111.29189), 'Missoula': ('Missoula, Missoula County, Montana, United States', 46.8701049, -113.995267), 'Minot': ("Minot, Montbard, Côte-d'Or, Bourgogne-Franche-Comté, France métropolitaine, 21510, France", 47.6698594, 4.8786165), 'Fargo': ('Fargo, Cass County, North Dakota, United States', 46.877229, -96.789821), 'Hilo': ('Hilo, Hawaiʻi County, Hawaii, 96720, United States', 19.7073734, -155.08158), 'Olympia': ('Ολυμπία, ΕΟ74, Αρχαία Ολυμπία, Δημοτική Ενότητα Αρχαίας Ολυμπίας, Δήμος Αρχαίας Ολυμπίας, Περιφερειακή Ενότητα Ηλείας, Περιφέρεια Δυτικής Ελλάδας, Αποκεντρωμένη Διοίκηση Πελοποννήσου, Δυτικής Ελλάδας και Ιονίου, 270 65, Ελλάς', 37.638250299999996, 21.630566024011667), 'Spokane': ('Spokane, Spokane County, Washington, United States', 47.6571934, -117.42351), 'Vancouver': ('Vancouver, Metro Vancouver Regional District, British Columbia, Canada', 49.2608724, -123.113952), 'Flagstaff': ('Flagstaff, Coconino County, Arizona, United States', 35.1987522, -111.651822), 'Tucson': ('Tucson, Pima County, Arizona, United States', 32.2228765, -110.974847), 'Santa Barbara': ('Santa Barbara, Santa Barbara County, California, United States', 34.4221319, -119.702667), 'Fresno': ('Fresno, Fresno County, California, United States', 36.7394421, -119.78483), 'Eureka': ('Eureka, Humboldt County, California, United States', 40.7906871, -124.1673746), 'Colorado Springs': ('Colorado Springs, El Paso County, Colorado, United States', 38.8339578, -104.825348), 'Reno': ('Reno, Washoe County, Nevada, United States', 39.5261206, -119.8126581), 'Elko': ('Elko County, Nevada, United States', 41.1958128, -115.3272864), 'Albuquerque': ('Albuquerque, Bernalillo County, New Mexico, United States', 35.0841034, -106.650985), 'Salem': ('Salem, Marion County, Oregon, United States', 44.9391565, -123.033121), 'Casper': ('Casper, Natrona County, Wyoming, United States', 42.8501191, -106.325138), 'Topeka': ('Topeka, Shawnee County, Kansas, United States', 39.049011, -95.677556), 'Kansas City': ('Kansas City, Jackson County, Missouri, United States', 39.100105, -94.5781416), 'Tulsa': ('Tulsa, Tulsa County, Oklahoma, United States', 36.1563122, -95.9927516), 'Sioux Falls': ('Sioux Falls, Sioux Falls Township, Minnehaha County, South Dakota, United States', 43.5476008, -96.7293629), 'Shreveport': ('Shreveport, Caddo Parish, Louisiana, United States', 32.5135356, -93.7477839), 'Baton Rouge': ('Baton Rouge, East Baton Rouge Parish, Louisiana, United States', 30.4494155, -91.1869659), 'Ft. Worth': ('Fort Worth, Tarrant County, Texas, United States', 32.753177, -97.3327459), 'Corpus Christi': ('Corpus Christi, Nueces County, Texas, United States', 27.7635302, -97.4033191), 'Austin': ('Austin, Travis County, Texas, United States', 30.2711286, -97.7436995), 'Amarillo': ('Amarillo, Potter County, Texas, United States', 35.20729, -101.8371192), 'El Paso': ('El Paso, El Paso County, Texas, United States', 31.7601164, -106.4870404), 'Laredo': ('Laredo, Webb County, Texas, United States', 27.5075005, -99.5069922), 'Burlington': ('Burlington, Chittenden County, Vermont, United States', 44.4761601, -73.212906), 'Montgomery': ('Montgomery, Montgomery County, Alabama, United States', 32.37742, -86.3091683), 'Tallahassee': ('Tallahassee, Leon County, Florida, United States', 30.4380832, -84.2809332), 'Orlando': ('Orlando, Orange County, Florida, United States', 28.5421109, -81.3790304), 'Jacksonville': ('Jacksonville, Duval County, Florida, United States', 30.3321838, -81.655651), 'Savannah': ('Savannah, Chatham County, Georgia, United States', 32.0790074, -81.0921335), 'Columbia': ('South Carolina, US', 4.099917, -72.9088133), 'Indianapolis': ('Indianapolis, Marion County, Indiana, United States', 39.7683331, -86.1583502), 'Wilmington': ('Wilmington, New Castle County, Delaware, United States', 39.7459468, -75.546589), 'Knoxville': ('Knoxville, Knox County, East Tennessee, Tennessee, United States', 35.9603948, -83.9210261), 'Richmond': ('Richmond, Virginia, United States', 37.5385087, -77.43428), 'Charleston': ('Charleston, Charleston County, South Carolina, United States', 32.7884363, -79.9399309), 'Baltimore': ('Baltimore, Maryland, United States', 39.2908816, -76.610759), 'Syracuse': ('City of Syracuse, Onondaga County, New York, United States', 43.0481221, -76.1474244), 'Augusta': ('Augusta, Richmond County, Georgia, United States', 33.4709714, -81.9748429), 'Sault Ste. Marie': ('Sault Ste. Marie, Algoma District, Northeastern Ontario, Ontario, Canada', 46.5126554, -84.3330301), 'Sitka': ('Sitka, Alaska, 99835, United States', 57.4086082, -135.4596206), 'Helena': ('Helena, Lewis and Clark County, Montana, United States', 46.5927425, -112.036277), 'Bismarck': ('Bismarck, Burleigh County, North Dakota, United States', 46.808327, -100.783739), 'Boise': ('Boise, Ada County, Idaho, United States', 43.6166163, -116.200886), 'San Jose': ('San Jose, Santa Clara County, California, United States', 37.3361663, -121.890591), 'Sacramento': ('Sacramento, Sacramento County, California, United States', 38.5810606, -121.493895), 'Las Vegas': ('Las Vegas, Clark County, Nevada, United States', 36.2533896, -115.2794366262601), 'Santa Fe': ('Santa Fe, Argentina', -30.3154739, -61.1645076), 'Portland': ('Portland, Multnomah County, Oregon, United States', 45.5202471, -122.674194), 'Salt Lake City': ('Salt Lake City, Salt Lake County, Utah, United States', 40.7596198, -111.886797), 'Cheyenne': ('Cheyenne, Laramie County, Wyoming, United States', 41.139981, -104.820246), 'Des Moines': ('Des Moines, Polk County, Iowa, United States', 41.5868654, -93.6249494), 'Omaha': ('Omaha, Douglas County, Nebraska, United States', 41.2587459, -95.9383758), 'Oklahoma City': ('Oklahoma City, Oklahoma County, Oklahoma, United States', 35.4729886, -97.5170536), 'Pierre': ('Pierre, Hughes County, South Dakota, 57501, United States', 44.3683644, -100.351136), 'San Antonio': ('San Antonio, Bexar County, Texas, United States', 29.4246002, -98.4951405), 'Jackson': ('Jackson, Hinds County, Mississippi, United States', 32.2998686, -90.1830408), 'Raleigh': ('Raleigh, Wake County, North Carolina, United States', 35.7803977, -78.6390989), 'Cleveland': ('Cleveland, Cuyahoga County, Ohio, United States', 41.4996574, -81.6936772), 'Cincinnati': ('Cincinnati, Hamilton County, Ohio, United States', 39.1014537, -84.5124602), 'Nashville': ('Nashville, Davidson County, Middle Tennessee, Tennessee, United States', 36.1622767, -86.7742984), 'Memphis': ('Memphis, Shelby County, West Tennessee, Tennessee, United States', 35.1460249, -90.0517638), 'Norfolk': ('Norfolk, England, United Kingdom', 52.666667, 1.0), 'Milwaukee': ('Milwaukee, Milwaukee County, Wisconsin, United States', 43.0386475, -87.9090751), 'Buffalo': ('Buffalo, Erie County, New York, United States', 42.8867166, -78.8783922), 'Pittsburgh': ('Pittsburgh, Allegheny County, Pennsylvania, United States', 40.4416941, -79.9900861), 'Kodiak': ('Kodiak, Kodiak Island Borough, Alaska, United States', 57.7901661, -152.4067073), 'Cold Bay': ('Cold Bay, Aleutians East Borough, Alaska, 99571, United States', 55.2071632, -162.7146533), 'Bethel': ('Bethel, Unorganized Borough, Alaska, 99559, United States', 60.7922222, -161.755833), 'Barrow': ('Barrow, Westmorland and Furness, England, United Kingdom', 54.1007661, -3.2087523941640113), 'Nome': ('Nome, Unorganized Borough, Alaska, United States', 64.4975098, -165.4061701), 'Valdez': ('Valdez, Unorganized Borough, Alaska, 99686, United States', 61.1299396, -146.349363), 'Juneau': ('Juneau, Alaska, United States', 58.3019496, -134.419734), 'Fairbanks': ('Fairbanks, Fairbanks North Star Borough, Alaska, United States', 64.837845, -147.716675), 'Prudhoe Bay': ('Prudhoe Bay, Alaska, 99734, United States', 70.326677, -148.94325269685487), 'Minneapolis': ('Minneapolis, Hennepin County, Minnesota, United States', 44.9772995, -93.2654692), 'Honolulu': ('Honolulu, Honolulu County, Hawaii, United States', 21.304547, -157.855676), 'Seattle': ('Seattle, King County, Washington, United States', 47.6038321, -122.330062), 'Phoenix': ('Phoenix, Maricopa County, Arizona, United States', 33.4484367, -112.074141), 'San Diego': ('San Diego, San Diego County, California, United States', 32.7174202, -117.162772), 'St. Louis': ('Saint Louis, Missouri, United States', 38.6280278, -90.1910154), 'New Orleans': ('New Orleans, Orleans Parish, Louisiana, United States', 29.9759983, -90.0782127), 'Dallas': ('Dallas, Dallas County, Texas, United States', 32.7762719, -96.7968559), 'Boston': ('Boston, Suffolk County, Massachusetts, United States', 42.3554334, -71.060511), 'Tampa': ('Tampa, Hillsborough County, Florida, United States', 27.9477595, -82.458444), 'Philadelphia': ('Philadelphia, Philadelphia County, Pennsylvania, United States', 39.9527237, -75.1635262), 'Detroit': ('Detroit, Wayne County, Michigan, United States', 42.3315509, -83.0466403), 'Anchorage': ('Anchorage, Alaska, United States', 61.2163129, -149.894852), 'San Francisco': ('San Francisco, California, United States', 37.7792588, -122.4193286), 'Denver': ('Denver, Colorado, United States', 39.7392364, -104.984862), 'Houston': ('Houston, Harris County, Texas, United States', 29.7589382, -95.3676974), 'Miami': ('Miami, Miami-Dade County, Florida, United States', 25.7741728, -80.19362), 'Atlanta': ('Atlanta, Fulton County, Georgia, United States', 33.7489924, -84.3902644), 'Chicago': ('Chicago, Cook County, Illinois, United States', 41.8755616, -87.6244212), 'Los Angeles': ('Los Angeles, Los Angeles County, California, United States', 34.0536909, -118.242766), 'Washington D.C.': ('Washington, Maryland, United States', 38.8950368, -77.0365427), 'New York': ('City of New York, New York, United States', 40.7127281, -74.0060152)}
    
    state = []
    for city in tqdm(df["City"]):
        state.append(cities[city][0].split(",")[-2].strip())
    df["State"] = state
    df.to_csv("./data/2024_election_stance_v2.csv", index=False)


def test_sentence_similarity(s1, s2):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print(s1, s2)
    e1 = model.encode(s1)
    e2 = model.encode(s2)
    sim = model.similarity(e1, e2)
    return sim


def add_verdict_to_raw():
    # load factual claims from politifact.csv
    with open("./data/politifact.csv", "r") as f:
        politifact_data = pd.read_csv(f)
        print(politifact_data.columns)
        claim2verdict = {}
        for i, row in politifact_data.iterrows():
            claim2verdict[row["Claim"]] = row["Verdict"]
    print(len(claim2verdict))
    for k, v in claim2verdict.items():
        print(k, v)
        break
        
    # load tweets_latest_2025_mar_v2.json
    with open("./data/tweets_latest_2025_mar_v2_local.json", "r") as f:
        data = json.load(f)
        print(len(data))
        # add verdict toe each object
        for claim_tweet_pair in data:
            claim = claim_tweet_pair["claim"]
            if claim in claim2verdict:
                claim_tweet_pair["verdict"] = claim2verdict[claim]
            else:
                print(claim)
                claim_tweet_pair["verdict"] = "Unknown"
        print(data[0])
    # save the data to a new json file
    with open("./data/tweets_latest_2025_mar_v2_local_with_verdict.json", "w") as f:
        json.dump(data, f, indent=4)


def add_location_to_raw():
    locations = set()
    # load tweets_latest_2025_mar_v2_local_with_verdict.json
    with open("./data/tweets_latest_2025_mar_v2_local_with_verdict.json", "r") as f:
        data = json.load(f)
        for claim_tweet_pair in data:
            location = claim_tweet_pair["tweet_user"]['location']
            locations.add(location)
    
    location2geo = {}
    for location in tqdm(locations):
        sleep(1.5)
        if location == '':
            continue
        try:
            address, lat, long = get_geo(location)
        except Exception as e:
            print(e)
            continue
        if address == None:
            continue
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

        if country == "United States":
            print(f'{location} -> {address} | {state} | {county} | {city} | {lat} | {long}')
            location2geo[location] = {
                "state": state,
                "county": county,
                "city": city,
                "lat": lat,
                "long": long
            }
    print(location2geo)
    # # save the data to a new json file
    # with open("./data/tweets_latest_2025_mar_v2_local_with_verdict_location.json", "w") as f:
    #     json.dump(data, f, indent=4)
        
        
def metric_calculation(TP, FN, FP, TN):
    """
    Calculate the precision, recall, F1-score, and accuracy
    """
    precision = TP / (TP + FP) if TP + FP != 0 else 0
    recall = TP / (TP + FN) if TP + FN != 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall != 0 else 0

    precision_false = TN / (TN + FN) if TN + FN != 0 else 0
    recall_false = TN / (TN + FP) if TN + FP != 0 else 0
    f1_false = 2 * precision_false * recall_false / (precision_false + recall_false) if precision_false + recall_false != 0 else 0

    macro_f1 = (f1 + f1_false) / 2
    
    true_accuracy = TP / (TP + FN) if TP + FN != 0 else 0
    false_accuracy = TN / (TN + FP) if TN + FP != 0 else 0
    accuracy = (true_accuracy + false_accuracy) / 2

    return round(accuracy, 3), round(macro_f1, 3)


def macro_statistics():
    """
    'Public Health': 9325
    'Elections': 7360
    'Immigration': 6075
    'Economy': 4643,
    'Abortion': 4204
    'Federal Budget': 2624
    'Education': 2570
    'Climate Change': 1844
    """
    df = pd.read_csv("./data/stancemap_eval.csv")
    # election_df = pd.read_csv("./data/2024_election_stance_v2.csv")
    print(df.columns) # 'City', 'Claim', 'Tweet', 'Latitude', 'Longitude', 'User', 'Timestamp', 'Stance', 'Category', 'State', 'Verdict']
    # print(election_df.columns)
    
    # print the number of unique verdict
    print(df["Verdict"].unique())

    cnt = defaultdict(lambda: [0,0,0,0,0,0])
    for i, row in df.iterrows():
        category = row["Category"]
        category = eval(category)
        if len(category) > 0:
            category = category[0]
        else:
            continue
        verdict = row["Verdict"].lower()
        if verdict in ('full-flop', 'half-flip'):
            continue
        verdict = 'True' if verdict in ('true', 'mostly-true', 'half-true') else 'False'
        stance = row["Stance"]
        if verdict == "True" and stance == 0:
            cnt[category][0] += 1
        elif verdict == "True" and stance == 2:
            cnt[category][1] += 1
        elif verdict == "False" and stance == 0:
            cnt[category][2] += 1
        elif verdict == "False" and stance == 2:
            cnt[category][3] += 1
        
    for k, v in cnt.items():
        tp, fn, fp, tn = v[0], v[1], v[2], v[3]
        acc, f1 = metric_calculation(tp, fn, fp, tn)
        cnt[k][4] = acc
        cnt[k][5] = f1
    # sort the dictionary by the sum of the values
    cnt = dict(sorted(cnt.items(), key=lambda x: sum(x[1]), reverse=True))
    # print top 20 items
    for k, v in list(cnt.items())[:20]:
        print(k, v)

    state_cnt = defaultdict(lambda: [0,0,0,0, 0, 0])
    for i, row in df.iterrows():
        state = row["State"]
        verdict = row["Verdict"].lower()
        if verdict in ('full-flop', 'half-flip'):
            continue
        verdict = 'True' if verdict in ('true', 'mostly true', 'half true') else 'False'
        stance = row["Stance"]
        if verdict == "True" and stance == 0:
            state_cnt[state][0] += 1
        elif verdict == "True" and stance == 2:
            state_cnt[state][1] += 1
        elif verdict == "False" and stance == 0:
            state_cnt[state][2] += 1
        elif verdict == "False" and stance == 2:
            state_cnt[state][3] += 1
    for k, v in state_cnt.items():
        tp, fn, fp, tn = v[0], v[1], v[2], v[3]
        acc, f1 = metric_calculation(tp, fn, fp, tn)
        state_cnt[k][4] = acc
        state_cnt[k][5] = f1
    # sort the dictionary by the sum of the values
    state_cnt = dict(sorted(state_cnt.items(), key=lambda x: sum(x[1]), reverse=True))
    # print top 20 items
    for k, v in list(state_cnt.items())[:20]:
        print(k, v)
    

def macro_statistics():
    df = pd.read_csv("./data/stancemap_eval.csv")
    cnt = {
        'Truth-$\oplus$': 0,
        'Misi-$\oplus$': 0,
        'Truth-$\odot$': 0,
        'Misi-$\odot$': 0,
        'Truth-$\ominus$': 0,
        'Misi-$\ominus$': 0
    }
    for i, row in df.iterrows():
        verdict = row["Verdict"].lower()
        if verdict in ('full-flop', 'half-flip'):
            continue
        verdict = 'True' if verdict in ('true', 'mostly-true', 'half-true') else 'False'
        stance = row["Stance"]
        if stance == 0:
            if verdict == "True":
                cnt['Truth-$\oplus$'] += 1
            else:
                cnt['Misi-$\oplus$'] += 1
        elif stance == 1:
            if verdict == "True":
                cnt['Truth-$\odot$'] += 1
            else:
                cnt['Misi-$\odot$'] += 1
        elif stance == 2:
            if verdict == "True":
                cnt['Truth-$\ominus$'] += 1
            else:
                cnt['Misi-$\ominus$'] += 1
    for k, v in cnt.items():
        print(k, v)
    # print the percentage
    total = sum(cnt.values())
    for k, v in cnt.items():
        print(k, v / total)

    # draw a bar chart
    colors = ['green', 'green', 'orange', 'orange', 'red', 'red']
    plt.figure(figsize=(12, 6))  # Increase the resolution by setting the figure size
    plt.bar(cnt.keys(), cnt.values(), color=colors)
    plt.show()

def us_stance_heatmap():
    full2abbr = {
        "Alabama": "AL",
        "Alaska": "AK",
        "Arizona": "AZ",
        "Arkansas": "AR",
        "California": "CA",
        "Colorado": "CO",
        "Connecticut": "CT",
        "Delaware": "DE",
        "Florida": "FL",
        "Georgia": "GA",
        "Hawaii": "HI",
        "Idaho": "ID",
        "Illinois": "IL",
        "Indiana": "IN",
        "Iowa": "IA",
        "Kansas": "KS",
        "Kentucky": "KY",
        "Louisiana": "LA",
        "Maine": "ME",
        "Maryland": "MD",
        "Massachusetts": "MA",
        "Michigan": "MI",
        "Minnesota": "MN",
        "Mississippi": "MS",
        "Missouri": "MO",
        "Montana": "MT",
        "Nebraska": "NE",
        "Nevada": "NV",
        "New Hampshire": "NH",
        "New Jersey": "NJ",
        "New Mexico": "NM",
        "New York": "NY",
        "North Carolina": "NC",
        "North Dakota": "ND",
        "Ohio": "OH",
        "Oklahoma": "OK",
        "Oregon": "OR",
        "Pennsylvania": "PA",
        "Rhode Island": "RI",
        "South Carolina": "SC",
        "South Dakota": "SD",
        "Tennessee": "TN",
        "Texas": "TX",
        "Utah": "UT",
        "Vermont": "VT",
        "Virginia": "VA",
        "Washington": "WA",
        "West Virginia": "WV",
        "Wisconsin": "WI",
        "Wyoming": "WY"
    }
        
    df = pd.read_csv("./data/stancemap_eval.csv")
    state_cnt = Counter()
    for i, row in df.iterrows():
        state = row["State"]
        if state not in full2abbr:
            continue
        state = full2abbr[state]
        state_cnt[state] += 1
    # draw a us map and color the states based on the number of tweets
    print(state_cnt)
    state_df = pd.DataFrame(state_cnt.items(), columns=["state", "count"])
    
    # Plotly expects state codes (e.g., "CA", "TX")
    fig = px.choropleth(
        state_df,
        locations="state",           # column with state abbreviations
        locationmode="USA-states",   # tells plotly these are state codes
        color="count",               # column with data to color by
        scope="usa",                 # limit map to US
        color_continuous_scale="Reds",
        title="Tweet Count by State"
    )

    fig.show()
    
def dataset_statistics():
    df1 = pd.read_csv("./data/2024_election_stance_v2_cleaned.csv")
    df2 = pd.read_csv("./data/stancemap_eval.csv")
    # concatenate the two dataframes
    df = pd.concat([df1, df2])
    print(f'df length: {len(df)}')
    # unique claim
    print(f'unique claim: {len(df["Claim"].unique())}')
    # find all the rows that State is not "None"
    df_with_state = df[df["State"] != "None"]
    print(f'df with state: {len(df_with_state)}')


    



if __name__ == "__main__":
    # add_verdict_to_raw()
    # add_location_to_raw()
    # micro_statistics()
    # macro_statistics()
    # us_stance_heatmap()
    # clean_us_stance()

    dataset_statistics()
    



    # update_stance_value()
    # get_politifact_categories_first_only()
    # print(get_geo("CA "))
    # add_state_geo()

#     print(test_sentence_similarity(
#         """The Trump assassination attempts were staged""", 
#         """
#         FACT CHECK: trump just said they didn't find a single gun, not one gun was fired on January 6th.

# Another blatant lie.
# https://t.co/DFJplKwPWQ https://t.co/SaiPO5g7rU
#         """))

# """
# 0.3465
# BREAKING: A group of illegal migrants in San Diego County, California tried to hijack TWO school buses full of Elementary &amp; Middle school kids from the Jamul-Dulzura Union District on Highway 94

# Border Czar Kamala is RESPONSIBLE

# The District issued a WARNING to all drivers and https://t.co/lP7MNOYlu7
# ---
# 0.3363
# And here it is,
# The Border State of Arizona CONFIRMS the US invasion,
# 10,000 illegals using the same exact SS number voted in the Nov 3, 2020 election with 420,987 mail in ballots to have NO SIGNATURE match. JUST IN MARICOPA COUNTY. Damn right the State of Texas has standing
# """
