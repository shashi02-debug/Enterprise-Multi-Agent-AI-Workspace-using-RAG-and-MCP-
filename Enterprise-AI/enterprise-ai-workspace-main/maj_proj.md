# Enterprise AI Workspace --- Project Reference & Progress

**Last updated:** 29 August 2026

## 1. Project Overview

Enterprise AI Workspace is a full-stack enterprise AI application
intended to bring documents, organizational knowledge, AI assistants,
agents, and workflow automation into one workspace.

### Core vision

The completed product should allow users to:

-   Upload and manage enterprise documents.
-   Read and inspect uploaded document content.
-   Ask natural-language questions about the workspace.
-   Retrieve information from documents and knowledge sources.
-   Receive AI-generated answers with Markdown formatting and source
    references.
-   Create specialized AI agents for business workflows.
-   Create and monitor AI-driven tasks and automations.
-   Manage workspace data securely.

------------------------------------------------------------------------

## 2. Technology Stack

### Frontend

-   React
-   JSX
-   CSS
-   Vite
-   Browser `fetch()` for API communication
-   Responsive/mobile UI

### Backend

-   Python
-   FastAPI
-   Uvicorn
-   REST APIs
-   `.env` configuration

### AI / Knowledge

-   Document ingestion
-   Embeddings / semantic retrieval
-   Chroma vector database
-   RAG-style workspace question answering

------------------------------------------------------------------------

## 3. Current Project Structure

``` text
enterprise-ai-workspace/
│
├── backend/
│   ├── .venv/
│   ├── app/
│   │   ├── __pycache__/
│   │   ├── chroma_db/
│   │   ├── uploads/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── main.py
│   │   └── models.py
│   ├── .env
│   └── requirements.txt
│
└── frontend/
    ├── node_modules/
    ├── public/
    ├── src/
    │   ├── assets/
    │   ├── App.css
    │   ├── App.jsx
    │   ├── index.css
    │   └── main.jsx
    ├── .gitignore
    ├── package.json
    └── ...
```

------------------------------------------------------------------------

# 4. Application Architecture

``` text
User / Browser
      │
      ▼
React Frontend
      │
      │ REST / HTTP
      ▼
FastAPI Backend
      │
      ├── Documents
      ├── Chat / RAG
      ├── Knowledge
      ├── Agents
      └── Tasks
      │
      ├──────────────► File Storage
      │
      └──────────────► Chroma Vector Database
```

The frontend should communicate with the backend through stable API
contracts. AI/model secrets must remain on the backend.

------------------------------------------------------------------------

# 5. Main Navigation

The current application contains:

1.  Workspace
2.  Documents
3.  Knowledge
4.  Agents
5.  Tasks

The sidebar also contains:

-   Current workspace information
-   Backend connection status
-   Settings
-   User profile
-   Mobile navigation controls

------------------------------------------------------------------------

# 6. Workspace Module

## Current functionality

The Workspace page is the main landing page.

It currently contains:

-   Enterprise AI branding
-   Workspace introduction
-   AI question/search input
-   Enter-to-submit
-   Arrow-button submit
-   AI loading state
-   AI error state
-   AI answer card
-   Suggested workflows
-   Workspace information cards
-   Footer

## Chat API

The frontend sends:

``` http
POST /chat
```

with:

``` json
{
  "message": "user question"
}
```

The frontend currently accepts answer fields such as:

``` text
answer
response
message
text
```

## Current flow

``` text
User question
    ↓
handleAsk()
    ↓
POST /chat
    ↓
FastAPI
    ↓
Retrieval / AI
    ↓
Response
    ↓
React answer card
```

------------------------------------------------------------------------

# 7. Markdown AI Responses

## Requirement

AI responses should support Markdown rather than displaying raw/plain
text.

Expected support:

-   Headings
-   Bold
-   Italic
-   Bullet lists
-   Numbered lists
-   Links
-   Inline code
-   Code blocks
-   Blockquotes
-   Tables

## Recommended implementation

Use:

``` text
react-markdown
remark-gfm
```

The current plain rendering:

``` jsx
{chatAnswer}
```

should be replaced with a Markdown renderer.

The Markdown renderer should be styled to match the Enterprise AI
design.

------------------------------------------------------------------------

# 8. AI Answer Card

The answer card should look like a polished enterprise assistant
response rather than a plain text box.

Recommended structure:

``` text
┌─────────────────────────────────────────────┐
│ ✦  ENTERPRISE AI                            │
│    Workspace Assistant                      │
│                                             │
│    Answer heading                           │
│                                             │
│    Markdown response...                     │
│                                             │
│    • Important point                        │
│    • Another point                          │
│                                             │
│    ┌─────────────────────────────────────┐  │
│    │ Code / structured information       │  │
│    └─────────────────────────────────────┘  │
│                                             │
│    Sources                                  │
│    • document.pdf — Page 2                 │
└─────────────────────────────────────────────┘
```

### UI goals

-   Clear AI identity/header
-   Strong typography hierarchy
-   Comfortable line spacing
-   Styled Markdown
-   Styled code blocks
-   Styled tables
-   Subtle border
-   Subtle shadow
-   Consistent purple accent
-   Good spacing
-   Responsive behavior
-   Good long-answer handling

------------------------------------------------------------------------

# 9. Documents Module

The Documents module is currently one of the most developed parts of the
frontend.

## Current functionality

-   Document listing
-   Upload
-   File validation
-   Refresh
-   Open
-   Document viewer
-   Delete
-   Loading states
-   Empty states
-   Error states

------------------------------------------------------------------------

# 10. Supported Documents

Current frontend support:

``` text
PDF
DOCX
TXT
```

The file picker accepts:

``` text
.pdf
.docx
.txt
```

The frontend also checks the filename extension before upload.

------------------------------------------------------------------------

# 11. Document Upload

## API

``` http
POST /documents/upload
```

Multipart form field:

``` text
file
```

## Flow

``` text
Select file
    ↓
Validate extension
    ↓
Create FormData
    ↓
POST /documents/upload
    ↓
Backend stores/processes file
    ↓
Reload document list
```

## UI states

-   Uploading...
-   Upload success
-   Upload failure
-   Unsupported file type
-   Empty document list

------------------------------------------------------------------------

# 12. Document Listing

## API

``` http
GET /documents
```

The frontend can currently handle either:

``` json
{
  "documents": []
}
```

or a direct array.

Document information currently used by the UI includes:

``` text
filename
file_type
size
```

Each document card contains:

-   File type
-   Filename
-   File size
-   Open
-   Delete

------------------------------------------------------------------------

# 13. Document Viewer

The frontend currently attempts several possible content endpoints:

``` text
/documents/{filename}/content
/documents/{filename}/read
/documents/{filename}/text
/documents/content/{filename}
/documents/read/{filename}
/documents/{filename}
```

## Recommended cleanup

Finalize one official endpoint, preferably:

``` http
GET /documents/{filename}/content
```

Then remove endpoint guessing from the frontend.

This creates a cleaner and more maintainable API contract.

------------------------------------------------------------------------

# 14. Document Content

The current `DocumentContent` component can handle:

-   `pages`
-   array `content`
-   `text`
-   string `content`
-   plain string responses
-   generic JSON fallback

PDF/DOCX-style display:

``` text
PAGE 1
Extracted content...

PAGE 2
Extracted content...
```

TXT display:

``` text
CONTENT
Text...
```

------------------------------------------------------------------------

# 15. Document Deletion

## API

``` http
DELETE /documents/{filename}
```

The filename is URL encoded.

After successful deletion:

-   Remove document from UI.
-   Close viewer if that document is open.
-   Display success message.

A confirmation dialog is currently shown before deletion.

------------------------------------------------------------------------

# 16. Document Processing Pipeline

The intended backend pipeline is:

``` text
Upload
  ↓
Validate
  ↓
Store original file
  ↓
Extract text
  ↓
Normalize text
  ↓
Split into chunks
  ↓
Generate embeddings
  ↓
Store vectors
  ↓
Store metadata
  ↓
Make searchable
```

### PDF

``` text
PDF → page-aware extraction → chunks
```

### DOCX

``` text
DOCX → paragraph/text extraction → chunks
```

### TXT

``` text
TXT → text → chunks
```

------------------------------------------------------------------------

# 17. Chroma / Vector Database

The project currently contains:

``` text
backend/app/chroma_db/
```

The intended RAG flow is:

``` text
Document
   ↓
Text extraction
   ↓
Chunking
   ↓
Embeddings
   ↓
Chroma
   ↓
Similarity search
   ↓
Relevant chunks
   ↓
LLM
   ↓
Answer
```

Recommended metadata:

``` text
filename
document_id
page_number
chunk_id
source
```

Metadata should make AI answers traceable to their source documents.

------------------------------------------------------------------------

# 18. RAG / Workspace Question Answering

The intended `/chat` architecture:

``` text
Question
   ↓
Question preprocessing
   ↓
Semantic retrieval
   ↓
Search Chroma
   ↓
Relevant chunks
   ↓
Context construction
   ↓
LLM prompt
   ↓
Answer generation
   ↓
Answer + sources
```

The backend should retrieve relevant chunks rather than sending the
entire document collection to the model for every question.

------------------------------------------------------------------------

# 19. Recommended Chat Response

Eventually `/chat` should return structured data:

``` json
{
  "answer": "The requested information is ...",
  "sources": [
    {
      "filename": "example.pdf",
      "page": 2
    }
  ]
}
```

The frontend can then show:

``` text
Answer

Sources
• example.pdf — Page 2
• policy.docx — Section 4
```

Source attribution is important for an enterprise knowledge system.

------------------------------------------------------------------------

# 20. Knowledge Module

## Current status

Navigation exists, but the page is currently a Coming Soon screen.

## Planned purpose

Knowledge management should handle information beyond individual
uploaded documents.

Potential features:

-   Knowledge collections
-   Enterprise policies
-   FAQs
-   Procedures
-   Structured information
-   Connected sources
-   Search
-   Retrieval configuration
-   Permissions

## Planned pipeline

``` text
Knowledge Source
      ↓
Ingestion
      ↓
Chunking / Structuring
      ↓
Embeddings
      ↓
Vector / Knowledge Store
      ↓
Retrieval
      ↓
AI
```

------------------------------------------------------------------------

# 21. Agents Module

## Current status

Navigation exists, but the page is currently a Coming Soon screen.

## Planned purpose

Users should be able to create specialized AI agents.

Examples:

-   HR assistant
-   Document analyst
-   Customer support assistant
-   Sales assistant
-   Research assistant
-   Internal policy assistant
-   Meeting assistant

## Agent configuration

Potential fields:

``` text
Agent Name
Description
System Instructions
Knowledge Sources
Allowed Tools
Model
Temperature
Output Format
Access Permissions
```

## Agent lifecycle

``` text
Create
  ↓
Configure instructions
  ↓
Connect knowledge
  ↓
Configure tools
  ↓
Test
  ↓
Save / Publish
  ↓
Run
```

------------------------------------------------------------------------

# 22. Tasks / Automation Module

## Current status

Navigation exists, but the page is currently a Coming Soon screen.

## Planned purpose

Automate repetitive enterprise workflows.

Example:

``` text
Incoming document
      ↓
Extract information
      ↓
Analyze
      ↓
Generate report/response
      ↓
Store or send result
```

Potential task fields:

-   Task name
-   Trigger
-   Schedule
-   Input
-   AI agent
-   Knowledge sources
-   Actions
-   Output
-   Execution history
-   Status
-   Logs

------------------------------------------------------------------------

# 23. Backend

Backend location:

``` text
backend/app/
```

Important current files:

``` text
main.py
database.py
models.py
```

## `main.py`

Main FastAPI application entry point.

Expected responsibilities:

-   FastAPI initialization
-   Routes
-   CORS
-   Health check
-   Chat
-   Documents
-   Future Knowledge APIs
-   Future Agent APIs
-   Future Task APIs

## `database.py`

Database responsibilities may include:

-   Connection
-   Session management
-   Initialization
-   CRUD operations
-   Workspace data
-   User data
-   Agent data
-   Task data
-   Document metadata

## `models.py`

Potential domain models:

``` text
User
Workspace
Document
KnowledgeSource
Agent
Task
TaskExecution
ChatSession
ChatMessage
```

The actual database schema should remain synchronized with the backend
implementation.

------------------------------------------------------------------------

# 24. Current API Contract

  ---------------------------------------------------------------------------------
  Method                  Endpoint                          Purpose
  ----------------------- --------------------------------- -----------------------
  GET                     `/health`                         Backend health

  GET                     `/documents`                      List documents

  POST                    `/documents/upload`               Upload document

  DELETE                  `/documents/{filename}`           Delete document

  GET                     `/documents/{filename}/content`   Recommended final
                                                            content endpoint

  POST                    `/chat`                           Ask workspace AI
  ---------------------------------------------------------------------------------

The document content endpoint should be finalized and used consistently.

------------------------------------------------------------------------

# 25. Responsive Design

## Desktop

``` text
Sidebar + Main Content
```

## Tablet

``` text
Collapsible Sidebar
Flexible Content
```

## Mobile

``` text
Top Header
Hamburger
Off-canvas Sidebar
Full-width Content
Stacked Cards
```

The frontend already has a `sidebarOpen` state and mobile overlay/close
behavior.

### Mobile requirements

-   Sidebar becomes off-canvas.
-   Main content uses available width.
-   Chat input remains easy to use.
-   AI cards never overflow horizontally.
-   Document cards stack.
-   Buttons remain touch-friendly.
-   Document modal uses most of the screen.
-   Code blocks/tables scroll horizontally where needed.

------------------------------------------------------------------------

# 26. UI / Design System

The current visual direction is modern enterprise SaaS.

Core characteristics:

-   Light background
-   Purple primary accent
-   Rounded cards
-   Soft borders
-   Subtle shadows
-   Large headings
-   Spacious layout
-   Clean typography
-   Minimal clutter
-   Responsive behavior

All modules should use the same visual language.

------------------------------------------------------------------------

# 27. Error Handling

Current frontend handles:

-   Backend health failure
-   Document loading errors
-   Upload errors
-   Unsupported files
-   Delete errors
-   Document reading errors
-   Chat errors

Recommended backend error format:

``` json
{
  "detail": "Human-readable error message"
}
```

Useful HTTP statuses:

``` text
400 Bad Request
404 Not Found
413 Payload Too Large
422 Validation Error
500 Internal Server Error
503 Service Unavailable
```

------------------------------------------------------------------------

# 28. Security Roadmap

Before production:

-   Authentication
-   Authorization
-   Workspace isolation
-   File validation
-   File size limits
-   Secure filenames
-   Input validation
-   Correct CORS configuration
-   Secret management
-   Document access control
-   Prompt-injection defenses for retrieved content
-   Audit logging

Never expose AI/API secrets in frontend code.

Do not commit:

``` text
.env
.venv/
node_modules/
chroma_db/
uploaded private documents
API keys
```

------------------------------------------------------------------------

# 29. Authentication & Authorization

Future structure:

``` text
User
 ↓
Login
 ↓
Workspace
 ↓
Role
 ↓
Permissions
```

Possible roles:

``` text
Admin
Member
Viewer
```

Permissions can control:

-   Upload
-   Delete
-   Knowledge management
-   Agent creation
-   Task creation
-   Workspace settings

------------------------------------------------------------------------

# 30. Workspace Model

The final application should organize everything under a workspace:

``` text
Workspace
│
├── Members
├── Documents
├── Knowledge
├── Agents
├── Tasks
└── Settings
```

Workspace association is essential for future multi-user/multi-tenant
support.

------------------------------------------------------------------------

# 31. Settings

Current sidebar contains Settings.

Future settings can include:

### Workspace

-   Workspace name
-   Description
-   Members

### AI

-   Default model
-   Response configuration
-   Retrieval settings

### Documents

-   Allowed file types
-   File limits
-   Retention

### Security

-   Authentication
-   Roles
-   Permissions
-   API configuration

------------------------------------------------------------------------

# 32. Development Phases

## Phase 1 --- Foundation

**Status: Mostly implemented**

-   [x] React frontend
-   [x] FastAPI backend
-   [x] Workspace UI
-   [x] Sidebar
-   [x] Responsive sidebar foundation
-   [x] Backend health check
-   [x] API connection indicator

## Phase 2 --- Documents

**Status: Frontend largely implemented**

-   [x] Documents page
-   [x] Document list
-   [x] PDF support
-   [x] DOCX support
-   [x] TXT support
-   [x] Upload
-   [x] Validation
-   [x] Delete
-   [x] Viewer
-   [x] Loading states
-   [x] Empty states
-   [x] Error states
-   [ ] Finalize content API
-   [ ] Improve extraction reliability
-   [ ] Add processing status
-   [ ] Add metadata
-   [ ] Add search/filter/sort

## Phase 3 --- RAG / AI Workspace

**Status: Core functionality implemented**

-   [x] Question input
-   [x] Enter submit
-   [x] Arrow submit
-   [x] `/chat` integration
-   [x] Loading state
-   [x] Error state
-   [x] AI answer display
-   [ ] Markdown rendering
-   [ ] Improved answer card
-   [ ] Source citations
-   [ ] Retrieval quality improvements
-   [ ] Chat history
-   [ ] Chat sessions
-   [ ] Streaming responses
-   [ ] Better context handling

## Phase 4 --- Knowledge

**Status: Planned**

-   [ ] Knowledge page
-   [ ] Collections
-   [ ] Knowledge sources
-   [ ] Search
-   [ ] Management
-   [ ] Metadata
-   [ ] Retrieval configuration
-   [ ] Permissions

## Phase 5 --- Agents

**Status: Planned**

-   [ ] Agent list
-   [ ] Create
-   [ ] Edit
-   [ ] Delete
-   [ ] Instructions
-   [ ] Knowledge selection
-   [ ] Tools
-   [ ] Testing
-   [ ] Execution
-   [ ] Permissions

## Phase 6 --- Tasks

**Status: Planned**

-   [ ] Task dashboard
-   [ ] Create task
-   [ ] Triggers
-   [ ] Agent selection
-   [ ] Knowledge selection
-   [ ] Actions
-   [ ] Scheduling
-   [ ] Execution
-   [ ] History
-   [ ] Logs
-   [ ] Retry handling

## Phase 7 --- Security

**Status: Planned**

-   [ ] Authentication
-   [ ] Authorization
-   [ ] Workspace isolation
-   [ ] Secure uploads
-   [ ] Roles
-   [ ] Audit logs

## Phase 8 --- Production

**Status: Planned**

-   [ ] Production database
-   [ ] Production vector store
-   [ ] Logging
-   [ ] Monitoring
-   [ ] Error tracking
-   [ ] Automated tests
-   [ ] API documentation
-   [ ] Deployment
-   [ ] HTTPS
-   [ ] Backups
-   [ ] Performance optimization

------------------------------------------------------------------------

# 33. Testing Plan

## Frontend

Test:

-   Navigation
-   Upload
-   File validation
-   Delete
-   Open
-   Chat
-   Markdown
-   Loading states
-   Error states
-   Mobile navigation
-   Responsive layouts
-   Viewer modal

## Backend

Test:

-   `/health`
-   `/documents`
-   Upload
-   Delete
-   Content extraction
-   Chroma insertion
-   Retrieval
-   `/chat`
-   AI generation

## End-to-end

``` text
Upload document
      ↓
Process document
      ↓
Document appears
      ↓
Ask question
      ↓
Retrieve relevant content
      ↓
AI answers
      ↓
Source is shown
```

------------------------------------------------------------------------

# 34. Git / Version Control

Recommended commit style:

``` text
feat: add document upload
feat: add workspace chat
feat: add markdown AI responses
fix: handle document API errors
style: improve AI response card
refactor: simplify document content API
docs: update project roadmap
```

Keep secrets and generated/private data out of Git.

------------------------------------------------------------------------

# 35. Development Commands

## Backend

``` bash
cd backend
uvicorn app.main:app --reload
```

Expected local backend:

``` text
http://127.0.0.1:8000
```

Health:

``` text
http://127.0.0.1:8000/health
```

## Frontend

``` bash
cd frontend
npm install
npm run dev
```

The current frontend is served by Vite.

------------------------------------------------------------------------

# 36. Frontend API Configuration

Current frontend configuration:

``` javascript
const API_BASE_URL = "http://127.0.0.1:8000";
```

For production, move this to a Vite environment variable such as:

``` text
VITE_API_BASE_URL
```

This allows separate development, testing, and production backend URLs.

------------------------------------------------------------------------

# 37. Priority Improvements

## High priority

1.  Add Markdown rendering.
2.  Improve AI answer card design.
3.  Add source citations.
4.  Finalize document content API.
5.  Improve RAG quality.
6.  Add chat history/session support.
7.  Improve mobile document viewer.

## Medium priority

8.  Document processing status.
9.  Document metadata.
10. Search/filter/sort.
11. Knowledge module.
12. Agent module.
13. Task module.
14. Settings page.

## Later

15. Authentication.
16. Roles and permissions.
17. Audit logs.
18. Production deployment.
19. Monitoring.
20. Automated testing.

------------------------------------------------------------------------

# 38. Definition of Done

The MVP should eventually satisfy:

### Workspace

-   [ ] Polished workspace
-   [ ] Reliable AI chat
-   [ ] Markdown responses
-   [ ] Sources
-   [ ] Good error handling

### Documents

-   [x] Upload
-   [x] List
-   [x] Delete
-   [x] Open
-   [ ] Reliable extraction
-   [ ] Processing status
-   [ ] Search/filter

### Knowledge

-   [ ] Sources
-   [ ] Search
-   [ ] Retrieval
-   [ ] Management

### Agents

-   [ ] Create
-   [ ] Configure
-   [ ] Test
-   [ ] Run

### Tasks

-   [ ] Create
-   [ ] Schedule
-   [ ] Execute
-   [ ] Monitor

### Security

-   [ ] Authentication
-   [ ] Authorization
-   [ ] Workspace isolation

### Production

-   [ ] Tests
-   [ ] Logging
-   [ ] Monitoring
-   [ ] Deployment
-   [ ] Documentation

------------------------------------------------------------------------

# 39. Current Progress Snapshot

  Module                  Status
  ----------------------- ----------------
  React frontend          🟢 Implemented
  FastAPI backend         🟢 Implemented
  Workspace UI            🟢 Implemented
  Health check            🟢 Implemented
  API status              🟢 Implemented
  Document listing        🟢 Implemented
  Document upload         🟢 Implemented
  PDF support             🟢 Implemented
  DOCX support            🟢 Implemented
  TXT support             🟢 Implemented
  Document deletion       🟢 Implemented
  Document viewer         🟢 Implemented
  Workspace chat          🟢 Implemented
  AI answer display       🟢 Implemented
  Markdown responses      🟡 Next
  Improved answer card    🟡 Next
  Source citations        🟡 Planned
  Knowledge               🟡 Planned
  Agents                  🟡 Planned
  Tasks                   🟡 Planned
  Authentication          🟡 Planned
  Permissions             🟡 Planned
  Production deployment   ⚪ Future

------------------------------------------------------------------------

# 40. Progress Log

## 29 August 2026

### Current state

-   Enterprise AI Workspace frontend established.
-   React/Vite frontend connected to FastAPI backend.
-   Workspace navigation created.
-   Backend health check implemented.
-   API online/offline indicator implemented.
-   Documents page implemented.
-   PDF/DOCX/TXT upload support implemented.
-   Document listing implemented.
-   Document deletion implemented.
-   Document viewer implemented.
-   Workspace `/chat` integration implemented.
-   AI answers are being displayed successfully.
-   Enter key and arrow button submit the workspace question.
-   Responsive/mobile sidebar foundation exists.

### Immediate next step

``` text
Markdown AI responses
        ↓
Improved AI answer card
        ↓
Source citations
        ↓
Better RAG quality
```

------------------------------------------------------------------------

# 41. How to Maintain This Document

Whenever a feature is completed:

1.  Change its checkbox.
2.  Update the Progress Snapshot.
3.  Add an entry to the Progress Log.
4.  Record important API changes.
5.  Record important architecture decisions.
6.  Record known bugs or limitations.

Keep the historical Progress Log so the development journey can be
tracked.

------------------------------------------------------------------------

# 42. Project Development Principle

Build the project in layers:

``` text
Reliable Backend
      ↓
Stable API Contracts
      ↓
Clean Frontend
      ↓
Good UX
      ↓
RAG / AI Quality
      ↓
Agents
      ↓
Automation
      ↓
Security
      ↓
Production
```

The objective is not merely to add screens. Every major module should
eventually have a reliable backend, stable API, useful AI behavior,
clear error handling, and consistent UX.

------------------------------------------------------------------------

# 43. Final Product Vision

``` text
                 ENTERPRISE AI WORKSPACE
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
   Documents           Knowledge              AI
       │                   │                   │
       └────────────┬──────┴──────┬────────────┘
                    │             │
                 Retrieval      Agents
                    │             │
                    └──────┬──────┘
                           │
                         Tasks
                           │
                           ▼
                  Automated Workflows
```

The long-term goal is to make documents, enterprise knowledge, AI
reasoning, specialized agents, and workflow automation operate together
inside one secure enterprise workspace.
