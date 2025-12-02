"""
Knowledge Base Agent for RAG (Retrieval Augmented Generation).
Allows users to upload documents and query them.
"""
from typing import Optional, Dict, Any, List
import os
import numpy as np
from PyPDF2 import PdfReader
import faiss
from sentence_transformers import SentenceTransformer

from agents.base_agent import BaseAgent
from llm.prompts import KNOWLEDGE_AGENT_PROMPT
from database.db_manager import DatabaseManager


class KnowledgeAgent(BaseAgent):
    """Agent for document-based question answering using RAG."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize Knowledge Agent."""
        super().__init__(
            agent_name="knowledge",
            system_prompt=KNOWLEDGE_AGENT_PROMPT,
            db_manager=db_manager
        )
        # Initialize embedding model (lightweight, runs locally)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.chunks = []
        self.document_name = None
    
    def ingest_document(self, file_path: str, file_name: str) -> str:
        """
        Ingest a PDF document into the knowledge base.
        
        Args:
            file_path: Path to the PDF file
            file_name: Name of the file
            
        Returns:
            Status message
        """
        try:
            # Extract text from PDF
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            # Chunk the text (simple chunking by paragraphs)
            self.chunks = self._chunk_text(text)
            
            if not self.chunks:
                return "❌ Could not extract text from the document."
            
            # Create embeddings
            embeddings = self.embedding_model.encode(self.chunks)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(np.array(embeddings).astype('float32'))
            
            self.document_name = file_name
            
            return f"✅ Successfully ingested **{file_name}** ({len(self.chunks)} chunks)"
        
        except Exception as e:
            return f"❌ Error ingesting document: {str(e)}"
    
    def process(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a knowledge base query.
        
        Args:
            user_id: User ID
            message: User message
            context: Optional context
            
        Returns:
            Answer based on document
        """
        if not self.index or not self.chunks:
            response = "📚 No documents have been uploaded yet. Please upload a PDF to get started."
        else:
            # Retrieve relevant chunks
            relevant_chunks = self._retrieve_relevant_chunks(message, top_k=3)
            
            # Generate response using LLM with retrieved context
            doc_context = f"Document: {self.document_name}\n\nRelevant passages:\n"
            for i, chunk in enumerate(relevant_chunks, 1):
                doc_context += f"\n{i}. {chunk}\n"
            
            response = self.create_response(
                user_id,
                message,
                additional_context=doc_context
            )
        
        # Save conversation
        self.db_manager.add_conversation(
            user_id=user_id,
            agent_type=self.agent_name,
            message=message,
            response=response,
            metadata={'document': self.document_name}
        )
        
        return response
    
    def process_stream(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Process a knowledge base query and stream response."""
        if not self.index or not self.chunks:
            response = "📚 No documents have been uploaded yet. Please upload a PDF to get started."
            yield response
            
            # Save conversation
            self.db_manager.add_conversation(
                user_id=user_id,
                agent_type=self.agent_name,
                message=message,
                response=response,
                metadata={'document': None}
            )
        else:
            # Retrieve relevant chunks
            relevant_chunks = self._retrieve_relevant_chunks(message, top_k=3)
            
            # Generate response using LLM with retrieved context
            doc_context = f"Document: {self.document_name}\n\nRelevant passages:\n"
            for i, chunk in enumerate(relevant_chunks, 1):
                doc_context += f"\n{i}. {chunk}\n"
            
            # Stream response
            full_response = ""
            for chunk in self.create_response_stream(
                user_id,
                message,
                additional_context=doc_context
            ):
                full_response += chunk
                yield chunk
            
            # Save conversation
            self.db_manager.add_conversation(
                user_id=user_id,
                agent_type=self.agent_name,
                message=message,
                response=full_response,
                metadata={'document': self.document_name}
            )
    
    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Chunk text into smaller pieces."""
        # Simple chunking by sentences/paragraphs
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [c for c in chunks if len(c) > 50]  # Filter out very short chunks
    
    def _retrieve_relevant_chunks(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve most relevant chunks for a query."""
        # Encode query
        query_embedding = self.embedding_model.encode([query])
        
        # Search in FAISS index
        distances, indices = self.index.search(
            np.array(query_embedding).astype('float32'),
            top_k
        )
        
        # Return relevant chunks
        return [self.chunks[i] for i in indices[0] if i < len(self.chunks)]
