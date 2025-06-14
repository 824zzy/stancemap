import asyncio
from twikit import Client
from collections import defaultdict
import json
from retrying import retry
from time import sleep
from datetime import datetime
import spacy
import pandas as pd
from tqdm import tqdm
from credentials import USERNAME, PASSWORD, EMAIL

# Initialize client
client = Client(
    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


async def main(politifact_keywords):
    def write_to_file(tweets):
        page_cnt = 0
        for tweet in tweets:
            page_cnt += 1
            tweet_data = {
                "claim": clm,
                "keyword": query,
                "categories": categories,
                "tweet": {
                    "id": tweet.id,
                    "created_at": tweet.created_at,
                    "text": tweet.text,
                    "lang": tweet.lang,
                    "in_reply_to": tweet.in_reply_to,
                    "is_quote_status": tweet.is_quote_status,
                    "possibly_sensitive": tweet.possibly_sensitive,
                    "possibly_sensitive_editable": tweet.possibly_sensitive_editable,
                    "quote_count": tweet.quote_count,
                    "reply_count": tweet.reply_count,
                    "favorite_count": tweet.favorite_count,
                    "favorited": tweet.favorited,
                    "view_count": tweet.view_count,
                    "view_count_state": tweet.view_count_state,
                    "retweet_count": tweet.retweet_count,
                    "place": None
                    if tweet.place == None
                    else {
                        "id": tweet.place.id,
                        "name": tweet.place.name,
                        "full_name": tweet.place.full_name,
                        "country_code": tweet.place.country_code,
                        "country": tweet.place.country,
                        "place_type": tweet.place.place_type,
                        "bounding_box": tweet.place.bounding_box,
                        "contained_within": tweet.place.contained_within,
                    },
                    "editable_until_msecs": tweet.editable_until_msecs,
                    "is_translatable": tweet.is_translatable,
                    "is_edit_eligible": tweet.is_edit_eligible,
                    "edits_remaining": tweet.edits_remaining,
                    "hashtags": tweet.hashtags,
                },
                "tweet_user": {
                    "uid": tweet.user.id,
                    "created_at": tweet.user.created_at,
                    "name": tweet.user.name,
                    "screen_name": tweet.user.screen_name,
                    "profile_image_url": tweet.user.profile_image_url,
                    "profile_banner_url": tweet.user.profile_banner_url,
                    "url": tweet.user.url,
                    "location": tweet.user.location,
                    "description": tweet.user.description,
                    "description_urls": tweet.user.description_urls,
                    "urls": tweet.user.urls,
                    "pinned_tweet_ids": tweet.user.pinned_tweet_ids,
                    "is_blue_verified": tweet.user.is_blue_verified,
                    "is_verified": tweet.user.verified,
                    "possibly_sensitive": tweet.user.possibly_sensitive,
                    "can_dm": tweet.user.can_dm,
                    "can_media_tag": tweet.user.can_media_tag,
                    "want_retweets": tweet.user.want_retweets,
                    "default_profile": tweet.user.default_profile,
                    "default_profile_image": tweet.user.default_profile_image,
                    "followers_count": tweet.user.followers_count,
                    "fast_followers_count": tweet.user.fast_followers_count,
                    "normal_followers_count": tweet.user.normal_followers_count,
                    "following_count": tweet.user.following_count,
                    "favourites_count": tweet.user.favourites_count,
                    "listed_count": tweet.user.listed_count,
                    "media_count": tweet.user.media_count,
                    "statuses_count": tweet.user.statuses_count,
                },
                "created_at": tweet.created_at,
            }
            with open("data/tweets_latest_2025_mar_v2.json", "a") as f:
                json.dump(tweet_data, f, indent=4)
                f.write("\n")
        return page_cnt

    await client.login(auth_info_1=USERNAME, auth_info_2=EMAIL, password=PASSWORD)
    cnt = 0
    for idx, obj in tqdm(
        politifact_keywords.items(), total=len(politifact_keywords.items())
    ):
        clm = obj["claim"]
        query = " ".join(obj["keywords"])
        categories = obj["categories"]
        claim_tweet_cnt = 0
        try:
            tweets_on_page = await client.search_tweet(query, "Latest")
        except Exception as e:
            print(f"Time out for searching first page of tweets for {clm}, [{query}]")
            # sleep for 15 minutes
            sleep(910)
            tweets_on_page = await client.search_tweet(query, "Latest")
        page_cnt = write_to_file(tweets_on_page)
        claim_tweet_cnt += page_cnt
        cnt += page_cnt
        print(f"{cnt}: {clm}, [{query}] - {claim_tweet_cnt}")
        if page_cnt == 0:
            continue
        while True:
            try:
                tweets_on_page = await tweets_on_page.next()
            except Exception as e:
                print(
                    f"Time out for searching next page of tweets for {clm}, [{query}]"
                )
                # sleep for 15 minutes
                sleep(910)
                tweets_on_page = await tweets_on_page.next()
            page_cnt = write_to_file(tweets_on_page)
            claim_tweet_cnt += page_cnt
            cnt += page_cnt
            if claim_tweet_cnt > 400 or page_cnt == 0:
                break
            print(f"{cnt}: {clm}, [{query}] - {claim_tweet_cnt}")
    print(cnt)


def extract_keywords():
    nlp = spacy.load("en_core_web_sm")
    politifact_df = pd.read_csv("data/politifact.csv")
    politifact_claims = politifact_df["Claim"]
    politifact_claim_tags = politifact_df["Tags"]
    # reverse the order of claims
    politifact_claims = politifact_claims[::-1]
    politifact_claim_tags = politifact_claim_tags[::-1]
    claim2keywords = {}
    idx = 0
    for claim, tag in tqdm(
        zip(politifact_claims, politifact_claim_tags), total=len(politifact_claims)
    ):
        doc = nlp(claim)
        keywords = set()
        for token in doc:
            if token.pos_ == "NOUN" or token.pos_ == "PROPN" or token.pos_ == "VERB":
                keywords.add(token.text)
        categories = []
        if not pd.isna(tag):
            for c in tag.split(","):
                categories.append(c.strip())
        if len(keywords) > 3 and len(keywords) < 9:  # none: 24758; 10: 24758; 8:
            claim2keywords[idx] = {
                "claim": claim,
                "keywords": list(keywords),
                "categories": categories,
            }
            idx += 1

    # save claim2keywords as json
    with open("data/politifact_claim2keywords.json", "w") as f:
        json.dump(claim2keywords, f, indent=4)


if __name__ == "__main__":
    # extract_keywords()
    politifact_keywords = json.load(open("data/politifact_claim2keywords.json"))
    asyncio.run(main(politifact_keywords))
