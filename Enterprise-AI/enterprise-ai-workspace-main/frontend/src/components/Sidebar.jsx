import "./Sidebar.css";

import {
  useEffect,
  useState,
} from "react";

import {
  getConversations,
  getConversation,
  deleteConversation,
} from "../services/api";


function Sidebar({
  sidebarOpen,
  setSidebarOpen,
  apiOnline,
  conversationId,
  onNewChat,
  onSelectConversation,
  conversationRefreshKey,
}) {

  // =================================================
  // SETTINGS
  // =================================================

  const [settingsOpen, setSettingsOpen] =
    useState(false);


  // =================================================
  // CONVERSATIONS
  // =================================================

  const [conversations, setConversations] =
    useState([]);

  const [conversationsLoading, setConversationsLoading] =
    useState(false);

  const [conversationLoadingId, setConversationLoadingId] =
    useState(null);


  // =================================================
  // HOVER & DELETE STATES
  // =================================================

  const [
    hoveredConversationId,
    setHoveredConversationId,
  ] = useState(null);

  const [
    deletingConversationId,
    setDeletingConversationId,
  ] = useState(null);


  // =================================================
  // LOAD CONVERSATIONS
  // =================================================

  const loadConversations = async () => {

    try {

      setConversationsLoading(true);

      const response =
        await getConversations(50);

      setConversations(
        response?.conversations || []
      );

    } catch (error) {

      console.error(
        "Failed to load conversations:",
        error
      );

    } finally {

      setConversationsLoading(false);

    }

  };


  useEffect(() => {

    loadConversations();

  }, [
    conversationRefreshKey,
  ]);


  // =================================================
  // SELECT CONVERSATION
  // =================================================

  const handleConversationClick = async (
    selectedConversation
  ) => {

    if (
      !selectedConversation?.id
    ) {
      return;
    }


    // Already selected

    if (
      selectedConversation.id ===
      conversationId
    ) {

      setSidebarOpen(false);

      return;

    }


    try {

      setConversationLoadingId(
        selectedConversation.id
      );


      const conversation =
        await getConversation(
          selectedConversation.id
        );


      if (
        onSelectConversation
      ) {

        onSelectConversation(
          conversation
        );

      }


      setSidebarOpen(false);

    } catch (error) {

      console.error(
        "Failed to load conversation:",
        error
      );

    } finally {

      setConversationLoadingId(
        null
      );

    }

  };


  // =================================================
  // DELETE CONVERSATION
  // =================================================

  const handleDeleteConversation = async (
    event,
    selectedConversation
  ) => {

    event.stopPropagation();


    if (
      !selectedConversation?.id ||
      deletingConversationId
    ) {
      return;
    }


    const conversationTitle =
      selectedConversation.title ||
      "this chat";


    const confirmed =
      window.confirm(
        `Delete "${conversationTitle}"?`
      );


    if (!confirmed) {
      return;
    }


    try {

      setDeletingConversationId(
        selectedConversation.id
      );


      await deleteConversation(
        selectedConversation.id
      );


      // Remove from UI immediately

      setConversations(
        (previous) =>
          previous.filter(
            (conversation) =>
              conversation.id !==
              selectedConversation.id
          )
      );


      // If current conversation was deleted,
      // create a fresh chat.

      if (
        selectedConversation.id ===
        conversationId
      ) {

        if (onNewChat) {
          onNewChat();
        }

      }

    } catch (error) {

      console.error(
        "Failed to delete conversation:",
        error
      );


      window.alert(
        error?.message ||
        "Unable to delete this conversation."
      );

    } finally {

      setDeletingConversationId(
        null
      );

      setHoveredConversationId(
        null
      );

    }

  };


  // =================================================
  // DATE FORMATTER
  // =================================================

  const formatConversationDate = (
    value
  ) => {

    if (!value) {
      return "";
    }


    const date =
      new Date(value);


    if (
      Number.isNaN(
        date.getTime()
      )
    ) {
      return "";
    }


    const now =
      new Date();


    const isToday =
      date.toDateString() ===
      now.toDateString();


    if (isToday) {

      return date.toLocaleTimeString(
        [],
        {
          hour: "numeric",
          minute: "2-digit",
        }
      );

    }


    return date.toLocaleDateString(
      [],
      {
        month: "short",
        day: "numeric",
      }
    );

  };


  // =================================================
  // NEW CHAT
  // =================================================

  const handleNewChat = () => {

    if (onNewChat) {
      onNewChat();
    }

    setSidebarOpen(false);

  };


  // =================================================
  // RENDER
  // =================================================

  return (
    <>

      {/* =================================================
          MOBILE OVERLAY
      ================================================= */}

      {sidebarOpen && (

        <div
          className="sidebar-overlay"
          onClick={() =>
            setSidebarOpen(false)
          }
        />

      )}


      {/* =================================================
          SIDEBAR
      ================================================= */}

      <aside
        className={`sidebar ${
          sidebarOpen
            ? "sidebar-open"
            : ""
        }`}
      >

        {/* =================================================
            SIDEBAR HEADER
        ================================================= */}

        <div className="sidebar-top">

          <div className="brand">

            <div className="brand-logo">
              AI
            </div>

            <div className="brand-text">

              <strong>
                Enterprise AI
              </strong>

              <span>
                Workspace
              </span>

            </div>

          </div>


          {/* Mobile close */}

          <button
            type="button"
            className="mobile-close"
            onClick={() =>
              setSidebarOpen(false)
            }
            aria-label="Close menu"
          >
            ×
          </button>

        </div>


        {/* =================================================
            RECENT CHATS
        ================================================= */}

        <div className="recent-chats">

          {/* =================================================
              RECENT CHAT HEADER
          ================================================= */}

          <div className="recent-chats-header">

            <span className="recent-chats-label">
              RECENT CHATS
            </span>


            <button
              type="button"
              className="new-chat-button"
              onClick={handleNewChat}
            >
              + New Chat
            </button>

          </div>


          {/* =================================================
              CHAT LIST

              This is the ONLY scrollable area.
              It uses all available vertical space.
          ================================================= */}

          <div className="recent-chats-list">

            {/* Loading */}

            {conversationsLoading &&
              conversations.length === 0 && (

                <div className="recent-chat-message">
                  Loading chats...
                </div>

              )}


            {/* Empty */}

            {!conversationsLoading &&
              conversations.length === 0 && (

                <div className="recent-chat-message">
                  Your conversations
                  will appear here.
                </div>

              )}


            {/* =================================================
                ALL CONVERSATIONS

                IMPORTANT:
                No slice(0, 8).

                Every conversation returned by the
                backend is available in the scroll area.
            ================================================= */}

            {conversations.map(
              (conversation) => {

                const selected =
                  conversation.id ===
                  conversationId;

                const loading =
                  conversationLoadingId ===
                  conversation.id;

                const deleting =
                  deletingConversationId ===
                  conversation.id;

                const hovered =
                  hoveredConversationId ===
                  conversation.id;


                return (

                  <div
                    key={
                      conversation.id
                    }

                    className={`conversation-item ${
                      selected
                        ? "selected"
                        : ""
                    }`}

                    onMouseEnter={() =>
                      setHoveredConversationId(
                        conversation.id
                      )
                    }

                    onMouseLeave={() =>
                      setHoveredConversationId(
                        null
                      )
                    }
                  >

                    {/* =================================================
                        CONVERSATION BUTTON
                    ================================================= */}

                    <button
                      type="button"
                      className="conversation-button"

                      onClick={() =>
                        handleConversationClick(
                          conversation
                        )
                      }

                      disabled={
                        loading ||
                        deleting
                      }
                    >

                      {/* Conversation dot */}

                      <span className="conversation-dot" />


                      {/* =================================================
                          TITLE

                          title attribute means hovering over a
                          long title shows the complete title.
                      ================================================= */}

                      <span
                        className="conversation-title"

                        title={
                          conversation.title ||
                          "New Chat"
                        }
                      >

                        {loading
                          ? "Loading..."
                          : deleting
                          ? "Deleting..."
                          : conversation.title ||
                            "New Chat"}

                      </span>


                      {/* Date */}

                      {!loading &&
                        !deleting && (

                          <span
                            className="conversation-date"
                          >

                            {formatConversationDate(
                              conversation.updated_at
                            )}

                          </span>

                        )}

                    </button>


                    {/* =================================================
                        DELETE BUTTON
                    ================================================= */}

                    <button
                      type="button"

                      className={`conversation-delete ${
                        hovered || deleting
                          ? "visible"
                          : ""
                      }`}

                      aria-label={`Delete ${
                        conversation.title ||
                        "conversation"
                      }`}

                      title="Delete chat"

                      disabled={
                        loading ||
                        deleting
                      }

                      onClick={(event) =>
                        handleDeleteConversation(
                          event,
                          conversation
                        )
                      }
                    >

                      {deleting
                        ? "…"
                        : "🗑"}

                    </button>

                  </div>

                );

              }
            )}

          </div>

        </div>


        {/* =================================================
            SIDEBAR UTILITIES

            KEEPING:
            - API Online
            - Theme
            - Help
            - Settings
        ================================================= */}

        <div className="sidebar-bottom">

          {/* =================================================
              API STATUS
          ================================================= */}

          <div className="sidebar-utility-status">

            <span
              className={`sidebar-status-dot ${
                apiOnline
                  ? "online"
                  : ""
              }`}
            />

            <span>
              {apiOnline
                ? "API Online"
                : "API Offline"}
            </span>

          </div>


          {/* =================================================
              THEME
          ================================================= */}

          <button
            type="button"
            className="sidebar-utility-button"
            title="Theme"
          >

            <span className="sidebar-utility-icon">
              ◇
            </span>

            <span>
              Theme
            </span>

          </button>


          {/* =================================================
              HELP
          ================================================= */}

          <button
            type="button"
            className="sidebar-utility-button"
            title="Help"
          >

            <span className="sidebar-utility-icon">
              ?
            </span>

            <span>
              Help
            </span>

          </button>


          {/* =================================================
              SETTINGS
          ================================================= */}

          <button
            type="button"
            className="settings-button"
            onClick={() =>
              setSettingsOpen(true)
            }
          >

            <span>
              ⚙
            </span>

            <span>
              Settings
            </span>

          </button>

        </div>

      </aside>


      {/* =================================================
          SETTINGS MODAL
      ================================================= */}

      {settingsOpen && (

        <div
          className="settings-modal-overlay"

          onClick={() =>
            setSettingsOpen(false)
          }
        >

          <div
            className="settings-modal"

            onClick={(event) =>
              event.stopPropagation()
            }
          >

            {/* =================================================
                MODAL HEADER
            ================================================= */}

            <div className="settings-modal-header">

              <div>

                <div className="settings-modal-eyebrow">

                  <span>
                    ⚙
                  </span>

                  WORKSPACE SETTINGS

                </div>


                <h2>
                  Settings
                </h2>


                <p>
                  Manage your Enterprise AI workspace.
                </p>

              </div>


              <button
                type="button"

                className="settings-close-button"

                onClick={() =>
                  setSettingsOpen(false)
                }

                aria-label="Close settings"
              >
                ×
              </button>

            </div>


            {/* =================================================
                SETTINGS CONTENT
            ================================================= */}

            <div className="settings-modal-content">

              {/* =================================================
                  WORKSPACE
              ================================================= */}

              <div className="settings-section">

                <div className="settings-section-title">
                  WORKSPACE
                </div>


                <div className="settings-workspace-card">

                  <div className="settings-workspace-name">
                    Enterprise AI Workspace
                  </div>

                  <div className="settings-workspace-description">
                    Current workspace
                  </div>

                </div>

              </div>


              {/* =================================================
                  AI CONFIGURATION
              ================================================= */}

              <div className="settings-section">

                <div className="settings-section-title">
                  AI CONFIGURATION
                </div>


                <div className="settings-rows">

                  <SettingRow
                    label="AI Model"
                    value="Connected"
                    active={true}
                  />


                  <SettingRow
                    label="RAG Knowledge Base"
                    value="Active"
                    active={true}
                  />

                </div>

              </div>


              {/* =================================================
                  INTEGRATIONS
              ================================================= */}

              <div className="settings-section">

                <div className="settings-section-title">
                  INTEGRATIONS
                </div>


                <div className="settings-rows">

                  <SettingRow
                    label="Google Drive MCP"
                    value="Connected"
                    active={true}
                  />


                  <SettingRow
                    label="Gmail MCP"
                    value="Connected"
                    active={true}
                  />


                  <SettingRow
                    label="Google Calendar MCP"
                    value="Planned"
                    active={false}
                    planned={true}
                  />

                </div>

              </div>


              {/* =================================================
                  APPLICATION
              ================================================= */}

              <div className="settings-section">

                <div className="settings-section-title">
                  APPLICATION
                </div>


                <SettingRow
                  label="Version"
                  value="Prototype v1.0"
                  active={false}
                />

              </div>

            </div>


            {/* =================================================
                MODAL FOOTER
            ================================================= */}

            <div className="settings-modal-footer">

              <button
                type="button"
                className="settings-modal-close"
                onClick={() =>
                  setSettingsOpen(false)
                }
              >
                Close
              </button>

            </div>

          </div>

        </div>

      )}

    </>
  );
}


// =====================================================
// SETTINGS ROW
// =====================================================

function SettingRow({
  label,
  value,
  active,
  planned,
}) {

  return (

    <div className="settings-row">

      <span className="settings-row-label">
        {label}
      </span>


      <span
        className={`settings-row-value ${
          planned
            ? "planned"
            : active
            ? "active"
            : "inactive"
        }`}
      >

        {!planned && (

          <span className="settings-row-dot" />

        )}

        {value}

      </span>

    </div>

  );
}


export default Sidebar;