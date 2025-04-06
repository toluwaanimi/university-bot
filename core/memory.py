session_memory = {
    "turns": [],  # History of {"user": "...", "ai": "..."}
    "last_intent": None,
    "last_subject": None,
    "last_ucas": None,
    "last_courses": []
}

def update_memory(parsed, response, user_query, matched_ids):
    session_memory["turns"].append({
        "user": user_query,
        "ai": response
    })
    session_memory["last_intent"] = parsed.get("intent")
    session_memory["last_subject"] = parsed["entities"].get("subject")
    session_memory["last_ucas"] = parsed["user_preferences"].get("ucas_points")
    session_memory["last_courses"] = matched_ids

def get_conversation_history():
    return session_memory["turns"] 