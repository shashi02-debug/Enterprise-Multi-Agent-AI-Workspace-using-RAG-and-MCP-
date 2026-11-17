function getFileType(filename = "") {
  const extension = filename
    .split(".")
    .pop()
    ?.toLowerCase();

  switch (extension) {
    case "pdf":
      return "PDF";
    case "docx":
      return "DOCX";
    case "txt":
      return "TXT";
    default:
      return "FILE";
  }
}

function formatFileSize(bytes) {
  if (!bytes || bytes === 0) {
    return "0 KB";
  }

  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(
    bytes /
    (1024 * 1024)
  ).toFixed(2)} MB`;
}

function DocumentList({
  documents,
  loading,
  onRefresh,
  onOpen,
  onDelete,
}) {
  if (loading && documents.length === 0) {
    return (
      <div className="documents-empty">
        <div className="loading-spinner" />

        <h3>Loading documents...</h3>

        <p>
          Connecting to your workspace.
        </p>
      </div>
    );
  }

  if (!loading && documents.length === 0) {
    return (
      <div className="documents-empty">
        <div className="empty-icon">▤</div>

        <h3>No documents yet</h3>

        <p>
          Upload your first PDF, DOCX or TXT
          document to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="document-list">
      {documents.map((document) => {
        const fileType =
          document.file_type ||
          getFileType(document.filename);

        return (
          <div
            className="document-card"
            key={document.filename}
          >
            <div className="document-file-icon">
              {fileType}
            </div>

            <div className="document-details">
              <h4
                title={document.filename}
              >
                {document.filename}
              </h4>

              <p>
                {fileType} •{" "}
                {formatFileSize(
                  document.size
                )}
              </p>
            </div>

            <div className="document-actions">
              <button
                className="document-open-button"
                onClick={() =>
                  onOpen(document)
                }
              >
                Open
              </button>

              <button
                className="document-delete-button"
                onClick={() =>
                  onDelete(
                    document.filename
                  )
                }
              >
                Delete
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default DocumentList;