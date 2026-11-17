# Enterprise Multi-Agent AI Workspace using RAG and MCP

An AI-powered enterprise workspace designed to simplify organizational knowledge management, intelligent document retrieval, and workflow automation using Retrieval-Augmented Generation (RAG), multi-agent orchestration, and the Model Context Protocol (MCP).

## Overview

Modern organizations manage large amounts of information across documents, emails, cloud storage platforms, and business applications. Finding relevant information and performing repetitive tasks across these systems can be time-consuming.

The **Enterprise Multi-Agent AI Workspace** addresses this challenge by providing a centralized AI-powered environment where users can interact with organizational knowledge, retrieve contextually relevant information, and connect with external services.

The system combines RAG-based knowledge retrieval with LangGraph-powered AI orchestration and MCP integrations to support intelligent information access and enterprise workflow automation.

## Key Features

- **AI-Powered Chat Interface:** Interact with the workspace through a conversational interface.
- **Retrieval-Augmented Generation (RAG):** Retrieve relevant document content and generate context-aware responses.
- **Document Processing:** Upload and process PDF, DOCX, and TXT documents.
- **Semantic Search:** Search indexed documents based on contextual similarity rather than exact keyword matching.
- **Vector Database:** Store and retrieve document embeddings using ChromaDB.
- **Multi-Agent Orchestration:** Organize AI workflows using LangGraph.
- **MCP Integration:** Connect with external services, including Google Drive, through the Model Context Protocol.
- **Conversation Management:** Create, retrieve, and delete conversations with persistent message history.
- **Database Integration:** Store application data using PostgreSQL and SQLAlchemy.
- **Backend Health Monitoring:** Monitor API, database, RAG, and integration status.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React.js, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI |
| LLM Integration | Groq API |
| AI Orchestration | LangGraph |
| RAG Framework | Retrieval-Augmented Generation |
| Embedding Model | Sentence Transformers (`all-MiniLM-L6-v2`) |
| Vector Database | ChromaDB |
| Relational Database | PostgreSQL |
| ORM | SQLAlchemy |
| Document Processing | PyPDF, python-docx |
| External Integration | Model Context Protocol (MCP), Google Drive |
| Version Control | Git, GitHub |

## System Architecture

The application follows a frontend-backend architecture with separate modules for user interaction, AI processing, document retrieval, database operations, and external service integration.

```text
                  USER
                    |
                    v
          REACT FRONTEND
                    |
                    v
             FASTAPI BACKEND
                    |
          +---------+----------+
          |                    |
          v                    v
    AI ORCHESTRATION       DATABASE LAYER
      (LangGraph)          (PostgreSQL)
          |
          v
       RAG PIPELINE
          |
    +-----+------+
    |            |
    v            v
 Embeddings   ChromaDB
    |            |
    +-----+------+
          |
          v
   CONTEXT RETRIEVAL
          |
          v
      GROQ LLM
          |
          v
   CONTEXTUAL RESPONSE
          |
          v
      USER INTERFACE

    EXTERNAL INTEGRATIONS
          |
          v
     MCP CLIENT
          |
          v
       GOOGLE DRIVE
```

## RAG Workflow

The Retrieval-Augmented Generation pipeline enables the system to answer questions using information extracted from uploaded documents.

1. **Document Upload:** Users upload PDF, DOCX, or TXT files.
2. **Text Extraction:** The backend extracts readable text from the uploaded documents.
3. **Text Chunking:** Extracted content is divided into smaller overlapping chunks.
4. **Embedding Generation:** Sentence Transformers converts text chunks into numerical vector representations.
5. **Vector Storage:** Embeddings and document metadata are stored in ChromaDB.
6. **Semantic Retrieval:** User queries are converted into embeddings and matched against relevant document chunks.
7. **Context Construction:** Relevant retrieved content is assembled into context.
8. **Response Generation:** The Groq-powered language model generates a response using the retrieved context.

## Multi-Agent Orchestration

LangGraph is used to structure and manage AI processing workflows. The orchestration layer provides a foundation for coordinating different stages of the AI workflow, including retrieval and response generation.

The architecture is designed to support extensible agent-based processing and future enterprise automation capabilities.

## MCP Integration

The Model Context Protocol provides a standardized approach for connecting AI applications with external tools and services.

The project includes Google Drive integration to support enterprise document access and external knowledge retrieval.

MCP helps extend the workspace beyond locally uploaded documents by enabling connections to external business resources.

## Project Structure

The repository is organized into frontend and backend components.

```text
Enterprise-Multi-Agent-AI-Workspace/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── ...
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── main.py
│   │   └── mcp/
│   ├── uploads/
│   ├── chroma_db/
│   ├── requirements.txt
│   └── ...
│
├── README.md
└── .gitignore
```

*Note: The directory tree above illustrates the intended logical organization. Adjust the paths to match the actual repository structure.*

## Prerequisites

Before running the application, ensure that you have:

- Python 3.11 or later
- Node.js and npm
- PostgreSQL
- Git
- A Groq API key
- Google Drive credentials for the relevant MCP integration

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/shashi02-debug/Enterprise-Multi-Agent-AI-Workspace-using-RAG-and-MCP-.git

cd Enterprise-Multi-Agent-AI-Workspace-using-RAG-and-MCP-
```

### 2. Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create and activate a virtual environment.

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**Install dependencies:**

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the backend directory.

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b

DATABASE_URL=postgresql://username:password@localhost:5432/enterprise_ai
```

Replace the placeholder values with your actual credentials.

Configure additional Google Drive/MCP credentials according to the integration module.

**Important:** Never upload API keys, passwords, credentials, or `.env` files to GitHub.

### 4. Configure PostgreSQL

Create a PostgreSQL database named:

```sql
CREATE DATABASE enterprise_ai;
```

Ensure that the database connection URL matches your PostgreSQL configuration.

### 5. Start the Backend Server

From the backend directory, run:

```bash
uvicorn app.main:app --reload
```

Backend API:

```text
http://127.0.0.1:8000
```

FastAPI interactive documentation:

```text
http://127.0.0.1:8000/docs
```

### 6. Frontend Setup

Open another terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Frontend:

```text
http://localhost:5173
```

*Note: Verify the actual frontend and backend directory names and entry points in your repository before running these commands.*

## API Endpoints

The backend exposes REST APIs for application operations.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Checks application and integration status |
| GET | `/database/health` | Checks PostgreSQL connectivity |
| POST | `/conversations` | Creates a conversation |
| GET | `/conversations` | Retrieves conversations |
| GET | `/conversations/{conversation_id}` | Retrieves conversation messages |
| POST | `/conversations/{conversation_id}/messages` | Adds a conversation message |
| DELETE | `/conversations/{conversation_id}` | Deletes a conversation |

Additional document upload, retrieval, and MCP endpoints are implemented in the backend.

## Future Enhancements

- Expand multi-agent collaboration with specialized planning, retrieval, reasoning, and validation agents.
- Add role-based access control and enterprise authentication.
- Extend MCP integrations to Gmail, Google Calendar, GitHub, and other business applications.
- Introduce approval-based execution for sensitive enterprise actions.
- Improve document-level permissions and retrieval security.
- Add comprehensive monitoring, logging, and evaluation of AI-generated responses.
- Support additional document formats and enterprise data sources.

## Learning Outcomes

This project demonstrates practical implementation of:

- Full-stack application development.
- REST API development using FastAPI.
- Retrieval-Augmented Generation (RAG).
- Semantic search and vector databases.
- LLM integration and prompt engineering.
- Graph-based AI workflow orchestration.
- Relational database integration.
- External tool and service integration using MCP.
- Git-based collaborative development.

## Author

**Shashikiran**

GitHub: [@shashi02-debug](https://github.com/shashi02-debug)

## License

This project is intended for academic and educational purposes. Add an appropriate open-source license if you plan to distribute or reuse the project publicly.
