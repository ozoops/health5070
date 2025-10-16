import os
import sqlite3
import pandas as pd
import logging
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from backend.config import DB_PATH, FAISS_INDEX_DIR

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RAGProcessor:
    def __init__(self, db_path=None, index_path=None):
        logging.info("Initializing RAGProcessor...")
        self.db_path = db_path or DB_PATH
        self.index_path = index_path or FAISS_INDEX_DIR
        
        logging.info(f"Database path: {self.db_path}")
        logging.info(f"FAISS index path: {self.index_path}")

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logging.error("OPENAI_API_KEY environment variable not found!")
            raise ValueError("OPENAI_API_KEY not found")
        else:
            logging.info("OPENAI_API_KEY found.")

        self.embeddings = OpenAIEmbeddings(api_key=api_key)
        logging.info("RAGProcessor initialized successfully.")

    def _load_articles_from_db(self):
        """Loads all articles from the SQLite database."""
        logging.info("Loading articles from the database...")
        if not os.path.exists(self.db_path):
            logging.error(f"Database file not found at {self.db_path}")
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT 
                a.id as article_id,
                COALESCE(ga.generated_title, a.title) as title,
                COALESCE(ga.generated_content, a.content) as content
            FROM articles a
            LEFT JOIN generated_articles ga ON a.id = ga.article_id
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            logging.info(f"Loaded {len(df)} articles from the database.")
            return df
        except Exception as e:
            logging.error(f"Failed to load articles from database: {e}")
            return []

    def build_and_save_vector_store(self):
        """Builds the FAISS vector store from articles and saves it locally."""
        logging.info("Starting to build and save vector store.")
        articles_df = self._load_articles_from_db()
        if articles_df.empty:
            logging.warning("No articles found to build the vector store. Aborting.")
            return

        documents = [
            Document(
                page_content=row['content'],
                metadata={'title': row['title'], 'article_id': row['article_id']}
            ) for index, row in articles_df.iterrows()
        ]
        logging.info(f"Converted {len(documents)} articles to LangChain documents.")

        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        doc_chunks = text_splitter.split_documents(documents)
        logging.info(f"Split documents into {len(doc_chunks)} chunks.")

        logging.info("Building FAISS vector store from document chunks... This may take a while.")
        try:
            vector_store = FAISS.from_documents(doc_chunks, self.embeddings)
            logging.info("FAISS vector store built successfully.")
        except Exception as e:
            logging.error(f"Failed to build FAISS vector store: {e}")
            raise

        logging.info(f"Saving vector store to {self.index_path}...")
        try:
            vector_store.save_local(self.index_path)
            logging.info(f"Vector store saved successfully to {self.index_path}")
        except Exception as e:
            logging.error(f"Failed to save vector store: {e}")
            raise

    def load_vector_store(self):
        """Loads the FAISS vector store from a local path."""
        logging.info(f"Attempting to load vector store from {self.index_path}.")
        if not os.path.exists(self.index_path):
            logging.warning(f"Vector store index not found at {self.index_path}. Building a new one.")
            self.build_and_save_vector_store()
        
        logging.info(f"Loading vector store from {self.index_path}...")
        try:
            return FAISS.load_local(self.index_path, self.embeddings, allow_dangerous_deserialization=True)
        except Exception as e:
            logging.error(f"Failed to load vector store from {self.index_path}: {e}")
            # If loading fails, maybe the index is corrupt. Try rebuilding.
            logging.warning("Failed to load index, attempting to rebuild.")
            self.build_and_save_vector_store()
            return FAISS.load_local(self.index_path, self.embeddings, allow_dangerous_deserialization=True)

if __name__ == '__main__':
    logging.info("Running rag_processor.py script directly to build the index.")
    processor = RAGProcessor()
    processor.build_and_save_vector_store()
    logging.info("Index build script finished.")
