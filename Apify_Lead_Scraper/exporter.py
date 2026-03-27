"""
Handles safe OS interactions and CSV writing.
"""
import os
import csv

def save_to_csv(leads, filepath):
    """
    Safely build directories and write extracted dicts to disk as a CSV.
    """
    fieldnames = ["Company Name", "Website", "Phone", "City"]

    # Verify and dynamically create subdirectories to prevent FileNotFoundError
    output_dir = os.path.dirname(filepath)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(leads)

    print(f"📁  Saved {len(leads)} leads to {filepath}")
