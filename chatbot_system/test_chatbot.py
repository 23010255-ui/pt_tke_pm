from chatbot import ProjectChatbot

def main():
    print("Khởi tạo chatbot...")
    try:
        bot = ProjectChatbot()
        print("Chatbot đã sẵn sàng! Gõ 'quit' hoặc 'exit' để thoát.\n")
        
        while True:
            question = input("Bạn: ")
            if question.lower() in ['quit', 'exit']:
                break
                
            if not question.strip():
                continue
                
            print("\nChatbot đang suy nghĩ...")
            answer = bot.ask(question)
            print(f"Chatbot: {answer}\n")
            
    except Exception as e:
        print(f"Lỗi khởi tạo chatbot: {e}")
        print("Gợi ý: Đảm bảo bạn đã điền OPENAI_API_KEY trong file .env và đã chạy build_vector_db.py")

if __name__ == "__main__":
    main()
