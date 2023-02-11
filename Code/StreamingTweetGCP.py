from env import *
import requests
import json
import datetime
from env import * 
from google.cloud import pubsub_v1


# Config
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path("snsdisasteralert", "snsstream")


# Method to push messages to pubsub
def write_to_pubsub(data):
    print("writing...")
    try:
        if data["data"]["lang"] == "en":
            context=[]
            if "context_annotations" in data["data"]:
                for annotation in data["data"]["context_annotations"]: 
                    context.append(annotation["domain"]["name"]) if annotation["domain"]["name"] not in context else context
                    
            publisher.publish(topic_path, data=json.dumps({
                "text": data["data"]["text"],
                "author_id": data["data"]["author_id"],
                "id": data["data"]["id"],
                "tag": data["matching_rules"][0]["tag"],
                "followers_count" : data["includes"]["users"][0]["public_metrics"]["followers_count"],
                "following_count" : data["includes"]["users"][0]["public_metrics"]["following_count"],
                "context" : context,
                "created_at": datetime.datetime.strptime(data["data"]["created_at"], '%Y-%m-%dT%H:%M:%S.%f%z')
            }, indent=4, default=str).encode("utf-8"), tweet_id=str(data["data"]["id"]).encode("utf-8"))
    except Exception as e:
        raise


#------------------------------------------------------------------------
 
def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FilteredStreamPython"
    return r


def get_rules():
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    # print(json.dumps(response.json()))
    return response.json()


def delete_all_rules(rules):
    if rules is None or "data" not in rules:
        return None

    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot delete rules (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    # print(json.dumps(response.json()))


def set_rules(delete):
    # You can adjust the rules if needed
    sample_rules = [
        {"value": "amazon lang:en -is:retweet -is:quote -is:reply -url:amazon", "tag" : "Amazon"},      
        {"value": "apple lang:en -is:retweet -is:quote -is:reply -url:apple", "tag" : "apple"},      
        {"value": "accenture lang:en -is:retweet -is:quote -is:reply -url:accenture", "tag" : "accenture"},      
        {"value": "deloitte lang:en -is:retweet -is:quote -is:reply -url:deloitte", "tag" : "deloitte"},      
        {"value": "intel lang:en -is:retweet -is:quote -is:reply -url:intel", "tag" : "intel"},      
        {"value": "united healthcare lang:en -is:retweet -is:quote -is:reply ", "tag" : "united healthcare"},      
        {"value": "csv health lang:en -is:retweet -is:quote -is:reply ", "tag" : "csv health"},      
        {"value": "hca healthcare lang:en -is:retweet -is:quote -is:reply ", "tag" : "hca healthcare"},      
        {"value": "optum lang:en -is:retweet -is:quote -is:reply -url:optum", "tag" : "optum"},      
        {"value": "walmart lang:en -is:retweet -is:quote -is:reply -url:walmart", "tag" : "walmart"},      
        {"value": "home depot lang:en -is:retweet -is:quote -is:reply ", "tag" : "home depot"},      
        {"value": "tesla lang:en -is:retweet -is:quote -is:reply -url:tesla", "tag" : "tesla"},      
        {"value": "mcdonalds lang:en -is:retweet -is:quote -is:reply -url:mcdonalds", "tag" : "mcdonalds"},      
        {"value": "microsoft lang:en -is:retweet -is:quote -is:reply -url:microsoft", "tag" : "microsoft"},      
        {"value": "verizon lang:en -is:retweet -is:quote -is:reply -url:verizon", "tag" : "verizon"},      
        {"value": "at&t lang:en -is:retweet -is:quote -is:reply -url:at&t", "tag" : "at&t"},      
        {"value": "comcast corporation lang:en -is:retweet -is:quote -is:reply ", "tag" : "comcast corporation"},      
        {"value": "bank of america lang:en -is:retweet -is:quote -is:reply ", "tag" : "bank of america"},      
        {"value": "wells fargo lang:en -is:retweet -is:quote -is:reply ", "tag" : "wells fargo"},      
        {"value": "capital one lang:en -is:retweet -is:quote -is:reply ", "tag" : "capital one"},      
        {"value": "ups lang:en -is:retweet -is:quote -is:reply -url:ups", "tag" : "ups"},      
        {"value": "fedex lang:en -is:retweet -is:quote -is:reply -url:fedex", "tag" : "fedex"},      
        {"value": "general electric lang:en -is:retweet -is:quote -is:reply", "tag" : "general electric"},      
        {"value": "boeing lang:en -is:retweet -is:quote -is:reply -url:boeing", "tag" : "boeing"},      
        {"value": "google lang:en -is:retweet -is:quote -is:reply -url:google", "tag" : "google"},      
        {"value": "disney lang:en -is:retweet -is:quote -is:reply -url:disney", "tag" : "disney"},      
        {"value": "marlboro lang:en -is:retweet -is:quote -is:reply -url:marlboro", "tag" : "marlboro"},      
        {"value": "coca cola lang:en -is:retweet -is:quote -is:reply -url:cocacola", "tag" : "cocacola"},      
        {"value": "Consolidated Edison lang:en -is:retweet -is:quote -is:reply ", "tag" : "Consolidated Edison"},      
        {"value": "dominion energy lang:en -is:retweet -is:quote -is:reply -url:dominionenergy", "tag" : "dominion energy"},      
        {"value": "dte energy lang:en -is:retweet -is:quote -is:reply -url:dteenergy", "tag" : "dte energy"},      
        {"value": "duke energy lang:en -is:retweet -is:quote -is:reply -url:dukeenergy", "tag" : "duke energy"},      
        {"value": "Berkshire Hathaway HomeServices lang:en -is:retweet -is:quote -is:reply", "tag" : "Berkshire Hathaway HomeServices"},      
        {"value": "american tower lang:en -is:retweet -is:quote -is:reply -url:dteenergy", "tag" : "dte energy"},      
        {"value": "prologis lang:en -is:retweet -is:quote -is:reply -url:prologis", "tag" : "prologis"},      
        {"value": "cown castle lang:en -is:retweet -is:quote -is:reply", "tag" : "cown castle"},      
    ]
    payload = {"add": sample_rules}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    # print(json.dumps(response.json()))


def get_stream(set):
    # setup the API request
    endpoint = 'https://api.twitter.com/2/tweets/search/stream'
    params = {
        'expansions': 'author_id',
        'tweet.fields': 'created_at,lang,text,author_id,public_metrics,context_annotations',
        'user.fields': 'name,username,public_metrics'
    }

    response = requests.get(endpoint,
                            params=params,
                            auth=bearer_oauth, 
                            stream=True
                            )  # send the request

    # print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            "Cannot get stream (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    for response_line in response.iter_lines():
        if response_line:
            json_response = json.loads(response_line)
            write_to_pubsub(json_response)

     
def main():
    rules = get_rules()
    delete = delete_all_rules(rules)
    set = set_rules(delete)
    get_stream(set)
    
# main()


