import os.path
from datetime import datetime, timedelta, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dateutil import parser
from logger_config import get_logger

logger = get_logger(__name__)
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """
    This function handles authentication with Google
    
    How it works:
    1. Checks if token.json exists (saved credentials)
    2. If yes and valid → use it
    3. If expired → refresh it
    4. If no token → open browser for user to log in
    5. Save new token for next time
    6. Return authenticated 'service' object
    """
    logger.debug("Getting calendar service...")
    creds = None

    # Do we have saved credentials?
    if os.path.exists('token.json'):
        logger.debug("Found existing token.json")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Are they valid?
    if not creds or not creds.valid:
        # Try to refresh if expired
        if creds and creds.expired and creds.refresh_token:
            logger.info("Access token expired, refreshing...")
            creds.refresh(Request())
        else:
            # No valid creds → log in via browser
            logger.info("No valid credentials, starting OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save for next time
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        logger.debug("Saved credentials to token.json")

    # Return service object (used to make API calls)
    logger.debug("Calendar service authenticated successfully")
    return build('calendar', 'v3', credentials=creds)

def create_event(title, date, time, duration_minutes=60, description=""):
    """
    Create a calendar event
    
    Args:
        title: Event title/summary
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (24-hour)
        duration_minutes: Duration in minutes (default 60)
        description: Optional event description
    
    Returns:
        Dictionary with event details
    """
    logger.info(f"Creating event: '{title}' on {date} at {time} for {duration_minutes} min")
    
    try:
        service = get_calendar_service()
        
        # Parse datetime
        datetime_str = f"{date} {time}"
        start_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/New_York',  # Change to your timezone if needed
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/New_York',
            },
        }
        # Step 5: Send to Google Calendar API
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        logger.info(f"Successfully created event: {created_event['id']}")
        logger.debug(f"Event details: {created_event}")

        return {
            'id': created_event['id'],
            'title': created_event['summary'],
            'start': created_event['start']['dateTime'],
            'link': created_event.get('htmlLink')
        }

    except Exception as e:
        logger.error(f"Failed to create event '{title}': {str(e)}", exc_info=True)
        raise
    
def list_events(date=None, days_ahead=1):
    """
    List calendar events
    
    Args:
        date: Specific date in YYYY-MM-DD format (or 'today'). If None, uses today
        days_ahead: Number of days to look ahead (default 1)
    
    Returns:
        List of event dictionaries
    """
    logger.info(f"Listing events for date={date}, days_ahead={days_ahead}")

    try:
        service = get_calendar_service()
        
        # Parse date
        if date == "today" or date is None:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = datetime.strptime(date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        
        end_date = start_date + timedelta(days=days_ahead)
        
        time_min = start_date.astimezone().isoformat()
        time_max = end_date.astimezone().isoformat()

        logger.debug(f"Querying events from {time_min} to {time_max}")

        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        logger.info(f"Found {len(events)} events")

        result = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            result.append({
                'id': event['id'],
                'title': event['summary'],
                'start': start,
                'description': event.get('description', '')
            })
            logger.debug(f"Event: {event['summary']} at {start}")
        
        return result
    except Exception as e:
        logger.error(f"Failed to list events: {str(e)}", exc_info=True)
        raise

def delete_event(event_id):
    """Delete a calendar event by ID"""
    logger.info(f"Deleting event with ID: {event_id}")

    try:
        service = get_calendar_service()
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return {'success': True, 'message': f'Event {event_id} deleted'}
    except Exception as e:
        logger.error(f"Failed to delete event {event_id}: {str(e)}", exc_info=True)
        raise

def delete_event_by_title(title, date="today", days_ahead=1):
    logger.info(f"Attempting to delete event by title: '{title}' on {date}")

    try:
        service = get_calendar_service()

        events_list = list_events(date=date, days_ahead=days_ahead)
        if not events_list:
            logger.warning(f"No events found on {date}")
            return {
                "success": False,
                "message": f"No events found on {date}"
            }

        for event in events_list:
            if event['title'].lower() == title.lower():
                logger.info(f"Found matching event: '{event['title']}' (ID: {event['id']})")

                try:
                    delete_event(event['id'])
                    return {
                        "success": True,
                        "message": f"Deleted event: {event['title']}"
                    }
                except Exception as e:
                    logger.error(f"Error during deletion: {str(e)}")
                    return {
                        "success": False,
                        "message": f"Error deleting event: {str(e)}"
                    }
        logger.warning(f"No event found matching title '{title}' on {date}")
        return {
            "success": False,
            "message": f"Could not find an event with title '{title}' on {date}"
        }
    except Exception as e:
        logger.error(f"Failed to delete event by title '{title}': {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

def update_event(event_id, title=None, date=None, time=None, duration_minutes=None):
    """Update an existing event"""
    service = get_calendar_service()
    
    # Get existing event
    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    
    # Update fields if provided
    if title:
        event['summary'] = title
    
    if date and time:
        datetime_str = f"{date} {time}"
        start_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        
        if duration_minutes:
            end_time = start_time + timedelta(minutes=duration_minutes)
        else:
            # Keep original duration
            original_start = parser.parse(event['start']['dateTime'])
            original_end = parser.parse(event['end']['dateTime'])
            original_duration = (original_end - original_start).total_seconds() / 60
            end_time = start_time + timedelta(minutes=original_duration)
        
        event['start']['dateTime'] = start_time.isoformat()
        event['end']['dateTime'] = end_time.isoformat()
    
    updated_event = service.events().update(
        calendarId='primary',
        eventId=event_id,
        body=event
    ).execute()
    
    return {
        'id': updated_event['id'],
        'title': updated_event['summary'],
        'start': updated_event['start']['dateTime']
    }

# Test functions
if __name__ == '__main__':
    print("Testing calendar tools...")
    
    # Test list events
    print("\n📅 Today's events:")
    events = list_events('today')
    for e in events:
        print(f"  - {e['title']} at {e['start']}")
    
    # Test create event
    print("\n➕ Creating test event...")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    new_event = create_event(
        title="Test from Voice Agent",
        date=tomorrow,
        time="15:00",
        duration_minutes=30
    )
    print(f"  Created: {new_event['title']} at {new_event['start']}")
    print(f"  Link: {new_event['link']}")