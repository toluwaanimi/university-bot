import pandas as pd
import json

def load_courses(filepath="data/clean_structured_example.json"):
    with open(filepath) as f:
        data = json.load(f)

    flat = []
    for course in data:
        for opt in course["study_options"]:
            flat.append({
                "id": course["id"],
                "name": course["name"],
                "university": course["university"],
                "overview": course["overview"][:300],
                "study_mode": opt["study_mode"],
                "duration": opt["duration"],
                "start_date": opt["start_date"],
                "entry_requirements": opt["entry_requirements"],
                "fees": opt["fees"],
                "campus": opt["campus"]["name"],
                "external_url": opt["external_url"]
            })
    return pd.DataFrame(flat) 