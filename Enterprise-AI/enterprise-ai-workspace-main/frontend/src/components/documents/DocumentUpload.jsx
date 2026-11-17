import { useRef, useState } from "react";
import {
  uploadDocument,
} from "../../services/api";

function DocumentUpload({
  onUploadSuccess,
}) {
  const fileInputRef = useRef(null);

  const [uploading, setUploading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [message, setMessage] =
    useState("");

  const handleUploadClick = () => {
    setMessage("");
    setError("");

    fileInputRef.current?.click();
  };

  const handleFileSelected = async (
    event
  ) => {
    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    setUploading(true);
    setMessage("");
    setError("");

    const allowedTypes = [
      ".pdf",
      ".docx",
      ".txt",
    ];

    const filename =
      file.name.toLowerCase();

    const isAllowed =
      allowedTypes.some(
        (extension) =>
          filename.endsWith(extension)
      );

    if (!isAllowed) {
      setError(
        "Unsupported file type. Please upload PDF, DOCX or TXT."
      );

      setUploading(false);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      return;
    }

    try {
      const data =
        await uploadDocument(file);

      setMessage(
        `${data?.filename || file.name} uploaded successfully.`
      );

      if (onUploadSuccess) {
        await onUploadSuccess();
      }
    } catch (uploadError) {
      console.error(
        "Upload error:",
        uploadError
      );

      setError(
        uploadError?.message ||
          "Unable to upload document."
      );
    } finally {
      setUploading(false);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.txt"
        className="hidden-file-input"
        onChange={handleFileSelected}
      />

      <button
        className="upload-button"
        onClick={handleUploadClick}
        disabled={uploading}
      >
        <span>
          {uploading ? "↻" : "+"}
        </span>

        {uploading
          ? "Uploading..."
          : "Upload Document"}
      </button>

      {message && (
        <div
          style={{
            marginTop: "16px",
            color: "#29926f",
            fontSize: "14px",
            fontWeight: "600",
          }}
        >
          {message}
        </div>
      )}

      {error && (
        <div className="document-error">
          {error}
        </div>
      )}
    </>
  );
}

export default DocumentUpload;