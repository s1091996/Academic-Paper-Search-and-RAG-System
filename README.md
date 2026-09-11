# Academic Paper Search and RAG QA System

An academic paper search and question-answering system that combines large language models, OpenAlex, arXiv, and retrieval-augmented generation (RAG) to help researchers discover and analyze relevant research papers.

## Features

* Generate multiple academic search queries based on research requirements.
* Search academic papers through OpenAlex.
* Use a large language model to evaluate whether retrieved papers match the user's research criteria.
* Generate Traditional Chinese summaries for selected papers.
* Automatically retrieve corresponding arXiv papers and download their PDFs.
* Extract and split PDF content into text chunks.
* Build a vector index for semantic retrieval.
* Answer questions based on the content of the selected papers using RAG.

## System Workflow

```text
Research Requirements
        ↓
LLM Query Generation
        ↓
OpenAlex Paper Search
        ↓
LLM Paper Evaluation
        ↓
Selected Papers
        ↓
arXiv ID Retrieval
        ↓
PDF Download
        ↓
Text Extraction & Chunking
        ↓
Vector Index
        ↓
Question
        ↓
Relevant Content Retrieval
        ↓
LLM Answer
```

## Project Structure

```text
.
├── app.py
├── config.py
├── llm.py
├── paper_search.py
├── rag.py
├── utils.py
├── .env
└── README.md
```

### File Description

* `app.py` — Gradio interface and application entry point.
* `config.py` — Centralized configuration settings.
* `llm.py` — LLM API access, search query generation, paper evaluation, and summary generation.
* `paper_search.py` — OpenAlex paper search, paper filtering, and arXiv ID retrieval.
* `rag.py` — PDF processing, text chunking, vector indexing, retrieval, and question answering.
* `utils.py` — Shared utility functions.
* `.env` — Stores the Groq API key locally.

## Technologies

* Python
* Gradio
* Groq API
* OpenAlex
* arXiv
* Sentence Transformers
* FAISS
* PyMuPDF

## Installation

Clone the repository and install the required dependencies:

```bash
pip install gradio groq pyalex requests pymupdf numpy faiss-cpu sentence-transformers python-dotenv
```

Create a `.env` file in the project root:

```text
GROQ_API_KEY=your_api_key
```

## Usage

Run the application:

```bash
python app.py
```

The application provides two main functions:

### 1. Academic Paper Search

Enter the research topic, application domain, keywords, publication year range, and other preferences. The system generates multiple search queries, retrieves papers from OpenAlex, and uses an LLM to evaluate their relevance.

Selected papers are displayed with their publication year, citation count, and Traditional Chinese summaries.

### 2. Paper Question Answering

After selecting papers, build the RAG system. The system downloads available arXiv PDFs, extracts their text, creates vector embeddings, and builds a FAISS index.

Users can then ask questions about the selected papers. Relevant passages are retrieved and provided to the LLM to generate an answer.

## Environment Variables

The following environment variable is required:

```text
GROQ_API_KEY
```

Do not commit `.env` or expose your API key in the repository.

## Notes

The system relies on publicly available metadata from OpenAlex and paper PDFs available through arXiv. Not every OpenAlex paper has a corresponding arXiv version, so some selected papers may be skipped during RAG construction.

The quality of paper selection and question answering depends on the retrieved papers, available PDF content, embedding model, and LLM responses.
