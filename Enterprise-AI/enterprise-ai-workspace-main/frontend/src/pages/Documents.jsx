import "./Documents.css";

import { useEffect, useState } from "react";
import {
  deleteDocument,
  getDocuments,
} from "../services/api";

import DocumentUpload from "../components/documents/DocumentUpload";
import DocumentList from "../components/documents/DocumentList";
import DocumentViewer from "../components/documents/DocumentViewer";

function Documents() {
  const [documents, setDocuments] =
    useState([]);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [selectedDocument, setSelectedDocument] =
    useState(null);

  const [actionMessage, setActionMessage] =
    useState("");

  const loadDocuments = async () => {
    setLoading(true);
    setError("");

    try {
      const data =
        await getDocuments();

      setDocuments(
        Array.isArray(data?.documents)
          ? data.documents
          : Array.isArray(data)
          ? data
          : []
      );
    } catch (requestError) {
      console.error(
        "Load documents error:",
        requestError
      );

      setError(
        requestError?.message ||
          "Unable to connect to the backend."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleDelete = async (
    filename
  ) => {
    const confirmed =
      window.confirm(
        `Are you sure you want to delete "${filename}"?`
      );

    if (!confirmed) {
      return;
    }

    setError("");
    setActionMessage("");

    try {
      await deleteDocument(filename);

      setDocuments(
        (currentDocuments) =>
          currentDocuments.filter(
            (document) =>
              document.filename !==
              filename
          )
      );

      if (
        selectedDocument?.filename ===
        filename
      ) {
        setSelectedDocument(null);
      }

      setActionMessage(
        `${filename} deleted successfully.`
      );
    } catch (deleteError) {
      console.error(
        "Delete error:",
        deleteError
      );

      setError(
        deleteError?.message ||
          "Unable to delete document."
      );
    }
  };

  return (
    <div className="documents-page">
      <section className="documents-hero">
        <div className="hero-badge">
          <span>▤</span>
          DOCUMENT MANAGEMENT
        </div>

        <h2>
          Your knowledge,
          <br />
          <span>in one place.</span>
        </h2>

        <p>
          Upload your enterprise documents
          and organize them inside your
          intelligent workspace.
        </p>

        <DocumentUpload
          onUploadSuccess={loadDocuments}
        />

        {actionMessage && (
          <div
            style={{
              marginTop: "16px",
              color: "#29926f",
              fontSize: "14px",
              fontWeight: "600",
            }}
          >
            {actionMessage}
          </div>
        )}

        {error && (
          <div className="document-error">
            {error}
          </div>
        )}
      </section>

      <section className="documents-section">
        <div className="documents-section-header">
          <div>
            <h3>Your documents</h3>

            <p>
              {documents.length}{" "}
              {documents.length === 1
                ? "document"
                : "documents"}{" "}
              in your workspace.
            </p>
          </div>

          <button
            className="refresh-button"
            onClick={loadDocuments}
            disabled={loading}
          >
            {loading
              ? "Refreshing..."
              : "↻ Refresh"}
          </button>
        </div>

        <DocumentList
          documents={documents}
          loading={loading}
          onRefresh={loadDocuments}
          onOpen={setSelectedDocument}
          onDelete={handleDelete}
        />
      </section>

      {selectedDocument && (
        <DocumentViewer
          document={selectedDocument}
          onClose={() =>
            setSelectedDocument(null)
          }
        />
      )}
    </div>
  );
}

export default Documents;