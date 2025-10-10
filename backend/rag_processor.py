import os
import sqlite3
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document

class RAGProcessor:
    def __init__(self, db_path='health_dongA.db', index_path='faiss_index'):
        self.db_path = db_path
        self.index_path = index_path
        self.embeddings = OpenAIEmbeddings(api_key=os.environ.get("OPENAI_API_KEY"))

    def _load_articles_from_db(self):
        """Loads all articles from the SQLite database."""
        if not os.path.exists(self.db_path):
            print(f"Database file not found at {self.db_path}")
            return []
        
        conn = sqlite3.connect(self.db_path)
        # Load articles and generated_articles, preferring the generated one if it exists.
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
        
        print(f"Loaded {len(df)} articles from the database.")
        return df

    def build_and_save_vector_store(self):
        """Builds the FAISS vector store from articles and saves it locally."""
        articles_df = self._load_articles_from_db()
        if articles_df.empty:
            print("No articles found to build the vector store.")
            return

        # Convert DataFrame rows to LangChain Document objects
        documents = [
            Document(
                page_content=row['content'],
                metadata={'title': row['title'], 'article_id': row['article_id']}
            ) for index, row in articles_df.iterrows()
        ]

        # Split documents into smaller chunks
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        doc_chunks = text_splitter.split_documents(documents)
        
        print(f"Created {len(doc_chunks)} document chunks.")

        # Create the FAISS vector store from the document chunks
        print("Building FAISS vector store... This may take a moment.")
        vector_store = FAISS.from_documents(doc_chunks, self.embeddings)
        
        # Save the vector store locally
        vector_store.save_local(self.index_path)
        print(f"Vector store saved successfully to {self.index_path}")

    def load_vector_store(self):
        """Loads the FAISS vector store from a local path."""
        if not os.path.exists(self.index_path):
            print(f"Vector store index not found at {self.index_path}. Building a new one.")
            self.build_and_save_vector_store()
        
        print(f"Loading vector store from {self.index_path}...")
        return FAISS.load_local(self.index_path, self.embeddings, allow_dangerous_deserialization=True)

if __name__ == '__main__':
    # This allows running the script directly to build the index
    processor = RAGProcessor()
    processor.build_and_save_vector_store()
