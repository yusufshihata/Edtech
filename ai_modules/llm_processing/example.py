from langchain.llms import HuggingFacePipeline
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# Step 1: Load LLM
model_name = "distilbert/distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
hf_pipeline = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_length=200,
    num_beams=4,
    no_repeat_ngram_size=2,
    device=-1
)
llm = HuggingFacePipeline(pipeline=hf_pipeline)

# Step 2: Prepare documents
documents = [
    Document(page_content="The capital of France is Paris. It is known for the Eiffel Tower."),
    Document(page_content="Italy's capital is Rome, famous for the Colosseum."),
    Document(page_content="Japan's capital is Tokyo, a hub for technology and culture.")
]

# Step 3: Create vector store
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = FAISS.from_documents(documents, embeddings)

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
response = rag_chain.run(query)
print(response)
