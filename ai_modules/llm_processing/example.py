import warnings
warnings.filterwarnings("ignore")

from langchain.llms import HuggingFacePipeline
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from web_scrappers.github_scrapper import fetch_github_data

# Step 1: Load LLM
model_name = "distilbert/distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
hf_pipeline = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_length=1024,
    num_beams=4,
    no_repeat_ngram_size=2,
    device=-1
)
llm = HuggingFacePipeline(pipeline=hf_pipeline)

# Prepare the text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=128,
    separators=['\\n', '\n', ' ']
)

# Step 2: Prepare documents
data = fetch_github_data("Databases")

documents = [Document(repo['content'], meta_data=repo.get('url', 'unknown')) for repo in data if repo['content'] != None]


chunked_documents = []
for doc in documents:
    chunks = text_splitter.split_text(doc.page_content)
    for i, chunk in enumerate(chunks):
        chunked_doc = Document(
            page_content = chunk,
            metadata = {**doc.metadata, "chunk_id": i}
        )
        chunked_documents.append(chunked_doc)

# Step 3: Create vector store
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = FAISS.from_documents(chunked_documents, embeddings)

# Step 4: Set up RAG
prompt_template = """Answer this question in one word bitch

Context: {context}

Question: {question}

Answer: """
prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
rag_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vector_store.as_retriever(search_kwargs={"k": 1}),
    chain_type_kwargs={"prompt": prompt}
)

# Step 5: Query
query = "How to learn Databases?"
response = rag_chain.invoke(query)
print(response)
