def filter_courses(parsed, df):
    ents = parsed["entities"]
    prefs = parsed["user_preferences"]
    result = df.copy()

    if ents.get("subject"):
        result = result[result["name"].str.contains(ents["subject"], case=False)]
    if ents.get("university"):
        result = result[result["university"].str.contains(ents["university"], case=False)]
    if ents.get("study_mode"):
        result = result[result["study_mode"] == ents["study_mode"]]

    if prefs.get("ucas_points"):
        def valid(reqs):
            for r in reqs:
                if r["type"] == "UCAS Tariff":
                    try:
                        return int(r["min_entry"]) <= prefs["ucas_points"]
                    except:
                        return False
            return False
        result = result[result["entry_requirements"].apply(valid)]

    return result.head(3) 