# VidMind AI

VidMind AI is a YouTube video assistant that summarizes videos and lets users chat with the transcript using a RAG pipeline.

## Features

- Summarize regular YouTube videos 
- Chat with AI about the video after summary generation
- Transcript-based answers using LangChain, FAISS, and Groq
- Chrome extension popup with a purple neon UI
- Flask backend API for summary and chat

## Project Structure

```text
VidMind AI/
├── backend/
│   ├── __init__.py
│   ├── app.py          # Flask API routes
│   └── rag.py          # YouTube transcript + RAG logic
├── Extension/
│   ├── manifest.json   # Chrome extension config
│   ├── popup.html      # Extension UI
│   └── popup.js        # Extension API calls and chat behavior
├── app.py              # Backend launcher
├── main.py             # CLI launcher
├── requirements.txt
└── README.md
```

## Setup

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

## Run the Backend

```powershell
python app.py
```

The Flask server runs at:

```text
http://127.0.0.1:5000
```

## Run the CLI

```powershell
python main.py
```

Paste a YouTube URL when prompted, then ask questions about the video transcript.

## Load the Chrome Extension

1. Open Chrome and go to:

```text
chrome://extensions
```

2. Enable **Developer mode**.
3. Click **Load unpacked**.
4. Select the `Extension/` folder.
5. Open a YouTube video.
6. Click the extension and press **Summary**.
7. Ask any doubt related to the lecture.

Make sure the Flask backend is running before using the extension.

## API Endpoints

### Summarize

```http
POST /summarize
```

Request:

```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

Response:

```json
{
  "video_id": "VIDEO_ID",
  "summary": "Video summary..."
}
```

### Chat

```http
POST /chat
```

Request:

```json
{
  "video_id": "VIDEO_ID",
  "question": "What is the main topic?"
}
```

Response:

```json
{
  "answer": "AI answer based on the transcript..."
}
```

## Notes

- The app answers using only the video transcript context.
- Chat sessions are stored in backend memory, so restarting the Flask server clears active sessions.
