from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from backend.rag import (
        ask_video,
        build_chain,
        extract_video_id
    )
except ImportError:
    from rag import (
        ask_video,
        build_chain,
        extract_video_id
    )


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)

# Allow requests from Chrome Extension / local frontend
CORS(app)


# ============================================================
# VIDEO SESSIONS
# ============================================================

# Stores the RAG chain for each processed YouTube video.
#
# Example:
#
# video_sessions = {
#     "abc123xyz89": {
#         "chain": ...,
#         "llm": ...,
#         "history": [...]
#     }
# }

video_sessions = {}


# ============================================================
# HOME / HEALTH CHECK
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "status": "success",
        "message": "VidMind AI backend is running 🚀"
    })


# ============================================================
# SUMMARIZE VIDEO
# ============================================================

@app.route("/summarize", methods=["POST"])
def summarize():

    # --------------------------------------------------------
    # Get request data
    # --------------------------------------------------------

    data = request.get_json(
        silent=True
    ) or {}

    video_url = data.get("url")


    # --------------------------------------------------------
    # Validate URL
    # --------------------------------------------------------

    if not video_url:

        return jsonify({
            "error": "Missing YouTube URL."
        }), 400


    # --------------------------------------------------------
    # Extract video ID
    # --------------------------------------------------------

    video_id = extract_video_id(
        video_url
    )


    if not video_id:

        return jsonify({
            "error": "Invalid YouTube URL."
        }), 400


    # --------------------------------------------------------
    # Check if video is already processed
    # --------------------------------------------------------

    if video_id in video_sessions:

        session = video_sessions[video_id]

        return jsonify({
            "video_id": video_id,
            "summary": session["summary"],
            "message": "Video already processed."
        })


    # --------------------------------------------------------
    # Build RAG chain
    # --------------------------------------------------------

    try:

        print(
            f"\nProcessing YouTube video: {video_id}"
        )

        chain, llm = build_chain(
            video_url
        )


        # ----------------------------------------------------
        # Generate summary
        # ----------------------------------------------------

        summary = ask_video(
            chain,
            llm,
            "Provide a concise summary of this video based on the transcript.",
            history=[]
        )


        # ----------------------------------------------------
        # Store session
        # ----------------------------------------------------

        video_sessions[video_id] = {

            "chain": chain,

            "llm": llm,

            "summary": summary,

            # Previous conversation only.
            # The summary itself is not treated as
            # a user/AI conversation exchange.
            "history": []

        }


        print(
            f"Video {video_id} processed successfully."
        )


    except Exception as e:

        print(
            f"Error processing video: {e}"
        )

        return jsonify({
            "error": str(e)
        }), 500


    # --------------------------------------------------------
    # Return summary
    # --------------------------------------------------------

    return jsonify({

        "video_id": video_id,

        "summary": summary

    })


# ============================================================
# CHAT WITH VIDEO
# ============================================================

@app.route("/chat", methods=["POST"])
def chat():

    # --------------------------------------------------------
    # Get request data
    # --------------------------------------------------------

    data = request.get_json(
        silent=True
    ) or {}

    video_id = data.get("video_id")

    question = data.get("question")


    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not video_id or not question:

        return jsonify({
            "error": "Missing video_id or question."
        }), 400


    # --------------------------------------------------------
    # Find existing video session
    # --------------------------------------------------------

    session = video_sessions.get(
        video_id
    )


    if not session:

        return jsonify({
            "error": "Please summarize this video first."
        }), 404


    # --------------------------------------------------------
    # Ask question
    # --------------------------------------------------------

    try:

        # IMPORTANT:
        # Pass only previous conversation history.
        previous_history = session["history"]


        answer = ask_video(
            session["chain"],
            session["llm"],
            question,
            previous_history
        )


        # ----------------------------------------------------
        # Store current conversation AFTER generating answer
        # ----------------------------------------------------

        session["history"].append(
            ("user", question)
        )

        session["history"].append(
            ("ai", answer)
        )


    except Exception as e:

        print(
            f"Error answering question: {e}"
        )

        return jsonify({
            "error": str(e)
        }), 500


    # --------------------------------------------------------
    # Return answer
    # --------------------------------------------------------

    return jsonify({

        "video_id": video_id,

        "answer": answer

    })


# ============================================================
# RUN FLASK SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )