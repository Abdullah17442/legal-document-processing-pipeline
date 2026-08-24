import React, { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [chunks, setChunks] = useState({});

  // Store metadata/details for each document
  const [documentDetails, setDocumentDetails] = useState({});

  const [expandedDocument, setExpandedDocument] = useState(null);
  const [expandedDetails, setExpandedDetails] = useState(null);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [uploading, setUploading] = useState(false);
  const [loadingChunks, setLoadingChunks] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(null);

  const MAX_SIZE = 10 * 1024 * 1024; // 10 MB

  // ==================================================
  // LOAD DOCUMENTS WHEN PAGE OPENS
  // ==================================================

  useEffect(() => {
    fetchDocuments();
  }, []);

  // ==================================================
  // GET ALL DOCUMENTS
  // ==================================================

  const fetchDocuments = async () => {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/documents"
      );

      const data = await response.json();

      if (data.success) {
        setDocuments(data.documents);
      }
    } catch (err) {
      console.error(err);
      setError("Could not load documents.");
    }
  };

  // ==================================================
  // FILE SELECTION
  // ==================================================

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];

    if (!selectedFile) return;

    setError("");
    setMessage("");

    // Validate PDF
    if (selectedFile.type !== "application/pdf") {
      setError("Only PDF files are supported.");
      setFile(null);
      return;
    }

    // Validate size
    if (selectedFile.size > MAX_SIZE) {
      setError("File size must not exceed 10 MB.");
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  // ==================================================
  // UPLOAD DOCUMENT
  // ==================================================

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a PDF first.");
      return;
    }

    setUploading(true);
    setError("");
    setMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (response.ok && data.success) {
        setMessage(
          `${data.message} Created ${data.chunks} chunks.`
        );

        setFile(null);

        // Refresh documents
        await fetchDocuments();

        // Automatically store metadata in frontend
        if (data.metadata) {
          setDocumentDetails((prev) => ({
            ...prev,
            [data.document_id]: {
              ...data,
              ...data.metadata,
            },
          }));
        }
      } else {
        setError(data.message || "Upload failed.");
      }
    } catch (err) {
      console.error(err);
      setError("Could not connect to the backend.");
    }

    setUploading(false);
  };

  // ==================================================
  // GET DOCUMENT DETAILS / LEGAL METADATA
  // ==================================================

  const fetchDocumentDetails = async (documentId) => {
    // Collapse if already open
    if (expandedDetails === documentId) {
      setExpandedDetails(null);
      return;
    }

    setLoadingDetails(documentId);
    setError("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/documents/${documentId}`
      );

      const data = await response.json();

      if (response.ok && data.success) {
        setDocumentDetails((prev) => ({
          ...prev,
          [documentId]: data.document,
        }));

        setExpandedDetails(documentId);
      } else {
        setError(
          data.message || "Could not load document details."
        );
      }
    } catch (err) {
      console.error(err);
      setError("Could not connect to the backend.");
    }

    setLoadingDetails(null);
  };

  // ==================================================
  // GET DOCUMENT CHUNKS
  // ==================================================

  const fetchChunks = async (documentId) => {
    // Collapse if already expanded
    if (expandedDocument === documentId) {
      setExpandedDocument(null);
      return;
    }

    setLoadingChunks(documentId);
    setError("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/documents/${documentId}/chunks`
      );

      const data = await response.json();

      if (response.ok && data.success) {
        setChunks((prev) => ({
          ...prev,
          [documentId]: data.chunks,
        }));

        setExpandedDocument(documentId);
      } else {
        setError(
          data.message || "Could not load chunks."
        );
      }
    } catch (err) {
      console.error(err);
      setError("Could not connect to the backend.");
    }

    setLoadingChunks(null);
  };

  // ==================================================
  // DELETE DOCUMENT
  // ==================================================

  const deleteDocument = async (id) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this document and all its chunks?"
    );

    if (!confirmed) return;

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/documents/${id}`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json();

      if (data.success) {
        // Remove chunks
        setChunks((prev) => {
          const updated = { ...prev };
          delete updated[id];
          return updated;
        });

        // Remove metadata
        setDocumentDetails((prev) => {
          const updated = { ...prev };
          delete updated[id];
          return updated;
        });

        // Collapse details
        if (expandedDetails === id) {
          setExpandedDetails(null);
        }

        // Collapse chunks
        if (expandedDocument === id) {
          setExpandedDocument(null);
        }

        await fetchDocuments();

        setMessage("Document deleted successfully.");
      } else {
        setError(data.message || "Delete failed.");
      }
    } catch (err) {
      console.error(err);
      setError("Could not connect to the backend.");
    }
  };

  // ==================================================
  // UI
  // ==================================================

  return (
    <div className="app">

      {/* ==================================================
          HEADER
      ================================================== */}

      <header className="header">
        <h1>Legal Assistant</h1>
      </header>

      <main className="container">

        <div className="upload-card">

          {/* ==================================================
              UPLOAD SECTION
          ================================================== */}

          <h2>Upload Legal Document</h2>

          <p className="subtitle">
            Supported format: <strong>PDF</strong>{" "}
            (Maximum size: 10 MB)
          </p>

          <input
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileChange}
          />

          {file && (
            <div className="success">
              <strong>Selected File:</strong>
              <br />
              {file.name}
            </div>
          )}

          <button
            className="upload-btn"
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading ? "Processing..." : "Upload PDF"}
          </button>

          {message && (
            <div className="success">
              {message}
            </div>
          )}

          {error && (
            <div className="error">
              {error}
            </div>
          )}

          {/* ==================================================
              DOCUMENTS
          ================================================== */}

          <hr />

          <h2>Uploaded Documents</h2>

          {documents.length === 0 ? (
            <p className="empty">
              No documents uploaded yet.
            </p>
          ) : (
            <div className="documents-list">

              {documents.map((doc) => {

                const details =
                  documentDetails[doc.id];

                return (
                  <div
                    className="document-wrapper"
                    key={doc.id}
                  >

                    {/* ==================================================
                        DOCUMENT HEADER
                    ================================================== */}

                    <div className="document-item">

                      <div className="document-info">

                        <strong>
                          📄 {doc.filename}
                        </strong>

                        <small>
                          {doc.pages} pages
                          {" • "}
                          {doc.characters
                            ? doc.characters.toLocaleString()
                            : 0}{" "}
                          characters
                        </small>

                      </div>

                      <div className="document-actions">

                        {/* VIEW DETAILS */}

                        <button
                          className="details-btn"
                          onClick={() =>
                            fetchDocumentDetails(doc.id)
                          }
                        >
                          {loadingDetails === doc.id
                            ? "Loading..."
                            : expandedDetails === doc.id
                            ? "Hide Details"
                            : "View Details"}
                        </button>

                        {/* VIEW CHUNKS */}

                        <button
                          className="view-btn"
                          onClick={() =>
                            fetchChunks(doc.id)
                          }
                        >
                          {loadingChunks === doc.id
                            ? "Loading..."
                            : expandedDocument === doc.id
                            ? "Hide Chunks"
                            : "View Chunks"}
                        </button>

                        {/* DELETE */}

                        <button
                          className="delete-btn"
                          onClick={() =>
                            deleteDocument(doc.id)
                          }
                        >
                          Delete
                        </button>

                      </div>

                    </div>

                    {/* ==================================================
                        LEGAL METADATA
                    ================================================== */}

                    {expandedDetails === doc.id &&
                      details && (

                        <div className="metadata-container">

                          <div className="metadata-header">
                            <strong>
                              ⚖️ Legal Document Information
                            </strong>
                          </div>

                          <div className="metadata-grid">

                            <div className="metadata-item">
                              <span>
                                Case Number
                              </span>

                              <strong>
                                {details.case_number ||
                                  "Not identified"}
                              </strong>
                            </div>

                            <div className="metadata-item">
                              <span>
                                Judge
                              </span>

                              <strong>
                                {details.judge_name ||
                                  "Not identified"}
                              </strong>
                            </div>

                            <div className="metadata-item">
                              <span>
                                Petitioner
                              </span>

                              <strong>
                                {details.petitioner_name ||
                                  "Not identified"}
                              </strong>
                            </div>

                            <div className="metadata-item">
                              <span>
                                Respondent
                              </span>

                              <strong>
                                {details.respondent_name ||
                                  "Not identified"}
                              </strong>
                            </div>

                            <div className="metadata-item">
                              <span>
                                Court
                              </span>

                              <strong>
                                {details.court ||
                                  "Not identified"}
                              </strong>
                            </div>

                            <div className="metadata-item">
                              <span>
                                Pages
                              </span>

                              <strong>
                                {details.pages || 0}
                              </strong>
                            </div>

                            <div className="metadata-item">
                              <span>
                                Characters
                              </span>

                              <strong>
                                {details.characters
                                  ? details.characters.toLocaleString()
                                  : 0}
                              </strong>
                            </div>

                          </div>

                          {/* ==================================================
                              IMPORTANT PARTS
                          ================================================== */}

                          <div className="important-parts">

                            <h3>
                              Important Parts of Judgment
                            </h3>

                            {details.important_parts ? (
                              (() => {
                                try {
                                  const parts =
                                    typeof details.important_parts ===
                                    "string"
                                      ? JSON.parse(
                                          details.important_parts
                                        )
                                      : details.important_parts;

                                  if (
                                    Array.isArray(parts)
                                  ) {
                                    return (
                                      <ul>
                                        {parts.map(
                                          (part, index) => (
                                            <li
                                              key={index}
                                            >
                                              {typeof part ===
                                              "object"
                                                ? JSON.stringify(
                                                    part
                                                  )
                                                : part}
                                            </li>
                                          )
                                        )}
                                      </ul>
                                    );
                                  }

                                  return (
                                    <p>
                                      {String(parts)}
                                    </p>
                                  );

                                } catch {
                                  return (
                                    <p>
                                      {
                                        details.important_parts
                                      }
                                    </p>
                                  );
                                }
                              })()
                            ) : (
                              <p>
                                No important parts identified.
                              </p>
                            )}

                          </div>

                        </div>
                      )}

                    {/* ==================================================
                        CHUNKS
                    ================================================== */}

                    {expandedDocument === doc.id &&
                      chunks[doc.id] && (

                        <div className="chunks-container">

                          <div className="chunks-header">

                            <strong>
                              Document Chunks
                            </strong>

                            <span>
                              {chunks[doc.id].length} chunks
                            </span>

                          </div>

                          {chunks[doc.id].map(
                            (chunk) => (

                              <div
                                className="chunk-item"
                                key={chunk.id}
                              >

                                <div className="chunk-header">

                                  <strong>
                                    Chunk{" "}
                                    {chunk.chunk_number}
                                  </strong>

                                  <span>
                                    Characters{" "}
                                    {chunk.char_start}
                                    {" - "}
                                    {chunk.char_end}
                                  </span>

                                </div>

                                <p>
                                  {chunk.chunk_text}
                                </p>

                              </div>
                            )
                          )}

                        </div>
                      )}

                  </div>
                );
              })}

            </div>
          )}

        </div>

      </main>

    </div>
  );
}

export default App;