"""
=============================================================================
  Vectra Automation – Apify Google Maps Scraper
  Target: High-ticket SMB local businesses (e.g., Commercial HVAC, Premium
          Real Estate) for outbound lead generation.
=============================================================================

OVERVIEW
--------
This script follows a four-phase pipeline:

  1. CONFIG   → Load secrets from .env, define search queries & Apify payload.
  2. SCRAPE   → Call the Apify Google Maps Scraper actor synchronously.
  3. EXTRACT  → Pull exactly 4 fields from each result (name, website, phone,
                city) while safely handling missing data.
  4. EXPORT   → Write every extracted record into a local CSV file so it can
                feed directly into the downstream outreach pipeline.

DEPENDENCIES
------------
  pip install apify-client python-dotenv
  (or)  pip install -r requirements.txt

USAGE
-----
  1. Put your Apify API token in the .env file next to this script.
  2. Run:  python script.py
  3. Output is saved to smb_leads.csv in the same directory.
"""

# ──────────────────────────────────────────────────────────────────────────────
#  IMPORTS
# ──────────────────────────────────────────────────────────────────────────────
import os       # Access environment variables
import sys      # Controlled exit on fatal errors
import csv      # Built-in CSV writer – no extra dependency needed

# python-dotenv reads the .env file and injects its variables into the
# process environment so we can retrieve them with os.environ.get().
from dotenv import load_dotenv

# The official Apify SDK for Python.  ApifyClient handles authentication,
# actor invocation, and dataset retrieval under the hood.
from apify_client import ApifyClient


# ──────────────────────────────────────────────────────────────────────────────
#  PHASE 1 – CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────

def load_config():
    """
    Load the Apify API token from .env and return it.

    Why a function?  Isolating config into its own callable makes it easy to
    unit-test later (mock os.environ) and keeps the top-level flow readable.
    """

    # load_dotenv() searches for a file named ".env" in the current working
    # directory (or any parent directory) and sets each KEY=VALUE pair as an
    # environment variable in the running process.
    load_dotenv()

    # os.environ.get() returns None if the key is missing – we never hardcode
    # the token so there is zero risk of it leaking into version control.
    api_token = os.environ.get("APIFY_API_TOKEN")

    if not api_token or api_token == "your_token_here":
        # Fail fast with a human-readable message so the user knows exactly
        # what to fix instead of hitting a cryptic downstream error.
        print("❌  ERROR: APIFY_API_TOKEN is not set.")
        print("   → Open the .env file and paste your Apify API token.")
        sys.exit(1)

    return api_token


# ──────────────────────────────────────────────────────────────────────────────
#  SEARCH QUERIES – edit this list whenever you want to target new niches
# ──────────────────────────────────────────────────────────────────────────────

# Each string is a "what + where" query, exactly like you'd type into Google
# Maps.  Add or remove entries to expand into new verticals or cities.
SEARCH_QUERIES = [
    "Commercial HVAC in Austin, Texas",
    "Premium Real Estate in Austin, Texas",
]

# Name of the output CSV that the downstream pipeline will consume.
OUTPUT_CSV = "smb_leads.csv"


# ──────────────────────────────────────────────────────────────────────────────
#  PHASE 2 – APIFY ACTOR CALL (SCRAPE)
# ──────────────────────────────────────────────────────────────────────────────

def build_actor_input(search_queries, max_results=50):
    """
    Build the dictionary payload that configures the Apify Google Maps
    Scraper actor.

    HOW THE PAYLOAD WORKS
    ---------------------
    The Apify actor expects a JSON-like dictionary.  Each key maps to a
    setting on the actor's input schema (documented at
    https://apify.com/compass/crawler-google-places#input-schema).

    Key fields explained:
      • searchStringsArray  – A Python list of search strings.  The actor
                              runs one Google Maps search per string.
      • maxCrawledPlacesPerSearch – The maximum number of place results the
                              actor will crawl *per search query*.  Setting
                              this to 50 keeps us well within the free tier.
      • language            – Language code for the results (ISO 639-1).
      • includeWebResults   – If True, also scrapes organic web results.
                              We don't need them, so False.
      • includeReviews      – Scraping reviews is expensive (many API calls
                              per place).  Disabled to save credits.
      • includeImages       – Same rationale – images are irrelevant for
                              our lead list.
      • includePopularTimes – Popular-times data requires extra scraping
                              passes.  Disabled.

    Returns
    -------
    dict : The fully formed actor input payload, ready to pass to
           actor.call(run_input=...).
    """

    actor_input = {
        # ── What to search for ──────────────────────────────────────────
        "searchStringsArray": search_queries,

        # ── Result cap (per query) ──────────────────────────────────────
        # With 2 queries × 50 results, one run produces ≤ 100 leads.
        "maxCrawledPlacesPerSearch": max_results,

        # ── Localisation ────────────────────────────────────────────────
        "language": "en",

        # ── Disable expensive extras to stay fast & cheap ───────────────
        "includeWebResults": False,
        "includeReviews": False,
        "includeImages": False,
        "includePopularTimes": False,
    }

    return actor_input


def run_scraper(api_token, actor_input):
    """
    Invoke the Apify Google Maps Scraper actor synchronously and return
    the run metadata dict.

    The actor ID "nwua9Gu5YrADL7ZDj" is the public identifier for the
    "Google Maps Scraper" actor on the Apify platform (by Compass).

    .call() is a *synchronous* method – it starts the actor run on Apify's
    cloud and blocks until the run finishes (or times out).  The returned
    dict contains metadata including "defaultDatasetId", which is the key
    we use in Phase 3 to fetch the actual scraped data.

    Raises
    ------
    Exception
        Any network, timeout, or Apify-side error is propagated to the
        caller so the top-level handler can log and exit gracefully.
    """

    # Instantiate the client with our token.  All subsequent API calls
    # will automatically include this token in the Authorization header.
    client = ApifyClient(api_token)

    print("🚀  Starting Apify Google Maps Scraper run...")
    print(f"   Queries : {actor_input['searchStringsArray']}")
    print(f"   Max/query: {actor_input['maxCrawledPlacesPerSearch']}")

    # .call() sends the payload to Apify's REST API, starts a new actor
    # run, and polls until the run reaches a terminal state (SUCCEEDED,
    # FAILED, TIMED_OUT, etc.).
    run = client.actor("nwua9Gu5YrADL7ZDj").call(run_input=actor_input)

    print("✅  Scraper run finished successfully.")
    return client, run


# ──────────────────────────────────────────────────────────────────────────────
#  PHASE 3 – DATA EXTRACTION
# ──────────────────────────────────────────────────────────────────────────────

def extract_leads(client, run):
    """
    Iterate through the actor's output dataset and extract exactly four
    fields per result.

    HOW DATASET ITERATION WORKS
    ----------------------------
    Every Apify actor run stores its output rows in a "dataset".  The run
    metadata dict contains a key called "defaultDatasetId" which is the
    unique ID of that dataset.

    client.dataset(<id>).iterate_items() returns a Python *generator* that
    lazily fetches pages of results from Apify's API.  Each yielded item
    is a dict representing one Google Maps place.

    FIELD MAPPING
    -------------
    The Google Maps Scraper returns many fields per place.  We only keep
    four (the minimum our outreach pipeline needs):

      Apify field  →  Our CSV column
      ───────────     ─────────────
      title        →  Company Name
      website      →  Website
      phone        →  Phone
      city         →  City

    We use dict.get(key, "N/A") so that if any field is missing from a
    particular result, we get the string "N/A" instead of a KeyError crash.

    Returns
    -------
    list[dict] : A flat list of dicts, each with exactly four keys:
                 "Company Name", "Website", "Phone", "City".
    """

    leads = []

    # Retrieve the dataset using the ID stored in the run metadata.
    dataset_items = client.dataset(run["defaultDatasetId"]).iterate_items()

    for item in dataset_items:
        # .get() is the safe accessor – it returns the second argument
        # ("N/A") when the key doesn't exist in the dict, preventing
        # KeyError exceptions from blowing up the script.
        lead = {
            "Company Name": item.get("title", "N/A"),
            "Website":      item.get("website", "N/A"),
            "Phone":        item.get("phone", "N/A"),
            "City":         item.get("city", "N/A"),
        }
        leads.append(lead)

    return leads


# ──────────────────────────────────────────────────────────────────────────────
#  PHASE 4 – CSV EXPORT
# ──────────────────────────────────────────────────────────────────────────────

def save_to_csv(leads, filepath):
    """
    Write the extracted leads to a local CSV file.

    HOW csv.DictWriter WORKS
    -------------------------
    Python's built-in `csv` module includes DictWriter, which maps Python
    dicts to CSV rows automatically.

    Steps:
      1. Open (or create) the file in write mode with UTF-8 encoding and
         newline="" (required on Windows to avoid blank rows between lines).
      2. Instantiate DictWriter with `fieldnames` – this defines both the
         CSV column headers and the dict keys it will look for in each row.
      3. Call writer.writeheader() to output the first row (column headers).
      4. Call writer.writerows(leads) to iterate through the entire list of
         lead dicts and write one CSV row per dict.  DictWriter handles the
         key-to-column mapping for us.

    Parameters
    ----------
    leads : list[dict]
        The list produced by extract_leads().
    filepath : str
        Relative or absolute path for the output CSV file.
    """

    # Define the column order.  DictWriter will write columns in this
    # exact sequence.
    fieldnames = ["Company Name", "Website", "Phone", "City"]

    # newline="" is CRITICAL on Windows – without it, csv.writer inserts
    # an extra blank line between every row.
    with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header row first (Company Name, Website, Phone, City).
        writer.writeheader()

        # writerows() loops through each dict in `leads` and writes its
        # values as a single CSV row, matching keys to fieldnames.
        writer.writerows(leads)

    print(f"📁  Saved {len(leads)} leads to {filepath}")


# ──────────────────────────────────────────────────────────────────────────────
#  MAIN ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

def main():
    """
    Orchestrates the four-phase pipeline:
      CONFIG → SCRAPE → EXTRACT → EXPORT

    All Apify and network operations are wrapped in a try/except so that
    transient failures (API timeouts, rate limits, connectivity issues)
    produce a user-friendly error message instead of an ugly traceback.
    """

    # ── Phase 1: Config ─────────────────────────────────────────────────
    api_token = load_config()
    actor_input = build_actor_input(SEARCH_QUERIES)

    # ── Phases 2-4 are wrapped in error handling ────────────────────────
    try:
        # ── Phase 2: Scrape ─────────────────────────────────────────────
        client, run = run_scraper(api_token, actor_input)

        # ── Phase 3: Extract ────────────────────────────────────────────
        leads = extract_leads(client, run)

        # Guard: if the actor returned zero results, warn instead of
        # writing an empty CSV that might confuse the outreach pipeline.
        if not leads:
            print("⚠️  The scraper returned 0 results.")
            print("   Try broadening your search queries or checking the")
            print("   Apify console for run logs.")
            sys.exit(0)

        # ── Phase 4: Export ─────────────────────────────────────────────
        save_to_csv(leads, OUTPUT_CSV)

    except ConnectionError as exc:
        # Raised when the HTTP connection to Apify's API cannot be
        # established (e.g., no internet, DNS failure).
        print(f"🌐  Network error: {exc}")
        print("   Check your internet connection and try again.")
        sys.exit(1)

    except TimeoutError as exc:
        # Raised if the actor run exceeds Apify's or the SDK's timeout.
        print(f"⏱️  Timeout error: {exc}")
        print("   The scraper run took too long.  Try reducing")
        print("   maxCrawledPlacesPerSearch or narrowing your queries.")
        sys.exit(1)

    except Exception as exc:
        # Catch-all for any other unexpected errors (API key invalid,
        # Apify service outage, malformed response, etc.).
        print(f"💥  Unexpected error: {exc}")
        print("   Check the Apify console for detailed run logs.")
        sys.exit(1)

    print("🎯  Done!  Your leads are ready for outreach.")


# Standard Python idiom: only run main() when the script is executed
# directly (python script.py), NOT when it is imported as a module.
if __name__ == "__main__":
    main()
