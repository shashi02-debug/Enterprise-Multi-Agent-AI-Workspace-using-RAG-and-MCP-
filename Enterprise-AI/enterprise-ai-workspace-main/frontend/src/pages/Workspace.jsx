import "./Workspace.css";

import ChatBox from "../components/chat/ChatBox";


function Workspace({

  // ===================================================
  // BACKEND
  // ===================================================

  apiOnline,

  setApiOnline,


  // ===================================================
  // CURRENT INPUT
  // ===================================================

  query,

  setQuery,


  // ===================================================
  // CURRENT CHAT
  // ===================================================

  chatQuestion,

  setChatQuestion,

  chatAnswer,

  setChatAnswer,

  chatSources,

  setChatSources,

  chatLoading,

  setChatLoading,

  chatError,

  setChatError,


  // ===================================================
  // CONVERSATION
  // ===================================================

  conversationId,

  conversationMessages,

  addConversationMessage,

  setConversationMessages,

}) {

  return (

    <section className="workspace-page">

      {/* =================================================
          HERO
      ================================================= */}

      <section className="hero">

        {/* =================================================
            HERO BADGE
        ================================================= */}

        <div className="hero-badge">

          <span>
            ✦
          </span>

          AI WORKSPACE

        </div>


        {/* =================================================
            HERO TITLE
        ================================================= */}

        <h2>

          Work smarter with

          <br />

          <span>
            Enterprise AI.
          </span>

        </h2>


        {/* =================================================
            HERO DESCRIPTION
        ================================================= */}

        <p>

          Bring your documents, knowledge and
          workflows together

          <br className="desktop-only" />

          in one intelligent workspace.

        </p>


        {/* =================================================
            CHAT
        ================================================= */}

        <ChatBox

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
            setConversationMessages
          }

        />

      </section>

    </section>

  );
}


export default Workspace;