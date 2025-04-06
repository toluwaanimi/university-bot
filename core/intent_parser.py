import openai
import json
import re
from config.gpt_prompt_templates import INTENT_SYSTEM_PROMPT

def parse_intent(user_query, history=[], api_key=None):
    # Create messages array with system prompt
    messages = [{"role": "system", "content": INTENT_SYSTEM_PROMPT}]
    
    # Add complete conversation history to messages
    for turn in history:  # Use complete history
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": turn["ai"]})
    
    # Add current query
    messages.append({"role": "user", "content": user_query})

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        
        # Check if response is empty
        if not response.choices or not response.choices[0].message.content:
            # Return a default intent if response is empty
            return {
                "intent": "search",
                "entities": {},
                "user_preferences": {},
                "comparison_details": {},
                "clarification_needed": None
            }
        
        content = response.choices[0].message.content
        
        # Try to extract JSON from the response if it's not pure JSON
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                # If JSON parsing fails, return a default intent
                print(f"Failed to parse JSON from: {json_match.group(0)}")
                return {
                    "intent": "search",
                    "entities": {},
                    "user_preferences": {},
                    "comparison_details": {},
                    "clarification_needed": None
                }
        else:
            # If no JSON found in the response, return a default intent
            print(f"No JSON found in response: {content}")
            return {
                "intent": "search",
                "entities": {},
                "user_preferences": {},
                "comparison_details": {},
                "clarification_needed": None
            }
            
    except Exception as e:
        # Log the error and return a default intent
        print(f"Error in parse_intent: {str(e)}")
        return {
            "intent": "search",
            "entities": {},
            "user_preferences": {},
            "comparison_details": {},
            "clarification_needed": None
        } 