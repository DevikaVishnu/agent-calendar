# Voice Calendar Agent

AI-powered voice assistant for Google Calendar

## Setup

1. Clone the repo:
```bash
   git clone <your-repo-url>
   cd agent-calender
```

2. Install dependencies:
```bash
   pip install -r requirements.txt
```

3. Set up Google Calendar API:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Google Calendar API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download as `credentials.json` and place in project root

4. Create `.env` file with your API keys:
```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   OPENAI_API_KEY=sk-your-key-here
```

5. Run:
```bash
   python voice_calendar.py
```

## Environment Variables Required

- `ANTHROPIC_API_KEY` - Get from [Anthropic Console](https://console.anthropic.com/)
- `OPENAI_API_KEY` - Get from [OpenAI Platform](https://platform.openai.com/api-keys)

## Files Not in Repo (You Need to Create)

- `.env` - Your API keys
- `credentials.json` - Google OAuth credentials
- `token.json` - Auto-generated on first run
