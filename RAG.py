from langchain import hub
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_community.vectorstores.chroma import Chroma
from langchain_community.llms.ollama import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import chainlit as cl
from langchain.chains import RetrievalQA,RetrievalQAWithSourcesChain

QA_CHAIN_PROMPT = hub.pull("rlm/rag-prompt-mistral")

def load_llm():
 llm = Ollama(
 model="dolphin2.2-mistral"
 verbose=True,
 callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
 )
 return llm


def retrieval_qa_chain(llm,vectorstore):
 qa_chain = RetrievalQA.from_chain_type(
    llm,
    retriever=vectorstore.as_retriever(),
    chain_type_kwargs={"prompt": QA_CHAIN_PROMPT},
    return_source_documents=True,
)
 return qa_chain


def qa_bot(): 
 llm=load_llm() 
 DB_PATH = "vectorstores/db/"
 vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=GPT4AllEmbeddings())

 qa = retrieval_qa_chain(llm,vectorstore)
 return qa 

@cl.on_chat_start
async def start():
 chain=qa_bot()
 msg=cl.Message(content="Firing up the research info bot...")
 await msg.send()
 msg.content= "Hi, welcome to research info bot. What is your query?"
 await msg.update()
 cl.user_session.set("chain",chain)

@cl.on_message
async def main(message):
 chain=cl.user_session.get("chain")
 cb = cl.AsyncLangchainCallbackHandler(
 stream_final_answer=True,
 answer_prefix_tokens=["FINAL", "ANSWER"]
 )
 cb.answer_reached=True
 res=await chain.ainvoke(message.content, callbacks=[cb])
 print(f"response: {res}")
 answer=res["result"]
 answer=answer.replace(".",".\n")
 sources=res["source_documents"]

 if sources:
  answer+=f"\nSources: "+str(str(sources))
 else:
  answer+=f"\nNo Sources found"

 await cl.Message(content=answer).send() 