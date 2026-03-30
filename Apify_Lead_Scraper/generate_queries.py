def generate_apify_queries():
    # 1. Put your target keywords here. Keep the quotes around them if you want 
    # Apify to treat them as exact phrases.
    keywords = [
        '"commercial HVAC contractors"',
        '"industrial HVAC design build"',
        '"commercial chiller repair"',
        '"rooftop unit RTU installation"',
        '"commercial HVAC preventative maintenance"'
    ]

    # 2. The Tiered City List (State abbreviations included)
    cities_by_tier = {
        "=== TIER 1: THE MEGA-MARKETS (Set Apify Max Results to: 50 - 75) ===": [
            "Chicago IL", "Los Angeles CA", 
            "Phoenix AZ", "Atlanta GA", "Miami FL", "Philadelphia PA", 
            "Brooklyn NY", "Queens NY", "San Diego CA", 
            "Seattle WA", "Denver CO", "Washington DC"
        ],
        "=== TIER 2: HIGH-GROWTH HUBS (Set Apify Max Results to: 25 - 40) ===": [
            "Austin TX", "Nashville TN", "Charlotte NC", "Las Vegas NV", 
            "Orlando FL", "Tampa FL", "Columbus OH", "Indianapolis IN", 
            "Raleigh NC", "Salt Lake City UT", "Kansas City MO", "Minneapolis MN", 
            "Portland OR", "San Jose CA", "Jacksonville FL", "Richmond VA", 
            "Oklahoma City OK", "Louisville KY"
        ],
        "=== TIER 3: REGIONAL HUBS (Set Apify Max Results to: 10 - 20) ===": [
            "Omaha NE", "Tulsa OK", "Boise ID", "Des Moines IA", 
            "Reno NV", "Spokane WA", "Madison WI", "Grand Rapids MI", 
            "Huntsville AL", "Wichita KS", "Baton Rouge LA", "Toledo OH", 
            "Fort Wayne IN", "Fargo ND", "Little Rock AR", "Sioux Falls SD", 
            "Chattanooga TN", "Knoxville TN"
        ]
    }

    output_filename = "apify_search_queries.txt"

    # 3. Generate the combinations and write them to a text file
    with open(output_filename, "w") as file:
        total_queries = 0
        
        for tier_name, cities in cities_by_tier.items():
            file.write(f"{tier_name}\n\n")
            
            for city in cities:
                for keyword in keywords:
                    # Combines the keyword and the city (e.g., "commercial chiller repair" Dallas TX)
                    query = f"{keyword} {city}\n"
                    file.write(query)
                    total_queries += 1
            
            file.write("\n" + "="*70 + "\n\n")

    print(f"Success! Generated {total_queries} highly targeted search queries.")
    print(f"Open '{output_filename}' to copy and paste them into Apify.")

if __name__ == "__main__":
    generate_apify_queries()