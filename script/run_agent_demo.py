from __future__ import annotations

import sys
from pathlib import Path

# Add src/ to python path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from core.config import load_settings
from retrieval.index import LocalEmbeddingIndex
from retrieval.agent import build_agent, run_agent_question


def main() -> None:
    print("Loading settings...")
    settings = load_settings()
    
    print("Loading Chroma DB persistent store...")
    try:
        index = LocalEmbeddingIndex.load(settings)
    except Exception as e:
        print(f"Error loading Chroma index: {e}")
        print("Please build the database index first by running python3 script/run_phase1.py")
        sys.exit(1)
        
    print(f"Loaded Chroma collection: {index.collection_name} containing {len(index.documents)} documents.")
    
    print("Building agent with tools and local LLM...")
    agent = build_agent(settings, index)
    print("Agent constructed successfully!")
    
    print("\n=== RAG Agent Interactive Session ===")
    print("Ask the agent questions about the indexed documents. Type 'exit' or 'quit' to quit.")
    
    while True:
        try:
            query = input("\nUser: ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit"):
                print("Goodbye!")
                break
            
            print("Agent is thinking...")
            answer = run_agent_question(agent, query)
            print(f"Agent: {answer}")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Agent encountered error: {e}")


if __name__ == "__main__":
    main()
