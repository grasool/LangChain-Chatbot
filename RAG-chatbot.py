# Conversational agent with RAG
#
#from openai import OpenAI
from langchain.llms import OpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import streamlit as st

template_1 = """
    Answer the question based only on the following context:
    {context} 
    The answer has to specify the source document used for the answer.
    If you can not answer the question based on the context, answer the question based on your own knowledge but beginning the sentence with "The relevant information is not available in the context, but based on my own knowledge".
    Question: {question}
    """
    # Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")
prompt = ChatPromptTemplate.from_template(template_1)
qa_chain = prompt | client | StrOutputParser()
def main():



    markdown_path = "./knowledgebase/"
    markdown_loader = DirectoryLoader(markdown_path, glob='./*.md', loader_cls=UnstructuredMarkdownLoader)
    markdown_docs = markdown_loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=00)
    docs = text_splitter.split_documents(markdown_docs)

    # Generate the embeddings
    model="sentence-transformers/all-MiniLM-L12-v2"
    embeddings = HuggingFaceEmbeddings(model_name=model)
    vector_db= Chroma.from_documents(documents=docs,embedding=embeddings,persist_directory="./chroma_db")

    #embedding_function=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    #vector_db = Chroma(documents=docs ,persist_directory="./chroma_db_nccn", embedding_function=embedding_function)
    history = [
        {"role": "system", "content": "You are an intelligent assistant. You always provide well-reasoned answers that are both correct and helpful."},
        ]
    if "history" not in st.session_state:
        st.session_state.history=history
    else:
        history=st.session_state.history      

    for history in st.session_state.history:
        with st.chat_message(history["role"]):
            st.markdown(history["content"])
    # completion = client.chat.completions.create(
    #     model="local-model",
    #     messages=history,
    #     temperature=0.7,
    #     stream=True,
    # )

    new_message = {"role": "assistant", "content": ""}
    
    # for chunk in completion:
    #     if chunk.choices[0].delta.content:
    #         print(chunk.choices[0].delta.content, end="", flush=True)
    #         new_message["content"] += chunk.choices[0].delta.content

    # history.append(new_message)
    # if(new_message["content"]!=""):
    #     with st.chat_message(new_message["role"]):
    #         st.markdown(new_message["content"])

    
    #Uncomment to see chat history
    # import json
    # gray_color = "\033[90m"
    # reset_color = "\033[0m"
    # print(f"{gray_color}\n{'-'*20} History dump {'-'*20}\n")
    # print(json.dumps(history, indent=2))
    # print(f"\n{'-'*55}\n{reset_color}")
    
    print()
    # next_input = input("> ")
    print("> ")
    if my_prompt := st.chat_input("Escribe tu mensaje..."):
        st.chat_message("user").markdown(my_prompt)
        st.session_state.history.append({"role": "user", "content": my_prompt})

        print(my_prompt)
        search_results = vector_db.similarity_search(my_prompt, k=10)
        some_context = ""
        for result in search_results:
            some_context += result.page_content + "\n\n"    
        #chain = LLMChain(llm=client, prompt=prompt)
        #respuesta = chain.run({"question": my_prompt, "context": some_context})
        respuesta = qa_chain.invoke({"question": my_prompt, "context": some_context})
        print(respuesta)
        respuesta=str(respuesta).replace('\n','\r\n')
        #history.append({"role": "assistant", "content": respuesta})
        st.chat_message("assistant").markdown(respuesta)
        st.session_state.history.append({"role": "assistant", "content": respuesta})
if __name__ == "__main__":
    main()