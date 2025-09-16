import React, { useState } from 'react';
import './FileUpload.css';

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) return alert("📄 Please select a file first!");
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:5000/validate", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Server error");

      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error("Upload failed:", err);
      setError("❌ Upload failed. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-card">
        <h1>🧠 AI Document Validator</h1>
        <p>Upload your document or ID (PDF, Word, or image) to verify and extract key info.</p>

        <input
          type="file"
          accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
          onChange={handleFileChange}
        />

        <button onClick={handleUpload} disabled={loading}>
          {loading ? "Uploading..." : "Upload & Validate"}
        </button>

        {file && file.type.startsWith("image/") && (
          <div className="image-preview">
            <img src={URL.createObjectURL(file)} alt="Uploaded" />
          </div>
        )}

        {error && <div className="error">{error}</div>}

        {result && (
          <div className="result-box">
            <h3>✅ Validation Result:</h3>
            <pre>{JSON.stringify(result.validationResult, null, 2)}</pre>

            <h3>📝 Document Summary:</h3>
            <p>{result.summary}</p>

            <h3>🔑 Extracted Key Info:</h3>
            <ul>
              {result.key_info && Object.entries(result.key_info).map(([key, value]) => (
                <li key={key}><strong>{key}:</strong> {value || "Not Found"}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUpload;
