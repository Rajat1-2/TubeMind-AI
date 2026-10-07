const API_BASE_URL = "https://tubemind-ai-ap91.onrender.com";

let currentVideoId = null;

const summarizeBtn = document.getElementById("summarizeBtn");
const summaryOutput = document.getElementById("summaryOutput");
const statusText = document.getElementById("status");
const chatLog = document.getElementById("chatLog");
const chatForm = document.getElementById("chatForm");
const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");

function setStatus(message) {
  statusText.innerText = message;
}

function showProgressSteps() {
  const steps = [
    "Input captured...",
    "Transcript fetched...",
    "Text splitter running...",
    "Embeddings created...",
    "Vector memory ready...",
    "Prompt prepared...",
    "LLM answering in English...",
    "Parser formatting...",
    "Chain complete...",
  ];

  let index = 0;
  setStatus(steps[index]);

  return setInterval(() => {
    index = Math.min(index + 1, steps.length - 1);
    setStatus(steps[index]);
  }, 1800);
}

function setChatEnabled(enabled) {
  questionInput.disabled = !enabled;
  sendBtn.disabled = !enabled;
}

function addMessage(role, text) {
  const message = document.createElement("div");
  message.className = `message ${role}`;
  message.innerText = text;
  chatLog.appendChild(message);
  chatLog.scrollTop = chatLog.scrollHeight;
}

async function getCurrentTabUrl() {
  const [tab] = await chrome.tabs.query({
    active: true,
    currentWindow: true,
  });

  return tab.url;
}

// ===============================
// SUMMARIZE VIDEO
// ===============================

summarizeBtn.addEventListener("click", async () => {
  summarizeBtn.disabled = true;
  setChatEnabled(false);

  const progressTimer = showProgressSteps();

  summaryOutput.innerText = "Loading summary...";
  chatLog.innerHTML = "";
  currentVideoId = null;

  try {
    const videoUrl = await getCurrentTabUrl();

    const response = await fetch(`${API_BASE_URL}/summarize`, {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        url: videoUrl,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Could not summarize this video.");
    }

    currentVideoId = data.video_id;

    summaryOutput.innerText = data.summary;

    addMessage("ai", "Summary ready. Ask me anything about this video.");

    setChatEnabled(true);

    questionInput.focus();

    setStatus("Ready to chat.");
  } catch (error) {
    summaryOutput.innerText = error.message;

    addMessage("ai", "I could not prepare this video. Please try again.");

    setStatus("Something went wrong.");
  } finally {
    clearInterval(progressTimer);

    summarizeBtn.disabled = false;
  }
});

// ===============================
// CHAT WITH VIDEO
// ===============================

chatForm.addEventListener("submit", async event => {
  event.preventDefault();

  const question = questionInput.value.trim();

  if (!question || !currentVideoId) {
    return;
  }

  questionInput.value = "";

  addMessage("user", question);

  setChatEnabled(false);

  setStatus("Thinking...");

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        video_id: currentVideoId,
        question: question,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Could not answer that question.");
    }

    addMessage("ai", data.answer);

    setStatus("Ready to chat.");
  } catch (error) {
    addMessage("ai", error.message);

    setStatus("Something went wrong.");
  } finally {
    setChatEnabled(true);

    questionInput.focus();
  }
});
