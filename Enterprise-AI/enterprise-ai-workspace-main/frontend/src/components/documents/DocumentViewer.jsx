import { useEffect, useState } from "react";
import { getDocumentContent } from "../../services/api";
import DocumentContent from "./DocumentContent";

function DocumentViewer({
  document,
  onClose,
}) {
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!document) {
      return;
    }

    const loadContent = async () => {
      setLoading(true);
      setError("");
      setContent(null);

      try {
        const data =
          await getDocumentContent(
            document.filename
          );

        setContent(data);
      } catch (requestError) {
        console.error(
          "Document viewer error:",
          requestError
        );

        setError(
          requestError?.message ||
            "Unable to read this document."
        );
      } finally {
        setLoading(false);
      }
    };

    loadContent();
  }, [document]);

  if (!document) {
    return null;
  }

  return (
    <div
      className="document-modal-overlay"
      onClick={(event) => {
        if (
          event.target ===
          event.currentTarget
        ) {
          onClose();
        }
      }}
    >
      <div className="document-modal">
        <div className="document-modal-header">
          <div>
            <span className="modal-label">
              DOCUMENT VIEWER
            </span>

            <h2 title={document.filename}>
              {document.filename}
            </h2>
          </div>

          <button
            className="modal-close"
            onClick={onClose}
            aria-label="Close document"
          >
            ×
          </button>
        </div>

        <div className="document-modal-body">
          {loading && (
            <div className="viewer-loading">
              <div className="loading-spinner" />
              <p>Reading document...</p>
            </div>
          )}

          {!loading && error && (
            <div className="viewer-error">
              <div className="empty-icon">
                !
              </div>

              <h3>
                Unable to read document
              </h3>

              <p>{error}</p>
            </div>
          )}

          {!loading &&
            !error &&
            content && (
              <DocumentContent
                content={content}
                document={document}
              />
            )}
        </div>
      </div>
    </div>
  );
}

export default DocumentViewer;