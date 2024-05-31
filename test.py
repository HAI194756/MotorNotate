import sys
import PyQt6 as Qt
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
import os
import cv2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from pymongo import MongoClient

class LoginForm(QWidget):
    def __init__(self):
        super().__init__()
        layout = QGridLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        self.setWindowTitle("Application")
        self.mongo_uri = os.getenv('MONGO_URI')
        self.setLayout(layout)

        # Title Label
        title = QLabel("Login")
        title.setProperty("class", "heading")
        layout.addWidget(title, 0, 0, 1, 3, Qt.AlignmentFlag.AlignCenter)

        # Username Label and Input
        user = QLabel("Username:")
        user.setProperty("class", "normal")
        layout.addWidget(user, 1, 0)
        self.input1 = QLineEdit()
        layout.addWidget(self.input1, 1, 1, 1, 2)

        # Password Label and Input
        pwd = QLabel("Password")
        pwd.setProperty("class", "normal")
        layout.addWidget(pwd, 2, 0)
        self.input2 = QLineEdit()
        self.input2.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.input2, 2, 1, 1, 2)

        # Register and Login Buttons
        button1 = QPushButton("Register")
        button1.clicked.connect(self.open_register_form)
        layout.addWidget(button1, 4, 1)

        button2 = QPushButton("Login")
        button2.clicked.connect(self.login)
        layout.addWidget(button2, 4, 2)

        self.input2.returnPressed.connect(self.login)

        # Connect to MongoDB
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client['user']
        self.users_collection = self.db['users']

    def open_register_form(self):
        self.new_window = RegisterForm()
        self.new_window.show()

    def login(self):
        username = self.input1.text()
        password = self.input2.text()

        user = self.users_collection.find_one({'username': username, 'password': password})
        if user:
            if user.get('status') == 'on':
                QMessageBox.warning(self, "Error", "This user is already logged in.")
                return

            self.users_collection.update_one({'username': username}, {"$set": {'status': 'on'}})

            print("Username and password are correct")
            role = user['role']
            self.new_window = MainMenu(username, role)
            self.close()
            self.new_window.show()
        else:
            print("Invalid")
            QMessageBox.warning(self, "Error", "Invalid username or password")
        self.setStyleSheet(open("style.qss", "r").read())

    def logout(self, username):
        self.users_collection.update_one({'username': username}, {"$set": {'status': 'off'}})
        self.new_window = LoginForm()
        self.close()
        self.new_window.show()

class RegisterForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)
        self.setWindowTitle("Register")
        self.mongo_uri = os.getenv('MONGO_URI')
        self.setLayout(layout)

        # Username Label and Input
        user_label = QLabel("Username:")
        layout.addWidget(user_label, 0, 0)
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input, 0, 1)

        # Password Label and Input
        pwd_label = QLabel("Password:")
        layout.addWidget(pwd_label, 1, 0)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input, 1, 1)

        # Register Button
        register_button = QPushButton("Register")
        register_button.clicked.connect(self.register)
        layout.addWidget(register_button, 3, 1)

        # Connect to MongoDB
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client['user']
        self.users_collection = self.db['users']

    def register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        role = "employer"

        if self.users_collection.find_one({'username': username}):
            QMessageBox.warning(self, "Error", "Username already exists.")
            return

        if username and password and role:
            user = {
                "username": username,
                "password": password,
                "role": role,
                "status": "off"
            }
            self.users_collection.insert_one(user)
            QMessageBox.information(self, "Registration Successful", "User has been registered successfully.")
            self.close()
        else:
            QMessageBox.warning(self, "Error", "All fields are required.")

class MainMenu(QWidget):
    def __init__(self, username, role):
        super().__init__()
        self.setWindowTitle("Welcome Page")
        self.resize(600, 300)
        self.mongo_uri = os.getenv('MONGO_URI')
        layout = QGridLayout()

        # Label chào mừng người dùng mới đăng nhập
        welcome_label = QLabel(f"Welcome, {username}!")
        layout.addWidget(welcome_label, 0, 0, 1, 3, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        button0 = QPushButton("Log Out")
        button0.setFixedSize(100, 50)
        button0.clicked.connect(lambda: self.logout(username))
        layout.addWidget(button0, 4, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignCenter)

        # Các nút bấm
        button1 = QPushButton("Labels Tool")
        button1.setFixedSize(100, 50)
        layout.addWidget(button1, 1, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignCenter)
        button1.clicked.connect(self.label_tool)

        button2 = QPushButton("Motor detection")
        button2.setFixedSize(100, 50)
        layout.addWidget(button2, 2, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignCenter)
        button2.clicked.connect(self.detect_tool)

        button3 = QPushButton("Statistic")
        button3.setFixedSize(100, 50)
        layout.addWidget(button3, 3, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignCenter)
        button3.clicked.connect(self.show_statistics)

        # Thêm nút Show Employers nếu role là admin
        if role == "admin":
            show_employers_button = QPushButton("Show Employers")
            show_employers_button.setFixedSize(150, 50)
            show_employers_button.clicked.connect(self.show_employers)
            layout.addWidget(show_employers_button, 0, 2, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

            view_csv_button = QPushButton("View Employer CSV Files")
            view_csv_button.setFixedSize(150, 50)
            view_csv_button.clicked.connect(self.open_admin_view_csv_dialog)
            layout.addWidget(view_csv_button, 1, 2, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        self.role = role
        self.username = username
        self.setLayout(layout)

    def logout(self, username):
        client = MongoClient(self.mongo_uri)
        db = client['user']
        users_collection = db['users']
        users_collection.update_one({'username': username}, {"$set": {'status': 'off'}})
        self.new_window = LoginForm()
        self.close()
        self.new_window.show()

    def closeEvent(self, event):
        client = MongoClient(self.mongo_uri)
        db = client['user']
        users_collection = db['users']
        users_collection.update_one({'username': self.username}, {"$set": {'status': 'off'}})
        event.accept()

    def label_tool(self):
        self.new_window = LabelsTool(self.username, self.role)
        self.close()
        self.new_window.show()

    def detect_tool(self):
        self.new_window = Detect(self.username, self.role)
        self.close()
        self.new_window.show()

    def show_statistics(self):
        if self.role == "employer":
            QMessageBox.warning(self, "Access Denied", "You do not have permission to access this feature.")
        else:
            self.new_window = StatisticForm(self.username, self.role)
            self.close()
            self.new_window.show()

    def show_employers(self):
        self.employer_window = EmployerListDialog()
        self.employer_window.exec()

    def open_admin_view_csv_dialog(self):
        dialog = AdminViewCsvDialog()
        dialog.exec()

class EmployerListDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("List of Employers")
        self.setFixedSize(400, 300)
        self.mongo_uri = os.getenv('MONGO_URI')
        layout = QVBoxLayout()

        self.client = MongoClient(self.mongo_uri)
        self.db = self.client['user']
        self.users_collection = self.db['users']
        
        employers = self.users_collection.find({'role': 'employer'})
        for employer in employers:
            h_layout = QHBoxLayout()
            label = QLabel(f"Username: {employer['username']}")
            h_layout.addWidget(label)

            promote_button = QPushButton("Promote to Admin")
            promote_button.clicked.connect(lambda _, username=employer['username']: self.promote_to_admin(username))
            h_layout.addWidget(promote_button)
            
            layout.addLayout(h_layout)
        
        self.setLayout(layout)
    
    def promote_to_admin(self, username):
        self.users_collection.update_one({'username': username}, {"$set": {'role': 'admin'}})
        QMessageBox.information(self, "Promotion Successful", f"{username} has been promoted to Admin.")

class AdminViewCsvDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("View Employer CSV Files")
        self.setGeometry(300, 300, 600, 400)

        self.layout = QVBoxLayout()
        self.csv_list_widget = QListWidget()
        self.layout.addWidget(self.csv_list_widget)
        self.mongo_uri = os.getenv('MONGO_URI')
        self.setLayout(self.layout)

        self.populate_csv_list()

    def populate_csv_list(self):
        client = MongoClient(self.mongo_uri)
        db = client['user']
        users_collection = db['users']
        employers = users_collection.find({"role": "employer"})

        for employer in employers:
            username = employer["username"]
            csv_folder = employer.get("assigned_folder", None)
            if csv_folder and os.path.isdir(csv_folder):
                csv_files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]
                if csv_files:
                    for csv_file in csv_files:
                        item = QListWidgetItem(f"{username}: {csv_file}")
                        self.csv_list_widget.addItem(item)

                        view_button = QPushButton("View CSV")
                        view_button.clicked.connect(lambda checked, username=username: self.view_csv(username))
                        self.csv_list_widget.setItemWidget(item, view_button)

    def view_csv(self, username):
        client = MongoClient(self.mongo_uri)
        db = client['user']
        users_collection = db['users']
        user = users_collection.find_one({"username": username})
        csv_content = user.get("csv_content", "")
        
        # Tạo một hộp thoại để hiển thị nội dung của trường csv_content
        csv_content_dialog = QDialog(self)
        csv_content_dialog.setWindowTitle(f"CSV Content for {username}")
        csv_content_dialog.setGeometry(400, 400, 600, 400)

        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setPlainText(csv_content)
        layout.addWidget(text_edit)
        
        csv_content_dialog.setLayout(layout)

        # Hiển thị hộp thoại
        csv_content_dialog.exec()

class Detect(QWidget):
    def __init__(self, username, role):
        super().__init__()
        self.setWindowTitle("Detector")
        self.resize(600, 300)
        self.mongo_uri = os.getenv('MONGO_URI')
        layout = QGridLayout()

        label = QLabel("Detector window!")
        layout.addWidget(label, 0, 0, 1, 3, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        button1 = QPushButton("Back")
        button1.setFixedSize(100, 50)
        layout.addWidget(button1, 1, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignCenter)
        button1.clicked.connect(self.main_menu)
        
        self.username = username
        self.role = role

        self.setLayout(layout)

    def closeEvent(self, event):
        client = MongoClient(self.mongo_uri)
        db = client['user']
        users_collection = db['users']
        users_collection.update_one({'username': self.username}, {"$set": {'status': 'off'}})
        event.accept()

    def main_menu(self):
        self.new_window = MainMenu(self.username, self.role)
        self.close()
        self.new_window.show()
        

class StatisticForm(QWidget):
    def __init__(self, username, role):
        super().__init__()
        self.setWindowTitle("Statistics")
        self.resize(800, 600)
        self.mongo_uri = os.getenv('MONGO_URI')
        layout = QVBoxLayout()

        button0 = QPushButton("Back")
        button0.setFixedSize(100, 50)
        button0.clicked.connect(self.main_menu)
        layout.addWidget(button0)

        self.username = username
        self.role = role
        self.setLayout(layout)

        chart_container = QWidget()
        layout.addWidget(chart_container)

        # Kết nối MongoDB và lấy dữ liệu
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client['user']
        self.data_collection = self.db['data']
        data = self.fetch_data()

        # Tạo biểu đồ và thêm vào QWidget
        self.plot_bar_chart(data, chart_container)

    def main_menu(self):
        self.new_window = MainMenu(self.username, self.role)
        self.close()
        self.new_window.show()

    def closeEvent(self, event):
        client = MongoClient(self.mongo_uri)
        db = client['user']
        users_collection = db['users']
        users_collection.update_one({'username': self.username}, {"$set": {'status': 'off'}})
        event.accept()

    def fetch_data(self):
        data = {
            'January': {'xe_ga': 0, 'xe_so': 0},
            'February': {'xe_ga': 0, 'xe_so': 0},
            'March': {'xe_ga': 0, 'xe_so': 0},
            # Thêm các tháng khác tương tự
        }

        cursor = self.data_collection.find()
        for document in cursor:
            month = document['month']
            if document['type'] == 'xe_ga':
                data[month]['xe_ga'] += 1
            elif document['type'] == 'xe_so':
                data[month]['xe_so'] += 1

        return data

    def plot_bar_chart(self, data, container):
        months = list(data.keys())
        xe_ga = [data[month]['xe_ga'] for month in months]
        xe_so = [data[month]['xe_so'] for month in months]

        fig, ax = plt.subplots()
        x = np.arange(len(months))
        width = 0.35

        rects1 = ax.bar(x - width/2, xe_ga, width, label='Xe Ga')
        rects2 = ax.bar(x + width/2, xe_so, width, label='Xe So')

        ax.set_xlabel('Tháng')
        ax.set_ylabel('Số lượng')
        ax.set_title('Số lượng xe ga và xe số theo tháng')
        ax.set_xticks(x)
        ax.set_xticklabels(months)
        ax.legend()

        plt.xticks(rotation=45, ha='right')

        # Tạo một FigureCanvas từ biểu đồ và thêm vào container
        canvas = FigureCanvas(fig)
        layout = QVBoxLayout(container)
        layout.addWidget(canvas)
        
app = QApplication(sys.argv)
window = LoginForm()
window.show()
sys.exit(app.exec())