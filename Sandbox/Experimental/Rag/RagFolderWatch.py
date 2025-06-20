import os
import time
from threading import Thread, Event
from ollama._client import Client
from sentence_transformers import SentenceTransformer, util
import numpy as np

# Step 1: Initialize Ollama client and embedding model
client = Client()
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Folder to monitor for RAG updates
RAG_FOLDER = r"C:\Users\cicai\PythonStuff\RAG"
os.makedirs(RAG_FOLDER, exist_ok=True)  # Ensure folder exists

# Global variables
doc_embeddings = []
documents = []
chat_disabled = Event()  # Event flag to disable/enable chat

# Step 2: Function to load and encode all documents
def load_documents(folder):
    global doc_embeddings, documents
    documents = []
    for file_name in os.listdir(folder):
        file_path = os.path.join(folder, file_name)
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                documents.append(f.read())
    doc_embeddings = embedding_model.encode(documents, convert_to_tensor=True)

# Step 3: Function to monitor folder for changes
def monitor_folder():
    print("Monitoring folder for changes...")
    seen_files = set(os.listdir(RAG_FOLDER))
    while True:
        current_files = set(os.listdir(RAG_FOLDER))
        if current_files != seen_files:
            chat_disabled.set()  # Disable chat
            print("\nUpdating RAG... Please wait.")
            load_documents(RAG_FOLDER)  # Update RAG
            seen_files = current_files
            print("RAG update complete. Chat is now enabled.\n")
            chat_disabled.clear()  # Enable chat
        time.sleep(1)

# Step 4: Function to retrieve relevant context
def retrieve_context(query, doc_embeddings, documents, top_k=2):
    query_embedding = embedding_model.encode(query, convert_to_tensor=True)
    scores = util.cos_sim(query_embedding, doc_embeddings)[0]
    top_results = scores.topk(k=top_k)
    return "\n".join([documents[idx] for idx in top_results.indices])

# Step 5: Chat with RAG
def chat_with_rag():
    model_name = "mxbai"
    print(f"Chatting with model: {model_name}")
    print("Type 'exit' to end the chat.\n")

    while True:
        user_query = input("You: ")
        if user_query.lower() == "exit":
            print("Chat ended.")
            break

        # Wait if chat is disabled (e.g., during RAG update)
        if chat_disabled.is_set():
            print("Chat is disabled. Please wait for RAG update to complete...")
            continue

        # Retrieve context and send to the model
        context = retrieve_context(user_query, doc_embeddings, documents)
        print(f"Retrieved Context:\n{context}\n")

        prompt = f"Context: {context}\n\nQuestion: {user_query}\n\nAnswer:"
        try:
            response = client.chat(model=model_name, messages=[{"role": "user", "content": prompt}])
            print(f"mxbai: {response.message.content}")
        except Exception as e:
            print(f"An error occurred: {e}")
            break

# Step 6: Main function
if __name__ == "__main__":
    # Load initial documents
    load_documents(RAG_FOLDER)

    # Start folder monitoring in a separate thread
    folder_monitor_thread = Thread(target=monitor_folder, daemon=True)
    folder_monitor_thread.start()

    # Start chat interface
    chat_with_rag()
