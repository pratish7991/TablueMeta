#  Tableau Dashboard Metadata Search with FAISS & Google Gemini

This Streamlit application lets you **search Tableau dashboards** using **semantic similarity** across **one or multiple workbooks**.  
It integrates **Google Generative AI embeddings** with **FAISS** for fast search, and uses **Gemini LLM** to automatically extract dashboard metadata (including KPIs) from exported Tableau PDF dashboards.

---

## Features

- **Automatic Metadata Extraction**  
  - Update Tableau dashboard PDFs and extract:
    - Dashboard Name
    - Description
    - Tags
    - KPI names and detailed descriptions (with values in context)
  - Powered by **Gemini 1.5 Flash** LLM.

- **Multiple Workbook Support**  
  - Select a specific workbook to work with.
  - **"All at Once" mode** to process & search across **all dashboards from all workbooks**.

- **Semantic Search with FAISS**  
  - Matches user queries against dashboard names, descriptions, tags, and KPI metadata.
  - Configurable **Top-K results**.

- **Per-Workbook & Global Embeddings**  
  - Generate embeddings per workbook or for all dashboards combined.

- **Interactive Streamlit UI**  
  - Tabs for **Metadata Creation**, **Embedding Generation**, and **Dashboard Search**.
  - Dropdown to select workbook or "All at Once" mode.

---

##  Project Structure

```
project/
│
├── app.py                              # Main Streamlit application
├── extract_metadata_from_pdf_llm.py    # PDF text extraction & Gemini metadata generation
├── pdfs/                               # Stores all workbooks & their PDFs
│   ├── {Woorkbook Name}/
│   │   ├── {Dashboard Name}.pdf
│   │   └── dashboards.json
│
├── embeddings/                         # Stores FAISS index & metadata.json per workbook
│   ├── {Woorkbook Name}/
│   │   ├── dashboards.index
│   │   └── metadata.json
│   └── All/                            # "All at Once" global index
│       ├── dashboards.index
│       └── metadata.json
│
├── .env                                # Contains Google API key
├── requirements.txt                    # Python dependencies
└── README.md
```

---

## 🛠 Installation

1️ **Clone the repository**
```bash
git clone https://github.com/pratish7991/TableauMetaSearch.git
cd TableauMetaSearch
```

2️ **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate     # Mac/Linux
venv\Scriptsctivate        # Windows
```

3️ **Install dependencies**
```bash
pip install -r requirements.txt
```

4️ **Set up `.env` file**
```
GOOGLE_API_KEY=your_google_api_key_here
```

---

##  Running the Application
```bash
streamlit run app.py
```

---

##  How to Use

### 1. **Select a Workbook**
- Dropdown will show all workbooks found in `pdfs/` folder.
- Select a **single workbook** or **All at Once**.

### 2. **Create Metadata**
- Go to **Create Metadata** tab.
- Click **"Create Metadata"** to extract metadata from all PDFs in the selected workbook.
- A `dashboards.json` file will be created inside the selected workbook folder.
- In **All at Once** mode, a combined `dashboards.json` will be created in `pdfs/` containing metadata from all workbooks.

### 3. **Generate Embeddings**
- Go to **Generate Embeddings** tab.
- Click **"Generate Embeddings"** to build FAISS index from metadata.
- Works per-workbook or for all dashboards combined.

### 4. **Search Dashboards**
- Go to **Search Dashboards** tab.
- Enter a search query (dashboard name, KPI name, description, etc.).
- Choose **Top-K results** to return.
- Click **Search** to see matching dashboards.

---

##  Example Queries
```
"Financial advisor performance with assets under management"
"Employee attrition rate and satisfaction analysis"
"Year-over-year retail sales by department"
"October 2022 toy store profit and daily sales"
```

---

##  Dependencies
```
streamlit
numpy
faiss-cpu
python-dotenv
google-generativeai
PyMuPDF
```
Install them with:
```bash
pip install -r requirements.txt
```

---

##  Notes
- **PDF Input**: Tableau dashboards must be exported as **PDFs** (manually via Tableau Public/Desktop or automated via Tableau Server API if available).
- **.twbx Extraction**: Direct `.twbx` parsing is not supported in this app; convert dashboards to PDFs first.
- **Enterprise Integration**: Tableau Server or Tableau Cloud with `tabcmd`/TSC can automate PDF exports, but require a paid license.
