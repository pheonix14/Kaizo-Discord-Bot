import json
import os
import sys

# Add root folder to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logger

def main():
    targets_file = os.path.join(os.path.dirname(__file__), "../awake/targets.json")
    if not os.path.exists(targets_file):
        print(f"Error: {targets_file} not found.")
        return

    with open(targets_file, "r") as f:
        targets = json.load(f)

    print(f"Loaded {len(targets)} targets from {targets_file}")

    # Fetch current mimic config
    db = logger.get_db()
    mimic = logger.get_mimic_config()
    if not isinstance(mimic, dict):
        mimic = {}

    # Set watchdog targets
    mimic["watchdog_targets"] = targets
    logger.save_mimic_config(mimic)
    print("Successfully synchronized watchdog targets to Supabase!")

if __name__ == "__main__":
    main()
