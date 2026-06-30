import os
import requests
from dotenv import load_dotenv

load_dotenv()

INVOKE_URL = os.getenv("NVIDIA_INVOKE_URL", "https://integrate.api.nvidia.com/v1/chat/completions")
API_KEY = os.getenv("NVIDIA_API_KEY", "")

def chat_completion(message, model="google/gemma-4-31b-it", stream=False, max_tokens=1024):
    if not API_KEY:
        raise RuntimeError("NVIDIA_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "text/event-stream" if stream else "application/json",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "max_tokens": max_tokens,
        "temperature": 1.0,
        "top_p": 0.95,
        "stream": stream,
        "chat_template_kwargs": {"enable_thinking": True},
    }

    resp = requests.post(INVOKE_URL, headers=headers, json=payload, stream=stream, timeout=30)
    resp.raise_for_status()
    if stream:
        for line in resp.iter_lines():
            if line:
                yield line.decode("utf-8")
    else:
        return resp.json()


def is_configured():
    """Return True when the NVIDIA API key is available."""
    return bool(API_KEY)


def extract_text_from_response(resp_json):
    """Attempt to extract assistant text from common completion response shapes.

    Returns a string or None.
    """
    if not isinstance(resp_json, dict):
        return None
    # Common shape: {'choices': [{'message': {'content': '...'}}]}
    choices = resp_json.get('choices')
    if isinstance(choices, list) and choices:
        first = choices[0]
        # message.content
        msg = first.get('message') or first.get('delta')
        if isinstance(msg, dict):
            content = msg.get('content') or msg.get('text')
            if isinstance(content, str):
                return content
        # older shape: {'choices': [{'text': '...'}]}
        text = first.get('text')
        if isinstance(text, str):
            return text
    # Fallback: try top-level 'text' or 'message'
    if isinstance(resp_json.get('text'), str):
        return resp_json.get('text')
    if isinstance(resp_json.get('message'), str):
        return resp_json.get('message')
    return None
