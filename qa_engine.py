# qa_engine.py
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings

# --- MODULAR IMPORTS ---
from langchain_core.documents import Document 
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- ADDED FOR MANUAL TEXT SPLITTING ---
from langchain_text_splitters import RecursiveCharacterTextSplitter 

from config import GROQ_API_KEY, MODEL_NAME, EMBEDDING_MODEL, VECTOR_DB_PATH
from gmail_fetcher import GmailFetcher 


# Defining the prompt for summarizing each individual chunk (MAP step)
MAP_PROMPT_TEMPLATE = """You are an expert summarizer. Summarize the following text chunk from an email archive in detail, preserving all key names, dates, and action items.

TEXT CHUNK:
---
{text}
---

CONCISE SUMMARY:
"""

# Defining the prompt for combining all summaries into one final output (REDUCE step)
REDUCE_PROMPT_TEMPLATE = """You are an expert email assistant. Combine the following separate summaries from an email archive into one single, unified summary. 
The final summary must be highly organized with bullet points under these headings. Be comprehensive:
1. Main Topics Discussed
2. Key Action Items
3. Senders and Dates

SEPARATE SUMMARIES:
---
{text}
---

UNIFIED SUMMARY:
"""

class QAEngine:
    """Manages the LangChain setup for summarizing fetched emails using stable LCEL components."""

    def __init__(self):
        # Initialize LLM with slightly lower temperature for factual summary
        self.llm = ChatGroq(temperature=0.1, groq_api_key=GROQ_API_KEY, model_name=MODEL_NAME)
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL) # Kept for consistency
        self.vectorstore = None
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=10000, # Chunk size suitable for most emails
            chunk_overlap=100 
        )
        self._email_chunks = []
        
        # Define the LCEL chains once
        map_prompt = ChatPromptTemplate.from_template(MAP_PROMPT_TEMPLATE)
        reduce_prompt = ChatPromptTemplate.from_template(REDUCE_PROMPT_TEMPLATE)

        # 1. Map Chain (Summarize one chunk)
        self._map_chain = (
            {"text": RunnablePassthrough()} 
            | map_prompt
            | self.llm
            | StrOutputParser()
        )

        # 2. Reduce Chain (Summarize all map outputs)
        self._reduce_chain = (
            {"text": RunnablePassthrough()} 
            | reduce_prompt
            | self.llm
            | StrOutputParser()
        )


    def _create_and_split_documents(self, emails: list[dict]) -> list[Document]:
        """Converts raw emails into documents and splits them into smaller chunks."""
        documents = []
        for email in emails:
            # Format the entire email content
            email_text = GmailFetcher.format_email_for_langchain(email)
            # Create a document for each email
            doc = Document(page_content=email_text)
            documents.append(doc)

        # Split all documents into chunks to prevent token limit errors
        all_chunks = self.text_splitter.split_documents(documents)
        return all_chunks


    def setup_summarization_chain(self, emails: list[dict]):
        """Sets up the documents and chunks needed for the two-step LCEL summarization."""
        
        # 1. Split the fetched emails into manageable chunks
        self._email_chunks = self._create_and_split_documents(emails)
        
        if not self._email_chunks:
            # This is a good place to catch cases where emails were too short or empty
            raise ValueError("No valid text chunks could be created for summarization.")
        
        print(f"✅ Summarization prepared. Total chunks created: {len(self._email_chunks)}")


    def get_summary(self) -> dict:
        """Generates a summary using the Map-Reduce pattern manually with LCEL."""
        
        if not self._email_chunks:
             return {"summary": "Error: Run setup_summarization_chain first."}

        # --- 1. MAP STEP: Summarize Each Chunk ---
        intermediate_summaries = []
        
        # We iterate over the chunks and call the LLM for each one (the "Map" process)
        for i, chunk in enumerate(self._email_chunks):
            # The map chain takes the chunk content (the raw text) as input
            try:
                summary = self._map_chain.invoke(chunk.page_content)
                intermediate_summaries.append(summary)
            except Exception as e:
                # Catch LLM/API errors on a per-chunk basis
                print(f"Warning: Failed to summarize chunk {i+1}. Error: {e}")
                intermediate_summaries.append(f"FAILED TO SUMMARIZE CHUNK {i+1}")


        # --- 2. REDUCE STEP: Combine Summaries into Final Output ---
        combined_summaries_text = "\n\n---\n\n".join(intermediate_summaries)
        
        # The reduce chain takes the list of intermediate summaries as input
        final_summary = self._reduce_chain.invoke(combined_summaries_text)
        
        # Return a dictionary with the final summary
        return {"summary": final_summary}