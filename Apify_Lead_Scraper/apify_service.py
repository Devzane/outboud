"""
Encapsulates all logic for building payloads and communicating with Apify.
"""
from apify_client import ApifyClient

def build_actor_input(search_queries, max_results=12):
    """
    Build the dictionary payload that configures the Apify Google Maps Scraper actor.
    """
    actor_input = {
        "searchStringsArray": search_queries,
        "maxCrawledPlacesPerSearch": max_results,
        "language": "en",
        "includeWebResults": False,
        "includeReviews": False,
        "includeImages": False,
        "includePopularTimes": False,
    }
    return actor_input

def run_scraper(api_token, actor_input):
    """
    Invoke the Apify Google Maps Scraper actor synchronously and return the run metadata.
    The actor ID "nwua9Gu5YrADL7ZDj" is the Compass Google Maps Scraper.
    """
    client = ApifyClient(api_token)

    print("🚀  Starting Apify Google Maps Scraper run...")
    print(f"   Queries : {len(actor_input['searchStringsArray'])} queries queued")
    print(f"   Max/query: {actor_input['maxCrawledPlacesPerSearch']}")

    # .call() polls until the Apify run terminates.
    run = client.actor("nwua9Gu5YrADL7ZDj").call(run_input=actor_input)

    print("✅  Scraper run finished successfully.")
    return client, run
