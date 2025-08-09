# 📊 Tableau Dashboard Search with FAISS & Google Embeddings

This Streamlit app allows you to **search Tableau dashboards** using **semantic similarity**.  
It uses **Google Generative AI embeddings** and stores them in a **FAISS index** for fast and accurate retrieval.

---

## 🚀 Features
- **Embedding Generation**: Converts dashboard metadata into vector embeddings.
- **FAISS Search**: Performs similarity search to find the most relevant dashboards.
- **Interactive UI**: Built with Streamlit for easy use.
- **Supports Metadata Search**: Matches across dashboard names, tags, and descriptions.

---

## 📂 Project Structure

project/
│
├── app.py # Main Streamlit application
├── dashboards.json # Metadata of dashboards
├── embeddings/ # Stores FAISS index and metadata
│ ├── dashboards.index
│ ├── metadata.json
├── .env # Contains Google API key
├── requirements.txt # Python dependencies
└── README.md # Documentation


---

## 🛠️ Installation

1️⃣ **Clone the repository**
```bash
git clone https://github.com/pratish7991/TablueMeta.git
cd TablueMeta

2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate     # Mac/Linux
venv\Scripts\activate        # Windows

3️⃣ Install dependencies
pip install -r requirements.txt

4️⃣ Set up .env file
GOOGLE_API_KEY=your_google_api_key_here

5️⃣ Create dashboards.json
  {
    "id": "dashboard_001",
    "name": "Customer Churn Overview",
    "description": "Shows churn trends, retention rates, and customer lifecycle across regions and segments.",
    "tags": ["churn", "retention", "customers", "lifecycle"],
    "url": "https://tableau.company.com/views/churn",
    "kpis": [
      {
        "name": "Monthly Churn Rate",
        "description": "Percentage of customers lost in a month compared to total active customers."
      },
      {
        "name": "Retention Rate",
        "description": "Percentage of customers retained over a given time period."
      },
      {
        "name": "Average Customer Lifespan",
        "description": "Average duration a customer stays active before churn."
      },
      {
        "name": "Net Promoter Score (NPS)",
        "description": "Measures customer satisfaction and likelihood to recommend the product."
      }
    ]
  }


▶️ Running the Application
streamlit run app.py


📥 How to Use
1. Generate Embeddings
Go to the "📥 Generate Embeddings" tab.
Click "Generate Embeddings".
The system will process all dashboards in dashboards.json and store them in FAISS.

2. Search Dashboards
Go to the "🔍 Search Dashboards" tab.
Enter a query in natural language (e.g., "Show me dashboards about customer retention").
Select the number of top results.
Click "Search" to view matching dashboards.

🔍 Example Queries
Here are some example search queries you can try:

"Quarterly sales performance"
"Dashboards for revenue analysis"
"Customer churn and retention insights"
"Marketing campaign analysis"
"KPI overview for executives"

📦 Dependencies
streamlit
numpy
faiss-cpu
python-dotenv
google-generativeai

Install them with:
pip install -r requirements.txt

