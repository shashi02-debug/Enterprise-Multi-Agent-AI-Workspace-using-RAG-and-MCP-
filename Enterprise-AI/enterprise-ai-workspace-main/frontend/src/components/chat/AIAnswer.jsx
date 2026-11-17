import "./AIAnswer.css";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function AIAnswer({ answer, question, sources = [] }) {
  if (!answer) {
    return null;
  }

  return (
    <div className="chat-answer">
      {/* ================================
          ANSWER HEADER
      ================================= */}
      <div className="chat-answer-header">
        <div className="answer-brand">
          <div className="answer-icon">
            ✦
          </div>

          <div className="answer-title">
            <strong>Enterprise AI</strong>
            <span>Workspace Assistant</span>
          </div>
        </div>

        <div className="answer-status">
          <span className="answer-status-dot" />
          AI Response
        </div>
      </div>

      <div className="chat-answer-divider" />

      {/* ================================
          USER QUESTION
      ================================= */}
      {question && (
        <div className="chat-answer-question">
          <span className="chat-answer-question-label">
            You asked
          </span>

          <p className="chat-answer-question-text">
            {question}
          </p>
        </div>
      )}

      {/* ================================
          ANSWER CONTENT
      ================================= */}
      <div className="chat-answer-content">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ children }) => (
              <h1>{children}</h1>
            ),

            h2: ({ children }) => (
              <h2>{children}</h2>
            ),

            h3: ({ children }) => (
              <h3>{children}</h3>
            ),

            p: ({ children }) => (
              <p>{children}</p>
            ),

            ul: ({ children }) => (
              <ul>{children}</ul>
            ),

            ol: ({ children }) => (
              <ol>{children}</ol>
            ),

            li: ({ children }) => (
              <li>{children}</li>
            ),

            strong: ({ children }) => (
              <strong>{children}</strong>
            ),

            blockquote: ({ children }) => (
              <blockquote>
                {children}
              </blockquote>
            ),

            /* ================================
               TABLE
               Prevents column/text overlap
            ================================= */
            table: ({ children }) => (
              <div
                className="markdown-table-wrapper"
                style={{
                  width: "100%",
                  maxWidth: "100%",
                  overflowX: "auto",
                  overflowY: "hidden",
                  margin: "20px 0",
                  WebkitOverflowScrolling: "touch",
                }}
              >
                <table
                  style={{
                    width: "max-content",
                    minWidth: "100%",
                    maxWidth: "none",
                    tableLayout: "auto",
                  }}
                >
                  {children}
                </table>
              </div>
            ),

            th: ({ children }) => (
              <th
                style={{
                  verticalAlign: "top",
                  whiteSpace: "normal",
                  overflowWrap: "anywhere",
                  wordBreak: "normal",
                }}
              >
                {children}
              </th>
            ),

            td: ({ children }) => (
              <td
                style={{
                  verticalAlign: "top",
                  whiteSpace: "normal",
                  overflowWrap: "anywhere",
                  wordBreak: "normal",
                }}
              >
                {children}
              </td>
            ),

            /* ================================
               CODE
            ================================= */
            code({
              inline,
              className,
              children,
              ...props
            }) {
              return inline ? (
                <code
                  className="inline-code"
                  {...props}
                >
                  {children}
                </code>
              ) : (
                <pre className="markdown-code-block">
                  <code
                    className={className}
                    {...props}
                  >
                    {children}
                  </code>
                </pre>
              );
            },
          }}
        >
          {answer}
        </ReactMarkdown>
      </div>

      {/* ================================
          SOURCES
      ================================= */}
      {sources.length > 0 && (
        <>
          <div className="chat-answer-divider" />

          <div className="answer-sources">
            <div className="sources-heading">
              <div className="sources-title">
                <span className="sources-icon">
                  📚
                </span>

                <strong>
                  Sources
                </strong>
              </div>

              <span className="sources-count">
                {sources.length}{" "}
                {sources.length === 1
                  ? "document"
                  : "documents"}
              </span>
            </div>

            <div className="sources-list">
              {sources.map(
                (source, index) => (
                  <div
                    className="source-item"
                    key={`${source}-${index}`}
                  >
                    <div className="source-file-icon">
                      📄
                    </div>

                    <div className="source-details">
                      <strong
                        title={source}
                      >
                        {source}
                      </strong>

                      <span>
                        Retrieved from
                        knowledge base
                      </span>
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
        </>
      )}

      {/* ================================
          FOOTER
      ================================= */}
      <div className="chat-answer-footer">
        <span>
          ✦ Generated by Enterprise AI
        </span>

        {sources.length > 0 && (
          <span>
            RAG grounded response
          </span>
        )}
      </div>
    </div>
  );
}

export default AIAnswer;