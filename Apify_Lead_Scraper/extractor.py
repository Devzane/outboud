"""
Isolates the data parsing logic from the raw Apify output.
"""

def extract_leads(client, run):
    """
    Iterate through the actor's output dataset and safely extract 
    metadata fields from each place row.
    """
    leads = []
    dataset_items = client.dataset(run["defaultDatasetId"]).iterate_items()

    for item in dataset_items:
        # We use `.get(key) or "N/A"` to ensure explicit None values 
        # evaluate to False and fall back to the placeholder safely.
        lead = {
            "Company Name": item.get("title") or "N/A",
            "Website":      item.get("website") or "N/A",
            "Phone":        item.get("phone") or "N/A",
            "City":         item.get("city") or "N/A",
        }
        leads.append(lead)

    return leads
