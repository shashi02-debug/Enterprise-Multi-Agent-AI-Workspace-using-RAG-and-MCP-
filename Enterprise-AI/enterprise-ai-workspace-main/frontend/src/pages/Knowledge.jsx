import "./Knowledge.css";

import { useEffect, useState } from "react";
import {
  API_BASE_URL,
  apiRequest,
  getDocuments,
} from "../services/api";


function Knowledge() {

  // =====================================================
  // STATE
  // =====================================================

  const [documents, setDocuments] =
    useState([]);

  const [ragStatus, setRagStatus] =
    useState(null);

  const [query, setQuery] =
    useState("");

  const [results, setResults] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [searching, setSearching] =
    useState(false);

  const [error, setError] =
    useState("");

  const [searchError, setSearchError] =
    useState("");


  // =====================================================
  // LOAD KNOWLEDGE STATUS
  // =====================================================

  useEffect(() => {
    loadKnowledge();
  }, []);


  const loadKnowledge = async () => {

    setLoading(true);
    setError("");

    try {

      // Load documents

      const documentData =
        await getDocuments();

      if (Array.isArray(documentData)) {

        setDocuments(
          documentData
        );

      } else if (
        Array.isArray(
          documentData?.documents
        )
      ) {

        setDocuments(
          documentData.documents
        );

      } else {

        setDocuments([]);

      }


      // Load RAG status

      try {

        const status =
          await apiRequest(
            "/rag/status"
          );

        setRagStatus(
          status
        );

      } catch (statusError) {

        console.warn(
          "RAG status unavailable:",
          statusError
        );

        // Don't make the entire page fail
        // if the status endpoint is unavailable.

        setRagStatus(null);
      }

    } catch (error) {

      console.error(
        "Knowledge loading failed:",
        error
      );

      setError(
        error?.message ||
          "Unable to load knowledge base."
      );

    } finally {

      setLoading(false);

    }
  };


  // =====================================================
  // SEARCH KNOWLEDGE
  // =====================================================

  const handleSearch = async () => {

    const trimmedQuery =
      query.trim();


    if (
      !trimmedQuery ||
      searching
    ) {
      return;
    }


    setSearching(true);
    setSearchError("");
    setResults([]);


    try {

      const response =
        await apiRequest(
          "/search",
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",

              Accept:
                "application/json",
            },

            body: JSON.stringify({
              query:
                trimmedQuery,

              top_k: 5,
            }),
          }
        );


      console.log(
        "Knowledge search response:",
        response
      );


      // ===============================================
      // NORMALIZE DIFFERENT POSSIBLE RESPONSE FORMATS
      // ===============================================

      let normalizedResults = [];


      if (
        Array.isArray(response)
      ) {

        normalizedResults =
          response;

      } else if (
        Array.isArray(
          response?.results
        )
      ) {

        normalizedResults =
          response.results;

      } else if (
        Array.isArray(
          response?.documents
        )
      ) {

        normalizedResults =
          response.documents;

      } else if (
        Array.isArray(
          response?.matches
        )
      ) {

        normalizedResults =
          response.matches;

      } else if (
        Array.isArray(
          response?.data
        )
      ) {

        normalizedResults =
          response.data;

      }


      setResults(
        normalizedResults
      );

    } catch (error) {

      console.error(
        "Knowledge search failed:",
        error
      );

      setSearchError(
        error?.message ||
          "Unable to search the knowledge base."
      );

    } finally {

      setSearching(false);

    }
  };


  // =====================================================
  // KEYBOARD
  // =====================================================

  const handleKeyDown = (
    event
  ) => {

    if (
      event.key === "Enter"
    ) {

      event.preventDefault();

      handleSearch();

    }

  };


  // =====================================================
  // RESULT HELPERS
  // =====================================================

  const getSourceName = (
    result
  ) => {

    return (
      result?.source ||
      result?.filename ||
      result?.file_name ||
      result?.metadata?.source ||
      result?.metadata?.filename ||
      result?.metadata?.file_name ||
      "Unknown document"
    );

  };


  const getResultText = (
    result
  ) => {

    return (
      result?.text ||
      result?.content ||
      result?.document ||
      result?.page_content ||
      result?.metadata?.text ||
      "No text available."
    );

  };


  const getDistance = (
    result
  ) => {

    const value =
      result?.distance ??
      result?.score ??
      result?.relevance ??
      result?.metadata?.distance;

    if (
      value === undefined ||
      value === null ||
      value === ""
    ) {
      return null;
    }

    if (
      typeof value === "number"
    ) {
      return value.toFixed(3);
    }

    return String(value);

  };


  // =====================================================
  // DERIVE STATS
  // =====================================================

  const documentCount =
    documents.length;


  const indexedCount =
    ragStatus?.document_count ??
    ragStatus?.documents ??
    ragStatus?.indexed_documents ??
    documentCount;


  const chunkCount =
    ragStatus?.chunk_count ??
    ragStatus?.chunks ??
    ragStatus?.indexed_chunks ??
    "—";


  const ragConnected =
    ragStatus
      ? (
          ragStatus.status === "ok" ||
          ragStatus.status === "healthy" ||
          ragStatus.status === "connected" ||
          ragStatus.available === true ||
          ragStatus.connected === true
        )
      : true;


  // =====================================================
  // UI
  // =====================================================

  return (
    <section className="knowledge-page">

      {/* =================================================
          HERO
      ================================================= */}

      <div className="documents-hero">

        <div className="hero-badge">
          <span>◇</span>
          KNOWLEDGE BASE
        </div>


        <h2>
          Your knowledge,
          <br />
          <span>ready for AI.</span>
        </h2>


        <p>
          Explore the enterprise knowledge
          stored in your AI workspace and
          test semantic retrieval directly.
        </p>

      </div>


      {/* =================================================
          ERROR
      ================================================= */}

      {error && (

        <div
          style={{
            width: "min(1100px, 100%)",
            margin: "24px auto",
            padding: "16px 20px",
            border: "1px solid #f0d4d4",
            borderRadius: "14px",
            background: "#fff8f8",
            color: "#a94442",
            fontSize: "14px",
          }}
        >

          {error}

        </div>

      )}


      {/* =================================================
          KNOWLEDGE STATS
      ================================================= */}

      <div
        style={{
          width: "min(1100px, 100%)",
          margin: "0 auto",
          padding: "0 40px",
        }}
      >

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(3, minmax(0, 1fr))",
            gap: "18px",
          }}
        >

          {/* Documents */}

          <div
            style={{
              border:
                "1px solid #e7e2ee",
              borderRadius: "18px",
              padding: "22px",
              background: "#ffffff",
              boxShadow:
                "0 8px 25px rgba(72,48,130,0.05)",
            }}
          >

            <div
              style={{
                width: "42px",
                height: "42px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "12px",
                background: "#f1ecff",
                color: "#6941e8",
                fontSize: "18px",
              }}
            >
              ▤
            </div>


            <div
              style={{
                marginTop: "18px",
                color: "#8b8497",
                fontSize: "12px",
                fontWeight: "600",
                textTransform:
                  "uppercase",
                letterSpacing:
                  "0.5px",
              }}
            >
              Indexed documents
            </div>


            <div
              style={{
                marginTop: "5px",
                color: "#29213d",
                fontSize: "28px",
                fontWeight: "800",
              }}
            >
              {loading
                ? "..."
                : indexedCount}
            </div>

          </div>


          {/* Chunks */}

          <div
            style={{
              border:
                "1px solid #e7e2ee",
              borderRadius: "18px",
              padding: "22px",
              background: "#ffffff",
              boxShadow:
                "0 8px 25px rgba(72,48,130,0.05)",
            }}
          >

            <div
              style={{
                width: "42px",
                height: "42px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "12px",
                background: "#f1ecff",
                color: "#6941e8",
                fontSize: "18px",
              }}
            >
              #
            </div>


            <div
              style={{
                marginTop: "18px",
                color: "#8b8497",
                fontSize: "12px",
                fontWeight: "600",
                textTransform:
                  "uppercase",
                letterSpacing:
                  "0.5px",
              }}
            >
              Knowledge chunks
            </div>


            <div
              style={{
                marginTop: "5px",
                color: "#29213d",
                fontSize: "28px",
                fontWeight: "800",
              }}
            >
              {loading
                ? "..."
                : chunkCount}
            </div>

          </div>


          {/* RAG */}

          <div
            style={{
              border:
                "1px solid #e7e2ee",
              borderRadius: "18px",
              padding: "22px",
              background: "#ffffff",
              boxShadow:
                "0 8px 25px rgba(72,48,130,0.05)",
            }}
          >

            <div
              style={{
                width: "42px",
                height: "42px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "12px",
                background: "#f1ecff",
                color: "#6941e8",
                fontSize: "18px",
              }}
            >
              ✦
            </div>


            <div
              style={{
                marginTop: "18px",
                color: "#8b8497",
                fontSize: "12px",
                fontWeight: "600",
                textTransform:
                  "uppercase",
                letterSpacing:
                  "0.5px",
              }}
            >
              RAG engine
            </div>


            <div
              style={{
                marginTop: "9px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                color:
                  ragConnected
                    ? "#29926f"
                    : "#c0392b",
                fontSize: "14px",
                fontWeight: "700",
              }}
            >

              <span
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "50%",
                  background:
                    ragConnected
                      ? "#36b88b"
                      : "#c0392b",
                }}
              />

              {ragConnected
                ? "Connected"
                : "Unavailable"}

            </div>

          </div>

        </div>

      </div>


      {/* =================================================
          SEMANTIC SEARCH
      ================================================= */}

      <div
        style={{
          width: "min(1100px, 100%)",
          margin: "38px auto 0",
          padding: "0 40px",
        }}
      >

        <div
          style={{
            border:
              "1px solid #e7e2ee",
            borderRadius: "20px",
            padding: "28px",
            background: "#ffffff",
            boxShadow:
              "0 10px 30px rgba(72,48,130,0.06)",
          }}
        >

          <div>

            <h3
              style={{
                margin: 0,
                color: "#29213d",
                fontSize: "20px",
                fontWeight: "750",
              }}
            >
              Semantic knowledge search
            </h3>


            <p
              style={{
                margin:
                  "8px 0 20px",
                color: "#8b8497",
                fontSize: "14px",
                lineHeight: "1.6",
              }}
            >
              Search your indexed documents
              using semantic similarity rather
              than exact keyword matching.
            </p>

          </div>


          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              border:
                "1px solid #ded8eb",
              borderRadius: "15px",
              padding: "6px",
              background: "#fbfaff",
            }}
          >

            <span
              style={{
                paddingLeft: "14px",
                color: "#6941e8",
                fontSize: "18px",
              }}
            >
              ⌕
            </span>


            <input
              type="text"
              value={query}
              onChange={(event) =>
                setQuery(
                  event.target.value
                )
              }
              onKeyDown={
                handleKeyDown
              }
              placeholder="Ask something about your enterprise knowledge..."
              disabled={searching}
              style={{
                flex: 1,
                minWidth: 0,
                height: "48px",
                border: 0,
                outline: 0,
                background:
                  "transparent",
                color: "#29213d",
                fontSize: "14px",
              }}
            />


            <button
              type="button"
              onClick={
                handleSearch
              }
              disabled={
                searching ||
                !query.trim()
              }
              style={{
                minWidth: "110px",
                height: "48px",
                border: 0,
                borderRadius: "11px",
                background:
                  searching ||
                  !query.trim()
                    ? "#d9d2ef"
                    : "#6844e5",
                color: "#ffffff",
                fontWeight: "700",
                cursor:
                  searching ||
                  !query.trim()
                    ? "default"
                    : "pointer",
              }}
            >
              {searching
                ? "Searching..."
                : "Search"}
            </button>

          </div>


          {/* Search error */}

          {searchError && (

            <div
              style={{
                marginTop: "15px",
                color: "#c0392b",
                fontSize: "13px",
              }}
            >
              {searchError}
            </div>

          )}

        </div>

      </div>


      {/* =================================================
          SEARCH RESULTS
      ================================================= */}

      {results.length > 0 && (

        <div
          style={{
            width: "min(1100px, 100%)",
            margin: "28px auto 0",
            padding: "0 40px 70px",
          }}
        >

          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent:
                "space-between",
              marginBottom: "16px",
            }}
          >

            <div>

              <h3
                style={{
                  margin: 0,
                  color: "#29213d",
                  fontSize: "20px",
                  fontWeight: "750",
                }}
              >
                Retrieved knowledge
              </h3>


              <p
                style={{
                  margin:
                    "6px 0 0",
                  color: "#8b8497",
                  fontSize: "13px",
                }}
              >
                {results.length} relevant
                chunk
                {results.length === 1
                  ? ""
                  : "s"}{" "}
                retrieved from ChromaDB.
              </p>

            </div>

          </div>


          <div
            style={{
              display: "flex",
              flexDirection:
                "column",
              gap: "14px",
            }}
          >

            {results.map(
              (result, index) => {

                const source =
                  getSourceName(
                    result
                  );

                const text =
                  getResultText(
                    result
                  );

                const distance =
                  getDistance(
                    result
                  );


                return (

                  <div
                    key={`${source}-${index}`}
                    style={{
                      border:
                        "1px solid #e7e2ee",
                      borderRadius: "16px",
                      padding: "20px",
                      background:
                        "#ffffff",
                      boxShadow:
                        "0 7px 22px rgba(72,48,130,0.04)",
                    }}
                  >

                    {/* Result header */}

                    <div
                      style={{
                        display: "flex",
                        alignItems:
                          "center",
                        justifyContent:
                          "space-between",
                        gap: "15px",
                      }}
                    >

                      <div
                        style={{
                          display: "flex",
                          alignItems:
                            "center",
                          gap: "10px",
                          minWidth: 0,
                        }}
                      >

                        <div
                          style={{
                            width: "34px",
                            height: "34px",
                            flexShrink: 0,
                            display: "flex",
                            alignItems:
                              "center",
                            justifyContent:
                              "center",
                            borderRadius:
                              "9px",
                            background:
                              "#f1ecff",
                            color:
                              "#6941e8",
                          }}
                        >
                          📄
                        </div>


                        <div
                          style={{
                            minWidth: 0,
                          }}
                        >

                          <strong
                            style={{
                              display:
                                "block",
                              overflow:
                                "hidden",
                              textOverflow:
                                "ellipsis",
                              whiteSpace:
                                "nowrap",
                              color:
                                "#302642",
                              fontSize:
                                "14px",
                            }}
                            title={source}
                          >
                            {source}
                          </strong>


                          <span
                            style={{
                              color:
                                "#9992a5",
                              fontSize:
                                "11px",
                            }}
                          >
                            Retrieved knowledge
                            chunk {index + 1}
                          </span>

                        </div>

                      </div>


                      {distance !== null && (

                        <span
                          style={{
                            flexShrink: 0,
                            padding:
                              "6px 10px",
                            borderRadius:
                              "999px",
                            background:
                              "#f7f4ff",
                            color:
                              "#6941e8",
                            fontSize:
                              "11px",
                            fontWeight:
                              "700",
                          }}
                        >
                          Score: {distance}
                        </span>

                      )}

                    </div>


                    {/* Chunk text */}

                    <div
                      style={{
                        marginTop: "16px",
                        padding:
                          "15px 16px",
                        borderRadius:
                          "12px",
                        background:
                          "#fbfaff",
                        color:
                          "#4d4658",
                        fontSize:
                          "13px",
                        lineHeight:
                          "1.7",
                        whiteSpace:
                          "pre-wrap",
                        overflowWrap:
                          "anywhere",
                      }}
                    >
                      {text}
                    </div>

                  </div>

                );

              }
            )}

          </div>

        </div>

      )}


      {/* =================================================
          EMPTY SEARCH STATE
      ================================================= */}

      {!loading &&
        !searching &&
        query.trim() &&
        results.length === 0 &&
        !searchError && (

          <div
            style={{
              width: "min(1100px, 100%)",
              margin: "28px auto",
              padding: "0 40px 70px",
            }}
          >

            <div
              style={{
                padding: "35px",
                textAlign: "center",
                border:
                  "1px dashed #ddd6eb",
                borderRadius: "18px",
                color: "#8b8497",
              }}
            >

              No relevant knowledge chunks
              were found.

            </div>

          </div>

        )}


      {/* =================================================
          DOCUMENT INVENTORY
      ================================================= */}

      {!query.trim() && (

        <div
          style={{
            width: "min(1100px, 100%)",
            margin: "38px auto 0",
            padding: "0 40px 70px",
          }}
        >

          <div
            style={{
              marginBottom: "16px",
            }}
          >

            <h3
              style={{
                margin: 0,
                color: "#29213d",
                fontSize: "20px",
                fontWeight: "750",
              }}
            >
              Knowledge sources
            </h3>


            <p
              style={{
                margin:
                  "6px 0 0",
                color: "#8b8497",
                fontSize: "13px",
              }}
            >
              Documents currently available
              to the enterprise RAG pipeline.
            </p>

          </div>


          {documents.length === 0 ? (

            <div
              style={{
                padding: "35px",
                textAlign: "center",
                border:
                  "1px dashed #ddd6eb",
                borderRadius: "18px",
                color: "#8b8497",
              }}
            >

              No documents have been
              indexed yet.

            </div>

          ) : (

            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(2, minmax(0, 1fr))",
                gap: "14px",
              }}
            >

              {documents.map(
                (document, index) => {

                  const filename =
                    document?.filename ||
                    document?.name ||
                    `Document ${index + 1}`;

                  const size =
                    document?.size ??
                    document?.file_size;

                  const fileType =
                    document?.file_type ||
                    filename
                      .split(".")
                      .pop()
                      ?.toUpperCase() ||
                    "FILE";


                  return (

                    <div
                      key={`${filename}-${index}`}
                      style={{
                        display: "flex",
                        alignItems:
                          "center",
                        gap: "13px",
                        minWidth: 0,
                        padding: "16px",
                        border:
                          "1px solid #e7e2ee",
                        borderRadius:
                          "14px",
                        background:
                          "#ffffff",
                      }}
                    >

                      <div
                        style={{
                          width: "38px",
                          height: "38px",
                          flexShrink: 0,
                          display:
                            "flex",
                          alignItems:
                            "center",
                          justifyContent:
                            "center",
                          borderRadius:
                            "10px",
                          background:
                            "#f1ecff",
                          color:
                            "#6941e8",
                          fontSize:
                            "13px",
                          fontWeight:
                            "700",
                        }}
                      >
                        {fileType
                          .slice(0, 3)}
                      </div>


                      <div
                        style={{
                          minWidth: 0,
                          flex: 1,
                        }}
                      >

                        <strong
                          style={{
                            display:
                              "block",
                            overflow:
                              "hidden",
                            textOverflow:
                              "ellipsis",
                            whiteSpace:
                              "nowrap",
                            color:
                              "#302642",
                            fontSize:
                              "13px",
                          }}
                          title={filename}
                        >
                          {filename}
                        </strong>


                        <span
                          style={{
                            color:
                              "#9992a5",
                            fontSize:
                              "11px",
                          }}
                        >
                          {size !== undefined
                            ? `${formatFileSize(
                                size
                              )} • `
                            : ""}
                          Indexed in knowledge base
                        </span>

                      </div>

                    </div>

                  );

                }
              )}

            </div>

          )}

        </div>

      )}

    </section>
  );
}


// =====================================================
// FILE SIZE
// =====================================================

function formatFileSize(
  bytes
) {

  if (
    bytes === null ||
    bytes === undefined ||
    Number.isNaN(
      Number(bytes)
    )
  ) {
    return "";
  }


  const value =
    Number(bytes);


  if (value < 1024) {
    return `${value} B`;
  }


  if (value < 1024 * 1024) {
    return `${(
      value / 1024
    ).toFixed(1)} KB`;
  }


  return `${(
    value /
    (1024 * 1024)
  ).toFixed(1)} MB`;

}


export default Knowledge;