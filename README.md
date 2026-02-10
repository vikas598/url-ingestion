# Millex URL Ingestor & Scraper

A robust FastAPI-based service designed to scrape, ingest, and process product data from Millex and Shopify stores. This system handles URL validation, raw data extraction, data normalization, and storage.

## 🚀 Features

- **Millex Scraper**: Specialized scraper for Millex products, collections, and homepage.
- **Shopify Integration**: Ingests product data from Shopify stores via JSON endpoints.
- **Data Processing**: Normalizes data into a unified schema (cleaning HTML, standardizing variants/prices).
- **Product Search & Recommendation**: Semantic search capabilities using FAISS vector database to find relevant products based on natural language queries.
- **File Storage**: Saves both raw and processed data in organized JSON files.
- **REST API**: Clean functionality exposed via FastAPI endpoints.

## 🛠️ Prerequisites

- Python 3.8+
- pip (Python package manager)

## 📥 Installation

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone <repository-url>
   cd millex
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirement.txt
   ```

## 🏃‍♂️ How to Run

Start the API server using Uvicorn. Run this command from the root directory:

```bash
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`.

### interactive API Docs
Open your browser and navigate to:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Recommender System
To enable semantic search, you need to generate embeddings for the processed products. Run the following command:

```bash
python -m app.services.recommender_system.embed_products
```

This will ingest processed products, generate embeddings using a pre-trained model, and build a FAISS index in `app/services/recommender_system/vector_store/`.

## 📡 API Endpoints

### Millex Endpoints (`/api/v1/millex`)

| Method | Endpoint | Description | Payload Example |
|--------|----------|-------------|-----------------|
| POST | `/scrape/product` | Scrape a single Millex product. | `{"url": "https://millex.in/products/..."}` |
| POST | `/scrape/collection` | Scrape all products from a collection. | `{"url": "https://millex.in/collections/..."}` |
| POST | `/scrape/homepage` | Scrape all products linked on the homepage. | `{"url": "https://millex.in"}` |

### Shopify Endpoints (`/shopify`)

| Method | Endpoint | Description | Payload Example |
|--------|----------|-------------|-----------------|
| POST | `/store` | Ingest data from a Shopify store. | `{"url": "https://shopifystore.com", "limit_collections": 1}` |

### General Product Endpoint (`/api/v1/product`)

| Method | Endpoint | Description | Payload Example |
|--------|----------|-------------|-----------------|
| POST | `/` | General product ingestion (redirects to specific handlers). | `{"url": "..."}` |

### Search & Recommendation (`/api/v1`)

| Method | Endpoint | Description | Payload Example |
|--------|----------|-------------|-----------------|
| POST | `/search` | Semantic search for products. | `{"query": "summer dress"}` |

## 📂 Project Structure & Functionality

```
millex/
├── app/
│   ├── api/                 # API Route Handlers
│   │   ├── millex.py        # logic for Millex scraping endpoints
│   │   ├── shopify.py       # logic for Shopify store ingestion
│   │   └── product.py       # General product ingestion entry point
│   ├── core/                # Core configurations & error handling
│   ├── models/              # Pydantic models for request validation
│   ├── services/            # Business Logic & Core Services
│   │   ├── scrapers/        # Scraper implementations (Millex vs Shopify)
│   │   ├── recommender_system/ # Search & Embedding logic
│   │   │   ├── embed_products.py # Script to generate FAISS index
│   │   │   ├── search_service.py # Search logic using FAISS
│   │   │   └── vector_store/    # Generated FAISS index & metadata
│   │   ├── processor.py     # Data cleaning & normalization logic
│   │   ├── storage.py       # functionality to save JSON files locally
│   │   └── url_handler.py   # URL parsing and validation helpers
│   └── main.py              # Application entry point & app configuration
├── data/                    # Generated Data
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation
```

### Key Services

- **`processor.py`**: Contains `process_millex_product` and `process_shopify_product`. These functions take raw scraped data, clean HTML descriptions, normalize price/currency, and format variants into a standard list.
- **`storage.py`**: Handles saving data to the `data/` directory. It manages file naming and directory creation ensuring data is organized by source and type (raw vs processed).
- **`url_handler.py`**: Helper utilities to validate URLs and construct Shopify JSON API URLs.

