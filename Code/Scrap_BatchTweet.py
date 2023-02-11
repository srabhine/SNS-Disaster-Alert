import requests
import json
import time
from datetime import datetime
from google.cloud import bigquery
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer


project_id = 'snsdisasteralert-372409'
client = bigquery.Client(project=project_id)

# Insert values in a table
from google.cloud import bigquery
# client = bigquery.Client()

dataset_id = "sns"
# For this sample, the table must already exist and have a defined schema
table_id = "tweets"
table_ref = client.dataset(dataset_id).table(table_id)
table = client.get_table(table_ref)


# To set your environment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token_academic="AAAAAAAAAAAAAAAAAAAAAAT4iAEAAAAA5OcF%2BJbRdQJqcT9w70TGCsHA%2B0c%3DJs1sHTVR8KNtC4caswoarwdO2ntDuAEHROTRQhxilbIfaLTxmG"
bearer_token = bearer_token_academic

search_url = "https://api.twitter.com/2/tweets/search/all"

# Optional params: start_time,end_time,since_id,until_id,max_results,next_token,
# expansions,tweet.fields,media.fields,poll.fields,place.fields,user.fields
def queryBuild(company,context):
    query_params = {'query': ' -is:retweet -is:quote -is:reply -url:' + company +' context:' + context ,
                    'start_time' :'2022-01-01T00:00:00Z',
                    'end_time' :'2023-01-01T00:00:00Z',
                    'tweet.fields': 'author_id,lang,public_metrics,created_at,context_annotations',
                    'user.fields': 'name,username,public_metrics',
                    'expansions': 'author_id',
                    'sort_order' : 'relevancy',
                    'max_results' : '100'
                    }
    return query_params

def analyze_sentiment(text):
    # Crée un objet SentimentIntensityAnalyzer
    analyzer = SentimentIntensityAnalyzer()
    
    # Analyse le sentiment du tweet
    sentiment = analyzer.polarity_scores(text)
    # Détermine le sentiment le plus probable
    if sentiment['compound'] >= 0.05:
        sentiment_label = 'positive'
    elif sentiment['compound'] <= -0.05:
        sentiment_label = 'negative'
    else:
        sentiment_label = 'neutral'

    # Retourne la liste des résultats
    return sentiment_label


# Number of requests allowed per time window
RATE_LIMIT = 300
# Time window (in seconds)
TIME_WINDOW = 60*15

# Bucket for tracking remaining requests
bucket = RATE_LIMIT
# Timestamp of last bucket refill
last_refill = time.time()

def connect_to_endpoint(url, params):
    time.sleep(1)
    global bucket
    global last_refill
    # Check if bucket is empty
    if bucket <= 0:
        # Check if time window has expired
        current_time = time.time()
        if current_time - last_refill > TIME_WINDOW:
            # Refill bucket and update timestamp
            bucket = RATE_LIMIT
            last_refill = current_time
        else:
            # Wait for time window to expire
            time_to_wait = last_refill + TIME_WINDOW - current_time
            time.sleep(time_to_wait)
            bucket = RATE_LIMIT
    # Send request
    response = requests.request("GET", search_url, auth=bearer_oauth, params=params)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    # Decrement bucket
    bucket -= 1
    return response.json()

def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FullArchiveSearchPython"
    return r


# def connect_to_endpoint(url, params):
#     response = requests.request("GET", search_url, auth=bearer_oauth, params=params)
#     print(response.status_code)
#     if response.status_code != 200:
#         raise Exception(response.status_code, response.text)
#     return response.json()


def paginateTweet(query_params,tag):
    json_response = connect_to_endpoint(search_url, query_params)
    jsonToDb(json_response,tag);
   
    while ("next_token" in json.dumps(json_response)):
        time.sleep(1)# to dodge 'too many request'
        query_params_next = query_params
        query_params_next["next_token"]=json_response["meta"]["next_token"]
        json_response = connect_to_endpoint(search_url, query_params_next)
        jsonToDb(json_response,tag);


def jsonToDb(json_response,tag):
    # print(json.dumps(json_response,indent=4))
    if 'data' in json_response:
        for tweet in json_response['data']:
            context=[]
            if "context_annotations" in tweet:
                for annotation in tweet["context_annotations"]: 
                    context.append(annotation["domain"]["name"]) if annotation["domain"]["name"] not in context else context
            tweet_id =tweet['id']
            author_id = tweet['author_id']
            retweet_count=int(tweet['public_metrics']['like_count'])
            like_count=int(tweet['public_metrics']['quote_count'])
            quote_count=int(tweet['public_metrics']['retweet_count'])
            created_at = str(datetime.strptime(tweet["created_at"], '%Y-%m-%dT%H:%M:%S.%f%z'))
            lang=tweet['lang']
            print(created_at,tag)
            text= tweet['text']
            # print(json_response["includes"]["users"])
            user_metrics = (users["public_metrics"] for users in json_response["includes"]["users"] if users["id"] == author_id)
            for metrics in user_metrics:
                followers_count = metrics["followers_count"]
                following_count = metrics["following_count"]

            now = datetime.now()
            metrics_date = now.strftime("%Y-%m-%d %H:%M:%S")
            sentiment = analyze_sentiment(text)
            
            # If tweet is in English
            if  lang=="en":
                # Creating a list of tuples with the values that shall be inserted into the table
            
                rows_to_insert = [{ u"id" : tweet_id ,u"author_id" : author_id , u"followers_count" : followers_count,
                                    u"following_count" :following_count,
                                    u"tag" : tag , u"context" : context , u"text" :text ,u"created_at" : created_at ,
                                    u'sentiment' : sentiment,
                                    u"public_metrics" :
                                    [{"like_count" : like_count , "quote_count" : quote_count ,
                                        "retweet_count" : retweet_count, "metrics_date" : metrics_date}]}]
                errors = client.insert_rows(table, rows_to_insert) 
                print(errors)
                        
        
if __name__ == "__main__":
    paginateTweet(queryBuild("amazon","47.10026792024"),"amazon")
    paginateTweet(queryBuild("amazon","131.10026792024"),"amazon")
    paginateTweet(queryBuild("mcdonalds","47.10026319212"),"mcdonalds")
    paginateTweet(queryBuild("mcdonalds","131.10026319212"),"mcdonalds")
    paginateTweet(queryBuild("tesla","47.10044199219"),"tesla")
    paginateTweet(queryBuild("tesla","131.10044199219"),"tesla")
    paginateTweet(queryBuild("apple","47.10026364281"),"apple")
    paginateTweet(queryBuild("apple","131.10026364281"),"apple")
    paginateTweet(queryBuild("twitter","47.10045225402"),"twitter")
    paginateTweet(queryBuild("twitter","131.10045225402"),"twitter")
    paginateTweet(queryBuild("coca cola","47.10026299835"),"coca cola")
    paginateTweet(queryBuild("coca cola","131.10026299835"),"coca cola")
    paginateTweet(queryBuild("walmart","47.10026347212"),"walmart")
    paginateTweet(queryBuild("walmart","131.10026347212"),"walmart")
    paginateTweet(queryBuild("disney","47.10037284711"),"disney")
    paginateTweet(queryBuild("disney","131.10037284711"),"disney")
    paginateTweet(queryBuild("S&P500","47.10044990657"),"S&P500")
    paginateTweet(queryBuild("S&P500","131.10026364281"),"S&P500")
    paginateTweet(queryBuild("intel","47.10026332285"),"intel")
    paginateTweet(queryBuild("intel","131.10026332285"),"intel")
    paginateTweet(queryBuild("google","47.10026378521"),"google")
    paginateTweet(queryBuild("google","48.1395474411180892160"),"google")

    
