import sys
import PyQt6 as Qt
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
import os
import cv2
import pandas as pd
import numpy as np
import re
import webbrowser
import csv
import matplotlib.pyplot as plt
import torch
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from io import StringIO
from pymongo import MongoClient
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from ultralytics import YOLO
from torchvision import transforms
from PIL import Image

class LoginForm(QWidget):
    def __init__(self):
        super().__init__()

        # Icon
        icon = QIcon()
        icon.addPixmap(QPixmap("icon.jpg"), QIcon.Mode.Disabled)
        self.setWindowIcon(icon)

        layout = QGridLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        self.setWindowTitle("Application")
        
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
        self.client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
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

        # Icon
        icon = QIcon()
        icon.addPixmap(QPixmap("icon.jpg"), QIcon.Mode.Disabled)
        self.setWindowIcon(icon)

        layout = QGridLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)
        self.setWindowTitle("Register")
        
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
        self.client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
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

        # Icon
        icon = QIcon()
        icon.addPixmap(QPixmap("icon.jpg"), QIcon.Mode.Disabled)
        self.setWindowIcon(icon)

        self.setWindowTitle("Welcome Page")
        self.resize(600, 300)
        self.role = role
        self.username = username
        
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

        button2 = QPushButton("Detector")
        button2.setFixedSize(100, 50)
        layout.addWidget(button2, 2, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignCenter)
        button2.clicked.connect(self.detect_tool)

        button3 = QPushButton("Statistic")
        button3.setFixedSize(100, 50)
        layout.addWidget(button3, 3, 1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignCenter)
        button3.clicked.connect(self.show_statistics)

        # Thêm nút Show Employers nếu role là admin
        if role == "admin":
            show_employers_button = QPushButton("Show Members")
            show_employers_button.setFixedSize(150, 50)
            show_employers_button.clicked.connect(self.show_employers)
            layout.addWidget(show_employers_button, 0, 2, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

            view_csv_button = QPushButton("View Member Progress")
            view_csv_button.setFixedSize(150, 50)
            view_csv_button.clicked.connect(self.open_admin_view_csv_dialog)
            layout.addWidget(view_csv_button, 1, 2, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        else:
            self.client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
            self.db = self.client['user']
            self.users_collection = self.db['users']
            user = self.users_collection.find_one({"username" : username})
            assigned_link = user.get("assigned_folder", "")
        
            if assigned_link:
                label = QLabel("!You have been assigned a folder from admin", self)
                layout.addWidget(label, 0, 0, 2, 3, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
            else:
                label1 = QLabel("!You have not been assigned any folder from admin", self)
                layout.addWidget(label1, 0, 0, 2, 3, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        
        self.setLayout(layout)

    def logout(self, username):
        client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
        db = client['user']
        users_collection = db['users']
        users_collection.update_one({'username': username}, {"$set": {'status': 'off'}})
        self.new_window = LoginForm()
        self.close()
        self.new_window.show()

    def closeEvent(self, event):
        client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
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
        dialog = AdminViewCsvDialog(self.username)
        dialog.exec()

class EmployerListDialog(QDialog):
    def __init__(self):
        super().__init__()

        # Icon
        icon = QIcon()
        icon.addPixmap(QPixmap("icon.jpg"), QIcon.Mode.Disabled)
        self.setWindowIcon(icon)

        self.setWindowTitle("List of Employers")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()

        self.client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
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
    def __init__(self, username):
        super().__init__()

        # Icon
        icon = QIcon()
        icon.addPixmap(QPixmap("icon.jpg"), QIcon.Mode.Disabled)
        self.setWindowIcon(icon)

        self.setWindowTitle("View CSV")
        self.setFixedSize(400, 300)

        # Layout chính
        main_layout = QVBoxLayout()

        # Checkbox để chuyển đổi chế độ hiển thị
        self.switch_checkbox = QCheckBox("Show only users with CSV content")
        self.switch_checkbox.stateChanged.connect(self.update_user_list)
        main_layout.addWidget(self.switch_checkbox)

        # Placeholder cho danh sách user
        self.user_layouts = QVBoxLayout()
        main_layout.addLayout(self.user_layouts)

        self.setLayout(main_layout)

        self.client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
        self.db = self.client['user']
        self.users_collection = self.db['users']

        self.update_user_list()

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

    def update_user_list(self):
        # Clear the previous user list
        self.clear_layout(self.user_layouts)

        show_only_with_csv = self.switch_checkbox.isChecked()
        employers = self.users_collection.find({'role': 'employer'})

        for employer in employers:
            csv_content = employer.get("csv_content", "")
            if show_only_with_csv and not csv_content:
                continue

            h_layout = QHBoxLayout()
            label = QLabel(f"Username: {employer['username']}")
            h_layout.addWidget(label)

            if csv_content:
                # Chuyển đổi nội dung CSV thành DataFrame
                df = pd.read_csv(StringIO(csv_content))

                # Tính toán số dòng đã được rating và tổng số dòng
                total_rows = len(df)
                rated_rows = df['Rating'].count()
                stats = f"Labeled Image: {rated_rows} / {total_rows}"
            else:
                stats = "No CSV content available."

            # Thêm thống kê vào hộp thoại
            stats_label = QLabel(stats)
            h_layout.addWidget(stats_label)

            button = QPushButton("View CSV")
            button.clicked.connect(lambda _, username=employer['username']: self.view_csv(username))
            h_layout.addWidget(button)

            self.user_layouts.addLayout(h_layout)

    def view_csv(self, username):
        client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
        db = client['user']
        users_collection = db['users']
        user = users_collection.find_one({"username": username})
        assigned_folder = user.get("assigned_folder", "")
        assigns = self.users_collection.find({'assigned_folder': assigned_folder})
    
        # Tạo một hộp thoại để hiển thị nội dung của trường csv_content
        csv_content_dialog = QDialog(self)
        csv_content_dialog.setWindowTitle(f"CSV Content for {username}")
        csv_content_dialog.setGeometry(400, 400, 600, 400)
        layout = QVBoxLayout()

        # Thêm QLabel để hiển thị assigned_folder
        folder_label = QLabel(f"Assigned Folder: {assigned_folder}")
        layout.addWidget(folder_label)

        combined_df = pd.DataFrame()
        usernames = []

        for assign in assigns:
            content = assign.get("csv_content", "")
            if content:
                temp_df = pd.read_csv(StringIO(content))
                usernames.append(assign['username'])
                temp_df.rename(columns={'Rating': assign['username']}, inplace=True)
                if combined_df.empty:
                    combined_df = temp_df
                else:
                    combined_df = pd.merge(combined_df, temp_df, on='Name', how='outer')

        # Combine the ratings
        if not combined_df.empty:
            combined_df['Rating'] = combined_df.apply(
                lambda row: '/'.join([str(row[col]) for col in combined_df.columns if col != 'Name' and not pd.isna(row[col])]), axis=1
            )
            combined_df = combined_df[['Name', 'Rating']]
    
        # Tính toán số lượng ảnh đã được đánh giá bởi ít nhất một user
        rated_images = combined_df['Rating'].apply(lambda x: any(rating != '' for rating in x.split('/'))).sum()

        # Tính toán số lượng ảnh có rating khác nhau giữa các user
        def different_ratings(rating):
            ratings = set(rating.split('/'))
            return len(ratings) > 1

        different_ratings_count = combined_df['Rating'].apply(different_ratings).sum()

        # Hiển thị số lượng ảnh đã được đánh giá
        rated_images_label = QLabel(f"Rated Images: {rated_images}")
        layout.addWidget(rated_images_label)

        # Hiển thị số lượng ảnh có rating khác nhau
        different_ratings_label = QLabel(f"Images with different ratings by users: {different_ratings_count}")
        layout.addWidget(different_ratings_label)

        # Convert combined DataFrame to HTML with custom styling
        def style_row(row):
            rating = row['Rating']
            if different_ratings(rating):
                return ['background-color: red'] * len(row)
            return [''] * len(row)

        styled_df = combined_df.style.apply(style_row, axis=1)
        styled_html = styled_df.to_html()
        
        # Add usernames as a header
        usernames_header = '/'.join(usernames) + '<br>'

        text = QTextEdit()
        text.setHtml(usernames_header + styled_html)
        layout.addWidget(text)

        csv_content_dialog.setLayout(layout)

        # Hiển thị hộp thoại
        csv_content_dialog.exec()

class AssignFolderDialog(QDialog):
    def __init__(self):
        super().__init__()

        # Icon
        icon = QIcon()
        icon.addPixmap(QPixmap("icon.jpg"), QIcon.Mode.Disabled)
        self.setWindowIcon(icon)

        self.setWindowTitle("Assign Link to Employer")
        self.setGeometry(200, 200, 400, 300)

        self.layout = QVBoxLayout()
        
        self.setLayout(self.layout)

        self.populate_employee_list()

    def populate_employee_list(self):
        # Connect to MongoDB and get the list of employees
        client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
        db = client['user']
        employees_collection = db['users']
        employees = employees_collection.find({"role": "employer"})

        # Add employees to the list widget
        for employee in employees:
            h_layout = QHBoxLayout()
            label = QLabel(f"Username: {employee['username']}")
            h_layout.addWidget(label)

            # Add a button to assign a link for each employee
            assign_btn = QPushButton("Assign Link")
            assign_btn.clicked.connect(lambda checked, username = employee['username']: self.assign_link(username))
            h_layout.addWidget(assign_btn)
            
            self.layout.addLayout(h_layout)
        self.setLayout(self.layout)

    def assign_link(self, username):
        client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
        db = client['user']
        employees_collection = db['users']
        user = employees_collection.find_one({'username': username})
        
        if not user.get('assigned_folder'):
            link, ok = QInputDialog.getText(self, f'Assign Link to {username}', 'Enter the link:')
            if ok and link:
                # Save the assigned link to the database
                employees_collection.update_one({'username': username}, {"$set": {'assigned_folder': link}})
                QMessageBox.information(self, "Success", f"Link assigned to {username}")
        else:
            QMessageBox.information(self, "Already Assigned", f"User {username} already has an assigned link.")

class FolderUploadDialog(QDialog):
    def __init__(self):
        super(FolderUploadDialog, self).__init__()

        # Icon
        icon = QIcon()
        icon.addPixmap(QPixmap("icon.jpg"), QIcon.Mode.Disabled)
        self.setWindowIcon(icon)

        self.setWindowTitle("Upload Folder")
        self.setGeometry(100, 100, 400, 200)
        
        self.layout = QVBoxLayout()
        
        self.upload_btn = QPushButton("Upload Folder")
        self.upload_btn.clicked.connect(self.upload_folder)
        self.layout.addWidget(self.upload_btn)

        self.upload_btn2 = QPushButton("Upload Folder to Google Drive")
        self.upload_btn2.clicked.connect(self.upload_drive)
        self.layout.addWidget(self.upload_btn2)
        
        self.assign_btn = QPushButton("Assign to...")
        self.assign_btn.clicked.connect(self.open_assign_folder_dialog)
        self.layout.addWidget(self.assign_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_btn)
        
        self.setLayout(self.layout)
        self.folder_path = None
    
    def authenticate(self):
        gauth = GoogleAuth()
        gauth.LoadCredentialsFile("credentials.json")

        if gauth.credentials is None:
            # Authenticate if they're not there
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            # Refresh them if expired
            gauth.Refresh()
        else:
            # Initialize the saved creds
            gauth.Authorize()
        
        gauth.SaveCredentialsFile("credentials.json")
        return GoogleDrive(gauth)
    
    def upload_drive(self):
        drive = self.authenticate()
        
        # Ask user if they want to upload a file or a folder
        choice, ok = QInputDialog.getItem(self, "Upload Option", "Do you want to upload a file or a folder?", ["File", "Folder"], 0, False)
        if not ok:
            return

        if choice == "File":
            self.upload_file(drive)
        elif choice == "Folder":
            self.upload_folder(drive)
    
    def extract_drive_id(self, url):
        match = re.search(r'drive/folders/([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
        else:
            return None

    def upload_file(self, drive):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select File', "C:\\", "All Files (*)")
        if file_path:
            drive_folder_url, ok = QInputDialog.getText(self, 'Upload to Google Drive', 'Enter Google Drive Folder URL:')
            if ok:
                drive_folder_id = self.extract_drive_id(drive_folder_url)
                if drive_folder_id:
                    try:
                        # Define file metadata and upload it
                        file_metadata = {
                            'title': os.path.basename(file_path),
                            'parents': [{'id': drive_folder_id}]
                        }
                        gfile = drive.CreateFile(file_metadata)
                        gfile.SetContentFile(file_path)
                        gfile.Upload()
                        QMessageBox.information(self, "Success", f"Uploaded: {file_path}")
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
                else:
                    QMessageBox.critical(self, "Error", "Invalid Google Drive Folder URL.")

    def upload_folder(self, drive):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder', "C:\\")
        if folder_path:
            drive_folder_url, ok = QInputDialog.getText(self, 'Upload to Google Drive', 'Enter Google Drive Folder URL:')
            if ok:
                drive_folder_id = self.extract_drive_id(drive_folder_url)
                if drive_folder_id:
                    try:
                        folder_id_map = {folder_path: drive_folder_id}
                        
                        # Create a folder on Google Drive
                        def create_drive_folder(folder_name, parent_id):
                            folder_metadata = {
                                'title': folder_name,
                                'mimeType': 'application/vnd.google-apps.folder',
                                'parents': [{'id': parent_id}] if parent_id else []
                            }
                            gfolder = drive.CreateFile(folder_metadata)
                            gfolder.Upload()
                            return gfolder['id']
                        
                        for root, dirs, files in os.walk(folder_path):
                            for dir_name in dirs:
                                dir_path = os.path.join(root, dir_name)
                                parent_path = os.path.dirname(dir_path)
                                parent_id = folder_id_map.get(parent_path, drive_folder_id)
                                
                                folder_id = create_drive_folder(dir_name, parent_id)
                                folder_id_map[dir_path] = folder_id
                                print(f"Created folder {dir_name} with ID {folder_id}")
                        
                        for root, dirs, files in os.walk(folder_path):
                            for filename in files:
                                file_path = os.path.join(root, filename)
                                parent_path = os.path.dirname(file_path)
                                parent_id = folder_id_map.get(parent_path, drive_folder_id)
                                
                                # Define file metadata and upload it
                                file_metadata = {
                                    'title': filename,
                                    'parents': [{'id': parent_id}] if parent_id else []
                                }
                                gfile = drive.CreateFile(file_metadata)
                                gfile.SetContentFile(file_path)
                                gfile.Upload()
                                print(f"Uploaded: {file_path}")
                        QMessageBox.information(self, "Success", f"Uploaded folder: {folder_path}")
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
                else:
                    QMessageBox.critical(self, "Error", "Invalid Google Drive Folder URL.")

    def open_assign_folder_dialog(self):
        assign_folder_dialog = AssignFolderDialog()
        assign_folder_dialog.exec()

    def get_folder_path(self):
        return self.folder_path

class FolderNotice(QDialog):
    def __init__(self, string, parent=None):
        super(FolderNotice, self).__init__(parent)

        # Icon
        icon = QIcon()
        icon.addPixmap(QPixmap("icon.jpg"), QIcon.Mode.Disabled)
        self.setWindowIcon(icon)

        self.setWindowTitle("Notification")
        self.setFixedSize(600, 300)

        self.layout = QVBoxLayout()

        self.label = QLabel(f"Access to the link and download the folder: {string}!")
        self.layout.addWidget(self.label)

        self.open_link = QPushButton("Open Link")
        self.open_link.clicked.connect(self.link_click)
        self.layout.addWidget(self.open_link)

        self.upload_btn = QPushButton("Upload Folder")
        self.upload_btn.clicked.connect(self.upload_folder)
        self.layout.addWidget(self.upload_btn)

        self.setLayout(self.layout)
        self.string = string
        self.uploaded = False

    def link_click(self):
        webbrowser.open_new(self.string)

    def upload_folder(self):
        self.close()

    def closeEvent(self, event):
        if not self.uploaded:
            reply = QMessageBox.question(self, 'Warning', 'You must upload the folder.',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
            else:
                event.accept()
        else:
            event.accept()

class LabelsTool(QDialog):
    def __init__(self, username, role):
        super(LabelsTool, self).__init__()

        self.setFixedSize(1000, 800)
        
        self.dataset = None 
        self.excel_path = None
        self.csv_file = None
        self.resized_mode = False
        self.convert_mode = False
        self.index = -1
        self.cropping = False
        self.crop_points = []
        self.current_image = None
        self.pixmap = None
        
        self.initDialog()
        self.initKeyBoard()
        
        self.setupButton()
        self.retranslateUi()

        self.username = username
        self.role = role

    def closePage(self, event):
        client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
        db = client['user']
        users_collection = db['users']
        users_collection.update_one({'username': self.username}, {"$set": {'status': 'off'}})
        event.accept()

    def main_menu(self):
        self.new_window = MainMenu(self.username, self.role)  
        self.close() 
        self.new_window.show()  
        
    def get_assigned_save_folder(self):
        client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
        db = client['user']
        users_collection = db['users']
        user = users_collection.find_one({'username': self.username})
        return user.get('assigned_folder')
    
    def change_view_mode(self):
        if self.index == -1:
            self.show_notification_pop_up("Need image", "Warn")
            return
        
        _translate = QCoreApplication.translate
        self.resized_mode = not(self.resized_mode)
        self.view_mode.setText(_translate("Dialog", "Fit Size" if not(self.resized_mode) else "Real Size")) 
        self.show_image(self.index, self.resized_mode)
    
    def load_image_dir_func(self):
        if self.role == "admin":
            self.open_folder_upload_dialog()
        else:
            self.fname = self.get_assigned_save_folder()

            if self.fname:
                FolderNotice(self.fname).exec()

                # Load image
                self.fname = QFileDialog.getExistingDirectory(self, 'Open Folder', "C:\\")
                self.csv_path = os.path.join(self.fname, "label_image.csv")

                if os.path.exists(self.fname):
                    self.dataset = os.listdir(self.fname)
                    self.index = 0
                    self.show_image(self.index, self.resized_mode)
                    self.total_image_label.setText("/" + str(len(self.dataset)))

                # Kiểm tra csv_path sau khi fname đã được gán giá trị
                if not os.path.exists(self.csv_path):
                    self.csv_file = pd.DataFrame()
                    self.csv_file["Name"] = pd.Series(self.dataset)
                    self.csv_file["Rating"] = pd.Series([])
                    self.csv_file.to_csv(self.csv_path, index=False)
                else:
                    self.csv_file = pd.read_csv(self.csv_path)

                self.show_image(self.index, self.resized_mode)
            else:
                QMessageBox.information(self, "No Folder Assigned", "No folder has been assigned to you yet. Please contact the admin.")
            
    def open_folder_upload_dialog(self):
        dialog = FolderUploadDialog()
        if dialog.exec():
            self.fname = dialog.get_folder_path()
            if self.fname and os.path.exists(self.fname):
                self.dataset = os.listdir(self.fname)
                self.index = 0
                self.show_image(self.index, self.resized_mode)
                self.total_image_label.setText("/" + str(len(self.dataset)))
    
    def read_csv_from_folder(self, folder_path):
        csv_path = os.path.join(folder_path, "label_image.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            return df
        else:
            print(f"CSV file 'label_image.csv' not found in folder '{folder_path}'")
        return None
        
    def show_image(self, index, resized_mode):
        name = self.dataset[index]
        print(name, self.fname)
        # current_image = cv2.imread(os.path.join(self.fname, name))

        # Resolve unicode path problem
        stream = open(u"{}".format(os.path.join(self.fname, name)), "rb")
        bytes = bytearray(stream.read())
        np_array = np.asarray(bytes, dtype=np.uint8)
        current_image = cv2.imdecode(np_array, cv2.IMREAD_UNCHANGED)
        
        image = QImage(current_image, current_image.shape[1], current_image.shape[0], current_image.shape[1] * 3, QImage.Format.Format_RGB888)
        pixmap = QPixmap(image)

        if not resized_mode:
            fixed_width, fixed_height = 800, 600  # Define fixed size
            pixmap = pixmap.scaled(fixed_width, fixed_height, Qt.AspectRatioMode.KeepAspectRatio)
        else:
            width, height = self.showscreen.width(), self.showscreen.height()
            pixmap = pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio)
        self.showscreen.setPixmap(pixmap)

        # Hiển thị rating đã label (nếu có)
        rating_label = self.get_image_rating(name)
        
        if rating_label != -1:
            self.result.setText(str(rating_label))
            self.label = rating_label
        else:
            self.result.setText("")
            self.label = -1
            
        # Update the index in image_index
        self.update_index_label(self.index)

    def crop_image(self):
        # Lấy đường dẫn của ảnh hiện tại từ dataset và fname
        index = self.index  # hoặc self.index, tùy vào cách bạn lưu trữ
        if index < 0 or index >= len(self.dataset):
            return

        name = self.dataset[index]
        image_path = os.path.join(self.fname, name)

        # Đọc ảnh từ đường dẫn sử dụng OpenCV
        current_image = cv2.imread(image_path)
        if current_image is None:
            QMessageBox.critical(self, "Error", f"Could not open image: {image_path}")
            return

        # Hiển thị cửa sổ chứa bức ảnh để crop
        cv2.namedWindow("Crop Image", cv2.WINDOW_NORMAL)
        cv2.imshow("Crop Image", cv2.cvtColor(current_image, cv2.COLOR_BGR2RGB))

        # Chờ người dùng chọn 4 điểm để crop
        points = cv2.selectROI("Crop Image", current_image, fromCenter=False)
        cv2.destroyWindow("Crop Image")

        # Nếu không có điểm nào được chọn, thoát
        if all(x == 0 for x in points):
            return
        
        # Xác nhận lại thao tác crop
        reply = QMessageBox.question(
            self,
            'Confirm Crop',
            'Do you want to save the cropped image?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            # Nếu người dùng không đồng ý, gọi lại hàm crop_image để thực hiện lại thao tác crop
            self.crop_image()
            return

        # Cắt ảnh từ 4 điểm được chọn
        x, y, w, h = points
        cropped_image = current_image[y:y+h, x:x+w]

        # Lưu ảnh mới vào đường dẫn ban đầu
        if not cv2.imwrite(image_path, cropped_image):
            QMessageBox.critical(self, "Error", "Could not save cropped image.")
            return

        # Cập nhật lại hiển thị ảnh đã cắt trong QLabel showscreen
        self.show_image(index, resized_mode=False)  # Cập nhật lại hiển thị với ảnh mới

        # Hiển thị thông báo thành công
        QMessageBox.information(self, "Crop Image", "Image cropped and saved successfully.")
        
    def get_image_rating(self, name):
        if self.csv_file is None:
            return -1
        
        record = self.csv_file[self.csv_file.Name == name].to_numpy()
        
        if len(record) == 0:
            return -1 
        else:
            record = record[0]
            
            try:
                int(record[1]) 
            except:
                return -1
            else:
                return int(record[1]) 
        
    def listen_key(self, event):
        key_press = event.key()
        
        if key_press == Qt.Key.Key_1:
            return 1 #xe_so
        elif key_press == Qt.Key.Key_2:
            return 2 #xe_ga
        elif key_press == Qt.Key.Key_3:
            return 3 #xe_dien 
        elif key_press == Qt.Key.Key_4:
            return 4 #phan_khoi_lon
        elif key_press == Qt.Key.Key_5:
            return 5 #ko_phai_xe_may
    def keyPressEvent(self, event):
        label = self.listen_key(event)
        
        if label is not None or label == -1:
            self.label = label 
            self.display_result(self.label)
            
    def display_result(self, rating):
        if rating is not None or rating == -1:
            self.result.setText(str(rating))
    
    # Cần đoạn code này do event ở key press không nhận các dấu mũi tên
    def initKeyBoard(self):
        # Next or previous image
        self.right = QShortcut(QKeySequence("Right"), self)
        self.right.activated.connect(self.go_next_image)
        
        self.left = QShortcut(QKeySequence("Left"), self)
        self.left.activated.connect(self.go_prev_image)
        
    def show_notification_pop_up(self, content, title):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(content)
        msg.setWindowTitle(title)
        msg.exec()
    
    def auto_save_label(self, name, rating):
        index = self.csv_file[self.csv_file.Name == name].index
        index = list(index)

        if len(index) <= 0:
            new_record = pd.DataFrame.from_dict({
                "Name": [name],
                "Rating": [rating]
            })

            self.csv_file = pd.concat([self.csv_file, new_record], axis=0)
        else:
            index = list(index)[0]
            self.csv_file.iat[index, 1] = int(rating)

        # Save CSV file
        self.csv_file.to_csv(self.csv_path, index=False)
        
        # Update MongoDB
        with open(self.csv_path, 'r') as file:
            csv_content = file.read()
        client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
        db = client['user']
        users_collection = db['users']
        users_collection.update_one({'username': self.username}, {"$set": {'csv_content': csv_content}})

        print("Auto-saved label for", name, "with rating", rating)  # Debugging statement

    def save_csv(self):
        if self.csv_file is not None and self.csv_path is not None:
            self.csv_file.to_csv(self.csv_path, index=False)
            self.show_notification_pop_up("Save successfully", "Success")

            with open(self.csv_path, 'r') as file:
                csv_content = file.read()
            client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
            db = client['user']
            users_collection = db['users']
            users_collection.update_one({'username': self.username}, {"$set": {'csv_content': csv_content}})

            print("CSV file saved")  # Debugging statement

    # Save file when closing app 
    def closeEvent(self, event):
        if self.csv_file is not None and self.csv_path is not None:
            self.csv_file.to_csv(self.csv_path, index=False)
            print("Auto save when closing")
    
    def go_next_image(self):
        print("Next image")
        
        if self.index == -1:
            self.show_notification_pop_up("You must select image dir by clicking to \"Select Dir\" button ", "Warn")
            return
        
        if self.csv_file is None:
            self.show_notification_pop_up("You must select image dir by clicking to \"Select Save Dir\" button ", "Warn")
            return 
        
        if self.label is None or self.label == -1:
            self.show_notification_pop_up("You must label image", "Warn")
            return 
        
        if self.index >= len(self.dataset) - 1:
            self.show_notification_pop_up("You have labeled all images", "Success")
            
            name = self.dataset[self.index]
            self.auto_save_label(name, self.label)
            
            if self.csv_file is not None and self.csv_path is not None:
                self.csv_file.to_csv(self.csv_path, index=False)
            return 
            
        name = self.dataset[self.index]
        self.auto_save_label(name, self.label)
            
        self.index += 1
        self.show_image(self.index, self.resized_mode)      
        
    def go_prev_image(self):
        print("Previous image")
        
        if self.index == -1:
            self.show_notification_pop_up("You must select image dir by clicking to \"Select Dir\" button ", "Warn")
            return 
        
        if self.csv_file is None:
            self.show_notification_pop_up("You must select image dir by clicking to \"Select Save Dir\" button ", "Warn")
            return 
        
        if self.label is None or self.label == -1:
            self.show_notification_pop_up("You must label image", "Warn")
            return 
        
        if self.index <= 0:
            self.show_notification_pop_up("There are no previous image", "Warn")
            return 
            
        name = self.dataset[self.index]
        self.auto_save_label(name, self.label)
            
        self.index -= 1
        self.show_image(self.index, self.resized_mode)
    
    def update_index_label(self, index):
        self.image_index.setText("{}".format(index + 1))
        
    def go_to_image(self):
        image_index = int(self.image_index.text())
        
        if image_index >= len(self.dataset) or image_index <= 0:
            self.show_notification_pop_up("Invalid index", "Warning")
        else:
            name = self.dataset[self.index]
            self.auto_save_label(name, self.label)
            
            self.index = image_index - 1
            self.show_image(self.index, self.resized_mode)
            
    def initDialog(self):
        # Icon
        icon = QIcon()
        icon.addPixmap(QPixmap("icon.jpg"), QIcon.Mode.Disabled)
        self.setWindowIcon(icon)

        # Screen Static
        self.screenStatic = QWidget(self)
        self.screenStatic.setGeometry(QRect(-1, -1, 1001, 801))
        self.screenStatic.setStyleSheet("QWidget#screenStatic{background-image: url(\"new2.jpg\");}")
        self.screenStatic.setObjectName("screenStatic")

        # Show image for labeling 
        self.showscreen = QLabel(self.screenStatic)
        self.showscreen.setGeometry(QRect(360, 120, 621, 651))
        self.showscreen.setStyleSheet("border-radius: 20px;\n""border-width: 10px;\n"
                                      "border-color: white;\n""background-color: rgba(255, 255, 255, 70);") # 170, 255, 255
        self.showscreen.setFrameShape(QFrame.Shape.Panel)
        self.showscreen.setFrameShadow(QFrame.Shadow.Sunken)
        self.showscreen.setText("")
        self.showscreen.setTextFormat(Qt.TextFormat.PlainText)
        self.showscreen.setPixmap(QPixmap("../../../../../../"))
        self.showscreen.setScaledContents(False)
        self.showscreen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.showscreen.setObjectName("showscreen")

        # Welcome to LabelsTool label
        self.welcome2 = QLabel(self.screenStatic)
        self.welcome2.setGeometry(QRect(430, 60, 511, 51))
        self.welcome2.setStyleSheet("font: 75 18pt \"MS Shell Dlg 2\";\n""color: rgb(255, 255, 255);")
        self.welcome2.setObjectName("welcome2")

        # Directory selection button
        self.dir_selection_btn = QPushButton(self.screenStatic)
        self.dir_selection_btn.setGeometry(QRect(60, 120, 211, 51))
        self.dir_selection_btn.setStyleSheet("border-radius: 20px;\n""font: 75 16pt \"MS Shell Dlg 2\";\n"
                                      "background-color: rgb(85, 255, 255);\n""color: #000000;")
        self.dir_selection_btn.setObjectName("dir_selection")

        # Add crop button
        self.crop_btn = QPushButton(self.screenStatic)
        self.crop_btn.setGeometry(QRect(60, 260, 211, 51))
        self.crop_btn.setStyleSheet("border-radius: 20px;\n""font: 75 16pt \"MS Shell Dlg 2\";\n"
                                  "background-color: rgb(85, 255, 255);\n""color: #000000;")
        self.crop_btn.setObjectName("crop_btn")

        # Manual save button 
        self.manual_save_btn = QPushButton(self.screenStatic)
        self.manual_save_btn.setGeometry(QRect(60, 190, 211, 51))
        self.manual_save_btn.setStyleSheet("border-radius: 20px;\n""font: 75 16pt \"MS Shell Dlg 2\";\n"
                                      "background-color: rgb(85, 255, 255);\n""color: #000000;")
        self.manual_save_btn.setObjectName("manual_save_btn")

        # Change view image mode
        self.view_mode = QPushButton(self.screenStatic)
        self.view_mode.setGeometry(QRect(60, 330, 211, 51))
        self.view_mode.setStyleSheet("border-radius: 20px;\n""font: 75 16pt \"MS Shell Dlg 2\";\n"
                                      "background-color: rgb(85, 255, 255);\n""color: #000000;")
        self.view_mode.setObjectName("view")

        # Back to Menu
        self.main_menu_btn = QPushButton(self.screenStatic)
        self.main_menu_btn.setGeometry(QRect(60, 400, 211, 51))
        self.main_menu_btn.setStyleSheet("border-radius: 20px;\n""font: 75 16pt \"MS Shell Dlg 2\";\n"
                                      "background-color: rgb(85, 255, 255);\n""color: #000000;")
        self.main_menu_btn.setObjectName("main_menu")
        
        # Image number label
        self.image_number_label = QLabel(self.screenStatic)
        self.image_number_label.setGeometry(QRect(70, 450, 191, 50))
        self.image_number_label.setStyleSheet("font: 75 18pt \"MS Shell Dlg 2\";\n""color: rgb(255, 255, 255);")
        self.image_number_label.setObjectName("welcome2")
        
        # Show the image number 
        self.image_index = QLineEdit(self.screenStatic)
        self.image_index.setGeometry(QRect(540, 60, 150, 50))
        self.image_index.setStyleSheet("border-radius: 20px;\n"
                                  "border-width:8px;\n"
                                  "border-color: black;\n"
                                  "background-color: rgb(255, 255, 255);\n"
                                  "font: 75 14pt 'MS Shell Dlg 2';\n"
                                  "color: rgb(0, 0, 0);")
        self.image_index.setText("")
        self.image_index.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_index.setObjectName("image_index")
        
        # Show the total number image 
        self.total_image_label = QLabel(self.screenStatic)
        self.total_image_label.setGeometry(QRect(700, 60, 200, 50)) 
        self.total_image_label.setStyleSheet("font: 75 18pt \"MS Shell Dlg 2\";\n""color: rgb(0, 0, 0);")
        self.total_image_label.setObjectName("welcome2")
        
        # Go to button 
        self.change_image_btn = QPushButton(self.screenStatic)
        self.change_image_btn.setGeometry(QRect(910, 60, 50, 50))
        self.change_image_btn.setStyleSheet("border-radius: 20px;\n""font: 75 16pt \"MS Shell Dlg 2\";\n"
                                      "background-color: rgb(255, 255, 255);\n""color: #000000;")
        self.change_image_btn.setObjectName("save_dir_btn")
        
        # Result 
        self.result_label = QLabel(self.screenStatic)
        self.result_label.setGeometry(QRect(70, 550, 191, 50))
        self.result_label.setStyleSheet("font: 75 18pt \"MS Shell Dlg 2\";\n""color: rgb(255, 255, 255);")
        self.result_label.setObjectName("welcome2")
        
        # Show click
        self.result = QLabel(self.screenStatic)
        self.result.setGeometry(QRect(70, 600, 191, 161))
        self.result.setStyleSheet("border-radius: 20px;\n"
                                  "border-width:5px;\n"
                                  "border-color: white;\n"
                                  "background-color: rgb(170, 255, 255);\n"
                                  "font: 75 18pt 'MS Shell Dlg 2';\n"
                                  "color: rgb(0, 0, 0);")
        self.result.setText("")
        self.result.setTextFormat(Qt.TextFormat.PlainText)
        self.result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result.setObjectName("result")
        
    def retranslateUi(self):
        _translate = QCoreApplication.translate
        self.setWindowTitle(_translate("Dialog", "LabelNow"))
        # Welcome to LabelsTool image
        self.welcome2.setText(_translate("Dialog", "Image:"))
        # Chọn đường dẫn đến folder chứa ảnh cần gán nhãn
        self.dir_selection_btn.setText(_translate("Dialog", "Select Dir"))
        # Thay đổi cách view hình ảnh
        self.view_mode.setText(_translate("Dialog", "Fit Size" if not(self.resized_mode) else "Real Size"))
        # Label result 
        self.result_label.setText(_translate("Dialog", "Result:"))
        # Manual save 
        self.manual_save_btn.setText(_translate("Dialog", "Save All Label"))
        # Go direct to image 
        self.change_image_btn.setText(_translate("Dialog", "Go"))
        #Back to menu
        self.main_menu_btn.setText(_translate("Dialog", "Back"))
        # Crop button
        self.crop_btn.setText(_translate("Dialog", "Crop Image"))
        
    def setupButton(self):
        self.dir_selection_btn.clicked.connect(self.load_image_dir_func)
        self.view_mode.clicked.connect(self.change_view_mode)
        self.manual_save_btn.clicked.connect(self.save_csv)
        self.change_image_btn.clicked.connect(self.go_to_image)
        self.main_menu_btn.clicked.connect(self.main_menu)
        self.crop_btn.clicked.connect(self.crop_image)

class Detect(QWidget):
    def __init__(self, username, role):
        super().__init__()

        # Icon
        icon = QIcon()
        icon.addPixmap(QPixmap("icon.jpg"), QIcon.Mode.Disabled)
        self.setWindowIcon(icon)

        self.setWindowTitle("Detector")
        self.resize(600, 300)
        self.username = username
        self.role = role
        
        layout = QGridLayout()

        self.video_label = QLabel("No video selected")
        layout.addWidget(self.video_label, 1, 0, 1, 3, Qt.AlignmentFlag.AlignCenter)

        self.upload_button = QPushButton("Upload Video")
        self.upload_button.setFixedSize(100, 50)
        layout.addWidget(self.upload_button, 2, 0, Qt.AlignmentFlag.AlignCenter)
        self.upload_button.clicked.connect(self.upload_video)

        self.train_button = QPushButton("Train Model")
        self.train_button.setFixedSize(100, 50)
        layout.addWidget(self.train_button, 3, 0, Qt.AlignmentFlag.AlignCenter)
        self.train_button.clicked.connect(self.train_model)

        self.preview_button = QPushButton("Preview Video")
        self.preview_button.setFixedSize(100, 50)
        layout.addWidget(self.preview_button, 2, 1, Qt.AlignmentFlag.AlignCenter)
        self.preview_button.clicked.connect(self.toggle_preview)
        self.preview_button.setEnabled(False)

        self.detect_button = QPushButton("Run Detection")
        self.detect_button.setFixedSize(100, 50)
        layout.addWidget(self.detect_button, 3, 1, Qt.AlignmentFlag.AlignCenter)
        self.detect_button.clicked.connect(self.toggle_detection)
        self.detect_button.setEnabled(False)

        button1 = QPushButton("Back")
        button1.setFixedSize(100, 50)
        layout.addWidget(button1, 2, 2, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignCenter)
        button1.clicked.connect(self.main_menu)

        self.model = YOLO('yolov8n.pt')
        self.video_path = None
        self.cap = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.is_detecting = False
        self.is_previewing = False

        self.setLayout(layout)

    def upload_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi *.mkv)")
        if file_path:
            self.video_path = file_path
            self.video_label.setText(f"Selected Video: {file_path}")
            self.preview_button.setEnabled(True)
            self.detect_button.setEnabled(True)

    def toggle_preview(self):
        if self.is_previewing:
            self.stop_preview()
        else:
            self.start_preview()

    def start_preview(self):
        if not self.video_path:
            return

        self.cap = cv2.VideoCapture(self.video_path)
        self.timer.start(30)  # Adjust the timer interval as needed
        self.preview_button.setText("Stop Preview")
        self.detect_button.setEnabled(False)
        self.is_previewing = True

    def stop_preview(self):
        if self.cap:
            self.cap.release()
        self.timer.stop()
        self.preview_button.setText("Preview Video")
        self.detect_button.setEnabled(True)
        self.is_previewing = False

    def toggle_detection(self):
        if self.is_detecting:
            self.stop_detection()
        else:
            self.start_detection()

    def start_detection(self):
        if not self.video_path:
            return

        self.cap = cv2.VideoCapture(self.video_path)
        self.timer.start(30)  # Adjust the timer interval as needed
        self.detect_button.setText("Stop Detection")
        self.preview_button.setEnabled(False)
        self.is_detecting = True

    def stop_detection(self):
        if self.cap:
            self.cap.release()
        self.timer.stop()
        self.detect_button.setText("Run Detection")
        self.preview_button.setEnabled(True)
        self.is_detecting = False

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.stop_preview() if self.is_previewing else self.stop_detection()
            return

        if self.is_detecting:
            results = self.model.predict(frame, conf=0.25)
            object_count = 0
            for result in results:
                boxes = result.boxes
                object_count += len(boxes)  # Đếm số lượng vật thể
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0]
                    cv2.rectangle(frame, (int(x1), (int(y1)), int(x2), int(y2)), (0, 255, 0), 2)

            # Lưu số lượng vật thể vào cơ sở dữ liệu
            client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
            db = client['user']
            detections_collection = db['detections']
            detection_record = {
                'object_count': object_count,
            }
            detections_collection.insert_one(detection_record)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.video_label.setPixmap(pixmap)

    def train_model(self):
        # Tải mô hình AlexNet đã huấn luyện trước
        model = torch.hub.load('pytorch/vision:v0.10.0', 'alexnet', pretrained=True)
        model.eval()

        # Đường dẫn đến thư mục chứa ảnh của bạn
        folder_path = "dataset/train"

        # Tiền xử lý ảnh
        preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        # Di chuyển model đến GPU nếu có để tăng tốc độ
        if torch.cuda.is_available():
            model.to('cuda')

        # Đọc các danh mục
        with open("image_classes.txt", "r") as f:
            categories = [s.strip() for s in f.readlines()]

        # Duyệt qua tất cả các tệp trong thư mục
        for filename in os.listdir(folder_path):
            if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):  # Kiểm tra định dạng tệp ảnh
                file_path = os.path.join(folder_path, filename)
                input_image = Image.open(file_path)

                # Tiền xử lý ảnh
                input_tensor = preprocess(input_image)
                input_batch = input_tensor.unsqueeze(0)  # tạo một mini-batch như mong đợi của mô hình

                # Di chuyển input đến GPU nếu có
                if torch.cuda.is_available():
                    input_batch = input_batch.to('cuda')

                with torch.no_grad():
                    output = model(input_batch)

                # Để lấy xác suất, bạn có thể chạy softmax trên nó
                probabilities = torch.nn.functional.softmax(output[0], dim=0)

                # Hiển thị các danh mục hàng đầu cho mỗi ảnh
                top5_prob, top5_catid = torch.topk(probabilities, 5)
                print(f"Results for {filename}:")
                for i in range(top5_prob.size(0)):
                    print(f"{categories[top5_catid[i]]}: {top5_prob[i].item()}")
                print("\n" + "-"*30 + "\n")  # Để phân cách kết quả giữa các ảnh

    def closeEvent(self, event):
        client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
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

        # Icon
        icon = QIcon()
        icon.addPixmap(QPixmap("icon.jpg"), QIcon.Mode.Disabled)
        self.setWindowIcon(icon)

        self.setWindowTitle("Statistics")
        self.resize(900, 700)
        
        layout = QVBoxLayout()

        button0 = QPushButton("Back")
        button0.setFixedSize(100, 50)
        button0.clicked.connect(self.main_menu)
        layout.addWidget(button0)

        # Calculate the total number of assigned folders
        total_assigned_folders = self.count_assigned_folders()

        # Create a label to display the total number of assigned folders
        self.assigned_folders_label = QLabel(f"Total assigned folders: {total_assigned_folders}")
        self.assigned_folders_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.assigned_folders_label)

        self.username = username
        self.role = role
        self.setLayout(layout)

        chart_container = QWidget()
        self.resize(800, 700)
        layout.addWidget(chart_container)

        # Prepare data
        data1 = self.count_rated_images()
        data2 = self.count_object()
        data = {'Detected objects': data2, 'Labelled image': data1}

        # Create the bar chart and add it to QWidget
        self.plot_bar_chart(data, chart_container)

    def main_menu(self):
        self.new_window = MainMenu(self.username, self.role)
        self.close()
        self.new_window.show()

    def closeEvent(self, event):
        client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
        db = client['user']
        users_collection = db['users']
        users_collection.update_one({'username': self.username}, {"$set": {'status': 'off'}})
        event.accept()

    def count_assigned_folders(self):
        # Connect to MongoDB and get the list of employees
        client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
        db = client['user']
        employees_collection = db['users']
        employees = employees_collection.find({"role": "employer"})
    
        total_assigned_folders = 0
    
        for employee in employees:
            if 'assigned_folder' in employee and employee['assigned_folder']:
                total_assigned_folders += 1
    
        return total_assigned_folders

    def count_rated_images(self):
        # Connect to MongoDB and get the list of employees
        client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
        db = client['user']
        employees_collection = db['users']
        employees = employees_collection.find({"role": "employer"})
    
        total_rated_images = 0
    
        for employee in employees:
            if 'csv_content' in employee:
                csv_content = employee['csv_content']
                # Convert the CSV content into a DataFrame
                csv_df = pd.read_csv(StringIO(csv_content))
                # Count the number of images that have been rated
                rated_images = csv_df['Rating'].notnull().sum()
                total_rated_images += rated_images
    
        return total_rated_images
    
    def count_object(self):
        client = MongoClient('mongodb+srv://hai798:Hai2001@application.ssy3iml.mongodb.net/')
        db = client['user']
        object_collection = db['detections']
        objects = object_collection.find()
        total_object = 0

        for object in objects:
            if 'object_count' in object:
                total_object += object['object_count']

        return total_object

    def plot_bar_chart(self, data, container):
        categories = list(data.keys())
        counts = [data[category] for category in categories]
        colors = ['blue', 'green']  # Different colors for each bar

        fig, ax = plt.subplots()
        y_pos = np.arange(len(categories))
        bar_width = 0.4  # Set bar thickness

        bars = ax.barh(y_pos, counts, align='center', color=colors, height=bar_width)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(categories)
        ax.set_xlabel('Count')
        ax.set_title('Statistics')

        # Display value at the end of each bar
        for i, bar in enumerate(bars):
            ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, str(counts[i]),
                    va='center', ha='right', color='white', fontweight='bold')

        # Add legend
        ax.legend(bars, categories)

        # Tạo một FigureCanvas từ biểu đồ và thêm vào container
        canvas = FigureCanvas(fig)
        layout = QVBoxLayout(container)
        layout.addWidget(canvas)

app = QApplication(sys.argv)
window = LoginForm()
window.show()
sys.exit(app.exec())