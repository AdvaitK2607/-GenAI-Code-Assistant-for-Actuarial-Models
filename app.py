import os
from io import BytesIO
from typing import List, Tuple

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

import google.generativeai as genai
import csv
from PyPDF2 import PdfReader

# --- Config ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in environment or .env file")

# Default model (override via request JSON field 'model')
DEFAULT_MODEL = "gemini-2.5-flash-preview-09-2025"

# Init app
app = Flask(__name__)
# Adjust CORS origins to your frontend origin if needed
CORS(app, resources={r"/*": {"origins": "*"}})

# Init Gemini
genai.configure(api_key=GEMINI_API_KEY)

# --- Helpers ---
def read_pdf(file_storage) -> str:
    """Extract text from a PDF upload."""
    text_chunks = []
    try:
        reader = PdfReader(file_storage)
        for page in reader.pages:
            txt = page.extract_text() or ""
            if txt.strip():
                text_chunks.append(txt)
    except Exception as e:
        text_chunks.append(f"[PDF parse error: {e}]")
    return "\n".join(text_chunks)

def read_txt(file_storage) -> str:
    try:
        content = file_storage.read()
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("latin-1", errors="ignore")
    except Exception as e:
        return f"[TXT read error: {e}]"

def read_csv(file_storage) -> str:
    """Convert small CSVs to a compact text table."""
    try:
        content = file_storage.read().decode("utf-8", errors="ignore")
        reader = csv.reader(content.splitlines())
        rows = list(reader)
        # Don’t dump massive CSVs
        max_rows = 60
        if len(rows) > max_rows:
            rows = rows[:max_rows] + [["... (truncated) ..."]]
        lines = [", ".join(r) for r in rows]
        return "\n".join(lines)
    except Exception as e:
        return f"[CSV read error: {e}]"

def process_files(files) -> List[Tuple[str, str]]:
    """
    Returns list of (filename, extracted_text).
    Supports pdf, txt, csv. Ignores unknown types.
    """
    results = []
    for f in files:
        mime = f.mimetype or ""
        name = f.filename or "uploaded_file"

        if mime == "application/pdf" or name.lower().endswith(".pdf"):
            text = read_pdf(f)
        elif mime.startswith("text/") or name.lower().endswith(".txt"):
            text = read_txt(f)
        elif name.lower().endswith(".csv") or "csv" in mime:
            text = read_csv(f)
        else:
            text = f"[Unsupported file type: {mime or name}]"
        results.append((name, text))
    return results

def build_prompt(user_prompt: str, files_ctx: List[Tuple[str, str]]) -> str:
    base_prompt = f"""
Analyze the following request and provide a comprehensive response.
Consider the context, provide insights, explanations, and any relevant information.
If a file is uploaded, extract the content fully and give detailed analysis based on that content.
USER REQUEST:
{user_prompt}
""".strip()

    if files_ctx:
        parts = []
        for fname, text in files_ctx:
            # Keep each file block to a reasonable size
            snippet = text[:12000]  # rough safety cut
            parts.append(f"File: {fname}\nContent:\n{snippet}")
        files_block = "\n\n".join(parts)
        base_prompt += f"\n\nADDITIONAL CONTEXT FROM UPLOADED FILES:\n{files_block}"

    analysis_prompt = f"""
{base_prompt}

Please format the response EXACTLY in this structure:

### Explanation
Provide a clear and concise explanation of the logic or concept in simple language.
if a file is provided, try to extract as musch relevant information as possible from the file.

### Code
Provide clean and well-formatted code. Avoid unnecessary comments and keep it readable.
if a file is provided, try to extract as much relevant information as possible from the file.

### Time & Space Complexity
- Time Complexity: Big-O notation with brief reasoning.
- Space Complexity: Big-O notation with brief reasoning.

Do NOT add extra sections. Do NOT add comparisons, analogies, historical notes, or extended descriptions.
Keep the answer focused and clean.
Provide only the requested sections with no additional commentary.
""".strip()
    return analysis_prompt

# --- Routes ---
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Accepts multipart/form-data:
      - prompt: string
      - model: optional string
      - files: one or more file inputs
    Returns: { content: "...", model: "..." }
    """
    try:
        prompt = request.form.get("prompt", "").strip()
        if not prompt:
            return jsonify({"error": "Missing 'prompt'"}), 400

        model_name = request.form.get("model", DEFAULT_MODEL)

        files = request.files.getlist("files")
        files_ctx = process_files(files) if files else []

        final_prompt = build_prompt(prompt, files_ctx)

        model = genai.GenerativeModel(model_name)
        resp = model.generate_content(final_prompt)
        content = getattr(resp, "text", None) or ""

        if not content.strip():
            return jsonify({"error": "Empty response from model"}), 502

        return jsonify({
            "content": content,
            "model": model_name
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Use 0.0.0.0 if you run in Docker/VPS
    app.run(host="127.0.0.1", port=5000, debug=True)
