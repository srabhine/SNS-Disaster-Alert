import requests
import os
import json
# from env import *
from google.cloud import bigquery
from datetime import datetime

client = bigquery.Client()

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token_academic="AAAAAAAAAAAAAAAAAAAAAJm%2BcgEAAAAAXYpKw0GK0tQtQH0coQVXw1SK%2Fwc%3DhMlBR1QNbP6mLXyEOqTkkmlsVkZ9G9w1zFlzY8niSbnF2iAoAu"

bearer_token = bearer_token_academic

sql = """
   UPDATE  sns_stream.tweets
     SET   public_metrics = ARRAY(
  SELECT  pb FROM UNNEST(public_metrics) AS  pb
  UNION ALL
  SELECT (@like_count,@retweet_count,@quote_count,@metrics_date)
) 
   WHERE id = @id
   """
   
sql2 = """
SELECT  id FROM `snsdisasteralert.sns_stream.tweets` WHERE ARRAY_LENGTH(public_metrics) = 0     LIMIT 99
"""
df1 = client.query(sql2).to_dataframe()
listIds = df1['id'].values.tolist()

idsp = "ids="
for id in listIds:
    if (idsp == "ids="):
         idsp = idsp + id
    idsp = idsp + "," + id
    
def create_url():
    tweet_fields = "tweet.fields=public_metrics"
    ids = idsp
    # You can adjust ids to include a single Tweets.
    # Or you can add to up to 100 comma-separated IDs
    url = "https://api.twitter.com/2/tweets?{}&{}".format(ids, tweet_fields)
    return url


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2TweetLookupPython"
    return r


def connect_to_endpoint(url):
    response = requests.request("GET", url, auth=bearer_oauth)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    return response.json()


def main():
    url = create_url()
    json_response = connect_to_endpoint(url)
    # print(json.dumps(json_response, indent=4, sort_keys=True))
    
    for tweet in json_response["data"]:
        lk=tweet["public_metrics"]["like_count"]
        rk=tweet["public_metrics"]["retweet_count"]
        qk=tweet["public_metrics"]["quote_count"]
        now = datetime.now()
        metrics_date = now.strftime("%Y-%d-%m %H:%M:%S")
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("like_count", "INT64", lk),
                bigquery.ScalarQueryParameter("retweet_count", "INT64", rk),
                bigquery.ScalarQueryParameter("quote_count", "INT64", qk),
                bigquery.ScalarQueryParameter("metrics_date", "STRING", metrics_date),
                bigquery.ScalarQueryParameter("id", "STRING", tweet["id"])
            ]
        )
        query_job = client.query(sql, job_config=job_config) 

        results = query_job.result()  # Wait for the job to complete.
        print(results)


if __name__ == "__main__":
    main()