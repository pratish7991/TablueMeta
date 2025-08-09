import os
import json
import faiss
import numpy as np
import streamlit as st
from dotenv import load_dotenv
from google import genai

# ====== CONFIG ======
EMBEDDINGS_DIR = "embeddings"
DASHBOARDS_FILE = "dashboards.json"

# Create folder for embeddings if it doesn't exist
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

# ====== LOAD API KEY ======
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    st.error("GOOGLE_API_KEY missing in .env file")
    st.stop()

client = genai.Client(api_key=API_KEY)

# ====== LOAD DASHBOARD METADATA ======
if not os.path.exists(DASHBOARDS_FILE):
    st.error(f"{DASHBOARDS_FILE} not found. Please create it with dashboard metadata.")
    st.stop()

with open(DASHBOARDS_FILE, "r") as f:
    dashboards = json.load(f)

# ====== EMBEDDING FUNCTION ======
def get_embedding(text: str):
    result = client.models.embed_content(
        model="models/embedding-001",
        contents=text
    )
    return np.array(result.embeddings[0].values, dtype="float32")

# ====== GENERATE EMBEDDINGS ======
def generate_embeddings():
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

    faiss.write_index(index, os.path.join(EMBEDDINGS_DIR, "dashboards.index"))
    with open(os.path.join(EMBEDDINGS_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    return True

# ====== SEARCH FUNCTION ======
def search_dashboards(query, top_k=3):
    index_path = os.path.join(EMBEDDINGS_DIR, "dashboards.index")
    metadata_path = os.path.join(EMBEDDINGS_DIR, "metadata.json")

    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        st.error("Please generate embeddings first.")
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

# ====== STREAMLIT UI ======
st.set_page_config(page_title="Tableau Dashboard Search", layout="centered")

tab1, tab2 = st.tabs(["Generate Embeddings", "Search Dashboards"])

with tab1:
    st.header("Generate and Store Embeddings")
    if st.button("Generate Embeddings"):
        with st.spinner("Generating embeddings..."):
            success = generate_embeddings()
        if success:
            st.success("Embeddings generated and stored successfully.")

with tab2:
    st.header("Search Dashboards")
    query = st.text_input("Enter search query (dashboard name, description, KPI name, KPI description, etc.)")
    top_k = st.number_input("Number of top results to return", min_value=1, max_value=20, value=3, step=1)
    if st.button("Search"):
        if query.strip():
            with st.spinner("Searching..."):
                results = search_dashboards(query, top_k=top_k)
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
