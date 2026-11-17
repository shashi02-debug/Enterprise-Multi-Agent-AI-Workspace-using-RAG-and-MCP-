import "./ChatBox.css";

import { useState } from "react";

import {
  runAgentWorkflow,
} from "../../services/api";

import AIAnswer from "./AIAnswer";


// =====================================================
// CLEAN AI ANSWER
// =====================================================

function cleanAnswer(answer) {
  if (!answer) {
    return "";
  }

  return String(answer)

    .replace(
      /<br\s*\/?>/gi,
      "\n"
    )

    .replace(
      /<\/(p|div|li|ul|ol|h1|h2|h3|h4|blockquote)>/gi,
      "\n"
    )

    .replace(
      /<(p|div|li|ul|ol|h1|h2|h3|h4|blockquote)[^>]*>/gi,
      ""
    )

    .replace(
      /\n{3,}/g,
      "\n\n"
    )

    .trim();
}


// =====================================================
// EXTRACT ANSWER
// =====================================================

function extractChatAnswer(data) {
  if (
    data === null ||
    data === undefined
  ) {
    return "";
  }


  if (
    typeof data === "string"
  ) {
    return cleanAnswer(data);
  }


  const possibleFields = [
    "answer",
    "response",
    "message",
    "text",
    "result",
    "content",
    "reply",
    "output",
  ];


  for (
    const field of possibleFields
  ) {
    if (
      typeof data[field] ===
        "string" &&
      data[field].trim()
    ) {
      return cleanAnswer(
        data[field]
      );
    }
  }


  if (
    data.data &&
    typeof data.data === "object"
  ) {
    return extractChatAnswer(
      data.data
    );
  }


  if (
    Array.isArray(data.choices) &&
    data.choices.length > 0
  ) {
    const choice =
      data.choices[0];


    if (
      typeof choice?.message
        ?.content === "string"
    ) {
      return cleanAnswer(
        choice.message.content
      );
    }


    if (
      typeof choice?.text === "string"
    ) {
      return cleanAnswer(
        choice.text
      );
    }
  }


  return "";
}


// =====================================================
// EXTRACT SOURCES
// =====================================================

function extractSources(data) {
  if (!data) {
    return [];
  }


  if (
    Array.isArray(data.sources)
  ) {
    return [
      ...new Set(
        data.sources
          .filter(
            (source) =>
              typeof source === "string"
          )
          .map(
            (source) =>
              source.trim()
          )
          .filter(Boolean)
      ),
    ];
  }


  if (
    typeof data.sources === "string"
  ) {
    const matches = [
      ...data.sources.matchAll(
        /\[Source:\s*([^\]]+)\]/gi
      ),
    ];


    return [
      ...new Set(
        matches
          .map(
            (match) =>
              match[1]?.trim()
          )
          .filter(Boolean)
      ),
    ];
  }


  if (
    data.data &&
    typeof data.data === "object"
  ) {
    return extractSources(
      data.data
    );
  }


  return [];
}


// =====================================================
// EXTRACT AGENT WORKFLOW
// =====================================================

function extractAgentWorkflow(data) {
  if (!data) {
    return [];
  }


  if (
    Array.isArray(
      data.agent_workflow
    )
  ) {
    return data.agent_workflow
      .filter(
        (agent) =>
          typeof agent === "string"
      )
      .map(
        (agent) =>
          agent.trim()
      )
      .filter(Boolean);
  }


  if (
    data.data &&
    typeof data.data === "object"
  ) {
    return extractAgentWorkflow(
      data.data
    );
  }


  return [];
}


// =====================================================
// EXTRACT ACTION RESULT
// =====================================================

function extractActionResult(data) {
  if (!data) {
    return null;
  }


  if (
    data.action_result &&
    typeof data.action_result ===
      "object"
  ) {
    return data.action_result;
  }


  if (
    data.data &&
    typeof data.data === "object"
  ) {
    return extractActionResult(
      data.data
    );
  }


  return null;
}


// =====================================================
// GENERATE SUGGESTED FOLLOW-UPS
//
// Frontend-only for now.
//
// Later these can come directly from the
// backend/LLM.
// =====================================================

function generateSuggestedFollowUps(
  question,
  answer,
  sources,
  actionResult
) {

  const normalizedQuestion =
    (question || "").toLowerCase();


  const normalizedAnswer =
    (answer || "").toLowerCase();


  // Gmail action

  if (
    actionResult?.type ===
      "gmail_draft"
  ) {

    return [
      "What should I change in the draft?",
      "Create another email",
      "Show me the document summary again",
    ];

  }


  // Accommodation / booking

  if (
    normalizedQuestion.includes(
      "accommodation"
    ) ||
    normalizedQuestion.includes(
      "booking"
    ) ||
    normalizedAnswer.includes(
      "accommodation"
    ) ||
    normalizedAnswer.includes(
      "booking"
    )
  ) {

    return [
      "What is the total amount?",
      "Who are the guests?",
      "Draft an email with this summary",
    ];

  }


  // Document / Drive questions

  if (
    normalizedQuestion.includes(
      "document"
    ) ||
    normalizedQuestion.includes(
      "google drive"
    ) ||
    normalizedQuestion.includes(
      "drive"
    ) ||
    sources.length > 0
  ) {

    return [
      "Summarize this document",
      "What are the key details?",
      "Draft an email with this information",
    ];

  }


  // Project / research questions

  if (
    normalizedQuestion.includes(
      "project"
    ) ||
    normalizedQuestion.includes(
      "research"
    )
  ) {

    return [
      "Explain this in more detail",
      "What are the key points?",
      "What should I do next?",
    ];

  }


  // Generic follow-ups

  return [
    "Can you explain that in more detail?",
    "What are the key points?",
    "What should I ask next?",
  ];
}


// =====================================================
// CREATE MESSAGE
// =====================================================

function createMessage(
  role,
  content,
  extra = {}
) {

  return {
    id:
      `${Date.now()}-${Math.random()
        .toString(36)
        .substring(2, 9)}`,

    role,

    content,

    createdAt:
      new Date().toISOString(),

    ...extra,
  };
}


// =====================================================
// CONVERSATION API
// =====================================================

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";


async function createOrGetConversation(
  conversationId,
  title
) {

  if (!conversationId) {
    throw new Error(
      "Conversation ID is missing."
    );
  }

  const response = await fetch(
    `${API_BASE}/conversations`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        title: title || "New Chat",
      }),
    }
  );

  const data = await response.json().catch(
    () => ({})
  );

  if (!response.ok) {
    throw new Error(
      data.detail ||
        "Unable to create the conversation."
    );
  }

  return data;
}


async function saveConversationMessage(
  conversationId,
  message
) {

  if (!conversationId) {
    throw new Error(
      "Conversation ID is missing."
    );
  }

  const response = await fetch(
    `${API_BASE}/conversations/${encodeURIComponent(
      conversationId
    )}/messages`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        role: message.role,
        content: message.content,
        sources: message.sources || [],
        agent_workflow:
          message.agentWorkflow ?? null,
        action_result:
          message.actionResult ?? null,
      }),
    }
  );

  const data = await response.json().catch(
    () => ({})
  );

  if (!response.ok) {
    throw new Error(
      data.detail ||
        "Unable to save the conversation message."
    );
  }

  return data;
}


// =====================================================
// CHAT BOX
// =====================================================

function ChatBox({

  // ===================================================
  // CONVERSATION
  // ===================================================

  conversationId,

  conversationMessages = [],

  addConversationMessage,

  setConversationMessages,

}) {

  // ===================================================
  // CURRENT INPUT
  // ===================================================

  const [query, setQuery] =
    useState("");


  // ===================================================
  // CURRENT REQUEST
  // ===================================================

  const [chatLoading, setChatLoading] =
    useState(false);


  // ===================================================
  // ERROR
  // ===================================================

  const [chatError, setChatError] =
    useState("");


  // ===================================================
  // ASK AI
  // ===================================================

  const handleAsk = async (
    providedQuery = null
  ) => {

    const rawQuery =
      providedQuery !== null
        ? providedQuery
        : query;


    const trimmedQuery =
      rawQuery.trim();


    if (
      !trimmedQuery ||
      chatLoading
    ) {
      return;
    }


    console.log(
      "Sending conversation request:",
      {
        conversationId,
        question:
          trimmedQuery,
      }
    );


    // -------------------------------------------------
    // Clear previous error
    // -------------------------------------------------

    setChatError("");

    setChatLoading(true);


    // -------------------------------------------------
    // Create the PostgreSQL conversation if it does not
    // already exist. The backend safely returns the
    // existing conversation when the ID is already known.
    // -------------------------------------------------

    const conversationTitle =
      trimmedQuery.length > 60
        ? `${trimmedQuery.slice(0, 57)}...`
        : trimmedQuery;

    const userMessage =
      createMessage(
        "user",
        trimmedQuery
      );

    // -------------------------------------------------
    // Clear input
    // -------------------------------------------------

    setQuery("");


    try {

      await createOrGetConversation(
        conversationId,
        conversationTitle
      );


      // Save the user's message before running the AI.

      await saveConversationMessage(
        conversationId,
        userMessage
      );


      // Update the UI only after PostgreSQL has accepted
      // the user message.

      if (
        typeof addConversationMessage ===
        "function"
      ) {

        addConversationMessage(
          userMessage
        );

      }


      // ===============================================
      // CALL CURRENT MULTI-AGENT BACKEND
      // ===============================================

      const data =
        await runAgentWorkflow(
          trimmedQuery
        );


      console.log(
        "Multi-agent response:",
        data
      );


      // ===============================================
      // ANSWER
      // ===============================================

      const answer =
        extractChatAnswer(
          data
        );


      if (!answer) {

        console.error(
          "Unexpected multi-agent response:",
          data
        );

        throw new Error(
          "The multi-agent backend responded successfully, but no answer was found."
        );

      }


      // ===============================================
      // SOURCES
      // ===============================================

      const sources =
        extractSources(
          data
        );


      // ===============================================
      // AGENT WORKFLOW
      // ===============================================

      const workflow =
        extractAgentWorkflow(
          data
        );


      // ===============================================
      // GMAIL ACTION
      // ===============================================

      const action =
        extractActionResult(
          data
        );


      console.log(
        "RAG sources:",
        sources
      );


      console.log(
        "Agent workflow:",
        workflow
      );


      console.log(
        "Action result:",
        action
      );


      // ===============================================
      // SUGGESTED FOLLOW-UPS
      // ===============================================

      const suggestions =
        generateSuggestedFollowUps(
          trimmedQuery,
          answer,
          sources,
          action
        );


      // ===============================================
      // ADD AI MESSAGE
      // ===============================================

      const assistantMessage =
        createMessage(
          "assistant",
          answer,
          {
            question:
              trimmedQuery,

            sources,

            agentWorkflow:
              workflow,

            actionResult:
              action,

            suggestedFollowUps:
              suggestions,
          }
        );


      // -------------------------------------------------
      // Persist the AI response in PostgreSQL.
      // -------------------------------------------------

      try {

        await saveConversationMessage(
          conversationId,
          assistantMessage
        );

      } catch (persistenceError) {

        console.error(
          "AI response generated, but PostgreSQL persistence failed:",
          persistenceError
        );

        setChatError(
          `AI response generated, but conversation history could not be saved. ${
            persistenceError?.message || ""
          }`.trim()
        );

      }


      // -------------------------------------------------
      // Add AI message to the visible conversation.
      // -------------------------------------------------

      if (
        typeof addConversationMessage ===
        "function"
      ) {

        addConversationMessage(
          assistantMessage
        );

      }


    } catch (error) {

      console.error(
        "Multi-agent request failed:",
        error
      );


      setChatError(
        error?.message ||
          "Unable to connect to the AI backend."
      );


      // -----------------------------------------------
      // Remove the user message if the request failed.
      //
      // This keeps the conversation clean.
      // -----------------------------------------------

      if (
        typeof setConversationMessages ===
        "function"
      ) {

        setConversationMessages(
          (previousMessages) =>
            previousMessages.filter(
              (message) =>
                message.id !==
                userMessage.id
            )
        );

      }


    } finally {

      setChatLoading(false);

    }

  };


  // ===================================================
  // KEYBOARD
  // ===================================================

  const handleKeyDown = (
    event
  ) => {

    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {

      event.preventDefault();

      handleAsk();

    }

  };


  // ===================================================
  // FOLLOW-UP CLICK
  // ===================================================

  const handleSuggestionClick = (
    suggestion
  ) => {

    if (
      !suggestion ||
      chatLoading
    ) {
      return;
    }


    setQuery(
      suggestion
    );


    // Automatically submit the suggestion.

    handleAsk(
      suggestion
    );

  };


  // ===================================================
  // EMPTY STATE
  // ===================================================

  const hasMessages =
    conversationMessages.length >
    0;


  // ===================================================
  // UI
  // ===================================================

  return (

    <>


      {/* =================================================
          SEARCH BOX
      ================================================= */}

      <div className="search-box">

        <span className="search-icon">
          💡
        </span>


        <input
          type="text"
          placeholder="Ask anything to your AI assistant..."
          value={query}
          disabled={chatLoading}
          onChange={(event) =>
            setQuery(
              event.target.value
            )
          }
          onKeyDown={
            handleKeyDown
          }
        />


        <button
          type="button"
          onClick={() =>
            handleAsk()
          }
          disabled={
            chatLoading ||
            !query.trim()
          }
          aria-label="Ask"
          title="Ask"
        >

          {chatLoading
            ? "..."
            : "→"}

        </button>

      </div>


      {/* =================================================
          CONVERSATION
      ================================================= */}

      {hasMessages && (

        <div
          className="conversation-thread"
          style={{
            marginTop:
              "24px",

            display:
              "flex",

            flexDirection:
              "column",

            gap:
              "20px",
          }}
        >

          {conversationMessages.map(
            (message) => {


              // =========================================
              // USER MESSAGE
              // =========================================

              if (
                message.role ===
                "user"
              ) {

                return (

                  <div
                    key={
                      message.id
                    }
                    style={{
                      display:
                        "flex",

                      justifyContent:
                        "flex-end",

                      width:
                        "100%",
                    }}
                  >

                    <div
                      style={{
                        maxWidth:
                          "78%",

                        padding:
                          "12px 16px",

                        borderRadius:
                          "16px 16px 4px 16px",

                        background:
                          "#6941e8",

                        color:
                          "#ffffff",

                        fontSize:
                          "14px",

                        lineHeight:
                          "1.55",

                        boxShadow:
                          "0 6px 18px rgba(105,65,232,0.14)",
                      }}
                    >

                      {message.content}

                    </div>

                  </div>

                );

              }


              // =========================================
              // ASSISTANT MESSAGE
              // =========================================

              if (
                message.role ===
                "assistant"
              ) {

                return (

                  <div
                    key={
                      message.id
                    }
                  >

                    <AIAnswer

                      answer={
                        message.content
                      }

                      question={
                        message.question
                      }

                      sources={
                        message.sources ||
                        []
                      }

                    />


                    {/* =================================
                        AGENT WORKFLOW
                    ================================= */}

                    {message.agentWorkflow &&
                      message.agentWorkflow.length >
                        0 && (

                      <div
                        style={{
                          marginTop:
                            "10px",

                          padding:
                            "10px 14px",

                          border:
                            "1px solid #ebe6f3",

                          borderRadius:
                            "10px",

                          background:
                            "#fcfbfe",

                          fontSize:
                            "11px",

                          color:
                            "#746c82",
                        }}
                      >

                        <strong
                          style={{
                            color:
                              "#51485f",
                          }}
                        >
                          Agent workflow:
                        </strong>{" "}

                        {message.agentWorkflow.join(
                          " → "
                        )}

                      </div>

                    )}


                    {/* =================================
                        GMAIL DRAFT
                    ================================= */}

                    {message.actionResult?.type ===
                      "gmail_draft" &&
                      message.actionResult?.status ===
                        "created" && (

                      <div
                        className="chat-response"
                        style={{
                          marginTop:
                            "14px",
                        }}
                      >

                        <div className="chat-response-label">
                          GMAIL
                        </div>


                        <div className="chat-response-text">

                          <div
                            style={{
                              fontWeight:
                                "700",

                              marginBottom:
                                "8px",
                            }}
                          >
                            Draft saved successfully
                          </div>


                          <div
                            style={{
                              display:
                                "grid",

                              gap:
                                "5px",

                              fontSize:
                                "14px",
                            }}
                          >

                            <div>

                              <strong>
                                To:
                              </strong>{" "}

                              {message.actionResult.recipient ||
                                "Recipient"}

                            </div>


                            {message.actionResult.subject && (

                              <div>

                                <strong>
                                  Subject:
                                </strong>{" "}

                                {
                                  message.actionResult.subject
                                }

                              </div>

                            )}

                          </div>


                          <div
                            style={{
                              marginTop:
                                "10px",

                              fontSize:
                                "13px",

                              opacity:
                                0.78,
                            }}
                          >

                            Review the draft in Gmail before sending.

                          </div>

                        </div>

                      </div>

                    )}


                    {/* =================================
                        SUGGESTED FOLLOW-UPS
                    ================================= */}

                    {message.suggestedFollowUps &&
                      message.suggestedFollowUps.length >
                        0 && (

                      <div
                        style={{
                          marginTop:
                            "14px",
                        }}
                      >

                        <div
                          style={{
                            marginBottom:
                              "8px",

                            fontSize:
                              "11px",

                            fontWeight:
                              "750",

                            color:
                              "#81788f",

                            textTransform:
                              "uppercase",

                            letterSpacing:
                              "0.04em",
                          }}
                        >

                          Suggested follow-ups

                        </div>


                        <div
                          style={{
                            display:
                              "flex",

                            flexWrap:
                              "wrap",

                            gap:
                              "8px",
                          }}
                        >

                          {message.suggestedFollowUps.map(
                            (
                              suggestion,
                              index
                            ) => (

                              <button
                                key={`${message.id}-suggestion-${index}`}
                                type="button"
                                disabled={
                                  chatLoading
                                }
                                onClick={() =>
                                  handleSuggestionClick(
                                    suggestion
                                  )
                                }
                                style={{
                                  border:
                                    "1px solid #ded6ed",

                                  borderRadius:
                                    "20px",

                                  padding:
                                    "8px 12px",

                                  background:
                                    "#ffffff",

                                  color:
                                    "#5e4a86",

                                  fontSize:
                                    "12px",

                                  fontWeight:
                                    "600",

                                  cursor:
                                    chatLoading
                                      ? "default"
                                      : "pointer",

                                  transition:
                                    "all 0.2s ease",
                                }}
                              >

                                {suggestion}

                              </button>

                            )
                          )}

                        </div>

                      </div>

                    )}

                  </div>

                );

              }


              return null;

            }
          )}

        </div>

      )}


      {/* =================================================
          LOADING
      ================================================= */}

      {chatLoading && (

        <div
          className="chat-response"
          style={{
            marginTop:
              "20px",
          }}
        >

          <div className="chat-response-label">

            ENTERPRISE AI

          </div>


          <div
            className="chat-response-text"
            style={{
              display:
                "flex",

              alignItems:
                "center",

              gap:
                "12px",
            }}
          >

            <div className="loading-spinner" />

            AI agents are analyzing your workspace...

          </div>

        </div>

      )}


      {/* =================================================
          ERROR
      ================================================= */}

      {!chatLoading &&
        chatError && (

          <div
            className="chat-response chat-error"
            style={{
              marginTop:
                "16px",
            }}
          >

            <div className="chat-response-label">

              ERROR

            </div>


            <div className="chat-response-text">

              {chatError}

            </div>


            <button
              type="button"
              onClick={() =>
                setChatError("")
              }
              style={{
                marginTop:
                  "14px",

                border:
                  "1px solid #e0d8ef",

                borderRadius:
                  "9px",

                padding:
                  "8px 14px",

                background:
                  "#ffffff",

                color:
                  "#6941e8",

                fontWeight:
                  "600",

                cursor:
                  "pointer",
              }}
            >

              Dismiss

            </button>

          </div>

        )}

    </>

  );

}


export default ChatBox;