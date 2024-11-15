# Conversational agent with RAG
#
#from openai import OpenAI
import asyncio
from openai import AsyncOpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import streamlit as st

template_1 = """
    Act as a techinal expert. Answer the question based only on the following context:
    {context}.
    Question: {question}
    """
    # Point to the local server
client = AsyncOpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")
prompt = ChatPromptTemplate.from_template(template_1)

@st.cache_resource
def prepareDB():
    markdown_path = "./knowledgebase/"
    markdown_loader = DirectoryLoader(markdown_path, glob='./*.md', loader_cls=UnstructuredMarkdownLoader)
    markdown_docs = markdown_loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=30)
    docs = text_splitter.split_documents(markdown_docs)

    # Generate the embeddings
    model="sentence-transformers/all-MiniLM-L12-v2"
    embeddings = HuggingFaceEmbeddings(model_name=model)
    vector_db= Chroma.from_documents(documents=docs,embedding=embeddings,persist_directory="./chroma_db")
    return vector_db

async def main():
    vector_db=prepareDB()
    #embedding_function=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    #vector_db = Chroma(documents=docs ,persist_directory="./chroma_db_nccn", embedding_function=embedding_function)
    history = [
        {"role": "assistant", "content": "Ask questions for PowerLogic HU280 RTU"},
        ]
    if "history" not in st.session_state:
        st.session_state.history=history
    else:
        history=st.session_state.history      

    for history in st.session_state.history:
        with st.chat_message(history["role"]):
            st.markdown(history["content"])

    new_message = {"role": "assistant", "content": ""}
    
    print()
    # next_input = input("> ")
    print("> ")
    if my_prompt := st.chat_input("Escribe tu mensaje..."):
        st.chat_message("user").markdown(my_prompt)
        st.session_state.history.append({"role": "user", "content": my_prompt})

        print(my_prompt)
        
        search_results = vector_db.similarity_search(my_prompt, k=3)
        some_context = ""
        for result in search_results:
            some_context += result.page_content + "\n\n"    
        
        prompt_value = template_1.format(context=some_context,question=my_prompt)
        completion = await client.chat.completions.create(
        model="local-model",
        messages=[{"role": "user", "content": prompt_value}],
        temperature=0.7,
        stream=True,
        )
        new_message = {"role": "assistant", "content": ""}
        async for chunk in completion:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="")
                respuesta=chunk.choices[0].delta.content
                new_message["content"] += chunk.choices[0].delta.content 
        if new_message["content"]!="":   
            st.chat_message("assistant").markdown(new_message["content"])
            st.session_state.history.append({"role": "assistant", "content": new_message["content"]})

if __name__ == "__main__":
    asyncio.run(main())