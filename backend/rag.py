import os
import re
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from youtube_transcript_api import YouTubeTranscriptApi


load_dotenv()

TARGET_LANGUAGES = ["en", "en-US", "en-GB", "hi", "es", "fr", "de"]
VIDEO_ID_PATTERN = r"[0-9A-Za-z_-]{11}"


def extract_video_id(url):
    """Extract the video ID from regular YouTube URLs, Shorts, embeds, and short links."""
    parsed_url = urlparse(url or "")
    hostname = parsed_url.hostname or ""

    if hostname.endswith("youtu.be"):
        video_id = parsed_url.path.strip("/").split("/")[0]
        return video_id if re.fullmatch(VIDEO_ID_PATTERN, video_id) else None

    if "youtube.com" in hostname:
        query_video_id = parse_qs(parsed_url.query).get("v", [None])[0]
        if query_video_id and re.fullmatch(VIDEO_ID_PATTERN, query_video_id):
            return query_video_id

        path_parts = [part for part in parsed_url.path.split("/") if part]
        if len(path_parts) >= 2 and path_parts[0] in ["shorts", "embed", "live"]:
            video_id = path_parts[1]
            return video_id if re.fullmatch(VIDEO_ID_PATTERN, video_id) else None

    return None


def get_llm():
    return ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)


def fetch_transcript_text(video_id):
    api = YouTubeTranscriptApi()
    transcript = api.fetch(video_id, languages=TARGET_LANGUAGES)
    return " ".join(item.text for item in transcript)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def format_history(history):
    if not history:
        return "No previous conversation."
    return "\n".join(f"{role}: {message}" for role, message in history)


def build_chain(video_url):
    video_id = extract_video_id(video_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL.")

    llm = get_llm()
    text = fetch_transcript_text(video_id)
    print("Successfully retrieved transcript.")

    docs = [Document(page_content=text)]
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    db = FAISS.from_documents(chunks, embeddings)
    retriever = db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5},
    )

    prompt = PromptTemplate.from_template("""
You are a helpful AI assistant having a conversation about a YouTube video.

Rules:
1. Use ONLY the provided transcript context to answer.
2. If the transcript does not include the answer, politely say that I'm sorry, but the video does not provide enough information on that topic.
3. If the user asks for a summary, provide a concise overview of the main points.
4. Maintain a helpful and conversational tone.
5. Always answer in English.
6. If the transcript context is in Hindi or any other language, translate only the final answer meaning into English.
7. Never output Hindi text or Devanagari script.

Transcript Context:
{context}

Conversation So Far:
{chat_history}

Current Question:
{question}

Assistant Answer:
""")

    chain = (
        {
            "context": lambda x: format_docs(retriever.invoke(x["question"])),
            "chat_history": lambda x: x["chat_history"],
            "question": lambda x: x["question"],
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, llm


def ask_video(chain, llm, question, history=None):
    return chain.invoke({
        "question": question,
        "chat_history": format_history(history or []),
    })


def run_cli():
    video_url = input("Please paste the YouTube URL: ")

    try:
        chain, llm = build_chain(video_url)
    except Exception as e:
        print(f"Error: {e}")
        return

    print("\n--- Summary ---")
    print(ask_video(
        chain,
        llm,
        "Provide a concise summary of this video based on the transcript.",
    ))

    print("\nStart Conversation! (Type 'exit' to quit)")
    history = []

    while True:
        user_query = input("\nuser: ")

        if user_query.lower() in ["exit"]:
            print("GoodBye! Keep learning, keep building, and keep moving forward.")
            break

        if not user_query.strip():
            continue

        history.append(("user", user_query))

        try:
            response = ask_video(chain, llm, user_query, history)
            history.append(("ai", response))
            print(f"\nai: {response}")
        except Exception as e:
            print(f"An error occurred while processing your question: {e}")
