import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from google import genai
from build_vector_db import GenAIEmbeddings

load_dotenv()

class ProjectChatbot:
    def __init__(self):
        current_dir = os.path.dirname(__file__)
        persist_dir = os.path.join(current_dir, 'vectorstore')
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("Không tìm thấy GEMINI_API_KEY trong file .env")
            
        self.embeddings = GenAIEmbeddings(api_key=api_key)
        self.vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embeddings
        )
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 5}
        )
        self.client = genai.Client(api_key=api_key.strip())

    def ask(self, question):
        # Retrieve relevant documents
        docs = self.retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Build prompt
        prompt = f"""Bạn là một trợ lý AI thông minh, am hiểu về lập trình và kiến trúc phần mềm.
Bạn đang giúp các lập trình viên giải đáp thắc mắc về một dự án phần mềm có sẵn.
Sử dụng thông tin ngữ cảnh được cung cấp dưới đây để trả lời câu hỏi.
Nếu bạn không biết câu trả lời, hãy nói rằng bạn không biết, đừng cố bịa ra câu trả lời.
Luôn trả lời bằng tiếng Việt trừ khi được yêu cầu khác.

--- NGỮ CẢNH ---
{context}

--- CÂU HỎI ---
{question}
"""
        # Generate response using genai client
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        return response.text
