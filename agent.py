import anthropic
import json
from datetime import datetime, timedelta
from calendar_tools import create_event, list_events, delete_event, update_event

# Initialize Claude
client = os.getenv("ANTHROPIC_API_KEY")
if ANTHROPIC_API_KEY is None:
    raise RuntimeError("ANTHROPIC_API_KEY env var not set")

# Define tools for Claude
CALENDAR_TOOLS = [
    {
        "name": "create_event",
        "description": "Create a new calendar event. Use this when the user wants to schedule, add, or create an event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "The event title or summary (e.g., 'Team meeting', 'Dentist appointment')"
                },
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format. If user says 'tomorrow', calculate tomorrow's date."
                },
                "time": {
                    "type": "string",
                    "description": "Start time in HH:MM format (24-hour). E.g., '14:00' for 2pm, '09:30' for 9:30am"
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Duration in minutes. Default is 60 if not specified.",
                    "default": 60
                },
                "description": {
                    "type": "string",
                    "description": "Optional description or notes for the event",
                    "default": ""
                }
            },
            "required": ["title", "date", "time"]
        }
    },
    {
        "name": "list_events",
        "description": "List calendar events for a specific date or date range. Use this when user asks 'what's on my calendar', 'what do I have today', etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format, or 'today' for today's date"
                },
                "days_ahead": {
                    "type": "integer",
                    "description": "Number of days to look ahead from the start date (default 1)",
                    "default": 1
                }
            },
            "required": ["date"]
        }
    }

]

def process_tool_call(tool_name, tool_input):
    """Execute the actual tool function"""
    
    if tool_name == "create_event":
        return create_event(**tool_input)
    
    elif tool_name == "list_events":
        return list_events(**tool_input)
    
    elif tool_name == "delete_event":
        return delete_event(**tool_input)
    
    elif tool_name == "update_event":
        return update_event(**tool_input)
    
    else:
        return {"error": f"Unknown tool: {tool_name}"}

def chat_with_agent(user_message):
    """
    Send a message to the agent and handle tool calls
    
    Args:
        user_message: The user's text command
    
    Returns:
        The agent's final response
    """
    
    # Add context about current date/time
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M")
    
    system_message = f"""You are a helpful voice calendar assistant. 
Current date: {current_date}
Current time: {current_time}

When the user mentions relative dates like 'tomorrow', 'next week', etc., calculate the exact date.
When they say times like '2pm', '3:30', convert to 24-hour format.
Be conversational and friendly in your responses."""

    messages = [{"role": "user", "content": user_message}]
    
    # Initial request to Claude
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=system_message,
        tools=CALENDAR_TOOLS,
        messages=messages
    )
    
    # Handle tool use loop
    while response.stop_reason == "tool_use":
        # Claude wants to call a tool!
        # Extract what tool and what parameters
        tool_use_block = next(block for block in response.content if block.type == "tool_use")
        tool_name = tool_use_block.name
        tool_input = tool_use_block.input
        
        print(f"\n🔧 Agent calling tool: {tool_name}")
        print(f"   Input: {json.dumps(tool_input, indent=2)}")
        
        # Execute the tool
        tool_result = process_tool_call(tool_name, tool_input)
        
        print(f"   Result: {json.dumps(tool_result, indent=2)}")
        
        # Continue conversation with tool result
        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use_block.id,
                "content": json.dumps(tool_result)
            }]
        })
        
        # Get next response from Claude
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system_message,
            tools=CALENDAR_TOOLS,
            messages=messages
        )
    
    # Extract final text response
    final_response = next(
        (block.text for block in response.content if hasattr(block, "text")),
        "Done!"
    )
    
    return final_response

# Test it!
if __name__ == '__main__':
    print("🗓️  Voice Calendar Agent (Text Mode)\n")
    print("Examples:")
    print("  - 'Schedule lunch with Sarah tomorrow at noon'")
    print("  - 'What's on my calendar today?'")
    print("  - 'Add a dentist appointment next Monday at 2pm'")
    print("\nType 'quit' to exit\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        try:
            response = chat_with_agent(user_input)
            print(f"\nAgent: {response}\n")
        
        except Exception as e:
            print(f"\n❌ Error: {e}\n")