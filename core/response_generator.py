import json
import openai
from config.gpt_prompt_templates import RESPONSE_SYSTEM_PROMPT

def generate_response(user_query, parsed, matched_df, history=[], api_key=None):
    simplified = []
    for _, row in matched_df.iterrows():
        fee = next((f for f in row["fees"] if f["region"] == "England"), {})
        
        entry_reqs = []
        for req in row["entry_requirements"]:
            if req["type"] == "UCAS Tariff":
                entry_reqs.append(f"UCAS Tariff: {req['min_entry']} points")
            else:
                entry_reqs.append(f"{req['type']}: {req.get('min_entry', 'N/A')}")
        
        simplified.append({
            "name": row["name"],
            "university": row["university"],
            "study_mode": row["study_mode"],
            "duration": row["duration"],
            "fee": f"£{fee.get('price', 'N/A')} per {fee.get('period', 'year')}",
            "campus": row["campus"],
            "url": row["external_url"],
            "entry_requirements": entry_reqs
        })

    system_prompt = f"""{RESPONSE_SYSTEM_PROMPT}

Available courses for this query:
{json.dumps(simplified, indent=2)}

Parsed user intent:
{json.dumps(parsed, indent=2)}"""

    messages = [{"role": "system", "content": system_prompt}]
    
    for turn in history:  # Use complete history
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": turn["ai"]})
    
    messages.append({"role": "user", "content": user_query})

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        
        # Check if response is empty
        if not response.choices or not response.choices[0].message.content:
            # Return a default response if the response is empty
            return "I'm sorry, I couldn't generate a response. Please try asking your question again."
            
        return response.choices[0].message.content
    except Exception as e:
        # Log the error and return a default response
        print(f"Error in generate_response: {str(e)}")
        return "I'm sorry, I encountered an error while processing your request. Please try again." 