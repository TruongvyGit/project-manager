from app import create_app
from app.database import init_db

# Khởi tạo database
init_db()

# Tạo ứng dụng
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)