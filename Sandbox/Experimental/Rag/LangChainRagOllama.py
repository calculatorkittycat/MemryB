from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import ollama

# Step 1: Load documents from a folder
loader = DirectoryLoader(
    r'C:\Users\cicai\PythonStuff\RAG',
    glob="./*.pdf",
    loader_cls=PyPDFLoader
)
docs = loader.load()

# Step 2: Split documents into manageable chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
texts = text_splitter.split_documents(docs)

# Step 3: Generate embeddings for the text chunks
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Step 4: Create a vector database
db = Chroma.from_documents(
    documents=texts,
    embedding=embeddings,
    collection_name="my_collection"  # optional
)

# Step 5: Perform a query and use Ollama for response generation
query = "What is supervised machine learning?"
results = db.similarity_search(query, k=3)  # returns the top-3 most relevant docs

data = "\n".join(doc.page_content for doc in results)

output = ollama.generate(
    model="llama3.2",
    prompt=f"Using this data: {data}. Respond to this prompt: {query}"
)

print(output['response'])
