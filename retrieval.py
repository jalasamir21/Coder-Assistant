import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

STACKEXCHANGE_SEARCH_URL = "https://api.stackexchange.com/2.3/search/excerpts"

_embeddings = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return _embeddings


def search_stackoverflow(query: str, max_results: int = 8) -> list:
    params = {
        "order": "desc",
        "sort": "relevance",
        "q": query,
        "site": "stackoverflow",
    }
    try:
        response = requests.get(STACKEXCHANGE_SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return []

    items = response.json().get("items", [])[:max_results]
    results = []
    for item in items:
        title = item.get("title", "")
        excerpt = item.get("excerpt", "") or item.get("body_excerpt", "")
        question_id = item.get("question_id")
        link = f"https://stackoverflow.com/q/{question_id}" if question_id else ""
        results.append({"title": title, "text": f"{title}\n{excerpt}", "link": link})
    return results


def retrieve_debug_context(query: str, k: int = 3):
    raw_results = search_stackoverflow(query)
    if not raw_results:
        return "", []

    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    documents = []
    for result in raw_results:
        for chunk in splitter.split_text(result["text"]):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={"title": result["title"], "link": result["link"]},
                )
            )

    if not documents:
        return "", []

    vector_store = FAISS.from_documents(documents, get_embeddings())
    top_docs = vector_store.similarity_search(query, k=min(k, len(documents)))

    context_parts = []
    sources = []
    for doc in top_docs:
        context_parts.append(f"Source: {doc.metadata['title']}\n{doc.page_content}")
        source = {"title": doc.metadata["title"], "link": doc.metadata["link"]}
        if source not in sources:
            sources.append(source)

    return "\n\n---\n\n".join(context_parts), sources