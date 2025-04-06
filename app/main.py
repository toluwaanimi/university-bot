import os
import sys
import traceback
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_loader import load_courses
from core.intent_parser import parse_intent
from core.course_filter import filter_courses
from core.response_generator import generate_response
from core.memory import update_memory, get_conversation_history

# Load environment variables
load_dotenv()

# Initialize OpenAI API key
import openai
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def main():
    # Load course data
    try:
        df = load_courses()
        print("🎓 Ask me anything about UK university courses!")
    except Exception as e:
        print(f"Error loading course data: {str(e)}")
        print("Please check that the courses.json file exists and is properly formatted.")
        return

    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nGoodbye! Have a great day!")
                break

            # Get conversation history
            history = get_conversation_history()
            
            # Parse user intent
            try:
                parsed = parse_intent(user_input, history)
            except Exception as e:
                print(f"\nError parsing intent: {str(e)}")
                print("Continuing with default intent...")
                parsed = {
                    "intent": "search",
                    "entities": {},
                    "user_preferences": {},
                    "comparison_details": {},
                    "clarification_needed": None
                }
            
            # Filter courses based on intent
            try:
                matched = filter_courses(parsed, df)
            except Exception as e:
                print(f"\nError filtering courses: {str(e)}")
                print("Continuing with empty results...")
                matched = df.iloc[0:0]  # Empty DataFrame
            
            # Generate response
            try:
                reply = generate_response(user_input, parsed, matched, history)
            except Exception as e:
                print(f"\nError generating response: {str(e)}")
                reply = "I'm sorry, I encountered an error while processing your request. Please try again."
            
            # Update memory
            try:
                update_memory(parsed, reply, user_input, matched["id"].tolist() if not matched.empty else [])
            except Exception as e:
                print(f"\nError updating memory: {str(e)}")
                # Continue without updating memory
            
            # Print response
            print(f"\nAI: {reply}\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye! Have a great day!")
            break
        except Exception as e:
            print(f"\nSorry, I encountered an unexpected error: {str(e)}")
            print("Please try again or type 'quit' to exit.")
            # Print the full traceback for debugging
            traceback.print_exc()

if __name__ == "__main__":
    main() 