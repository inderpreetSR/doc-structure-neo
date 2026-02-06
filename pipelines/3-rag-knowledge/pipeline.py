"""
Pipeline 3: RAG-Based Knowledge Base
Embeds codebase into a vector store for natural-language querying.
Requirements: pip install chromadb openai tiktoken
Run: python pipeline.py --source ./your-project [--query "How does X work?"]
"""

import os
import json
import hashlib
import argparse
import textwrap
from pathlib import Path
from datetime import datetime


class CodeChunker:
    """Split source files into meaningful chunks."""

    def __init__(self, max_chunk_size=1500):
        self.max_chunk_size = max_chunk_size

    def chunk_file(self, filepath):
        """Chunk a file by functions/classes or by line groups."""
        source = filepath.read_text(encoding='utf-8', errors='ignore')
        lines = source.splitlines()
        if not lines:
            return []

        chunks = []
        current_chunk = []
        current_size = 0

        for line in lines:
            current_chunk.append(line)
            current_size += len(line)

            if (current_size >= self.max_chunk_size and
                (line.strip() == '' or
                 line.startswith('def ') or
                 line.startswith('class ') or
                 line.startswith('function ') or
                 line.startswith('export '))):
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0

        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        return chunks


class VectorStore:
    """Manage embeddings in ChromaDB or in-memory fallback."""

    def __init__(self, db_path='./chroma_db', collection_name='codebase'):
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.available = True
            print("[store]  Using ChromaDB vector store")
        except ImportError:
            print("[store]  ChromaDB not installed, using in-memory keyword search")
            self.available = False
            self.memory_store = []

    def add_chunks(self, chunks, metadatas, ids):
        """Add chunks to the vector store."""
        if self.available:
            # ChromaDB has batch size limits
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                self.collection.upsert(
                    documents=chunks[i:i+batch_size],
                    metadatas=metadatas[i:i+batch_size],
                    ids=ids[i:i+batch_size]
                )
        else:
            for chunk, meta, id_ in zip(chunks, metadatas, ids):
                self.memory_store.append({
                    'id': id_, 'text': chunk, 'metadata': meta
                })

    def query(self, question, n_results=5):
        """Query the vector store for relevant chunks."""
        if self.available:
            results = self.collection.query(
                query_texts=[question],
                n_results=n_results
            )
            return results
        else:
            # Keyword matching fallback
            words = question.lower().split()
            scored = []
            for item in self.memory_store:
                text_lower = item['text'].lower()
                score = sum(1 for w in words if w in text_lower)
                if score > 0:
                    scored.append((score, item))
            scored.sort(key=lambda x: -x[0])
            top = scored[:n_results]
            return {
                'documents': [[s[1]['text'] for s in top]],
                'metadatas': [[s[1]['metadata'] for s in top]]
            }

    def count(self):
        """Return the number of items in the store."""
        if self.available:
            return self.collection.count()
        return len(self.memory_store)


class RAGDocPipeline:
    """Full RAG pipeline for codebase documentation."""

    SUPPORTED_EXTENSIONS = ('.py', '.js', '.ts', '.jsx', '.tsx', '.md', '.yaml', '.yml', '.json')
    IGNORE_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.tox', 'dist', 'build'}

    def __init__(self, source_dir, db_path='./chroma_db'):
        self.source_dir = Path(source_dir)
        self.chunker = CodeChunker()
        self.store = VectorStore(db_path)

    def _should_skip(self, filepath):
        """Check if file should be skipped."""
        parts = filepath.parts
        return any(d in parts for d in self.IGNORE_DIRS)

    def ingest(self):
        """Ingest all source files into the vector store."""
        files = []
        for ext in self.SUPPORTED_EXTENSIONS:
            files.extend(self.source_dir.rglob(f'*{ext}'))

        total_chunks = 0
        ingested_files = 0

        for filepath in sorted(files):
            if self._should_skip(filepath):
                continue

            rel = str(filepath.relative_to(self.source_dir))
            chunks = self.chunker.chunk_file(filepath)
            if not chunks:
                continue

            ids = [hashlib.md5(f"{rel}:{i}".encode()).hexdigest()
                   for i in range(len(chunks))]
            metadatas = [{
                'source': rel,
                'chunk_index': i,
                'language': filepath.suffix.lstrip('.'),
                'timestamp': datetime.now().isoformat()
            } for i in range(len(chunks))]

            self.store.add_chunks(chunks, metadatas, ids)
            total_chunks += len(chunks)
            ingested_files += 1
            print(f"[ingest] {rel} -> {len(chunks)} chunks")

        print(f"\n[done]   Ingested {total_chunks} chunks from {ingested_files} files")
        print(f"[done]   Vector store: {self.store.count()} total entries")

    def query(self, question, n_results=5):
        """Query the knowledge base and generate an answer."""
        results = self.store.query(question, n_results)
        context_parts = []
        sources = []

        if results['documents'] and results['documents'][0]:
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                context_parts.append(doc)
                sources.append(meta.get('source', 'unknown'))

        context = '\n\n---\n\n'.join(context_parts) if context_parts else 'No relevant context found.'

        llm_prompt = textwrap.dedent(f"""
        Based on the following code context, answer the question.
        Be specific and reference file paths and function names.

        CONTEXT:
        {context}

        QUESTION: {question}

        Provide a clear, detailed answer with code references.
        """).strip()

        return {
            'question': question,
            'context_chunks': len(context_parts),
            'sources': list(set(sources)),
            'llm_prompt': llm_prompt,
            'answer': (f"[Found {len(context_parts)} relevant chunks "
                       f"from: {', '.join(set(sources)) if sources else 'none'}]")
        }

    def interactive_mode(self):
        """Run an interactive query loop."""
        print("\n[query]  Interactive mode. Type 'quit' to exit.\n")
        while True:
            try:
                question = input("Question> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if question.lower() in ('quit', 'exit', 'q'):
                break
            if not question:
                continue
            result = self.query(question)
            print(f"\nSources: {', '.join(result['sources'])}")
            print(f"Chunks:  {result['context_chunks']}")
            print(f"Answer:  {result['answer']}\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RAG Documentation Pipeline')
    parser.add_argument('--source', required=True, help='Source directory to ingest')
    parser.add_argument('--query', help='Question to ask (skip for ingest-only)')
    parser.add_argument('--interactive', action='store_true', help='Interactive query mode')
    parser.add_argument('--db', default='./chroma_db', help='ChromaDB storage path')
    args = parser.parse_args()

    pipeline = RAGDocPipeline(args.source, args.db)
    pipeline.ingest()

    if args.interactive:
        pipeline.interactive_mode()
    elif args.query:
        result = pipeline.query(args.query)
        print(f"\nQuestion: {result['question']}")
        print(f"Sources:  {', '.join(result['sources'])}")
        print(f"Answer:   {result['answer']}")
