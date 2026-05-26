import os

from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from google import genai
from langchain_core.embeddings import Embeddings

load_dotenv()

class GenAIEmbeddings(Embeddings):
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key.strip())
        self.model = "models/gemini-embedding-2"
        
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # Phải nhúng từng đoạn một vì API của Google gom list thành 1 vector
        all_embeddings = []
        for text in texts:
            response = self.client.models.embed_content(
                model=self.model,
                contents=text
            )
            all_embeddings.append(response.embeddings[0].values)
        return all_embeddings
        
    def embed_query(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model=self.model,
            contents=text
        )
        return response.embeddings[0].values

def build_vector_db():
    current_dir = os.path.dirname(__file__)
    data_path = os.path.join(current_dir, 'docs', 'codebase_data.txt')
    persist_dir = os.path.join(current_dir, 'vectorstore')
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("Lỗi: Không tìm thấy GEMINI_API_KEY trong file .env")
        return

    if not os.path.exists(data_path):
        print("Lỗi: Không tìm thấy file dữ liệu. Vui lòng chạy extract_project_data.py trước.")
        return
        
    print("Đang tải dữ liệu...")
    loader = TextLoader(data_path, encoding='utf-8')
    documents = loader.load()
    
    # Bắt buộc phải lọc các đoạn văn bản trống
    documents = [doc for doc in documents if doc.page_content.strip()]
    
    print("Đang chia nhỏ dữ liệu (chunking)...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=150
    )
    docs = text_splitter.split_documents(documents)
    docs = [doc for doc in docs if doc.page_content.strip()]
    
    print(f"Tạo embedding cho {len(docs)} đoạn văn bản bằng Gemini API (tiến trình này có thể mất 1-2 phút)...")
    embeddings = GenAIEmbeddings(api_key=api_key)
    
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    
    print("Hoàn tất xây dựng Vector Database!")

if __name__ == "__main__":
    build_vector_db()
