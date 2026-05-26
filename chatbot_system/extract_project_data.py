import os

def extract_codebase(root_dir, output_file):
    exclude_dirs = {'.git', '__pycache__', 'venv', '.venv', 'node_modules', 'chatbot_system'}
    exclude_exts = {'.pyc', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.sqlite', '.db', '.pdf', '.zip'}
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Lọc các thư mục không cần thiết
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
            
            for file in filenames:
                ext = os.path.splitext(file)[1].lower()
                if ext in exclude_exts:
                    continue
                
                filepath = os.path.join(dirpath, file)
                rel_path = os.path.relpath(filepath, root_dir)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        outfile.write(f"--- BẮT ĐẦU FILE: {rel_path} ---\n")
                        outfile.write(content)
                        outfile.write(f"\n--- KẾT THÚC FILE: {rel_path} ---\n\n")
                except Exception as e:
                    print(f"Không thể đọc file {rel_path}: {e}")

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    output_path = os.path.join(os.path.dirname(__file__), 'docs', 'codebase_data.txt')
    
    print(f"Đang trích xuất dữ liệu dự án từ {project_root}...")
    extract_codebase(project_root, output_path)
    print(f"Đã trích xuất xong. Dữ liệu lưu tại {output_path}")
