# extract_metadata_from_pdf_llm.py
import fitz  # PyMuPDF
import os
import json
from dotenv import load_dotenv
from google import genai

# ===== Load API key =====
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise EnvironmentError("GOOGLE_API_KEY missing in .env file")

client = genai.Client(api_key=API_KEY)

# ===== PDF Reader =====
def read_pdf(file_path):
    """Read all text from a PDF file."""
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text.strip()

# ===== Gemini Extraction =====
def extract_dashboard_metadata(pdf_text, dashboard_id, dashboard_name, workbook_name, file_name):
    """Send PDF text to Gemini to extract structured metadata."""
    prompt = f"""
    You are an expert in reading Tableau dashboard PDF exports.
    The following text comes from a dashboard PDF.

    Extract and return ONLY a valid JSON object in the EXACT format:
    {{
      "id": "{dashboard_id}",
      "name": "<Dashboard Name>",
      "description": "<1-2 sentences summarizing purpose of dashboard>",
      "tags": ["tag1", "tag2", "tag3"],
      "url": "{workbook_name}/{file_name}",
      "kpis": [
        {{
          "name": "<KPI Name>",
          "description": "<Meaning of KPI and value in context>"
        }}
      ]
    }}

    IMPORTANT:
    - For each KPI description, explain what it represents and include the value in parentheses, e.g., 
      "Overall discount in dollars (198,837)" or "Current profit margin (-35%)".
    - If multiple values appear, mention them in the description.
    - Do not just output the numeric value; always add context from the KPI name and PDF text.
    - Tags should be keywords describing the dashboard topic (e.g., 'sales', 'finance', 'profit', 'discount').
    - Output must be strictly valid JSON with no comments or extra text before/after.

    PDF Text:
    {pdf_text}
    """

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )

    # Clean output to ensure valid JSON
    output = response.text.strip()
    if output.startswith("```json"):
        output = output[7:]
    if output.endswith("```"):
        output = output[:-3]
    output = output.strip()

    try:
        metadata = json.loads(output)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Gemini output is not valid JSON. Error: {e}\nOutput was:\n{output}"
        )

    return metadata

# ===== Process all PDFs in a single workbook =====
def process_workbook(workbook_folder):
    """Extract metadata for all PDFs in a given workbook folder."""
    workbook_name = os.path.basename(workbook_folder.rstrip("/"))
    dashboards_data = []

    for file_name in os.listdir(workbook_folder):
        if file_name.lower().endswith(".pdf"):
            file_path = os.path.join(workbook_folder, file_name)
            dashboard_name = os.path.splitext(file_name)[0]
            dashboard_id = f"{workbook_name}_{dashboard_name}".replace(" ", "_").lower()

            pdf_text = read_pdf(file_path)

            metadata = extract_dashboard_metadata(
                pdf_text,
                dashboard_id=dashboard_id,
                dashboard_name=dashboard_name,
                workbook_name=workbook_name,
                file_name=file_name
            )

            dashboards_data.append(metadata)

    return dashboards_data

# ===== Process ALL workbooks in the PDFs directory =====
def process_all_workbooks(pdfs_dir):
    """
    Loop through all subfolders in `pdfs/` and extract combined metadata.
    Returns a single list containing all dashboards from all workbooks.
    """
    all_dashboards = []
    for workbook_name in os.listdir(pdfs_dir):
        folder_path = os.path.join(pdfs_dir, workbook_name)
        if os.path.isdir(folder_path):
            dashboards = process_workbook(folder_path)
            all_dashboards.extend(dashboards)
    return all_dashboards

# ===== Main (for standalone testing) =====
if __name__ == "__main__":
    # Example: Process all at once
    pdfs_dir = "pdfs"
    dashboards = process_all_workbooks(pdfs_dir)
    output_file = os.path.join(pdfs_dir, "dashboards.json")
    with open(output_file, "w") as f:
        json.dump(dashboards, f, indent=2)
    print(f" Combined metadata for ALL workbooks saved to {output_file}")
