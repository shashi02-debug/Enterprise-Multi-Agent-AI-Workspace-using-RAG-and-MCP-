from __future__ import annotations

import asyncio
import base64
import concurrent.futures
import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx2
from dotenv import load_dotenv
from mcp import Client
from mcp.client.streamable_http import streamable_http_client


# ============================================================
# Environment
# ============================================================

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()

GOOGLE_GMAIL_REDIRECT_URI = os.getenv(
    "GOOGLE_GMAIL_REDIRECT_URI",
    "http://127.0.0.1:8000/mcp/gmail/callback",
).strip()

GOOGLE_GMAIL_MCP_URL = os.getenv(
    "GOOGLE_GMAIL_MCP_URL",
    "https://gmailmcp.googleapis.com/mcp/v1",
).strip()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

GOOGLE_GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]

# Gmail MCP resource binding.
GOOGLE_GMAIL_MCP_RESOURCE = GOOGLE_GMAIL_MCP_URL


# ============================================================
# Local MCP data storage
# ============================================================

DATA_DIR = Path(__file__).resolve().parents[2] / ".mcp_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GMAIL_TOKEN_FILE = DATA_DIR / "google_gmail_tokens.json"
GMAIL_OAUTH_STATE_FILE = DATA_DIR / "google_gmail_oauth_states.json"
GMAIL_OAUTH_VERIFIER_FILE = DATA_DIR / "google_gmail_oauth_code_verifier.json"

STATE_EXPIRY_SECONDS = 600


# ============================================================
# OAuth state
# ============================================================

def _load_oauth_states() -> Dict[str, Any]:
    if not GMAIL_OAUTH_STATE_FILE.exists():
        return {}

    try:
        with GMAIL_OAUTH_STATE_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, dict) else {}

    except (OSError, json.JSONDecodeError):
        return {}


def _save_oauth_states(states: Dict[str, Any]) -> None:
    temp_file = DATA_DIR / "google_gmail_oauth_states.tmp"

    with temp_file.open("w", encoding="utf-8") as file:
        json.dump(states, file, indent=2)

    temp_file.replace(GMAIL_OAUTH_STATE_FILE)


def create_gmail_oauth_state(
    code_verifier: Optional[str] = None,
) -> str:

    state = secrets.token_urlsafe(32)
    now = time.time()

    states = _load_oauth_states()
    cleaned: Dict[str, Any] = {}

    for key, value in states.items():
        try:
            created_at = (
                float(value.get("created_at", 0))
                if isinstance(value, dict)
                else float(value)
            )

            if now - created_at < STATE_EXPIRY_SECONDS:
                cleaned[str(key)] = value

        except (TypeError, ValueError):
            continue

    cleaned[state] = {
        "created_at": now,
        "code_verifier": code_verifier,
    }

    _save_oauth_states(cleaned)
    return state


def validate_gmail_oauth_state(state: str) -> bool:

    if not state:
        return False

    states = _load_oauth_states()
    entry = states.get(state)

    if entry is None:
        return False

    try:
        if isinstance(entry, dict):
            created_at = float(entry.get("created_at", 0))
            code_verifier = entry.get("code_verifier")
        else:
            created_at = float(entry)
            code_verifier = None

    except (TypeError, ValueError):
        return False

    if time.time() - created_at > STATE_EXPIRY_SECONDS:
        states.pop(state, None)
        _save_oauth_states(states)
        return False

    # Preserve the verifier for the callback exchange.
    if isinstance(code_verifier, str):
        _save_code_verifier(code_verifier)

    # OAuth state is single-use.
    states.pop(state, None)
    _save_oauth_states(states)

    return True


# ============================================================
# PKCE
# ============================================================

def _save_code_verifier(code_verifier: str) -> None:

    temp_file = DATA_DIR / "google_gmail_oauth_code_verifier.tmp"

    with temp_file.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "code_verifier": code_verifier,
                "created_at": time.time(),
            },
            file,
            indent=2,
        )

    temp_file.replace(GMAIL_OAUTH_VERIFIER_FILE)


def _load_code_verifier() -> Optional[str]:

    if not GMAIL_OAUTH_VERIFIER_FILE.exists():
        return None

    try:
        with GMAIL_OAUTH_VERIFIER_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return None

        created_at = float(data.get("created_at", 0))

        if time.time() - created_at > STATE_EXPIRY_SECONDS:
            return None

        verifier = data.get("code_verifier")
        return verifier if isinstance(verifier, str) else None

    except (
        OSError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):
        return None


def _delete_code_verifier() -> None:

    try:
        if GMAIL_OAUTH_VERIFIER_FILE.exists():
            GMAIL_OAUTH_VERIFIER_FILE.unlink()
    except OSError:
        pass


def _generate_pkce_verifier() -> str:
    return secrets.token_urlsafe(96)


def _generate_pkce_challenge(code_verifier: str) -> str:

    digest = hashlib.sha256(
        code_verifier.encode("ascii")
    ).digest()

    return (
        base64.urlsafe_b64encode(digest)
        .decode("ascii")
        .rstrip("=")
    )


# ============================================================
# Token persistence
# ============================================================

def _load_tokens() -> Dict[str, Any]:

    if not GMAIL_TOKEN_FILE.exists():
        return {}

    try:
        with GMAIL_TOKEN_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return data if isinstance(data, dict) else {}

    except (OSError, json.JSONDecodeError):
        return {}


def _save_tokens(tokens: Dict[str, Any]) -> None:

    temp_file = DATA_DIR / "google_gmail_tokens.tmp"

    with temp_file.open("w", encoding="utf-8") as file:
        json.dump(tokens, file, indent=2)

    temp_file.replace(GMAIL_TOKEN_FILE)


# ============================================================
# Gmail OAuth authorization
# ============================================================

def create_gmail_authorization_url() -> str:

    if not GOOGLE_CLIENT_ID:
        raise RuntimeError(
            "GOOGLE_CLIENT_ID is not configured."
        )

    if not GOOGLE_CLIENT_SECRET:
        raise RuntimeError(
            "GOOGLE_CLIENT_SECRET is not configured."
        )

    code_verifier = _generate_pkce_verifier()
    code_challenge = _generate_pkce_challenge(code_verifier)

    state = create_gmail_oauth_state(code_verifier)

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_GMAIL_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_GMAIL_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "resource": GOOGLE_GMAIL_MCP_RESOURCE,
    }

    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_gmail_authorization_code(
    code: str,
) -> Dict[str, Any]:

    if not code:
        raise ValueError("Authorization code is missing.")

    code_verifier = _load_code_verifier()

    if not code_verifier:
        raise RuntimeError(
            "Gmail PKCE code verifier is missing or expired. "
            "Please authorize Gmail again."
        )

    payload = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_GMAIL_REDIRECT_URI,
        "grant_type": "authorization_code",
        "code_verifier": code_verifier,
        "resource": GOOGLE_GMAIL_MCP_RESOURCE,
    }

    async with httpx2.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data=payload,
        )

    if response.status_code != 200:
        raise RuntimeError(
            "Google Gmail token exchange failed: "
            f"{response.text}"
        )

    token_data = response.json()

    expires_in = int(token_data.get("expires_in", 3600))

    token_data["expires_at"] = int(
        time.time() + expires_in
    )

    token_data["mcp_resource"] = GOOGLE_GMAIL_MCP_RESOURCE

    _save_tokens(token_data)
    _delete_code_verifier()

    return token_data


async def refresh_gmail_access_token(
    refresh_token: str,
) -> Dict[str, Any]:

    payload = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
        "resource": GOOGLE_GMAIL_MCP_RESOURCE,
    }

    async with httpx2.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data=payload,
        )

    if response.status_code != 200:
        raise RuntimeError(
            "Google Gmail token refresh failed: "
            f"{response.text}"
        )

    refreshed = response.json()

    expires_in = int(
        refreshed.get("expires_in", 3600)
    )

    refreshed["expires_at"] = int(
        time.time() + expires_in
    )

    refreshed["refresh_token"] = (
        refreshed.get("refresh_token")
        or refresh_token
    )

    refreshed["mcp_resource"] = (
        GOOGLE_GMAIL_MCP_RESOURCE
    )

    _save_tokens(refreshed)

    return refreshed


async def get_gmail_access_token() -> str:

    tokens = _load_tokens()

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    if not access_token:
        raise RuntimeError(
            "Gmail is not connected. Authorize Gmail first."
        )

    try:
        expires_at = float(
            tokens.get("expires_at", 0)
        )
    except (TypeError, ValueError):
        expires_at = 0

    # Refresh one minute before expiry.
    if time.time() >= expires_at - 60:

        if not refresh_token:
            raise RuntimeError(
                "Gmail access token expired and no refresh token "
                "is available."
            )

        refreshed = await refresh_gmail_access_token(
            refresh_token
        )

        access_token = refreshed.get("access_token")

        if not access_token:
            raise RuntimeError(
                "Gmail token refresh returned no access token."
            )

    return access_token


# ============================================================
# Gmail MCP status
# ============================================================

def get_gmail_status() -> Dict[str, Any]:

    tokens = _load_tokens()

    configured = bool(
        GOOGLE_CLIENT_ID
        and GOOGLE_CLIENT_SECRET
        and GOOGLE_GMAIL_REDIRECT_URI
        and GOOGLE_GMAIL_MCP_URL
    )

    connected = bool(
        tokens.get("access_token")
    )

    try:
        expires_at = float(
            tokens.get("expires_at", 0)
        )
        token_valid = time.time() < expires_at
    except (TypeError, ValueError):
        token_valid = False

    return {
        "configured": configured,
        "connected": connected,
        "token_valid": token_valid,
        "mcp_url": GOOGLE_GMAIL_MCP_URL,
        "mcp_resource": GOOGLE_GMAIL_MCP_RESOURCE,
        "redirect_uri": GOOGLE_GMAIL_REDIRECT_URI,
        "scopes": GOOGLE_GMAIL_SCOPES,
        "authentication": (
            "Google OAuth 2.0 with PKCE "
            "and MCP resource binding"
        ),
    }


# ============================================================
# MCP result conversion
# ============================================================

def _convert_mcp_result(result: Any) -> Any:

    if result is None:
        return None

    def normalize(value: Any) -> Any:

        if value is None:
            return None

        if isinstance(value, dict):
            return {
                str(key): normalize(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [
                normalize(item)
                for item in value
            ]

        model_dump = getattr(
            value,
            "model_dump",
            None,
        )

        if callable(model_dump):
            try:
                return normalize(
                    model_dump(mode="json")
                )
            except TypeError:
                return normalize(
                    model_dump()
                )

        text_value = getattr(
            value,
            "text",
            None,
        )

        if text_value is not None:

            try:
                return normalize(
                    json.loads(text_value)
                )
            except (
                json.JSONDecodeError,
                TypeError,
            ):
                return text_value

        data = getattr(
            value,
            "data",
            None,
        )

        if data is not None:
            return normalize(data)

        return str(value)

    structured = getattr(
        result,
        "structured_content",
        None,
    )

    if structured is None:
        structured = getattr(
            result,
            "structuredContent",
            None,
        )

    if structured is not None:
        return normalize(structured)

    content = getattr(
        result,
        "content",
        None,
    )

    if content is not None:

        converted = [
            normalize(item)
            for item in content
        ]

        if len(converted) == 1:
            return converted[0]

        return converted

    return normalize(result)


# ============================================================
# Gmail MCP tool call
# ============================================================

async def _call_gmail_mcp_tool(
    tool_name: str,
    arguments: Optional[Dict[str, Any]] = None,
) -> Any:

    access_token = await get_gmail_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    timeout = httpx2.Timeout(
        30.0,
        read=300.0,
    )

    async with httpx2.AsyncClient(
        headers=headers,
        timeout=timeout,
        follow_redirects=True,
    ) as http_client:

        transport = streamable_http_client(
            GOOGLE_GMAIL_MCP_URL,
            http_client=http_client,
        )

        async with Client(transport) as client:

            result = await client.call_tool(
                tool_name,
                arguments or {},
            )

            # MCP can report tool-level errors inside the result.
            if getattr(result, "is_error", False):

                error_details = _convert_mcp_result(result)

                raise RuntimeError(
                    f"Gmail MCP tool '{tool_name}' failed: "
                    f"{error_details}"
                )

            return _convert_mcp_result(result)


# ============================================================
# List Gmail MCP tools
# ============================================================

async def list_gmail_tools() -> List[Dict[str, Any]]:

    access_token = await get_gmail_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    timeout = httpx2.Timeout(
        30.0,
        read=300.0,
    )

    async with httpx2.AsyncClient(
        headers=headers,
        timeout=timeout,
        follow_redirects=True,
    ) as http_client:

        transport = streamable_http_client(
            GOOGLE_GMAIL_MCP_URL,
            http_client=http_client,
        )

        async with Client(transport) as client:

            tools_result = await client.list_tools()

            output = []

            for tool in tools_result.tools:

                item = {
                    "name": tool.name,
                    "description": tool.description,
                }

                input_schema = getattr(
                    tool,
                    "inputSchema",
                    None,
                )

                if input_schema is None:
                    input_schema = getattr(
                        tool,
                        "input_schema",
                        None,
                    )

                if input_schema is not None:
                    item["input_schema"] = input_schema

                output.append(item)

            return output


# ============================================================
# Gmail search
# ============================================================

async def search_gmail_threads(
    query: str,
    max_results: int = 10,
) -> Any:

    cleaned = (query or "").strip()

    if not cleaned:
        return []

    max_results = max(
        1,
        min(int(max_results), 50),
    )

    # IMPORTANT:
    # Google Gmail MCP uses pageSize, not maxResults.
    # maxResults causes the remote MCP server to reject
    # the tool call.
    return await _call_gmail_mcp_tool(
        "search_threads",
        {
            "query": cleaned,
            "pageSize": max_results,
            "view": "THREAD_VIEW_MINIMAL",
        },
    )


# ============================================================
# Get Gmail thread
# ============================================================

async def get_gmail_thread(
    thread_id: str,
    message_format: str = "FULL_CONTENT",
) -> Any:

    if not thread_id:
        raise ValueError(
            "Gmail thread ID is required."
        )

    return await _call_gmail_mcp_tool(
        "get_thread",
        {
            "threadId": thread_id,
            "messageFormat": message_format,
        },
    )


# ============================================================
# Get Gmail message
# ============================================================

async def get_gmail_message(
    message_id: str,
    message_format: str = "FULL_CONTENT",
) -> Any:

    if not message_id:
        raise ValueError(
            "Gmail message ID is required."
        )

    return await _call_gmail_mcp_tool(
        "get_message",
        {
            "messageId": message_id,
            "messageFormat": message_format,
        },
    )


# ============================================================
# List Gmail labels
# ============================================================

async def list_gmail_labels() -> Any:

    return await _call_gmail_mcp_tool(
        "list_labels",
        {},
    )


# ============================================================
# List Gmail drafts
# ============================================================

async def list_gmail_drafts(
    max_results: int = 20,
) -> Any:

    max_results = max(
        1,
        min(int(max_results), 50),
    )

    return await _call_gmail_mcp_tool(
        "list_drafts",
        {
            "pageSize": max_results,
            "view": "DRAFT_VIEW_FULL",
        },
    )


# ============================================================
# Get Gmail draft
# ============================================================

async def get_gmail_draft(
    draft_id: str,
    message_format: str = "FULL_CONTENT",
) -> Any:

    if not draft_id:
        raise ValueError(
            "Gmail draft ID is required."
        )

    return await _call_gmail_mcp_tool(
        "get_draft",
        {
            "draftId": draft_id,
            "messageFormat": message_format,
        },
    )


# ============================================================
# Create Gmail draft
# ============================================================

async def create_gmail_draft(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    thread_id: Optional[str] = None,
    html_body: Optional[str] = None,
) -> Any:

    if not to.strip():
        raise ValueError(
            "Recipient email address is required."
        )

    if not subject.strip():
        raise ValueError(
            "Email subject is required."
        )

    if not body.strip():
        raise ValueError(
            "Email body is required."
        )

    # IMPORTANT:
    # Gmail MCP expects recipient arrays and uses
    # replyToMessageId for replies, not threadId.
    arguments: Dict[str, Any] = {
        "to": [
            item.strip()
            for item in to.split(",")
            if item.strip()
        ],
        "subject": subject.strip(),
        "body": body,
    }

    if cc:
        arguments["cc"] = [
            item.strip()
            for item in cc.split(",")
            if item.strip()
        ]

    if bcc:
        arguments["bcc"] = [
            item.strip()
            for item in bcc.split(",")
            if item.strip()
        ]

    if html_body:
        arguments["htmlBody"] = html_body

    if thread_id:
        # Backward-compatible parameter name in this helper.
        # The actual MCP API expects a MESSAGE id when replying.
        arguments["replyToMessageId"] = thread_id.strip()

    return await _call_gmail_mcp_tool(
        "create_draft",
        arguments,
    )


# ============================================================
# Gmail labels
# ============================================================

async def label_gmail_message(
    message_id: str,
    label_ids: List[str],
) -> Any:

    if not message_id:
        raise ValueError(
            "Gmail message ID is required."
        )

    return await _call_gmail_mcp_tool(
        "label_message",
        {
            "messageId": message_id,
            "labelIds": label_ids,
        },
    )


async def label_gmail_thread(
    thread_id: str,
    label_ids: List[str],
) -> Any:

    if not thread_id:
        raise ValueError(
            "Gmail thread ID is required."
        )

    return await _call_gmail_mcp_tool(
        "label_thread",
        {
            "threadId": thread_id,
            "labelIds": label_ids,
        },
    )


# ============================================================
# Synchronous helpers
# ============================================================

def _run_async_sync(coroutine):

    try:
        return asyncio.run(coroutine)

    except RuntimeError as exc:

        if "asyncio.run()" not in str(exc):
            raise

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=1
        ) as executor:

            future = executor.submit(
                asyncio.run,
                coroutine,
            )

            return future.result()


def search_gmail_threads_sync(
    query: str,
    max_results: int = 10,
) -> Any:

    return _run_async_sync(
        search_gmail_threads(
            query,
            max_results=max_results,
        )
    )


def get_gmail_thread_sync(
    thread_id: str,
) -> Any:

    return _run_async_sync(
        get_gmail_thread(thread_id)
    )


def get_gmail_message_sync(
    message_id: str,
) -> Any:

    return _run_async_sync(
        get_gmail_message(message_id)
    )


def create_gmail_draft_sync(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    thread_id: Optional[str] = None,
    html_body: Optional[str] = None,
) -> Any:

    return _run_async_sync(
        create_gmail_draft(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            thread_id=thread_id,
            html_body=html_body,
        )
    )


# ============================================================
# Utility
# ============================================================

def gmail_is_configured() -> bool:

    return bool(
        GOOGLE_CLIENT_ID
        and GOOGLE_CLIENT_SECRET
        and GOOGLE_GMAIL_REDIRECT_URI
        and GOOGLE_GMAIL_MCP_URL
    )
