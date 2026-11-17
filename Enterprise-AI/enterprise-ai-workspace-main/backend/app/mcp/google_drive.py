import asyncio
import base64
import hashlib
import json
import os
import re
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


GOOGLE_CLIENT_ID = os.getenv(
    "GOOGLE_CLIENT_ID",
    "",
).strip()

GOOGLE_CLIENT_SECRET = os.getenv(
    "GOOGLE_CLIENT_SECRET",
    "",
).strip()

GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "http://127.0.0.1:8000/mcp/google/callback",
).strip()

GOOGLE_DRIVE_MCP_URL = os.getenv(
    "GOOGLE_DRIVE_MCP_URL",
    "https://drivemcp.googleapis.com/mcp/v1",
).strip()


# ============================================================
# Google OAuth configuration
# ============================================================

GOOGLE_AUTH_URL = (
    "https://accounts.google.com/o/oauth2/v2/auth"
)

GOOGLE_TOKEN_URL = (
    "https://oauth2.googleapis.com/token"
)

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
]

# IMPORTANT:
# This is the MCP resource being authorized.
#
# Google Drive MCP uses the MCP endpoint itself as the
# resource identifier.
GOOGLE_MCP_RESOURCE = (
    GOOGLE_DRIVE_MCP_URL
)


# ============================================================
# Local MCP data storage
# ============================================================

# backend/.mcp_data/
DATA_DIR = (
    Path(__file__).resolve().parents[2]
    / ".mcp_data"
)

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


TOKEN_FILE = (
    DATA_DIR
    / "google_drive_tokens.json"
)

OAUTH_STATE_FILE = (
    DATA_DIR
    / "google_oauth_states.json"
)

OAUTH_VERIFIER_FILE = (
    DATA_DIR
    / "google_oauth_code_verifier.json"
)


# ============================================================
# OAuth state persistence
# ============================================================

STATE_EXPIRY_SECONDS = 600


def _load_oauth_states() -> Dict[str, Any]:
    """
    Load pending OAuth states from disk.

    Older versions of the project stored:
        state -> timestamp

    The new version stores:
        state -> {
            "created_at": timestamp,
            "code_verifier": "..."
        }

    Both formats are tolerated so existing state files
    do not crash the application.
    """

    if not OAUTH_STATE_FILE.exists():
        return {}

    try:
        with OAUTH_STATE_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return {}

        return data

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}


def _save_oauth_states(
    states: Dict[str, Any],
) -> None:
    """
    Persist OAuth states atomically.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_file = (
        DATA_DIR
        / "google_oauth_states.tmp"
    )

    with temp_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            states,
            file,
            indent=2,
        )

    temp_file.replace(
        OAUTH_STATE_FILE
    )


def _save_code_verifier(
    code_verifier: str,
) -> None:
    """
    Persist the PKCE verifier temporarily.

    This allows the existing FastAPI callback flow to
    survive Uvicorn reloads/restarts between authorization
    and token exchange.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_file = (
        DATA_DIR
        / "google_oauth_code_verifier.tmp"
    )

    with temp_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {
                "code_verifier": code_verifier,
                "created_at": time.time(),
            },
            file,
            indent=2,
        )

    temp_file.replace(
        OAUTH_VERIFIER_FILE
    )


def _load_code_verifier() -> Optional[str]:
    """
    Load the persisted PKCE verifier.
    """

    if not OAUTH_VERIFIER_FILE.exists():
        return None

    try:
        with OAUTH_VERIFIER_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(
            data,
            dict,
        ):
            return None

        created_at = float(
            data.get(
                "created_at",
                0,
            )
        )

        if (
            time.time()
            - created_at
            > STATE_EXPIRY_SECONDS
        ):
            return None

        verifier = data.get(
            "code_verifier"
        )

        if isinstance(
            verifier,
            str,
        ):
            return verifier

    except (
        OSError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):
        pass

    return None


def _delete_code_verifier() -> None:
    """
    Delete the one-time PKCE verifier.
    """

    try:
        if OAUTH_VERIFIER_FILE.exists():
            OAUTH_VERIFIER_FILE.unlink()
    except OSError:
        pass


def _generate_pkce_verifier() -> str:
    """
    Generate a high-entropy PKCE verifier.

    RFC 7636 allows 43-128 characters.
    """

    return secrets.token_urlsafe(96)


def _generate_pkce_challenge(
    code_verifier: str,
) -> str:
    """
    Generate an S256 PKCE challenge.
    """

    digest = hashlib.sha256(
        code_verifier.encode(
            "ascii"
        )
    ).digest()

    return (
        base64.urlsafe_b64encode(
            digest
        )
        .decode("ascii")
        .rstrip("=")
    )


def create_oauth_state(
    code_verifier: Optional[str] = None,
) -> str:
    """
    Create and persist a new OAuth state.

    The PKCE verifier is stored alongside the state.
    """

    state = secrets.token_urlsafe(
        32
    )

    states = _load_oauth_states()

    now = time.time()

    cleaned: Dict[str, Any] = {}

    for key, value in states.items():

        try:

            if isinstance(
                value,
                dict,
            ):
                timestamp = float(
                    value.get(
                        "created_at",
                        0,
                    )
                )
            else:
                # Backward compatibility with old format.
                timestamp = float(
                    value
                )

            if (
                now - timestamp
                < STATE_EXPIRY_SECONDS
            ):
                cleaned[
                    str(key)
                ] = value

        except (
            TypeError,
            ValueError,
        ):
            continue

    cleaned[state] = {
        "created_at": now,
        "code_verifier": code_verifier,
    }

    _save_oauth_states(
        cleaned
    )

    return state


def validate_oauth_state(
    state: str,
) -> bool:
    """
    Validate a previously-created OAuth state.

    The state is single-use.

    The associated PKCE verifier is persisted separately
    so the existing callback implementation can continue
    calling exchange_authorization_code(code).
    """

    if not state:
        return False

    states = _load_oauth_states()

    entry = states.get(
        state
    )

    if entry is None:
        return False

    try:

        if isinstance(
            entry,
            dict,
        ):
            timestamp = float(
                entry.get(
                    "created_at",
                    0,
                )
            )

            code_verifier = entry.get(
                "code_verifier"
            )

        else:
            # Old format.
            timestamp = float(
                entry
            )
            code_verifier = None

    except (
        TypeError,
        ValueError,
    ):
        return False

    if (
        time.time()
        - timestamp
        > STATE_EXPIRY_SECONDS
    ):

        states.pop(
            state,
            None,
        )

        _save_oauth_states(
            states
        )

        return False

    # Persist verifier for token exchange.
    if isinstance(
        code_verifier,
        str,
    ):
        _save_code_verifier(
            code_verifier
        )

    # Single-use state.
    states.pop(
        state,
        None,
    )

    _save_oauth_states(
        states
    )

    return True


# ============================================================
# Token persistence
# ============================================================

def _load_tokens() -> Dict[str, Any]:

    if not TOKEN_FILE.exists():
        return {}

    try:

        with TOKEN_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(
                file
            )

        if isinstance(
            data,
            dict,
        ):
            return data

    except (
        OSError,
        json.JSONDecodeError,
    ):
        pass

    return {}


def _save_tokens(
    tokens: Dict[str, Any],
) -> None:

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_file = (
        DATA_DIR
        / "google_drive_tokens.tmp"
    )

    with temp_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            tokens,
            file,
            indent=2,
        )

    temp_file.replace(
        TOKEN_FILE
    )


# ============================================================
# OAuth authorization
# ============================================================

def create_google_authorization_url() -> str:
    """
    Create the Google OAuth authorization URL.

    IMPORTANT MCP additions:
      - PKCE
      - code_challenge_method=S256
      - resource=<Google Drive MCP URL>

    The resource parameter binds the authorization to
    the Google Drive MCP resource rather than merely to
    the normal Drive API.
    """

    if not GOOGLE_CLIENT_ID:
        raise RuntimeError(
            "GOOGLE_CLIENT_ID is not configured."
        )

    if not GOOGLE_CLIENT_SECRET:
        raise RuntimeError(
            "GOOGLE_CLIENT_SECRET is not configured."
        )

    code_verifier = (
        _generate_pkce_verifier()
    )

    code_challenge = (
        _generate_pkce_challenge(
            code_verifier
        )
    )

    state = create_oauth_state(
        code_verifier
    )

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",

        "scope": " ".join(
            GOOGLE_SCOPES
        ),

        "access_type": "offline",

        "prompt": "consent",

        "include_granted_scopes": "true",

        "state": state,

        # ----------------------------------------------------
        # PKCE
        # ----------------------------------------------------

        "code_challenge": (
            code_challenge
        ),

        "code_challenge_method": "S256",

        # ----------------------------------------------------
        # MCP resource binding
        # ----------------------------------------------------

        "resource": GOOGLE_MCP_RESOURCE,
    }

    return (
        f"{GOOGLE_AUTH_URL}?"
        f"{urlencode(params)}"
    )


# ============================================================
# OAuth token exchange
# ============================================================

async def exchange_authorization_code(
    code: str,
) -> Dict[str, Any]:
    """
    Exchange Google's authorization code for
    an MCP-bound access token.

    The PKCE verifier and MCP resource are included.
    """

    if not code:
        raise ValueError(
            "Authorization code is missing."
        )

    code_verifier = (
        _load_code_verifier()
    )

    if not code_verifier:
        raise RuntimeError(
            "PKCE code verifier is missing "
            "or expired. Please authorize "
            "Google Drive again."
        )

    payload = {
        "code": code,

        "client_id": GOOGLE_CLIENT_ID,

        "client_secret": (
            GOOGLE_CLIENT_SECRET
        ),

        "redirect_uri": (
            GOOGLE_REDIRECT_URI
        ),

        "grant_type": (
            "authorization_code"
        ),

        # ----------------------------------------------------
        # PKCE
        # ----------------------------------------------------

        "code_verifier": (
            code_verifier
        ),

        # ----------------------------------------------------
        # MCP resource binding
        # ----------------------------------------------------

        "resource": (
            GOOGLE_MCP_RESOURCE
        ),
    }

    async with httpx2.AsyncClient(
        timeout=30.0,
    ) as client:

        response = await client.post(
            GOOGLE_TOKEN_URL,
            data=payload,
        )

    if response.status_code != 200:

        raise RuntimeError(
            "Google token exchange failed: "
            f"{response.text}"
        )

    token_data = response.json()

    expires_in = int(
        token_data.get(
            "expires_in",
            3600,
        )
    )

    token_data[
        "expires_at"
    ] = int(
        time.time()
        + expires_in
    )

    # Keep a record of what this token was
    # authorized for.
    token_data[
        "mcp_resource"
    ] = GOOGLE_MCP_RESOURCE

    _save_tokens(
        token_data
    )

    # PKCE verifier is single-use.
    _delete_code_verifier()

    return token_data


# ============================================================
# Refresh access token
# ============================================================

async def refresh_google_access_token(
    refresh_token: str,
) -> Dict[str, Any]:
    """
    Refresh an expired Google access token.

    The MCP resource is included in the refresh request
    so the refreshed token remains associated with the
    Drive MCP resource.
    """

    payload = {
        "client_id": GOOGLE_CLIENT_ID,

        "client_secret": (
            GOOGLE_CLIENT_SECRET
        ),

        "refresh_token": refresh_token,

        "grant_type": (
            "refresh_token"
        ),

        "resource": (
            GOOGLE_MCP_RESOURCE
        ),
    }

    async with httpx2.AsyncClient(
        timeout=30.0,
    ) as client:

        response = await client.post(
            GOOGLE_TOKEN_URL,
            data=payload,
        )

    if response.status_code != 200:

        raise RuntimeError(
            "Google token refresh failed: "
            f"{response.text}"
        )

    refreshed = response.json()

    expires_in = int(
        refreshed.get(
            "expires_in",
            3600,
        )
    )

    refreshed[
        "expires_at"
    ] = int(
        time.time()
        + expires_in
    )

    # Google may not return a new refresh token.
    # Preserve the existing one.
    refreshed[
        "refresh_token"
    ] = (
        refreshed.get(
            "refresh_token"
        )
        or refresh_token
    )

    refreshed[
        "mcp_resource"
    ] = GOOGLE_MCP_RESOURCE

    _save_tokens(
        refreshed
    )

    return refreshed


# ============================================================
# Get valid access token
# ============================================================

async def get_google_access_token() -> str:
    """
    Return a valid Google access token.

    Automatically refreshes it when necessary.
    """

    tokens = _load_tokens()

    access_token = tokens.get(
        "access_token"
    )

    refresh_token = tokens.get(
        "refresh_token"
    )

    if not access_token:

        raise RuntimeError(
            "Google Drive is not connected. "
            "Authorize Google Drive first."
        )

    expires_at = tokens.get(
        "expires_at",
        0,
    )

    try:

        expires_at = float(
            expires_at
        )

    except (
        TypeError,
        ValueError,
    ):

        expires_at = 0

    # Refresh slightly before expiry.
    if (
        time.time()
        >= expires_at - 60
    ):

        if not refresh_token:

            raise RuntimeError(
                "Google access token expired "
                "and no refresh token is available."
            )

        refreshed = (
            await refresh_google_access_token(
                refresh_token
            )
        )

        access_token = (
            refreshed.get(
                "access_token"
            )
        )

        if not access_token:

            raise RuntimeError(
                "Google token refresh returned "
                "no access token."
            )

    return access_token


# ============================================================
# Google Drive connection status
# ============================================================

def get_google_drive_status() -> Dict[str, Any]:
    """
    Return local Google Drive MCP connection status.
    """

    tokens = _load_tokens()

    configured = bool(
        GOOGLE_CLIENT_ID
        and GOOGLE_CLIENT_SECRET
        and GOOGLE_REDIRECT_URI
        and GOOGLE_DRIVE_MCP_URL
    )

    connected = bool(
        tokens.get(
            "access_token"
        )
    )

    expires_at = tokens.get(
        "expires_at"
    )

    token_valid = False

    if expires_at:

        try:

            token_valid = (
                time.time()
                < float(expires_at)
            )

        except (
            TypeError,
            ValueError,
        ):

            token_valid = False

    return {
        "configured": configured,
        "connected": connected,
        "token_valid": token_valid,
        "mcp_url": (
            GOOGLE_DRIVE_MCP_URL
        ),
        "mcp_resource": (
            GOOGLE_MCP_RESOURCE
        ),
        "redirect_uri": (
            GOOGLE_REDIRECT_URI
        ),
        "scopes": GOOGLE_SCOPES,
        "authentication": (
            "Google OAuth 2.0 with PKCE "
            "and MCP resource binding"
        ),
    }


# ============================================================
# MCP result helpers
# ============================================================

def _convert_mcp_content_item(
    item: Any,
) -> Any:
    """
    Convert MCP content objects into JSON-friendly values.
    """

    if item is None:
        return None

    text = getattr(
        item,
        "text",
        None,
    )

    if text is not None:

        try:
            return json.loads(
                text
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):

            return text

    data = getattr(
        item,
        "data",
        None,
    )

    if data is not None:
        return data

    model_dump = getattr(
        item,
        "model_dump",
        None,
    )

    if callable(model_dump):

        try:

            return model_dump(
                mode="json"
            )

        except TypeError:

            return model_dump()

    return str(item)


def _convert_mcp_result(
    result: Any,
) -> Any:
    """
    Convert an MCP CallToolResult into normal
    JSON-friendly Python data.
    """

    if result is None:
        return None

    def normalize(
        value: Any,
    ) -> Any:

        if value is None:
            return None

        if isinstance(
            value,
            dict,
        ):

            return {
                str(key): normalize(
                    item
                )
                for key, item in value.items()
            }

        if isinstance(
            value,
            (
                list,
                tuple,
            ),
        ):

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
                    model_dump(
                        mode="json"
                    )
                )

            except TypeError:

                return normalize(
                    model_dump()
                )

        text = getattr(
            value,
            "text",
            None,
        )

        if text is not None:

            try:

                return normalize(
                    json.loads(text)
                )

            except (
                json.JSONDecodeError,
                TypeError,
            ):

                return text

        data = getattr(
            value,
            "data",
            None,
        )

        if data is not None:
            return data

        return value

    # --------------------------------------------------------
    # Structured content
    # --------------------------------------------------------

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

        return normalize(
            structured
        )

    # --------------------------------------------------------
    # Normal MCP content blocks
    # --------------------------------------------------------

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

    return normalize(
        result
    )


# ============================================================
# MCP tool call
# ============================================================

async def _call_mcp_tool(
    tool_name: str,
    arguments: Optional[
        Dict[str, Any]
    ] = None,
) -> Any:
    """
    Call a Google Drive MCP tool using Streamable HTTP.

    Uses the MCP-bound OAuth access token.
    """

    access_token = (
        await get_google_access_token()
    )

    headers = {
        "Authorization": (
            f"Bearer {access_token}"
        ),
        "Content-Type": (
            "application/json"
        ),
        "Accept": (
            "application/json, "
            "text/event-stream"
        ),
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

        transport = (
            streamable_http_client(
                GOOGLE_DRIVE_MCP_URL,
                http_client=http_client,
            )
        )

        async with Client(
            transport
        ) as client:

            result = (
                await client.call_tool(
                    tool_name,
                    arguments or {},
                )
            )

            return _convert_mcp_result(
                result
            )


# ============================================================
# List available Drive MCP tools
# ============================================================

async def list_google_drive_tools() -> List[Any]:
    """
    List tools exposed by Google's Drive MCP server.
    """

    access_token = (
        await get_google_access_token()
    )

    headers = {
        "Authorization": (
            f"Bearer {access_token}"
        ),
        "Content-Type": (
            "application/json"
        ),
        "Accept": (
            "application/json, "
            "text/event-stream"
        ),
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

        transport = (
            streamable_http_client(
                GOOGLE_DRIVE_MCP_URL,
                http_client=http_client,
            )
        )

        async with Client(
            transport
        ) as client:

            tools_result = (
                await client.list_tools()
            )

            output = []

            for tool in (
                tools_result.tools
            ):

                output.append(
                    {
                        "name": tool.name,
                        "description": (
                            tool.description
                        ),
                    }
                )

            return output


# ============================================================
# Search Google Drive
# ============================================================

def _build_drive_query(
    query: str,
) -> str:
    """
    Build a Google Drive MCP search query.
    """

    cleaned = (
        query or ""
    ).strip()

    if not cleaned:
        return "owner = 'me'"

    cleaned = re.sub(
        r"[\r\n]+",
        " ",
        cleaned,
    )

    cleaned = cleaned.replace(
        "\\",
        " ",
    )

    cleaned = cleaned.replace(
        "'",
        "\\'",
    )

    return (
        f"title contains '{cleaned}'"
    )


def _extract_drive_files(
    result: Any,
) -> List[Dict[str, Any]]:
    """
    Extract Google Drive file objects from
    the response returned by search_files.
    """

    if result is None:
        return []

    # --------------------------------------------------------
    # Direct dictionary response
    # --------------------------------------------------------

    if isinstance(
        result,
        dict,
    ):

        files = result.get(
            "files"
        )

        if isinstance(
            files,
            list,
        ):

            return [
                item
                for item in files
                if isinstance(
                    item,
                    dict,
                )
            ]

        # Handle nested MCP wrappers.
        for key in (
            "result",
            "data",
            "structured_content",
            "structuredContent",
        ):

            nested = result.get(
                key
            )

            if nested is not None:

                extracted = (
                    _extract_drive_files(
                        nested
                    )
                )

                if extracted:
                    return extracted

        return []

    # --------------------------------------------------------
    # List response
    # --------------------------------------------------------

    if isinstance(
        result,
        list,
    ):

        output: List[
            Dict[str, Any]
        ] = []

        for item in result:

            if isinstance(
                item,
                dict,
            ):

                if (
                    item.get("id")
                    or item.get("title")
                    or item.get("name")
                ):

                    output.append(
                        item
                    )

                    continue

                nested = (
                    _extract_drive_files(
                        item
                    )
                )

                output.extend(
                    nested
                )

        return output

    # --------------------------------------------------------
    # Pydantic / object response
    # --------------------------------------------------------

    model_dump = getattr(
        result,
        "model_dump",
        None,
    )

    if callable(model_dump):

        try:

            dumped = model_dump(
                mode="json"
            )

        except TypeError:

            dumped = model_dump()

        return _extract_drive_files(
            dumped
        )

    return []


async def search_google_drive(
    query: str,
    max_files: int = 5,
) -> List[Dict[str, Any]]:
    """
    Search Google Drive through the official
    Google Drive MCP search_files tool.
    """

    max_files = max(
        1,
        min(
            int(max_files),
            20,
        ),
    )

    cleaned = (
        query or ""
    ).strip()

    if not cleaned:
        return []

    # --------------------------------------------------------
    # 1. Search by title
    # --------------------------------------------------------

    title_query = (
        _build_drive_query(
            cleaned
        )
    )

    result = await _call_mcp_tool(
        "search_files",
        {
            "query": title_query,
            "pageSize": max_files,
            "excludeContentSnippets": False,
        },
    )

    files = _extract_drive_files(
        result
    )

    if files:
        return files[
            :max_files
        ]

    # --------------------------------------------------------
    # 2. Full-text fallback
    # --------------------------------------------------------

    safe_query = re.sub(
        r"[\r\n]+",
        " ",
        cleaned,
    )

    safe_query = safe_query.replace(
        "\\",
        " ",
    )

    safe_query = safe_query.replace(
        "'",
        "\\'",
    )

    full_text_query = (
        f"fullText contains "
        f"'{safe_query}'"
    )

    result = await _call_mcp_tool(
        "search_files",
        {
            "query": full_text_query,
            "pageSize": max_files,
            "excludeContentSnippets": False,
        },
    )

    files = _extract_drive_files(
        result
    )

    return files[
        :max_files
    ]


# ============================================================
# Read Google Drive file
# ============================================================

async def read_google_drive_file(
    file_id: str,
) -> Dict[str, Any]:
    """
    Read the text representation of a Drive file
    using Google's read_file_content MCP tool.
    """

    if not file_id:

        raise ValueError(
            "Google Drive file ID is required."
        )

    result = await _call_mcp_tool(
        "read_file_content",
        {
            "fileId": file_id,
        },
    )

    if isinstance(
        result,
        dict,
    ):

        return result

    if isinstance(
        result,
        str,
    ):

        return {
            "fileContent": result,
        }

    return {
        "result": result,
    }


# ============================================================
# Search and read
# ============================================================

async def search_and_read_google_drive(
    query: str,
    max_files: int = 3,
) -> List[Dict[str, Any]]:
    """
    Search Drive and read the content of the
    most relevant files.
    """

    files = await search_google_drive(
        query,
        max_files=max_files,
    )

    results = []

    for file in files:

        file_id = (
            file.get("id")
            or file.get("fileId")
        )

        if not file_id:
            continue

        title = (
            file.get("title")
            or file.get("name")
            or "Untitled"
        )

        try:

            content = (
                await read_google_drive_file(
                    file_id
                )
            )

            file_content = ""

            if isinstance(
                content,
                dict,
            ):

                file_content = (
                    content.get(
                        "fileContent"
                    )
                    or content.get(
                        "content"
                    )
                    or ""
                )

            results.append(
                {
                    "id": file_id,
                    "title": title,
                    "mimeType": (
                        file.get(
                            "mimeType"
                        )
                    ),
                    "viewUrl": (
                        file.get(
                            "viewUrl"
                        )
                    ),
                    "content": file_content,
                }
            )

        except Exception as exc:

            results.append(
                {
                    "id": file_id,
                    "title": title,
                    "mimeType": (
                        file.get(
                            "mimeType"
                        )
                    ),
                    "viewUrl": (
                        file.get(
                            "viewUrl"
                        )
                    ),
                    "content": "",
                    "error": str(exc),
                }
            )

    return results


# ============================================================
# Synchronous helper for LangGraph
# ============================================================

def search_google_drive_sync(
    query: str,
    max_files: int = 3,
) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper used by the existing
    LangGraph Knowledge Agent.
    """

    try:

        return asyncio.run(
            search_and_read_google_drive(
                query,
                max_files=max_files,
            )
        )

    except RuntimeError as exc:

        if (
            "asyncio.run()"
            not in str(exc)
        ):
            raise

        import concurrent.futures

        with (
            concurrent.futures
            .ThreadPoolExecutor(
                max_workers=1
            )
            as executor
        ):

            future = (
                executor.submit(
                    asyncio.run,
                    search_and_read_google_drive(
                        query,
                        max_files=max_files,
                    ),
                )
            )

            return future.result()


# ============================================================
# Utility
# ============================================================

def google_drive_is_configured() -> bool:
    return bool(
        GOOGLE_CLIENT_ID
        and GOOGLE_CLIENT_SECRET
        and GOOGLE_REDIRECT_URI
        and GOOGLE_DRIVE_MCP_URL
    )


# ============================================================
# List recent Google Drive files
# ============================================================

async def list_recent_google_drive_files(
    max_files: int = 10,
) -> Any:
    """
    Directly call Google's official
    list_recent_files MCP tool.

    This bypasses our natural-language search wrapper
    and lets us verify exactly what Google Drive MCP
    can see.
    """

    max_files = max(
        1,
        min(
            int(max_files),
            50,
        ),
    )

    result = await _call_mcp_tool(
        "list_recent_files",
        {
            "pageSize": max_files,
            "orderBy": "recency",
            "excludeContentSnippets": False,
        },
    )

    return result