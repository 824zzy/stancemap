import asyncio
from twikit import Client
from collections import defaultdict
import json
from retrying import retry
from time import sleep
from credentials import USERNAME, PASSWORD, EMAIL

# Initialize client
client = Client(
    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


async def main(politifact_keywords):
    await client.login(auth_info_1=USERNAME, auth_info_2=EMAIL, password=PASSWORD)
    # Define the location parameters
    city_geocodes = {
        "San Bernardino": {"latitude": 34.1083, "longitude": -117.2898},
        "Bridgeport": {"latitude": 41.1865, "longitude": -73.1952},
        "Rochester": {"latitude": 43.1566, "longitude": -77.6088},
        "St. Paul": {"latitude": 44.9537, "longitude": -93.0900},
        "Billings": {"latitude": 45.7833, "longitude": -108.5007},
        "Great Falls": {"latitude": 47.5053, "longitude": -111.3008},
        "Missoula": {"latitude": 46.8721, "longitude": -113.9940},
        "Minot": {"latitude": 48.2325, "longitude": -101.2963},
        "Fargo": {"latitude": 46.8772, "longitude": -96.7898},
        "Hilo": {"latitude": 19.7073, "longitude": -155.0814},
        "Olympia": {"latitude": 47.0379, "longitude": -122.9007},
        "Spokane": {"latitude": 47.6588, "longitude": -117.4260},
        "Vancouver": {"latitude": 45.6387, "longitude": -122.6615},
        "Flagstaff": {"latitude": 35.1983, "longitude": -111.6513},
        "Tucson": {"latitude": 32.2226, "longitude": -110.9747},
        "Santa Barbara": {"latitude": 34.4208, "longitude": -119.6982},
        "Fresno": {"latitude": 36.7378, "longitude": -119.7871},
        "Eureka": {"latitude": 40.8021, "longitude": -124.1637},
        "Colorado Springs": {"latitude": 38.8339, "longitude": -104.8214},
        "Reno": {"latitude": 39.5296, "longitude": -119.8138},
        "Elko": {"latitude": 40.8324, "longitude": -115.7631},
        "Albuquerque": {"latitude": 35.0844, "longitude": -106.6504},
        "Salem": {"latitude": 44.9429, "longitude": -123.0351},
        "Casper": {"latitude": 42.8501, "longitude": -106.3252},
        "Topeka": {"latitude": 39.0489, "longitude": -95.6780},
        "Kansas City": {"latitude": 39.0997, "longitude": -94.5786},
        "Tulsa": {"latitude": 36.1539, "longitude": -95.9928},
        "Sioux Falls": {"latitude": 43.5446, "longitude": -96.7311},
        "Shreveport": {"latitude": 32.5252, "longitude": -93.7502},
        "Baton Rouge": {"latitude": 30.4515, "longitude": -91.1871},
        "Ft. Worth": {"latitude": 32.7555, "longitude": -97.3308},
        "Corpus Christi": {"latitude": 27.8006, "longitude": -97.3964},
        "Austin": {"latitude": 30.2672, "longitude": -97.7431},
        "Amarillo": {"latitude": 35.2219, "longitude": -101.8313},
        "El Paso": {"latitude": 31.7619, "longitude": -106.4850},
        "Laredo": {"latitude": 27.5036, "longitude": -99.5075},
        "Burlington": {"latitude": 44.4759, "longitude": -73.2121},
        "Montgomery": {"latitude": 32.3792, "longitude": -86.3077},
        "Tallahassee": {"latitude": 30.4383, "longitude": -84.2807},
        "Orlando": {"latitude": 28.5383, "longitude": -81.3792},
        "Jacksonville": {"latitude": 30.3322, "longitude": -81.6557},
        "Savannah": {"latitude": 32.0809, "longitude": -81.0912},
        "Columbia": {"latitude": 34.0007, "longitude": -81.0348},
        "Indianapolis": {"latitude": 39.7684, "longitude": -86.1581},
        "Wilmington": {"latitude": 34.2257, "longitude": -77.9447},
        "Knoxville": {"latitude": 35.9606, "longitude": -83.9207},
        "Richmond": {"latitude": 37.5407, "longitude": -77.4360},
        "Charleston": {"latitude": 32.7765, "longitude": -79.9311},
        "Baltimore": {"latitude": 39.2904, "longitude": -76.6122},
        "Syracuse": {"latitude": 43.0481, "longitude": -76.1474},
        "Augusta": {"latitude": 44.3106, "longitude": -69.7795},
        "Sault Ste. Marie": {"latitude": 46.4953, "longitude": -84.3453},
        "Sitka": {"latitude": 57.0516, "longitude": -135.3319},
        "Helena": {"latitude": 46.5884, "longitude": -112.0245},
        "Bismarck": {"latitude": 46.8083, "longitude": -100.7837},
        "Boise": {"latitude": 43.6150, "longitude": -116.2023},
        "San Jose": {"latitude": 37.3382, "longitude": -121.8863},
        "Sacramento": {"latitude": 38.5816, "longitude": -121.4944},
        "Las Vegas": {"latitude": 36.1699, "longitude": -115.1398},
        "Santa Fe": {"latitude": 35.6870, "longitude": -105.9378},
        "Portland": {"latitude": 45.5051, "longitude": -122.6750},
        "Salt Lake City": {"latitude": 40.7608, "longitude": -111.8910},
        "Cheyenne": {"latitude": 41.1400, "longitude": -104.8202},
        "Des Moines": {"latitude": 41.5868, "longitude": -93.6250},
        "Omaha": {"latitude": 41.2565, "longitude": -95.9345},
        "Oklahoma City": {"latitude": 35.4676, "longitude": -97.5164},
        "Pierre": {"latitude": 44.3683, "longitude": -100.3510},
        "San Antonio": {"latitude": 29.4241, "longitude": -98.4936},
        "Jackson": {"latitude": 32.2988, "longitude": -90.1848},
        "Raleigh": {"latitude": 35.7796, "longitude": -78.6382},
        "Cleveland": {"latitude": 41.4993, "longitude": -81.6944},
        "Cincinnati": {"latitude": 39.1031, "longitude": -84.5120},
        "Nashville": {"latitude": 36.1627, "longitude": -86.7816},
        "Memphis": {"latitude": 35.1495, "longitude": -90.0490},
        "Norfolk": {"latitude": 36.8508, "longitude": -76.2859},
        "Milwaukee": {"latitude": 43.0389, "longitude": -87.9065},
        "Buffalo": {"latitude": 42.8864, "longitude": -78.8784},
        "Pittsburgh": {"latitude": 40.4406, "longitude": -79.9959},
        "Kodiak": {"latitude": 57.7900, "longitude": -152.4072},
        "Cold Bay": {"latitude": 55.2042, "longitude": -162.7213},
        "Bethel": {"latitude": 60.7922, "longitude": -161.7558},
        "Barrow": {"latitude": 71.2906, "longitude": -156.7886},
        "Nome": {"latitude": 64.5011, "longitude": -165.4064},
        "Valdez": {"latitude": 61.1308, "longitude": -146.3483},
        "Juneau": {"latitude": 58.3019, "longitude": -134.4197},
        "Fairbanks": {"latitude": 64.8378, "longitude": -147.7164},
        "Prudhoe Bay": {"latitude": 70.2553, "longitude": -148.3373},
        "Minneapolis": {"latitude": 44.9778, "longitude": -93.2650},
        "Honolulu": {"latitude": 21.3069, "longitude": -157.8583},
        "Seattle": {"latitude": 47.6062, "longitude": -122.3321},
        "Phoenix": {"latitude": 33.4484, "longitude": -112.0740},
        "San Diego": {"latitude": 32.7157, "longitude": -117.1611},
        "St. Louis": {"latitude": 38.6270, "longitude": -90.1994},
        "New Orleans": {"latitude": 29.9511, "longitude": -90.0715},
        "Dallas": {"latitude": 32.7767, "longitude": -96.7970},
        "Boston": {"latitude": 42.3601, "longitude": -71.0589},
        "Tampa": {"latitude": 27.9506, "longitude": -82.4572},
        "Philadelphia": {"latitude": 39.9526, "longitude": -75.1652},
        "Detroit": {"latitude": 42.3314, "longitude": -83.0458},
        "Anchorage": {"latitude": 61.2181, "longitude": -149.9003},
        "San Francisco": {"latitude": 37.7749, "longitude": -122.4194},
        "Denver": {"latitude": 39.7392, "longitude": -104.9903},
        "Houston": {"latitude": 29.7604, "longitude": -95.3698},
        "Miami": {"latitude": 25.7617, "longitude": -80.1918},
        "Atlanta": {"latitude": 33.7490, "longitude": -84.3880},
        "Chicago": {"latitude": 41.8781, "longitude": -87.6298},
        "Los Angeles": {"latitude": 34.0522, "longitude": -118.2437},
        "Washington D.C.": {"latitude": 38.9072, "longitude": -77.0369},
        "New York": {"latitude": 40.7128, "longitude": -74.0060},
    }
    dataset = defaultdict(list)
    cnt = 0
    for ct, geo in city_geocodes.items():
        lat, lon = geo["latitude"], geo["longitude"]
        for clm, kwd in politifact_keywords.items():
            query = f"{kwd} geocode:{lat},{lon},100km"
            try:
                tweets = await client.search_tweet(query, "Latest",)
            except Exception as e:
                print(f"Error: {e}")
                # sleep for 15 minutes
                sleep(910)
                tweets = await client.search_tweet(query, "Latest",)

            for tweet in tweets:
                cnt += 1
                dataset[ct].append(
                    [
                        clm,
                        kwd,
                        tweet.id,
                        tweet.created_at,
                        tweet.created_at_datetime,
                        tweet.user.tweet.user.name,
                        tweet.text,
                    ]
                )
            print(f"{ct}: {clm}, [{query}] - {len(tweets)}")
    print(cnt)
    # save the dataset as json under data folder
    with open("data/tweets_latest_2025_jan_v2.json", "w") as f:
        json.dump(dataset, f, indent=4)


asyncio.run(main())
