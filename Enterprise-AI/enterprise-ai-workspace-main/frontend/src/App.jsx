import {
  useEffect,
  useRef,
  useState,
} from "react";

import "./App.css";

import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import Footer from "./components/Footer";

import Workspace from "./pages/Workspace";
import Documents from "./pages/Documents";
import Knowledge from "./pages/Knowledge";
import Agents from "./pages/Agents";
import Tasks from "./pages/Tasks";

import {
  checkHealth,
  createConversation,
  saveConversationMessage,
} from "./services/api";


// =====================================================
// CREATE CONVERSATION ID
// =====================================================

function createConversationId() {

  return (
    Date.now().toString(36) +
    "-" +
    Math.random()
      .toString(36)
      .substring(2, 9)
  );
}


// =====================================================
// MAP DATABASE MESSAGE
// =====================================================

function mapDatabaseMessage(message) {

  return {

    id:
      String(message.id),

    conversationId:
      message.conversation_id,

    role:
      message.role,

    content:
      message.content,

    sources:
      message.sources || [],

    agentWorkflow:
      message.agent_workflow,

    actionResult:
      message.action_result,

    createdAt:
      message.created_at,

  };

}


// =====================================================
// APP
// =====================================================

function App() {

  // ===================================================
  // NAVIGATION
  // ===================================================

  const [activePage, setActivePage] =
    useState("Workspace");

  const [sidebarOpen, setSidebarOpen] =
    useState(false);


  // ===================================================
  // BACKEND STATUS
  // ===================================================

  const [apiOnline, setApiOnline] =
    useState(false);


  // ===================================================
  // CHAT INPUT STATE
  // ===================================================

  const [query, setQuery] =
    useState("");

  const [chatQuestion, setChatQuestion] =
    useState("");

  const [chatAnswer, setChatAnswer] =
    useState("");

  const [chatSources, setChatSources] =
    useState([]);

  const [chatLoading, setChatLoading] =
    useState(false);

  const [chatError, setChatError] =
    useState("");


  // ===================================================
  // CURRENT CONVERSATION
  // ===================================================

  const [conversationId, setConversationId] =
    useState(() =>
      createConversationId()
    );

  const [conversationMessages, setConversationMessages] =
    useState([]);


  // ===================================================
  // SIDEBAR REFRESH
  // ===================================================

  const [conversationRefreshKey, setConversationRefreshKey] =
    useState(0);


  // ===================================================
  // DATABASE CONVERSATION TRACKING
  // ===================================================

  const persistedConversationIds =
    useRef(new Set());

  const conversationCreationPromises =
    useRef(new Map());


  // ===================================================
  // BACKEND HEALTH CHECK
  // ===================================================

  useEffect(() => {

    checkBackend();

  }, []);


  const checkBackend = async () => {

    try {

      await checkHealth();

      setApiOnline(true);

    } catch (error) {

      console.error(
        "Backend health check failed:",
        error
      );

      setApiOnline(false);

    }

  };


  // ===================================================
  // NAVIGATION
  // ===================================================

  const handleNavigation = (
    page
  ) => {

    setActivePage(page);

    setSidebarOpen(false);

  };


  // ===================================================
  // ENSURE CONVERSATION EXISTS
  // ===================================================

  const ensureConversationExists = async (
    id,
    title
  ) => {

    if (
      persistedConversationIds.current.has(
        id
      )
    ) {

      return;

    }


    const existingPromise =
      conversationCreationPromises.current.get(
        id
      );


    if (existingPromise) {

      await existingPromise;

      return;

    }


    const creationPromise =
      createConversation(
        id,
        title || "New Chat"
      )
        .then(() => {

          persistedConversationIds.current.add(
            id
          );

          conversationCreationPromises.current.delete(
            id
          );

          setConversationRefreshKey(
            (value) =>
              value + 1
          );

        })
        .catch((error) => {

          conversationCreationPromises.current.delete(
            id
          );

          throw error;

        });


    conversationCreationPromises.current.set(
      id,
      creationPromise
    );


    await creationPromise;

  };


  // ===================================================
  // START NEW CONVERSATION
  // ===================================================

  const startNewConversation = () => {

    const newConversationId =
      createConversationId();


    console.log(
      "Starting new conversation:",
      newConversationId
    );


    setConversationId(
      newConversationId
    );


    setConversationMessages([]);


    setQuery("");

    setChatQuestion("");

    setChatAnswer("");

    setChatSources([]);

    setChatLoading(false);

    setChatError("");


    setActivePage(
      "Workspace"
    );


    setSidebarOpen(false);

  };


  // ===================================================
  // ADD MESSAGE
  // ===================================================

  const addConversationMessage = async (
    message
  ) => {

    const localMessageId =
      message.id ||
      `${Date.now()}-${Math.random()
        .toString(36)
        .substring(2, 8)}`;


    const localMessage = {

      ...message,

      id:
        localMessageId,

      conversationId,

      createdAt:
        message.createdAt ||
        new Date().toISOString(),

    };


    // =================================================
    // SHOW MESSAGE IMMEDIATELY
    // =================================================

    setConversationMessages(
      (previousMessages) => [
        ...previousMessages,
        localMessage,
      ]
    );


    // =================================================
    // SAVE TO POSTGRESQL
    // =================================================

    try {

      const title =
        message.role === "user"
          ? message.content
              .trim()
              .replace(
                /\s+/g,
                " "
              )
              .slice(
                0,
                70
              )
          : "New Chat";


      await ensureConversationExists(
        conversationId,
        title || "New Chat"
      );


      const savedMessage =
        await saveConversationMessage(
          conversationId,
          message
        );


      const databaseMessage =
        mapDatabaseMessage(
          savedMessage
        );


      setConversationMessages(
        (previousMessages) =>
          previousMessages.map(
            (item) =>
              item.id ===
              localMessageId
                ? {
                    ...item,
                    ...databaseMessage,
                  }
                : item
          )
      );


      setConversationRefreshKey(
        (value) =>
          value + 1
      );


    } catch (error) {

      console.error(
        "Failed to persist conversation message:",
        error
      );

      // Keep the local message visible.

    }

  };


  // ===================================================
  // UPDATE CURRENT CONVERSATION
  // ===================================================

  const updateConversationMessages = (
    updater
  ) => {

    setConversationMessages(
      updater
    );

  };


  // ===================================================
  // LOAD EXISTING CONVERSATION
  // ===================================================

  const handleSelectConversation = (
    conversation
  ) => {

    if (!conversation?.id) {
      return;
    }


    persistedConversationIds.current.add(
      conversation.id
    );


    const messages =
      (
        conversation.messages ||
        []
      ).map(
        mapDatabaseMessage
      );


    setConversationId(
      conversation.id
    );


    setConversationMessages(
      messages
    );


    setQuery("");

    setChatQuestion("");

    setChatAnswer("");

    setChatSources([]);

    setChatLoading(false);

    setChatError("");


    setActivePage(
      "Workspace"
    );


    setSidebarOpen(false);

  };


  // ===================================================
  // PAGE VISIBILITY
  // ===================================================

  const pageStyle = (
    page
  ) => ({

    display:
      activePage === page
        ? "block"
        : "none",

  });


  // ===================================================
  // APP SHELL
  // =====================================================

  return (

    <div className="app">


      {/* =================================================
          SIDEBAR
      ================================================= */}

      <Sidebar

        sidebarOpen={
          sidebarOpen
        }

        setSidebarOpen={
          setSidebarOpen
        }

        apiOnline={
          apiOnline
        }

        conversationId={
          conversationId
        }

        onNewChat={
          startNewConversation
        }

        onSelectConversation={
          handleSelectConversation
        }

        conversationRefreshKey={
          conversationRefreshKey
        }

      />


      {/* =================================================
          MAIN
      ================================================= */}

      <main className="main">


        {/* =================================================
            HEADER
        ================================================= */}

        <Header

          activePage={
            activePage
          }

          setSidebarOpen={
            setSidebarOpen
          }

          onNavigate={
            handleNavigation
          }

        />


        {/* =================================================
            PAGE CONTENT
        ================================================= */}

        <div className="page-container">


          {/* =================================================
              WORKSPACE
          ================================================= */}

          <div
            style={
              pageStyle(
                "Workspace"
              )
            }
          >

            <Workspace

              apiOnline={
                apiOnline
              }

              setApiOnline={
                setApiOnline
              }


              query={
                query
              }

              setQuery={
                setQuery
              }


              chatQuestion={
                chatQuestion
              }

              setChatQuestion={
                setChatQuestion
              }


              chatAnswer={
                chatAnswer
              }

              setChatAnswer={
                setChatAnswer
              }


              chatSources={
                chatSources
              }

              setChatSources={
                setChatSources
              }


              chatLoading={
                chatLoading
              }

              setChatLoading={
                setChatLoading
              }


              chatError={
                chatError
              }

              setChatError={
                setChatError
              }


              conversationId={
                conversationId
              }

              conversationMessages={
                conversationMessages
              }

              addConversationMessage={
                addConversationMessage
              }

              setConversationMessages={
                updateConversationMessages
              }

            />

          </div>


          {/* =================================================
              DOCUMENTS
          ================================================= */}

          <div
            style={
              pageStyle(
                "Documents"
              )
            }
          >

            <Documents />

          </div>


          {/* =================================================
              KNOWLEDGE
          ================================================= */}

          <div
            style={
              pageStyle(
                "Knowledge"
              )
            }
          >

            <Knowledge />

          </div>


          {/* =================================================
              AGENTS
          ================================================= */}

          <div
            style={
              pageStyle(
                "Agents"
              )
            }
          >

            <Agents />

          </div>


          {/* =================================================
              TASKS
          ================================================= */}

          <div
            style={
              pageStyle(
                "Tasks"
              )
            }
          >

            <Tasks />

          </div>


        </div>


        {/* =================================================
            GLOBAL FOOTER
        ================================================= */}

        <Footer />


      </main>

    </div>

  );
}


export default App;