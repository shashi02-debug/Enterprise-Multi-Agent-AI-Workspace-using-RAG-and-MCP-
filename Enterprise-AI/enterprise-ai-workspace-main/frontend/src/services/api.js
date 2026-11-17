const API_BASE_URL =
  "http://127.0.0.1:8000";


export {
  API_BASE_URL,
};


// =====================================================
// GENERIC API REQUEST
// =====================================================

export async function apiRequest(
  endpoint,
  options = {}
) {

  const response =
    await fetch(
      `${API_BASE_URL}${endpoint}`,
      options
    );


  const contentType =
    response.headers.get(
      "content-type"
    ) || "";


  let data;


  if (
    contentType.includes(
      "application/json"
    )
  ) {

    data =
      await response.json();

  } else {

    data =
      await response.text();

  }


  if (!response.ok) {

    let message =
      "Request failed.";


    if (
      typeof data ===
      "string"
    ) {

      message =
        data ||
        message;

    } else {

      message =
        data?.detail ||
        data?.message ||
        data?.error ||
        message;

    }


    throw new Error(
      message
    );

  }


  return data;
}


// =====================================================
// HEALTH
// =====================================================

export async function checkHealth() {

  return apiRequest(
    "/health"
  );

}


// =====================================================
// DATABASE HEALTH
// =====================================================

export async function checkDatabaseHealth() {

  return apiRequest(
    "/database/health"
  );

}


// =====================================================
// DOCUMENTS
// =====================================================

export async function getDocuments() {

  return apiRequest(
    "/documents"
  );

}


export async function uploadDocument(
  file
) {

  const formData =
    new FormData();

  formData.append(
    "file",
    file
  );


  return apiRequest(
    "/documents/upload",
    {
      method: "POST",
      body: formData,
    }
  );

}


export async function deleteDocument(
  filename
) {

  return apiRequest(
    `/documents/${encodeURIComponent(
      filename
    )}`,
    {
      method: "DELETE",
    }
  );

}


export async function getDocumentContent(
  filename
) {

  return apiRequest(
    `/documents/${encodeURIComponent(
      filename
    )}/content`
  );

}


// =====================================================
// DOCUMENT INDEX
// =====================================================

export async function indexDocument(
  filename
) {

  return apiRequest(
    `/documents/${encodeURIComponent(
      filename
    )}/index`,
    {
      method: "POST",
    }
  );

}


// =====================================================
// RAG
// =====================================================

export async function getRagStatus() {

  return apiRequest(
    "/rag/status"
  );

}


export async function searchKnowledge(
  query,
  topK = 5
) {

  return apiRequest(
    "/search",
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",

        Accept:
          "application/json",
      },

      body: JSON.stringify({
        query,
        top_k: topK,
      }),
    }
  );

}


// =====================================================
// LEGACY CHAT
// =====================================================

export async function askWorkspace(
  message
) {

  return apiRequest(
    "/chat",
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",

        Accept:
          "application/json",
      },

      body: JSON.stringify({
        message,
      }),
    }
  );

}


// =====================================================
// MULTI-AGENT WORKFLOW
// =====================================================

export async function runAgentWorkflow(
  message
) {

  return apiRequest(
    "/agents/run",
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",

        Accept:
          "application/json",
      },

      body: JSON.stringify({
        message,
      }),
    }
  );

}


// =====================================================
// CONVERSATIONS
// =====================================================

export async function createConversation(
  conversationId = null,
  title = "New Chat"
) {

  return apiRequest(
    "/conversations",
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",

        Accept:
          "application/json",
      },

      body: JSON.stringify({
        conversation_id:
          conversationId,
        title,
      }),
    }
  );

}


export async function getConversations(
  limit = 50
) {

  return apiRequest(
    `/conversations?limit=${limit}`
  );

}


export async function getConversation(
  conversationId
) {

  return apiRequest(
    `/conversations/${encodeURIComponent(
      conversationId
    )}`
  );

}


export async function saveConversationMessage(
  conversationId,
  message
) {

  return apiRequest(
    `/conversations/${encodeURIComponent(
      conversationId
    )}/messages`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",

        Accept:
          "application/json",
      },

      body: JSON.stringify({
        role:
          message.role,

        content:
          message.content,

        sources:
          message.sources ||
          null,

        agent_workflow:
          message.agentWorkflow ||
          null,

        action_result:
          message.actionResult ||
          null,
      }),
    }
  );

}


export async function deleteConversation(
  conversationId
) {

  return apiRequest(
    `/conversations/${encodeURIComponent(
      conversationId
    )}`,
    {
      method: "DELETE",
    }
  );

}