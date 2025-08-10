import os
import json
import faiss
import numpy as np
import streamlit as st
from dotenv import load_dotenv
from google import genai
from extract_metadata_from_pdf_llm import process_workbook

# ===== CONFIG =====
EMBEDDINGS_DIR = "embeddings"
PDFS_DIR = "pdfs"

os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

# ===== LOAD API KEY =====
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    st.error("GOOGLE_API_KEY missing in .env file")
    st.stop()

client = genai.Client(api_key=API_KEY)

# ===== EMBEDDING FUNCTION =====
def get_embedding(text: str):
    result = client.models.embed_content(
        model="models/embedding-001",
        contents=text
    )
    return np.array(result.embeddings[0].values, dtype="float32")

# ===== GENERATE EMBEDDINGS =====
def generate_embeddings(dashboards, workbook_name):
    texts = []
    for d in dashboards:
        kpi_texts = [f"{kpi['name']} - {kpi['description']}" for kpi in d.get("kpis", [])]
        combined_text = f"{d['name']} - {' '.join(d['tags'])} - {d['description']} - {' '.join(kpi_texts)}"
        texts.append(combined_text)

    first_emb = get_embedding(texts[0])
    dim = len(first_emb)

    index = faiss.IndexFlatL2(dim)
    metadata = []

    for d, text in zip(dashboards, texts):
        emb = get_embedding(text)
        index.add(np.array([emb]))
        metadata.append(d)

    emb_dir = os.path.join(EMBEDDINGS_DIR, workbook_name)
    os.makedirs(emb_dir, exist_ok=True)

    faiss.write_index(index, os.path.join(emb_dir, "dashboards.index"))
    with open(os.path.join(emb_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    return True

# ===== SEARCH FUNCTION =====
def search_dashboards(query, top_k, workbook_name):
    emb_dir = os.path.join(EMBEDDINGS_DIR, workbook_name)
    index_path = os.path.join(emb_dir, "dashboards.index")
    metadata_path = os.path.join(emb_dir, "metadata.json")

    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        st.error("Please generate embeddings first for this workbook.")
        return []

    index = faiss.read_index(index_path)
    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    query_emb = get_embedding(query)
    distances, indices = index.search(np.array([query_emb]), top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < len(metadata):
            results.append((metadata[idx], dist))

    results.sort(key=lambda x: x[1])
    return results

# ===== STREAMLIT UI =====
st.set_page_config(page_title="Tableau Dashboard Search", layout="centered")

# Dropdown to select workbook + "All at Once"
if not os.path.exists(PDFS_DIR):
    st.error(f"No '{PDFS_DIR}' directory found.")
    st.stop()

workbooks = [f for f in os.listdir(PDFS_DIR) if os.path.isdir(os.path.join(PDFS_DIR, f))]
workbooks.insert(0, "All at Once")  # Add special option
if not workbooks:
    st.error("No workbooks found in pdfs/ folder.")
    st.stop()

selected_workbook = st.selectbox("Select a workbook:", workbooks)

# Set dashboards.json path depending on selection
if selected_workbook == "All at Once":
    dashboards_file = os.path.join(PDFS_DIR, "dashboards.json")
else:
    dashboards_file = os.path.join(PDFS_DIR, selected_workbook, "dashboards.json")

tab1, tab2, tab3 = st.tabs(["Create Metadata", "Generate Embeddings", "Search Dashboards"])

# ===== CREATE METADATA TAB =====
with tab1:
    st.header(f"Create Metadata for '{selected_workbook}'")
    if st.button("Create Metadata"):
        with st.spinner("Extracting metadata from PDFs..."):
            if selected_workbook == "All at Once":
                all_dashboards = []
                for wb in [w for w in os.listdir(PDFS_DIR) if os.path.isdir(os.path.join(PDFS_DIR, w))]:
                    dashboards = process_workbook(os.path.join(PDFS_DIR, wb))
                    all_dashboards.extend(dashboards)
                with open(dashboards_file, "w") as f:
                    json.dump(all_dashboards, f, indent=2)
                st.success(f"Combined metadata for ALL workbooks saved to {dashboards_file}")
            else:
                dashboards = process_workbook(os.path.join(PDFS_DIR, selected_workbook))
                with open(dashboards_file, "w") as f:
                    json.dump(dashboards, f, indent=2)
                st.success(f"Metadata created and saved to {dashboards_file}")

# ===== GENERATE EMBEDDINGS TAB =====
with tab2:
    st.header(f"Generate and Store Embeddings for '{selected_workbook}'")
    if not os.path.exists(dashboards_file):
        st.warning("No dashboards.json found. Please create metadata first.")
    elif st.button("Generate Embeddings"):
        with st.spinner("Generating embeddings..."):
            with open(dashboards_file, "r") as f:
                dashboards = json.load(f)
            success = generate_embeddings(dashboards, selected_workbook.replace(" ", "_"))
        if success:
            st.success(f"Embeddings generated for '{selected_workbook}' successfully.")

# ===== SEARCH TAB =====
with tab3:
    st.header(f"Search Dashboards in '{selected_workbook}'")
    query = st.text_input("Enter search query")
    top_k = st.number_input("Number of top results", min_value=1, max_value=20, value=3, step=1)
    if st.button("Search"):
        if query.strip():
            with st.spinner("Searching..."):
                results = search_dashboards(query, top_k, selected_workbook.replace(" ", "_"))
            if results:
                st.subheader("Results")
                for meta, dist in results:
                    st.markdown(f"""
                        **[{meta['name']}]({meta['url']})**  
                        {meta['description']}  
                        Tags: {', '.join(meta['tags'])}  
                        **KPIs:**  
                        {"".join([f"- {k['name']}: {k['description']}  \n" for k in meta.get('kpis', [])])}
                        Distance: {dist:.4f}
                    """)
            else:
                st.warning("No results found.")
