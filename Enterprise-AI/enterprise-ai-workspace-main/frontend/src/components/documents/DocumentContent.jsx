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

function DocumentContent({
  content,
  document,
}) {
  let pages = [];

  if (Array.isArray(content?.pages)) {
    pages = content.pages;
  } else if (
    Array.isArray(content?.content)
  ) {
    pages = content.content;
  } else if (
    typeof content?.text === "string"
  ) {
    pages = [
      {
        page: 1,
        text: content.text,
      },
    ];
  } else if (
    typeof content?.content === "string"
  ) {
    pages = [
      {
        page: 1,
        text: content.content,
      },
    ];
  } else if (
    typeof content === "string"
  ) {
    pages = [
      {
        page: 1,
        text: content,
      },
    ];
  } else {
    pages = [
      {
        page: 1,
        text: JSON.stringify(
          content,
          null,
          2
        ),
      },
    ];
  }

  return (
    <div className="document-content">
      <div className="document-summary">
        <span>
          {document.file_type ||
            getFileType(
              document.filename
            )}
        </span>

        <span>
          {pages.length}{" "}
          {pages.length === 1
            ? "section"
            : "sections"}
        </span>
      </div>

      {pages.map((page, index) => {
        const pageNumber =
          page?.page ||
          page?.page_number ||
          index + 1;

        const pageText =
          typeof page === "string"
            ? page
            : page?.text ??
              page?.content ??
              "";

        return (
          <div
            className="document-page"
            key={index}
          >
            <div className="page-number">
              {getFileType(
                document.filename
              ) === "TXT"
                ? "CONTENT"
                : `PAGE ${pageNumber}`}
            </div>

            <div className="page-text">
              {pageText ||
                "No text extracted."}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default DocumentContent;