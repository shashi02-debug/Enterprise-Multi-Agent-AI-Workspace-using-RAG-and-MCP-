from __future__ import annotations

import re
from typing import Any, Dict, List, TypedDict

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from langchain_groq import ChatGroq


# =========================================================
# AGENT STATE
# =========================================================

class AgentState(
    TypedDict,
    total=False,
):
    question: str
    route: str
    context: str
    sources: List[str]
    retrieved_chunks: int
    answer: str
    error: str
    action_result: Any
    action_status: str


# =========================================================
# MODEL
# =========================================================

GROQ_MODEL = "openai/gpt-oss-20b"


def get_llm() -> ChatGroq:
    """
    Create the Groq LLM used by the agents.
    """

    return ChatGroq(
        model=GROQ_MODEL,
        temperature=0,
    )


# =========================================================
# DRIVE CONTEXT LIMITS
# =========================================================

DRIVE_MAX_FILES = 3

DRIVE_SEARCH_CANDIDATES = 10

DRIVE_RECENT_CANDIDATES = 20

DRIVE_MAX_FILE_CHARACTERS = 12000

DRIVE_MAX_TOTAL_CHARACTERS = 16000

# Minimum score required before accepting a Drive result.
DRIVE_STRONG_MATCH_SCORE = 8


# =========================================================
# DRIVE TOPIC / INTENT PHRASES
# =========================================================
#
# These are phrases that commonly identify the actual
# document/topic being requested.
#
# Example:
#
# "What is the total accommodation amount mentioned in
#  the accommodation booking document?"
#
# should identify:
#
# "accommodation booking"
#
# rather than:
#
# "total accommodation amount mentioned"
#
# =========================================================

DRIVE_TOPIC_PHRASES = [
    "accommodation booking",
    "accommodation",
    "booking",
    "registration",
    "kartik yatra",
    "yatra",
    "travel",
    "invoice",
    "receipt",
    "payment",
    "transaction",
    "certificate",
    "resume",
    "assignment",
    "course material",
    "course materials",
    "notes",
    "syllabus",
    "report",
    "project",
    "meeting",
    "attendance",
]


# =========================================================
# DRIVE QUESTION STOP WORDS
# =========================================================

DRIVE_STOP_WORDS = {
    "find",
    "search",
    "show",
    "get",
    "retrieve",
    "open",
    "read",
    "give",
    "tell",
    "please",
    "can",
    "you",
    "could",
    "would",
    "me",
    "my",
    "your",
    "the",
    "a",
    "an",
    "in",
    "from",
    "on",
    "of",
    "for",
    "to",
    "and",
    "or",
    "with",
    "about",
    "this",
    "that",
    "it",
    "its",
    "file",
    "files",
    "document",
    "documents",
    "google",
    "drive",
    "summarize",
    "summarise",
    "summary",
    "summarise",
    "explain",
    "describe",
    "analyze",
    "analyse",
    "mentioned",
    "mention",
    "according",
    "based",
    "information",
    "details",
    "detail",
    "what",
    "which",
    "who",
    "where",
    "when",
    "how",
    "is",
    "are",
    "was",
    "were",
    "do",
    "does",
    "did",
    "all",
    "list",
    "give",
    "provide",
    "total",
    "amount",
    "number",
    "names",
}


# =========================================================
# DRIVE QUESTION / SEARCH HELPERS
# =========================================================

def normalize_drive_text(
    text: str,
) -> str:
    """
    Normalize text for comparison.
    """

    text = str(
        text or ""
    ).lower()

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def extract_drive_topic_phrases(
    question: str,
) -> List[str]:
    """
    Extract known topic/document phrases from the user's
    natural-language question.

    This is especially important for questions such as:

        What is the total accommodation amount mentioned
        in the accommodation booking document?

    where "total", "amount", and "mentioned" should not
    dominate the actual document topic.
    """

    normalized = normalize_drive_text(
        question
    )

    matches: List[str] = []

    # -----------------------------------------------------
    # Prefer longer phrases first.
    # -----------------------------------------------------

    sorted_phrases = sorted(
        DRIVE_TOPIC_PHRASES,
        key=lambda value: len(
            value
        ),
        reverse=True,
    )

    for phrase in sorted_phrases:

        normalized_phrase = (
            normalize_drive_text(
                phrase
            )
        )

        if (
            normalized_phrase
            and normalized_phrase
            in normalized
            and normalized_phrase
            not in matches
        ):

            matches.append(
                normalized_phrase
            )

    return matches


def build_drive_search_queries(
    question: str,
) -> List[str]:
    """
    Build several focused Google Drive search queries.

    The first query is based on document/topic phrases.
    Additional queries contain meaningful question terms.

    Example:

        "What is the total accommodation amount mentioned
         in the accommodation booking document in my
         Google Drive?"

    produces approximately:

        [
            "accommodation booking",
            "accommodation booking accommodation",
        ]

    instead of sending the entire natural-language question
    to the Drive search engine.
    """

    normalized_question = normalize_drive_text(
        question
    )

    queries: List[str] = []

    # =====================================================
    # 1. Extract explicit topic phrases
    # =====================================================

    topic_phrases = (
        extract_drive_topic_phrases(
            question
        )
    )

    for phrase in topic_phrases:

        if phrase not in queries:

            queries.append(
                phrase
            )

    # =====================================================
    # 2. Extract meaningful individual words
    # =====================================================

    words = re.findall(
        r"[a-z0-9][a-z0-9_-]*",
        normalized_question,
    )

    meaningful_words = []

    for word in words:

        if (
            word in DRIVE_STOP_WORDS
        ):

            continue

        if len(word) <= 1:

            continue

        if word not in meaningful_words:

            meaningful_words.append(
                word
            )

    # -----------------------------------------------------
    # Keep only a small number of meaningful words.
    # -----------------------------------------------------

    meaningful_words = (
        meaningful_words[:10]
    )

    # =====================================================
    # 3. Topic + meaningful words
    # =====================================================

    if topic_phrases:

        primary_topic = (
            topic_phrases[0]
        )

        # Add the strongest topic phrase by itself.
        if (
            primary_topic
            not in queries
        ):

            queries.insert(
                0,
                primary_topic,
            )

        # Add topic + useful words if needed.
        combined_words = []

        for word in meaningful_words:

            if (
                word
                not in combined_words
            ):

                combined_words.append(
                    word
                )

        if combined_words:

            combined_query = (
                primary_topic
                + " "
                + " ".join(
                    combined_words[:4]
                )
            )

            if (
                combined_query
                not in queries
            ):

                queries.append(
                    combined_query
                )

    # =====================================================
    # 4. Fallback
    # =====================================================

    if not queries:

        fallback_words = [
            word
            for word in words
            if (
                word
                not in DRIVE_STOP_WORDS
                and len(word) > 1
            )
        ]

        fallback_words = list(
            dict.fromkeys(
                fallback_words
            )
        )[:8]

        if fallback_words:

            queries.append(
                " ".join(
                    fallback_words
                )
            )

    if not queries:

        queries.append(
            question[:120]
        )

    return queries[:4]


def build_drive_search_query(
    question: str,
) -> str:
    """
    Backward-compatible single-query builder.

    Returns the strongest query generated for the question.
    """

    queries = (
        build_drive_search_queries(
            question
        )
    )

    if queries:

        return queries[0]

    return question[:120]


# =========================================================
# GMAIL / EMAIL INTENT
# =========================================================

def is_gmail_query(
    question: str,
) -> bool:
    """Return True when the user is asking the workspace to perform
    an email/Gmail operation rather than merely discuss email."""

    normalized = (question or "").lower().strip()

    action_patterns = [
        r"\bcreate\s+(a\s+)?(gmail\s+)?draft\b",
        r"\bcreate\s+(an\s+)?email\b",
        r"\bdraft\s+(an?\s+)?email\b",
        r"\bdraft\s+an?\s+message\b",
        r"\bwrite\s+(an?\s+)?email\b",
        r"\bcompose\s+(an?\s+)?email\b",
        r"\bsave\s+(an?\s+)?email\s+as\s+a?\s*draft\b",
        r"\bsend\s+me\s+(an?\s+)?draft\b",
    ]

    explicit_gmail = [
        r"\bgmail\b",
        r"\binbox\b",
        r"\bemail\b",
        r"\be-mail\b",
    ]

    has_action = any(
        re.search(pattern, normalized)
        for pattern in action_patterns
    )

    has_email_context = any(
        re.search(pattern, normalized)
        for pattern in explicit_gmail
    )

    # Route explicit email actions to Gmail.
    return has_action or (has_email_context and any(
        word in normalized
        for word in (
            "create",
            "draft",
            "compose",
            "write",
            "reply",
            "respond",
        )
    ))




# =========================================================
# SUPERVISOR AGENT
# =========================================================

def is_drive_gmail_query(
    question: str,
) -> bool:
    """Return True when one request needs document retrieval and Gmail drafting.

    Combined requests are intentionally detected from the *whole user intent*,
    not only from the words ``Google Drive``. A user may say:

        "Summarize the IEEE document related to my major project and draft an
         email to the guide."

    In that case the document is still the information source for the email,
    so the workflow must retrieve the document before Gmail is invoked.
    """

    normalized = (question or "").lower().strip()

    if not is_gmail_query(normalized):
        return False

    # Explicit Drive language is the strongest signal.
    explicit_drive = is_drive_query(normalized)

    document_words = any(
        re.search(pattern, normalized)
        for pattern in (
            r"\bdocument\b",
            r"\bfile\b",
            r"\breport\b",
            r"\bpdf\b",
        )
    )

    summary_words = any(
        re.search(pattern, normalized)
        for pattern in (
            r"\bsummar(?:ize|ise|y)\b",
            r"\bexplain\b",
            r"\bdescribe\b",
            r"\banaly[sz]e\b",
            r"\banalyse\b",
        )
    )

    draft_words = any(
        re.search(pattern, normalized)
        for pattern in (
            r"\bdraft\b",
            r"\bcompose\b",
            r"\bwrite\b",
            r"\bcreate\s+(?:an?\s+)?email\b",
        )
    )

    # If the user explicitly mentions Drive, require a document-oriented
    # action as well so a normal "email about Drive" request stays Gmail-only.
    if explicit_drive:
        return document_words and (summary_words or draft_words)

    # Natural-language combined intent: document + summarization + email draft.
    return document_words and summary_words and draft_words


def supervisor_agent(
    state: AgentState,
) -> AgentState:

    question = state.get(
        "question",
        "",
    ).strip()

    if not question:

        return {
            **state,
            "route": "general",
            "error": (
                "No question was provided."
            ),
        }

    question_lower = (
        question.lower()
    )

    # =====================================================
    # GOOGLE DRIVE + GMAIL COMBINED INTENT
    # =====================================================

    if is_drive_gmail_query(question):

        return {
            **state,
            "route": "drive_gmail",
        }

    # =====================================================
    # GMAIL / EMAIL INTENT
    # =====================================================

    if is_gmail_query(question):

        return {
            **state,
            "route": "gmail",
        }

    # =====================================================
    # GOOGLE DRIVE INTENT
    # =====================================================

    if is_drive_query(question):

        return {
            **state,
            "route": "drive",
        }

    # =====================================================
    # KNOWLEDGE / DOCUMENT INTENT
    # =====================================================

    knowledge_patterns = [
        "document",
        "documents",
        "file",
        "files",
        "pdf",
        "report",
        "agreement",
        "booking",
        "registration",
        "according to",
        "from the document",
        "from my documents",
        "in the document",
        "in my files",
        "what does",
        "summarize",
        "summarise",
        "explain the document",
        "based on the document",
        "according to the file",
    ]

    if any(
        pattern in question_lower
        for pattern in knowledge_patterns
    ):

        return {
            **state,
            "route": "knowledge",
        }

    # =====================================================
    # GENERAL INTENT
    # =====================================================

    return {
        **state,
        "route": "general",
    }


# =========================================================
# GOOGLE DRIVE INTENT
# =========================================================

def is_drive_query(
    question: str,
) -> bool:

    normalized = (
        question.lower()
        .strip()
    )

    drive_patterns = [

        # -------------------------------------------------
        # Explicit Google Drive references
        # -------------------------------------------------

        r"\bgoogle drive\b",
        r"\bgoogle drive files\b",
        r"\bgoogle drive document\b",
        r"\bgoogle drive file\b",

        # -------------------------------------------------
        # Drive references
        # -------------------------------------------------

        r"\bdrive\b",
        r"\bdrive files\b",
        r"\bfrom drive\b",
        r"\bin drive\b",
        r"\bmy drive\b",

        # -------------------------------------------------
        # Drive actions
        # -------------------------------------------------

        r"\bsearch drive\b",
        r"\bsearch my drive\b",
        r"\bfind in drive\b",
        r"\bfind from drive\b",
        r"\bfind it in drive\b",
        r"\bfind the file in drive\b",
        r"\bfind the document in drive\b",

        # -------------------------------------------------
        # Google Drive context
        # -------------------------------------------------

        r"\bin my google drive\b",
        r"\bfrom my google drive\b",
        r"\bmy google drive\b",
    ]

    return any(
        re.search(
            pattern,
            normalized,
        )
        for pattern in drive_patterns
    )


# =========================================================
# KNOWLEDGE / LOCAL RAG AGENT
# =========================================================

def knowledge_agent(
    state: AgentState,
) -> AgentState:

    question = state.get(
        "question",
        "",
    ).strip()

    if not question:

        return {
            **state,
            "context": "",
            "sources": [],
            "retrieved_chunks": 0,
            "error": (
                "No question was provided."
            ),
        }

    try:

        # -------------------------------------------------
        # EXISTING LOCAL RAG
        # -------------------------------------------------

        from app.main import (
            retrieve_chunks,
        )

        from app.database import (
            SessionLocal,
        )

        db = SessionLocal()

        try:

            chunks = retrieve_chunks(
                question,
                db,
            )

        finally:

            db.close()

        # -------------------------------------------------
        # BUILD LOCAL CONTEXT
        # -------------------------------------------------

        context_parts: List[str] = []

        sources: List[str] = []

        for chunk in chunks:

            if isinstance(
                chunk,
                dict,
            ):

                source = (
                    chunk.get(
                        "source"
                    )
                    or chunk.get(
                        "filename"
                    )
                    or "Unknown document"
                )

                text = (
                    chunk.get(
                        "text"
                    )
                    or chunk.get(
                        "content"
                    )
                    or chunk.get(
                        "page_content"
                    )
                    or ""
                )

            else:

                source = (
                    "Unknown document"
                )

                text = str(
                    chunk
                )

            if not text.strip():

                continue

            context_parts.append(
                f"[Source: {source}]\n"
                f"{text.strip()}"
            )

            if source not in sources:

                sources.append(
                    source
                )

        # -------------------------------------------------
        # NO LOCAL RESULTS
        # -------------------------------------------------

        if not context_parts:

            return {
                **state,
                "context": "",
                "sources": [],
                "retrieved_chunks": 0,
            }

        # -------------------------------------------------
        # FINAL LOCAL CONTEXT
        # -------------------------------------------------

        context = "\n\n".join(
            context_parts
        )

        return {
            **state,
            "context": context,
            "sources": sources,
            "retrieved_chunks": len(
                context_parts
            ),
        }

    except Exception as exc:

        return {
            **state,
            "context": "",
            "sources": [],
            "retrieved_chunks": 0,
            "error": (
                "Knowledge Agent failed: "
                f"{exc}"
            ),
        }


# =========================================================
# DRIVE TEXT NORMALIZATION
# =========================================================

def _drive_text(
    value: Any,
) -> str:
    """
    Safely convert Google Drive metadata/content
    into searchable text.
    """

    if value is None:

        return ""

    if isinstance(
        value,
        dict,
    ):

        parts = []

        for key, item in value.items():

            parts.append(
                str(key)
            )

            parts.append(
                _drive_text(item)
            )

        return " ".join(
            parts
        )

    if isinstance(
        value,
        list,
    ):

        return " ".join(
            _drive_text(item)
            for item in value
        )

    return str(
        value
    )


def _drive_tokens(
    text: str,
) -> List[str]:
    """
    Tokenize searchable Drive text.
    """

    return re.findall(
        r"[a-z0-9]+",
        str(text).lower(),
    )


# =========================================================
# DRIVE RESULT NORMALIZATION
# =========================================================

def extract_drive_results(
    result: Any,
) -> List[Dict[str, Any]]:
    """
    Normalize different response shapes returned by
    the Google Drive MCP helper.
    """

    if result is None:

        return []

    # -----------------------------------------------------
    # Direct list
    # -----------------------------------------------------

    if isinstance(
        result,
        list,
    ):

        return [
            item
            for item in result
            if isinstance(
                item,
                dict,
            )
        ]

    # -----------------------------------------------------
    # Dictionary response
    # -----------------------------------------------------

    if isinstance(
        result,
        dict,
    ):

        for key in (
            "results",
            "files",
            "items",
            "data",
        ):

            value = result.get(
                key
            )

            if isinstance(
                value,
                list,
            ):

                return [
                    item
                    for item in value
                    if isinstance(
                        item,
                        dict,
                    )
                ]

        # -------------------------------------------------
        # Single file object
        # -------------------------------------------------

        if (
            result.get("id")
            or result.get("fileId")
            or result.get("file_id")
            or result.get("title")
            or result.get("name")
            or result.get("filename")
        ):

            return [
                result
            ]

    return []


# =========================================================
# DRIVE FILE METADATA HELPERS
# =========================================================

def get_drive_file_name(
    file_data: Dict[str, Any],
) -> str:

    return str(
        file_data.get(
            "filename"
        )
        or file_data.get(
            "title"
        )
        or file_data.get(
            "name"
        )
        or "Google Drive file"
    )


def get_drive_file_id(
    file_data: Dict[str, Any],
):
    return (
        file_data.get(
            "id"
        )
        or file_data.get(
            "fileId"
        )
        or file_data.get(
            "file_id"
        )
    )


def extract_drive_content(
    file_data: Any,
) -> str:
    """
    Extract readable content from a Google Drive
    MCP response.
    """

    if file_data is None:

        return ""

    if isinstance(
        file_data,
        str,
    ):

        return file_data

    if isinstance(
        file_data,
        dict,
    ):

        # -------------------------------------------------
        # Direct content fields
        # -------------------------------------------------

        for key in (
            "text",
            "content",
            "contentSnippet",
            "snippet",
            "body",
        ):

            value = file_data.get(
                key
            )

            if value:

                return _drive_text(
                    value
                )

        # -------------------------------------------------
        # Nested MCP result
        # -------------------------------------------------

        for key in (
            "result",
            "data",
        ):

            nested = file_data.get(
                key
            )

            if nested:

                nested_text = (
                    extract_drive_content(
                        nested
                    )
                )

                if nested_text:

                    return nested_text

    return ""


# =========================================================
# DRIVE RELEVANCE SCORING
# =========================================================

def score_drive_file(
    file_data: Dict[str, Any],
    search_query: str,
) -> tuple[int, Dict[str, Any]]:
    """
    Score a Google Drive file against a focused search query.

    Filename matches receive significantly higher weight
    than generic content matches.
    """

    if not isinstance(
        file_data,
        dict,
    ):

        return 0, {}

    title = get_drive_file_name(
        file_data
    )

    content = extract_drive_content(
        file_data
    )

    normalized_title = (
        normalize_drive_text(
            title
        )
    )

    normalized_content = (
        normalize_drive_text(
            content
        )
    )

    normalized_query = (
        normalize_drive_text(
            search_query
        )
    )

    query_tokens = set(
        _drive_tokens(
            normalized_query
        )
    )

    if not query_tokens:

        return 0, {
            "title": title,
            "matched_title": [],
            "matched_content": [],
            "score": 0,
        }

    title_tokens = set(
        _drive_tokens(
            normalized_title
        )
    )

    content_tokens = set(
        _drive_tokens(
            normalized_content
        )
    )

    matched_title = (
        query_tokens
        & title_tokens
    )

    matched_content = (
        query_tokens
        & content_tokens
    )

    score = 0

    # =====================================================
    # FILENAME MATCHES
    # =====================================================

    # Very strong signal.
    score += (
        len(matched_title) * 10
    )

    # Multiple filename matches.
    if len(matched_title) >= 2:

        score += 8

    if len(matched_title) >= 3:

        score += 8

    # -----------------------------------------------------
    # Exact query phrase in filename.
    # -----------------------------------------------------

    if (
        normalized_query
        and normalized_query
        in normalized_title
    ):

        score += 30

    # =====================================================
    # TOPIC PHRASE MATCHES
    # =====================================================
    #
    # A phrase such as "accommodation booking" is more
    # meaningful than separate generic words.
    #
    # =====================================================

    topic_matches = []

    for phrase in DRIVE_TOPIC_PHRASES:

        normalized_phrase = (
            normalize_drive_text(
                phrase
            )
        )

        if (
            normalized_phrase
            and normalized_phrase
            in normalized_title
        ):

            topic_matches.append(
                normalized_phrase
            )

    # Strong boost for topic/document phrase.
    if topic_matches:

        score += (
            len(topic_matches) * 20
        )

    # Additional boost for the strongest exact topic.
    if (
        "accommodation booking"
        in topic_matches
    ):

        score += 40

    # =====================================================
    # CONTENT MATCHES
    # =====================================================

    # Content matches are deliberately weaker.
    score += (
        len(matched_content) * 2
    )

    # =====================================================
    # MIME TYPE
    # =====================================================

    mime_type = str(
        file_data.get(
            "mimeType"
        )
        or ""
    ).lower()

    if mime_type == "application/pdf":

        score += 1

    return score, {
        "title": title,
        "matched_title": sorted(
            matched_title
        ),
        "matched_content": sorted(
            matched_content
        ),
        "topic_matches": topic_matches,
        "score": score,
    }


def rank_drive_files(
    files: List[Dict[str, Any]],
    search_query: str,
) -> List[Dict[str, Any]]:
    """
    Rank Drive candidates locally.
    """

    ranked = []

    for file_data in files:

        if not isinstance(
            file_data,
            dict,
        ):

            continue

        score, details = (
            score_drive_file(
                file_data,
                search_query,
            )
        )

        enriched = dict(
            file_data
        )

        enriched[
            "_relevance_score"
        ] = score

        enriched[
            "_relevance_details"
        ] = details

        ranked.append(
            enriched
        )

    # -----------------------------------------------------
    # Highest relevance first.
    # Modified time is only a secondary tie-breaker.
    # -----------------------------------------------------

    ranked.sort(
        key=lambda item: (
            item.get(
                "_relevance_score",
                0,
            ),
            item.get(
                "modifiedTime",
                "",
            ),
        ),
        reverse=True,
    )

    return ranked


def merge_drive_candidates(
    candidate_lists: List[List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Merge candidate lists while removing duplicate files.

    Deduplication is based on Drive file ID when available,
    otherwise filename.
    """

    merged: List[Dict[str, Any]] = []

    seen = set()

    for candidates in candidate_lists:

        for item in candidates:

            if not isinstance(
                item,
                dict,
            ):

                continue

            file_id = (
                get_drive_file_id(
                    item
                )
            )

            filename = (
                get_drive_file_name(
                    item
                )
            )

            identity = (
                f"id:{file_id}"
                if file_id
                else f"name:{filename.lower()}"
            )

            if identity in seen:

                continue

            seen.add(
                identity
            )

            merged.append(
                item
            )

    return merged


# =========================================================
# GOOGLE DRIVE AGENT
# =========================================================

def drive_agent(
    state: AgentState,
) -> AgentState:

    question = state.get(
        "question",
        "",
    ).strip()

    if not question:

        return {
            **state,
            "context": "",
            "sources": [],
            "retrieved_chunks": 0,
            "error": (
                "No question was provided."
            ),
        }

    try:

        # -------------------------------------------------
        # GOOGLE DRIVE MCP
        # -------------------------------------------------

        from app.mcp.google_drive import (
            search_google_drive_sync,
            list_recent_google_drive_files,
        )

        # =================================================
        # BUILD FOCUSED SEARCH QUERIES
        # =================================================

        search_queries = (
            build_drive_search_queries(
                question
            )
        )

        print(
            "Drive Agent search queries:",
            search_queries,
        )

        # =================================================
        # PHASE 1 — SEARCH MCP WITH MULTIPLE QUERIES
        # =================================================

        search_candidate_lists: List[
            List[Dict[str, Any]]
        ] = []

        for drive_query in search_queries:

            try:

                print(
                    "Drive Agent MCP search:",
                    drive_query,
                )

                search_result = (
                    search_google_drive_sync(
                        drive_query,
                        max_files=DRIVE_SEARCH_CANDIDATES,
                    )
                )

                search_files = (
                    extract_drive_results(
                        search_result
                    )
                )

                print(
                    "Drive Agent query returned:",
                    len(search_files),
                    "candidate(s)",
                )

                if search_files:

                    search_candidate_lists.append(
                        search_files
                    )

            except Exception as search_error:

                print(
                    "Drive Agent search failed for "
                    f"'{drive_query}': "
                    f"{search_error}"
                )

        # -------------------------------------------------
        # Merge all MCP search candidates.
        # -------------------------------------------------

        search_files = (
            merge_drive_candidates(
                search_candidate_lists
            )
        )

        print(
            "Drive Agent merged search candidates:",
            len(search_files),
        )

        # =================================================
        # RANK AGAINST ALL FOCUSED QUERIES
        # =================================================
        #
        # A file should receive the best score it obtains
        # against any of the focused queries.
        #
        # This prevents a useful exact-topic query from being
        # diluted by the broader natural-language question.
        #
        # =================================================

        ranked_search_files: List[
            Dict[str, Any]
        ] = []

        for file_data in search_files:

            best_file_score = 0

            best_details: Dict[str, Any] = {}

            for drive_query in search_queries:

                score, details = (
                    score_drive_file(
                        file_data,
                        drive_query,
                    )
                )

                if score > best_file_score:

                    best_file_score = score

                    best_details = details

            enriched = dict(
                file_data
            )

            enriched[
                "_relevance_score"
            ] = best_file_score

            enriched[
                "_relevance_details"
            ] = best_details

            ranked_search_files.append(
                enriched
            )

        ranked_search_files.sort(
            key=lambda item: (
                item.get(
                    "_relevance_score",
                    0,
                ),
                item.get(
                    "modifiedTime",
                    "",
                ),
            ),
            reverse=True,
        )

        best_search_score = (
            ranked_search_files[0].get(
                "_relevance_score",
                0,
            )
            if ranked_search_files
            else 0
        )

        print(
            "Drive Agent best search score:",
            best_search_score,
        )

        if ranked_search_files:

            print(
                "Drive Agent top search candidate:",
                get_drive_file_name(
                    ranked_search_files[0]
                ),
            )

            print(
                "Drive Agent top candidate details:",
                ranked_search_files[0].get(
                    "_relevance_details",
                    {},
                ),
            )

        # =================================================
        # PHASE 2 — RECENT FILE FALLBACK
        # =================================================
        #
        # If search does not produce a strong match,
        # inspect recent Drive files.
        #
        # =================================================

        if (
            best_search_score
            >= DRIVE_STRONG_MATCH_SCORE
        ):

            selected_files = (
                ranked_search_files[
                    :DRIVE_MAX_FILES
                ]
            )

        else:

            print(
                "Drive Agent search results "
                "did not contain a strong match."
            )

            print(
                "Drive Agent checking recent files..."
            )

            recent_result = (
                list_recent_google_drive_files(
                    max_files=DRIVE_RECENT_CANDIDATES
                )
            )

            recent_files = (
                extract_drive_results(
                    recent_result
                )
            )

            print(
                "Drive Agent recent files returned:",
                len(recent_files),
                "candidate(s)",
            )

            # -------------------------------------------------
            # Rank recent files using every focused query.
            # -------------------------------------------------

            ranked_recent_files: List[
                Dict[str, Any]
            ] = []

            for file_data in recent_files:

                best_file_score = 0

                best_details: Dict[str, Any] = {}

                for drive_query in search_queries:

                    score, details = (
                        score_drive_file(
                            file_data,
                            drive_query,
                        )
                    )

                    if score > best_file_score:

                        best_file_score = score

                        best_details = details

                enriched = dict(
                    file_data
                )

                enriched[
                    "_relevance_score"
                ] = best_file_score

                enriched[
                    "_relevance_details"
                ] = best_details

                ranked_recent_files.append(
                    enriched
                )

            ranked_recent_files.sort(
                key=lambda item: (
                    item.get(
                        "_relevance_score",
                        0,
                    ),
                    item.get(
                        "modifiedTime",
                        "",
                    ),
                ),
                reverse=True,
            )

            recent_best_score = (
                ranked_recent_files[0].get(
                    "_relevance_score",
                    0,
                )
                if ranked_recent_files
                else 0
            )

            print(
                "Drive Agent best recent score:",
                recent_best_score,
            )

            if ranked_recent_files:

                print(
                    "Drive Agent top recent candidate:",
                    get_drive_file_name(
                        ranked_recent_files[0]
                    ),
                )

                print(
                    "Drive Agent top recent details:",
                    ranked_recent_files[0].get(
                        "_relevance_details",
                        {},
                    ),
                )

            # -------------------------------------------------
            # Choose the better candidate set.
            # -------------------------------------------------

            if (
                recent_best_score
                > best_search_score
            ):

                selected_files = (
                    ranked_recent_files[
                        :DRIVE_MAX_FILES
                    ]
                )

            else:

                selected_files = (
                    ranked_search_files[
                        :DRIVE_MAX_FILES
                    ]
                )

        # =================================================
        # NO MATCH
        # =================================================

        if not selected_files:

            return {
                **state,
                "context": "",
                "sources": [],
                "retrieved_chunks": 0,
                "error": (
                    "No matching files were found "
                    "in Google Drive."
                ),
            }

        # =================================================
        # FINAL RELEVANCE CHECK
        # =================================================

        final_best_score = (
            selected_files[0].get(
                "_relevance_score",
                0,
            )
            if selected_files
            else 0
        )

        print(
            "Drive Agent final best score:",
            final_best_score,
        )

        if final_best_score <= 0:

            return {
                **state,
                "context": "",
                "sources": [],
                "retrieved_chunks": 0,
                "error": (
                    "No relevant Google Drive "
                    "document was identified."
                ),
            }

        # =================================================
        # BUILD CONTROLLED CONTEXT
        # =================================================

        context_parts: List[str] = []

        sources: List[str] = []

        total_characters = 0

        for drive_file in selected_files:

            if not isinstance(
                drive_file,
                dict,
            ):

                continue

            # -------------------------------------------------
            # File name
            # -------------------------------------------------

            filename = (
                get_drive_file_name(
                    drive_file
                )
            )

            # -------------------------------------------------
            # Relevance score
            # -------------------------------------------------

            relevance_score = (
                drive_file.get(
                    "_relevance_score",
                    0,
                )
            )

            relevance_details = (
                drive_file.get(
                    "_relevance_details",
                    {},
                )
            )

            print(
                "Drive Agent candidate:",
                filename,
                "| score:",
                relevance_score,
                "| title matches:",
                relevance_details.get(
                    "matched_title",
                    [],
                ),
                "| topic matches:",
                relevance_details.get(
                    "topic_matches",
                    [],
                ),
            )

            # -------------------------------------------------
            # Initial content
            # -------------------------------------------------

            drive_text = (
                extract_drive_content(
                    drive_file
                )
            ).strip()

            # -------------------------------------------------
            # Direct MCP read
            #
            # Search/recent responses may contain only metadata
            # or a short snippet.
            # -------------------------------------------------

            file_id = (
                get_drive_file_id(
                    drive_file
                )
            )

            if (
                file_id
                and len(drive_text) < 500
            ):

                try:

                    from app.mcp.google_drive import (
                        read_google_drive_file,
                    )

                    print(
                        "Drive Agent reading exact file:",
                        filename,
                    )

                    full_result = (
                        read_google_drive_file(
                            file_id
                        )
                    )

                    full_text = (
                        extract_drive_content(
                            full_result
                        )
                    ).strip()

                    if full_text:

                        drive_text = (
                            full_text
                        )

                except Exception as read_error:

                    print(
                        "Drive Agent direct MCP read "
                        f"failed for {filename}: "
                        f"{read_error}"
                    )

            # -------------------------------------------------
            # Skip files with no readable content.
            # -------------------------------------------------

            if not drive_text:

                print(
                    "Drive Agent skipped file because "
                    "no readable content was found:",
                    filename,
                )

                continue

            # =================================================
            # INDIVIDUAL FILE LIMIT
            # =================================================

            if len(drive_text) > (
                DRIVE_MAX_FILE_CHARACTERS
            ):

                drive_text = (
                    drive_text[
                        :DRIVE_MAX_FILE_CHARACTERS
                    ]
                    + "\n\n"
                    "[Document content truncated]"
                )

            # =================================================
            # TOTAL CONTEXT LIMIT
            # =================================================

            remaining_characters = (
                DRIVE_MAX_TOTAL_CHARACTERS
                - total_characters
            )

            if remaining_characters <= 0:

                break

            if len(drive_text) > (
                remaining_characters
            ):

                drive_text = (
                    drive_text[
                        :remaining_characters
                    ]
                    + "\n\n"
                    "[Additional content truncated]"
                )

            # =================================================
            # ADD CONTEXT
            # =================================================

            context_parts.append(
                "[Source: Google Drive / "
                f"{filename}]\n"
                f"{drive_text}"
            )

            source_name = (
                f"Google Drive / "
                f"{filename}"
            )

            if source_name not in sources:

                sources.append(
                    source_name
                )

            total_characters += (
                len(drive_text)
            )

            # -------------------------------------------------
            # If this is an extremely strong filename/topic
            # match, don't dilute the context.
            # -------------------------------------------------

            if relevance_score >= 30:

                print(
                    "Drive Agent found a strong "
                    "filename/topic match. "
                    "Stopping additional file retrieval."
                )

                break

            if total_characters >= (
                DRIVE_MAX_TOTAL_CHARACTERS
            ):

                break

        # =================================================
        # NO READABLE CONTEXT
        # =================================================

        if not context_parts:

            return {
                **state,
                "context": "",
                "sources": [],
                "retrieved_chunks": 0,
                "error": (
                    "The relevant Google Drive file "
                    "was identified, but readable "
                    "content could not be retrieved."
                ),
            }

        # =================================================
        # FINAL DRIVE CONTEXT
        # =================================================

        context = "\n\n".join(
            context_parts
        )

        print(
            "Drive Agent selected sources:",
            sources,
        )

        print(
            "Drive Agent context size:",
            len(context),
            "characters",
        )

        return {
            **state,
            "context": context,
            "sources": sources,
            "retrieved_chunks": len(
                context_parts
            ),
            "error": "",
        }

    except Exception as exc:

        print(
            "Drive Agent error:",
            exc,
        )

        return {
            **state,
            "context": "",
            "sources": [],
            "retrieved_chunks": 0,
            "error": (
                "Google Drive Agent failed: "
                f"{exc}"
            ),
        }


# =========================================================
# GMAIL HELPERS
# =========================================================

def _gmail_collect_email_candidates(
    value: Any,
) -> List[str]:
    """Extract likely recipient addresses from Gmail MCP search output.

    For sent messages, recipients are preferred; for received messages,
    senders are preferred. This keeps the agent from selecting the user's
    own address when resolving a person such as "Vivek".
    """

    email_pattern = re.compile(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    )
    candidates: List[str] = []

    def add(value_to_add: Any) -> None:
        if value_to_add is None:
            return
        for match in email_pattern.findall(str(value_to_add)):
            if match.lower() not in {
                item.lower() for item in candidates
            }:
                candidates.append(match)

    def visit(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                visit(item)
            return

        if not isinstance(node, dict):
            return

        labels = node.get("labelIds") or node.get("labels") or []
        if isinstance(labels, str):
            labels = [labels]
        sent = any(
            str(label).upper() == "SENT"
            for label in labels
        )

        if sent:
            for key in (
                "toRecipients",
                "ccRecipients",
                "bccRecipients",
                "to",
                "cc",
                "bcc",
            ):
                value_to_add = node.get(key)
                if value_to_add:
                    if isinstance(value_to_add, list):
                        for item in value_to_add:
                            add(item)
                    else:
                        add(value_to_add)
        else:
            for key in (
                "sender",
                "from",
                "fromAddress",
            ):
                if node.get(key):
                    add(node.get(key))

        # Also inspect nested thread/message structures.
        for key in (
            "messages",
            "threads",
            "thread",
            "result",
            "data",
        ):
            nested = node.get(key)
            if nested is not None:
                visit(nested)

    visit(value)
    return candidates


def _extract_explicit_email(
    question: str,
) -> str:
    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        question or "",
    )
    return match.group(0) if match else ""


def _extract_recipient_name(
    question: str,
) -> str:
    patterns = [
        r"\bto\s+([A-Za-z][A-Za-z .'-]{1,60}?)(?:\s+(?:saying|about|with|regarding|that|who|and)\b|[,.]|$)",
        r"\bfor\s+([A-Za-z][A-Za-z .'-]{1,60}?)(?:\s+(?:saying|about|with|regarding|that|who|and)\b|[,.]|$)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            question or "",
            flags=re.IGNORECASE,
        )
        if match:
            name = re.sub(
                r"\s+",
                " ",
                match.group(1),
            ).strip()
            if name:
                return name

    return "the recipient"


def _parse_generated_email(
    content: str,
    recipient_name: str,
) -> tuple[str, str]:
    """Parse the small JSON contract returned by the LLM."""

    text = str(content or "").strip()

    try:
        parsed = __import__("json").loads(text)
        subject = str(parsed.get("subject", "")).strip()
        body = str(parsed.get("body", "")).strip()
        if subject and body:
            return subject, body
    except Exception:
        pass

    subject_match = re.search(
        r"(?:^|\n)\s*Subject\s*:\s*(.+)",
        text,
        flags=re.IGNORECASE,
    )

    subject = (
        subject_match.group(1).strip()
        if subject_match
        else "Meeting Confirmation"
    )

    body = text
    if subject_match:
        body = text[subject_match.end():].strip()

    if not body:
        body = (
            f"Hi {recipient_name},\n\n"
            "I am writing to confirm that our meeting is confirmed. "
            "Please let me know if there are any changes or additional "
            "details we should coordinate.\n\n"
            "Best regards"
        )

    return subject, body


# =========================================================
# GMAIL ACTION AGENT
# =========================================================

def gmail_agent(
    state: AgentState,
) -> AgentState:
    """Resolve the recipient, generate email content, and create a Gmail draft."""

    question = state.get(
        "question",
        "",
    ).strip()

    if not question:
        return {
            **state,
            "error": "No email request was provided.",
            "action_status": "failed",
        }

    try:
        from app.mcp.gmail import (
            search_gmail_threads_sync,
            create_gmail_draft_sync,
        )

        # -----------------------------------------------------
        # STEP 1 — Resolve an explicit address if supplied.
        # Otherwise search Gmail for the named recipient.
        # -----------------------------------------------------
        recipient_email = _extract_explicit_email(question)
        recipient_name = _extract_recipient_name(question)

        if not recipient_email:
            search_query = recipient_name
            search_result = search_gmail_threads_sync(
                search_query,
                max_results=10,
            )

            candidates = _gmail_collect_email_candidates(
                search_result
            )

            if not candidates:
                return {
                    **state,
                    "error": (
                        f"I could not resolve an email address for "
                        f"{recipient_name} from Gmail. Please provide "
                        "the recipient's email address."
                    ),
                    "action_status": "failed",
                }

            recipient_email = candidates[0]

        print(
            "Gmail Agent resolved recipient:",
            recipient_name,
            "->",
            recipient_email,
        )

        # -----------------------------------------------------
        # STEP 2 — Generate subject/body without inventing
        # dates, times, locations, or other missing facts.
        # -----------------------------------------------------
        llm = get_llm()
        retrieved_context = state.get(
            "context",
            "",
        ).strip()

        # A combined Drive -> Gmail request must never create a generic
        # "please provide the document" draft. If Drive retrieval failed,
        # stop before Gmail MCP is called.
        if (
            state.get("route") == "drive_gmail"
            and not retrieved_context
        ):
            retrieval_error = state.get(
                "error",
                "",
            ).strip()

            return {
                **state,
                "action_status": "failed",
                "error": (
                    retrieval_error
                    or "The requested document could not be retrieved from Google Drive."
                ),
            }

        context_instruction = ""

        if retrieved_context:
            context_instruction = f"""

Retrieved Google Drive content:
{retrieved_context}

Use the retrieved Google Drive content as the factual basis
for the email. Summarize the relevant information in the
draft instead of merely saying that the document was found.
Do not invent any facts that are not present in the retrieved
content.
"""

        prompt = f"""
You are the Gmail Draft Agent in an Enterprise AI Workspace.

User request:
{question}

Recipient name:
{recipient_name}
{context_instruction}

Create a professional email draft that satisfies the request.

Rules:
1. Do not invent dates, times, locations, names, links, amounts, or other facts.
2. When retrieved Google Drive content is provided, use it as the factual source for the email.
3. If retrieved Google Drive content is present, the email MUST summarize that retrieved document. Do not ask the recipient to provide the document, do not describe the user's request instead of the document, and do not say that the document is unavailable.
4. If the user asks to summarize a document and then draft an email, include the actual factual summary of the retrieved document in the email.
5. If the user did not provide or retrieve a specific detail, do not add a fake placeholder such as [Date] or [Time].
6. Keep the email concise and natural.
7. Return ONLY valid JSON with exactly two string fields:
   {{"subject": "...", "body": "..."}}
8. Do not include Markdown fences.
"""

        generated = llm.invoke(prompt)
        generated_content = (
            generated.content
            if hasattr(generated, "content")
            else str(generated)
        )

        subject, body = _parse_generated_email(
            generated_content,
            recipient_name,
        )

        # -----------------------------------------------------
        # STEP 3 — Execute the real Gmail MCP action.
        # -----------------------------------------------------
        draft_result = create_gmail_draft_sync(
            to=recipient_email,
            subject=subject,
            body=body,
        )

        action_result = {
            "type": "gmail_draft",
            "status": "created",
            "recipient": recipient_email,
            "subject": subject,
            "draft": draft_result,
        }

        existing_sources = list(
            state.get(
                "sources",
                [],
            )
            or []
        )

        if "Gmail MCP" not in existing_sources:
            existing_sources.append(
                "Gmail MCP"
            )

        return {
            **state,
            "context": retrieved_context,
            "sources": existing_sources,
            "retrieved_chunks": state.get(
                "retrieved_chunks",
                0,
            ),
            "action_result": action_result,
            "action_status": "created",
            "answer": (
                f"Gmail draft created successfully for "
                f"{recipient_email}."
            ),
            "error": "",
        }

    except Exception as exc:
        print(
            "Gmail Agent error:",
            exc,
        )

        return {
            **state,
            "action_status": "failed",
            "error": (
                "Gmail Agent failed: "
                f"{exc}"
            ),
            "answer": (
                "I could not create the Gmail draft because "
                f"the Gmail action failed: {exc}"
            ),
        }



# =========================================================
# GENERAL AGENT
# =========================================================

def general_agent(
    state: AgentState,
) -> AgentState:

    return {
        **state,
        "context": "",
        "sources": [],
        "retrieved_chunks": 0,
    }


# =========================================================
# RESPONSE AGENT
# =========================================================

def response_agent(
    state: AgentState,
) -> AgentState:

    question = state.get(
        "question",
        "",
    ).strip()

    context = state.get(
        "context",
        "",
    ).strip()

    route = state.get(
        "route",
        "general",
    )

    error = state.get(
        "error",
        "",
    )

    # =====================================================
    # COMBINED DRIVE + GMAIL RESULT
    # =====================================================

    if route == "drive_gmail":

        if state.get("action_status") == "created" and context:

            llm = get_llm()

            prompt = f"""
You are the Response Agent in an Enterprise AI Workspace.

The user asked:
{question}

The following content was retrieved from Google Drive:
{context}

A Gmail draft has already been created using this retrieved document.
The frontend will separately show the Gmail draft confirmation card below
the answer.

Write ONLY the document summary for the main answer.

Requirements:
1. Provide a clear, structured summary of the retrieved document.
2. Preserve important names, dates, amounts, identifiers, locations, participants, and other factual details.
3. Use only facts supported by the retrieved content.
4. Do not invent missing information.
5. Do not describe the user's request as if it were the document content.
6. Do not ask the recipient to provide the document.
7. Use Markdown.
8. Do not output HTML.
9. Do not mention internal retrieval or implementation details unless asked.
10. Do not include a Gmail draft confirmation in this answer; the frontend handles that separately.

Return only the final document summary.
"""

            try:
                response = llm.invoke(prompt)
                answer = (
                    response.content
                    if hasattr(response, "content")
                    else str(response)
                )
                return {
                    **state,
                    "answer": clean_model_output(answer),
                }
            except Exception as exc:
                return {
                    **state,
                    "answer": (
                        "The document was retrieved and the Gmail draft was created, "
                        "but I could not generate the final summary: "
                        f"{exc}"
                    ),
                }

        if error and not context:
            return {
                **state,
                "answer": (
                    "I could not complete the Drive-to-Gmail workflow.\n\n"
                    f"{error}"
                ),
            }

    # =====================================================
    # GMAIL ACTION RESULT
    # =====================================================

    if route == "gmail":
        if state.get("action_status") == "created":
            action_result = state.get(
                "action_result",
                {},
            )
            recipient = action_result.get(
                "recipient",
                "the recipient",
            ) if isinstance(action_result, dict) else "the recipient"
            subject = action_result.get(
                "subject",
                "",
            ) if isinstance(action_result, dict) else ""

            subject_line = (
                f" with subject **{subject}**"
                if subject
                else ""
            )

            return {
                **state,
                "answer": (
                    "### Gmail Draft Created\n\n"
                    f"The email draft was created successfully "
                    f"for **{recipient}**{subject_line}.\n\n"
                    "You can review it in Gmail before sending."
                ),
            }

        if error:
            return {
                **state,
                "answer": (
                    "I could not create the Gmail draft.\n\n"
                    f"{error}"
                ),
            }

    # =====================================================
    # RETRIEVAL FAILED
    # =====================================================

    if error and not context:

        source_name = (
            "Google Drive"
            if route == "drive"
            else "knowledge"
        )

        return {
            **state,
            "answer": (
                "I was unable to complete the request "
                "because the "
                f"{source_name} retrieval step "
                "encountered an error: "
                f"{error}"
            ),
        }

    # =====================================================
    # GENERAL RESPONSE
    # =====================================================

    if route == "general":

        llm = get_llm()

        prompt = f"""
You are the General Response Agent in an Enterprise
AI Workspace.

User question:

{question}

Answer clearly and helpfully.

Use Markdown where useful.

Do not output HTML.

Do not output <br>, <div>, <span>, or other HTML tags.

Return only the final answer.
"""

        try:

            response = llm.invoke(
                prompt
            )

            answer = (
                response.content
                if hasattr(
                    response,
                    "content",
                )
                else str(
                    response
                )
            )

            answer = clean_model_output(
                answer
            )

            return {
                **state,
                "answer": answer,
            }

        except Exception as exc:

            return {
                **state,
                "answer": (
                    "The response agent could not "
                    "generate the final answer: "
                    f"{exc}"
                ),
            }

    # =====================================================
    # NO CONTEXT
    # =====================================================

    if not context:

        return {
            **state,
            "answer": (
                "I could not find enough relevant "
                "information to answer your question."
            ),
        }

    # =====================================================
    # GROUNDED RESPONSE
    # =====================================================

    llm = get_llm()

    if route == "drive":

        source_type = (
            "Google Drive"
        )

    else:

        source_type = (
            "the enterprise knowledge system"
        )

    prompt = f"""
You are the Response Agent in an Enterprise AI Workspace.

The user asked:

{question}

The following information was retrieved from
{source_type}:

{context}

Instructions:

1. Answer the user's question using the retrieved
   information.

2. Do not invent facts that are not supported by the
   retrieved context.

3. Preserve important names, numbers, dates, amounts,
   locations, participants, identifiers, and factual
   details.

4. If the user asks for a summary, provide a structured
   and comprehensive summary.

5. If information from multiple retrieved files belongs
   to the same requested topic, combine it coherently.

6. Use Markdown.

7. Do not output HTML.

8. Do not output <br>, <div>, <span>, or other HTML tags.

9. Do not create a separate Sources section.
   The frontend handles sources separately.

10. Do not mention ChromaDB, embeddings, vector search,
    retrieval, agents, or internal implementation
    details unless the user explicitly asks about them.

11. You may mention MCP if the user explicitly asks
    about how the information was obtained.

12. If the requested information is not available in
    the retrieved context, clearly say so.

13. When answering from Google Drive, identify the
    relevant document naturally when useful.

14. Do not assume that every retrieved document is
    relevant. Focus on the files and content that
    actually answer the user's question.

15. If the retrieved content has been truncated, answer
    using only the available content and do not invent
    the missing information.

Return only the final answer.
"""

    # =====================================================
    # CALL LLM
    # =====================================================

    try:

        response = llm.invoke(
            prompt
        )

        answer = (
            response.content
            if hasattr(
                response,
                "content",
            )
            else str(
                response
            )
        )

        answer = clean_model_output(
            answer
        )

        return {
            **state,
            "answer": answer,
        }

    except Exception as exc:

        return {
            **state,
            "answer": (
                "The response agent could not "
                "generate the final answer: "
                f"{exc}"
            ),
        }


# =========================================================
# CLEAN MODEL OUTPUT
# =========================================================

def clean_model_output(
    text: str,
) -> str:

    if not text:

        return ""

    text = str(
        text
    )

    # -----------------------------------------------------
    # Remove HTML line breaks
    # -----------------------------------------------------

    text = re.sub(
        r"<br\s*/?>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    # -----------------------------------------------------
    # Remove common HTML tags
    # -----------------------------------------------------

    text = re.sub(
        r"</?(div|span|p|li|ul|ol|h1|h2|h3|h4|blockquote)[^>]*>",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # -----------------------------------------------------
    # Remove excessive blank lines
    # -----------------------------------------------------

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


# =========================================================
# ROUTER
# =========================================================

def route_after_supervisor(
    state: AgentState,
) -> str:

    route = state.get(
        "route",
        "general",
    )

    if route == "drive_gmail":

        return "drive_gmail"

    if route == "gmail":

        return "gmail"

    if route == "drive":

        return "drive"

    if route == "knowledge":

        return "knowledge"

    return "general"


# =========================================================
# BUILD LANGGRAPH
# =========================================================

def build_agent_graph():

    graph = StateGraph(
        AgentState
    )

    # -----------------------------------------------------
    # Agent nodes
    # -----------------------------------------------------

    graph.add_node(
        "supervisor",
        supervisor_agent,
    )

    graph.add_node(
        "knowledge",
        knowledge_agent,
    )

    graph.add_node(
        "gmail",
        gmail_agent,
    )

    graph.add_node(
        "drive",
        drive_agent,
    )

    graph.add_node(
        "general",
        general_agent,
    )

    graph.add_node(
        "response",
        response_agent,
    )

    # -----------------------------------------------------
    # START
    # -----------------------------------------------------

    graph.add_edge(
        START,
        "supervisor",
    )

    # -----------------------------------------------------
    # SUPERVISOR ROUTING
    # -----------------------------------------------------

    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "knowledge": "knowledge",
            "gmail": "gmail",
            "drive": "drive",
            "drive_gmail": "drive",
            "general": "general",
        },
    )

    # -----------------------------------------------------
    # AGENTS → RESPONSE
    # -----------------------------------------------------

    graph.add_edge(
        "knowledge",
        "response",
    )

    graph.add_edge(
        "gmail",
        "response",
    )

    # Normal Drive requests finish after Drive retrieval.
    # Combined Drive + Gmail requests continue into Gmail.
    def route_after_drive(state: AgentState) -> str:
        if state.get("route") == "drive_gmail":
            return "gmail"
        return "response"

    graph.add_conditional_edges(
        "drive",
        route_after_drive,
        {
            "gmail": "gmail",
            "response": "response",
        },
    )

    graph.add_edge(
        "general",
        "response",
    )

    # -----------------------------------------------------
    # RESPONSE → END
    # -----------------------------------------------------

    graph.add_edge(
        "response",
        END,
    )

    return graph.compile()


# =========================================================
# COMPILED GRAPH
# =========================================================

agent_graph = (
    build_agent_graph()
)


# =========================================================
# PUBLIC WORKFLOW
# =========================================================

def run_agent_workflow(
    question: str,
) -> Dict[str, Any]:

    initial_state: AgentState = {

        "question": question,

        "route": "",

        "context": "",

        "sources": [],

        "retrieved_chunks": 0,

        "answer": "",

        "error": "",

        "action_result": None,

        "action_status": "",
    }

    result = agent_graph.invoke(
        initial_state
    )

    # -----------------------------------------------------
    # Determine workflow display
    # -----------------------------------------------------

    route = result.get(
        "route",
        "general",
    )

    if route == "drive_gmail":

        workflow = [
            "Supervisor Agent",
            "Drive Agent",
            "Google Drive MCP",
            "Gmail Agent",
            "Gmail MCP",
            "Response Agent",
        ]

    elif route == "gmail":

        workflow = [
            "Supervisor Agent",
            "Gmail Agent",
            "Gmail MCP",
            "Response Agent",
        ]

    elif route == "drive":

        workflow = [
            "Supervisor Agent",
            "Drive Agent",
            "Google Drive MCP",
            "Response Agent",
        ]

    elif route == "knowledge":

        workflow = [
            "Supervisor Agent",
            "Knowledge Agent",
            "Local RAG",
            "Response Agent",
        ]

    else:

        workflow = [
            "Supervisor Agent",
            "General Agent",
            "Response Agent",
        ]

    return {

        "question": result.get(
            "question",
            question,
        ),

        "route": route,

        "answer": result.get(
            "answer",
            "",
        ),

        "sources": result.get(
            "sources",
            [],
        ),

        "retrieved_chunks": result.get(
            "retrieved_chunks",
            0,
        ),

        "action_result": result.get(
            "action_result",
            None,
        ),

        "action_status": result.get(
            "action_status",
            "",
        ),

        "agent_workflow": workflow,
    }