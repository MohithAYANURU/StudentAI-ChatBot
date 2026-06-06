"""
models.py — all LLM API calls live here.
app.py never calls an API directly — it always goes through this file.
"""

import time
import groq
import google.generativeai as genai
from mistralai import Mistral
from config import (
    GROQ_API_KEY, GEMINI_API_KEY, MISTRAL_API_KEY,
    GROQ_MODEL, GEMINI_MODEL, MISTRAL_MODEL, MAX_TOKENS
)

# Initialize clients once at startup
groq_client    = groq.Groq(api_key=GROQ_API_KEY)
mistral_client = Mistral(api_key=MISTRAL_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)


def call_groq(messages: list) -> str:
    """Send a conversation to Groq and return the reply as a string."""
    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Groq error: {str(e)}"


def call_gemini(messages: list) -> str:
    """Send a conversation to Gemini and return the reply as a string."""
    try:
        # Gemini uses a different format — extract system prompt and history
        system_prompt = ""
        chat_history  = []

        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                chat_history.append({"role": "user",  "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                chat_history.append({"role": "model", "parts": [msg["content"]]})

        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=system_prompt
        )

        # Send everything except the last user message as history
        chat    = model.start_chat(history=chat_history[:-1])
        last    = chat_history[-1]["parts"][0]
        response = chat.send_message(last)
        return response.text
    except Exception as e:
        return f"Gemini error: {str(e)}"


def call_mistral(messages: list) -> str:
    """Send a conversation to Mistral and return the reply as a string."""
    try:
        response = mistral_client.chat.complete(
            model=MISTRAL_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Mistral error: {str(e)}"


def call_all_models(prompt: str, system_prompt: str) -> dict:
    """
    Send the same prompt to all 3 models simultaneously.
    Returns a dict with each model's reply and response time in ms.
    Used by the /compare endpoint for benchmarking.
    """
    results = {}
    models  = [
        ("groq",    call_groq),
        ("gemini",  call_gemini),
        ("mistral", call_mistral),
    ]

    for name, fn in models:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt}
        ]
        start           = time.time()
        reply           = fn(messages)
        elapsed         = round((time.time() - start) * 1000)
        results[name]   = {"reply": reply, "time_ms": elapsed}

    return results