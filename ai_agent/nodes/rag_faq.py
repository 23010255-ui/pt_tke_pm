"""
RAG FAQ Node: Tái sử dụng ChromaDB từ chatbot_system để trả lời câu hỏi chung.
"""
import os
from google import genai
from langchain_core.messages import AIMessage
from ai_agent.state import BookingState
from ai_agent.prompts import FAQ_PROMPT

# Đường dẫn tới vectorstore đã build
VECTORSTORE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'chatbot_system', 'vectorstore')


def rag_faq_node(state: BookingState) -> dict:
    """
    Tìm kiếm ngữ cảnh trong ChromaDB rồi gọi LLM trả lời câu hỏi FAQ.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    last_message = state["messages"][-1].content
    context = ""

    # Tái sử dụng ChromaDB từ chatbot_system nếu tồn tại
    try:
        import sys
        chatbot_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'chatbot_system')
        sys.path.insert(0, chatbot_dir)
        from build_vector_db import GenAIEmbeddings
        from langchain_chroma import Chroma

        embeddings = GenAIEmbeddings(api_key=api_key)
        vectorstore = Chroma(
            persist_directory=VECTORSTORE_DIR,
            embedding_function=embeddings
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        docs = retriever.invoke(last_message)
        context = "\n\n".join([doc.page_content for doc in docs])
    except Exception:
        context = "Không thể truy cập cơ sở dữ liệu kiến thức. Vui lòng trả lời dựa trên hiểu biết chung."

    prompt = FAQ_PROMPT.format(context=context)
    full_prompt = f"{prompt}\n\nCâu hỏi: {last_message}"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt
    )

    return {"messages": [AIMessage(content=response.text)]}
