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

class AssignFolderDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assign Folder to Employer")
        self.setGeometry(200, 200, 400, 300)

        self.layout = QVBoxLayout()
        self.employee_list_widget = QListWidget()
        self.layout.addWidget(self.employee_list_widget)
        self.mongo_uri = os.getenv('MONGO_URI')
        self.setLayout(self.layout)

        self.populate_employee_list()

    def populate_employee_list(self):
        # Connect to MongoDB and get the list of employees
        client = MongoClient(self.mongo_uri)
        db = client['user']
        employees_collection = db['users']
        employees = employees_collection.find({"role": "employer"})

        # Add employees to the list widget
        for employee in employees:
            name = employee["username"]
            item = QListWidgetItem(name)
            self.employee_list_widget.addItem(item)

            # Add a button to upload folder for each employee
            upload_btn = QPushButton("Upload Folder")
            upload_btn.clicked.connect(lambda checked, name=name: self.upload_folder(name))
            self.employee_list_widget.setItemWidget(item, upload_btn)

    def upload_folder(self, username):
        folder_path = QFileDialog.getExistingDirectory(self, f'Select Folder for {username}', "C:\\")
        if folder_path:
            # Save the assigned folder path to the database
            client = MongoClient(self.mongo_uri)
            db = client['user']
            employees_collection = db['users']
            employees_collection.update_one({'username': username}, {"$set": {'assigned_folder': folder_path}})
            QMessageBox.information(self, "Success", f"Folder assigned to {username}")

class FolderUploadDialog(QDialog):
    def __init__(self):
        super(FolderUploadDialog, self).__init__()
        self.setWindowTitle("Upload Folder")
        self.setGeometry(100, 100, 400, 200)
        
        self.layout = QVBoxLayout()
        
        self.upload_btn = QPushButton("Upload Folder")
        self.upload_btn.clicked.connect(self.upload_folder)
        self.layout.addWidget(self.upload_btn)
        
        self.assign_btn = QPushButton("Assign to...")
        self.assign_btn.clicked.connect(self.open_assign_folder_dialog)
        self.layout.addWidget(self.assign_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_btn)
        
        self.setLayout(self.layout)
        self.folder_path = None
    
    def upload_folder(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder', "C:\\")
        if self.folder_path:
            self.upload_btn.setText("Folder Selected")

    def open_assign_folder_dialog(self):
        assign_folder_dialog = AssignFolderDialog()
        assign_folder_dialog.exec()

    def get_folder_path(self):
        return self.folder_path

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
        
        self.initDialog()
        self.initKeyBoard()
        
        self.setupButton()
        self.retranslateUi()

        self.mongo_uri = os.getenv('MONGO_URI')
        self.username = username
        self.role = role

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
        
    def get_assigned_save_folder(self):
        client = MongoClient(self.mongo_uri)
        db = client['user']
        users_collection = db['users']
        user = users_collection.find_one({'username': self.username})
        return user.get('assigned_folder')
    
    def choose_excel_folder(self):
        if self.dataset is None:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText("You should click to \"Select Dir\" button to choose image dir")
            msg.setWindowTitle("Warn")
            msg.exec()
        else:
            if self.role == "employer":
                self.csv_folder = self.get_assigned_save_folder()
                if not self.csv_folder or not os.path.exists(self.csv_folder):
                    QMessageBox.information(self, "No Save Folder Assigned", "No save folder has been assigned to you yet. Please contact the admin.")
                    return
            else:
                self.csv_folder = QFileDialog.getExistingDirectory(self, 'Open Folder', "C:\\")
            
            self.csv_path = os.path.join(self.csv_folder, "label_image.csv")
            
            if not(os.path.exists(self.csv_path)):
                self.csv_file = pd.DataFrame()
                self.csv_file["Name"] = pd.Series(self.dataset)
                self.csv_file["Rating"] = pd.Series([])
                self.csv_file.to_csv(self.csv_path, index=False)
            else:
                self.csv_file = pd.read_csv(self.csv_path)
            
            # Đọc nội dung của file CSV
            with open(self.csv_path, 'r') as file:
                csv_content = file.read()

            # Lưu nội dung của file CSV vào cơ sở dữ liệu
            client = MongoClient(self.mongo_uri)
            db = client['user']
            users_collection = db['users']
            users_collection.update_one({'username': self.username}, {"$set": {'csv_content': csv_content}})
            QMessageBox.information(self, "Success", f"CSV content saved for {self.username}")
                
            self.show_image(self.index, self.resized_mode, self.convert_mode)

    def save_csv_content_to_db(self):
        if self.csv_path and self.username:
            # Đọc nội dung của file CSV
            with open(self.csv_path, 'r') as file:
                csv_content = file.read()

            # Lưu nội dung của file CSV vào cơ sở dữ liệu
            client = MongoClient(self.mongo_uri)
            db = client['user']
            users_collection = db['users']
            users_collection.update_one({'username': self.username}, {"$set": {'csv_content': csv_content}})
            QMessageBox.information(self, "Success", f"CSV content saved for {self.username}")


    def read_csv_from_folder(self, folder_path):
        csv_path = os.path.join(folder_path, "label_image.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            return df
        else:
            print(f"CSV file 'label_image.csv' not found in folder '{folder_path}'")
        return None

    def load_image_dir_func(self):
        if self.role == "admin":
            self.open_folder_upload_dialog()
        else:
            client = MongoClient(self.mongo_uri)
            db = client['user']
            users_collection = db['users']
            user = users_collection.find_one({'username': self.username})
            self.fname = user.get('assigned_folder')
            
            if self.fname and os.path.exists(self.fname):
                self.dataset = os.listdir(self.fname)
                self.index = 0
                self.show_image(self.index, self.resized_mode, self.convert_mode)
                self.total_image_label.setText("/" + str(len(self.dataset)))
            else:
                QMessageBox.information(self, "No Folder Assigned", "No folder has been assigned to you yet. Please contact the admin.")

    def open_folder_upload_dialog(self):
        dialog = FolderUploadDialog()
        if dialog.exec():
            self.fname = dialog.get_folder_path()
            if self.fname and os.path.exists(self.fname):
                self.dataset = os.listdir(self.fname)
                self.index = 0
                self.show_image(self.index, self.resized_mode, self.convert_mode)
                self.total_image_label.setText("/" + str(len(self.dataset)))
        
    def show_image(self, index):
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
        
    def save_csv(self):
        
        if self.csv_file is not None and self.csv_path is not None:
            self.csv_file.to_csv(self.csv_path, index=False)
            
            self.show_notification_pop_up("Save successfully", "Sucess")
        
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
        self.show_image(self.index, self.resized_mode, self.convert_mode)      
        
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
        self.show_image(self.index, self.resized_mode, self.convert_mode)
    
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
            self.show_image(self.index, self.resized_mode, self.convert_mode)
            
        
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

        # Save xlsx dir selection
        self.save_dir_btn = QPushButton(self.screenStatic)
        self.save_dir_btn.setGeometry(QRect(60, 190, 211, 51))
        self.save_dir_btn.setStyleSheet("border-radius: 20px;\n""font: 75 16pt \"MS Shell Dlg 2\";\n"
                                      "background-color: rgb(85, 255, 255);\n""color: #000000;")
        self.save_dir_btn.setObjectName("save_dir_btn")
        
        # Manual save button 
        self.manual_save_btn = QPushButton(self.screenStatic)
        self.manual_save_btn.setGeometry(QRect(60, 260, 211, 51))
        self.manual_save_btn.setStyleSheet("border-radius: 20px;\n""font: 75 16pt \"MS Shell Dlg 2\";\n"
                                      "background-color: rgb(85, 255, 255);\n""color: #000000;")
        self.manual_save_btn.setObjectName("manual_save_btn")

        # Back to Menu
        self.main_menu_btn = QPushButton(self.screenStatic)
        self.main_menu_btn.setGeometry(QRect(60, 330, 211, 51))
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
        # Chọn đường dẫn chứa file csv gán nhãn
        self.save_dir_btn.setText(_translate("Dialog", "Select Save Dir"))
        # Label result 
        self.result_label.setText(_translate("Dialog", "Result:"))
        # Manual save 
        self.manual_save_btn.setText(_translate("Dialog", "Save All Label"))
        # Go direct to image 
        self.change_image_btn.setText(_translate("Dialog", "Go"))
        #Back to menu
        self.main_menu_btn.setText(_translate("Dialog", "Back"))
        
    def setupButton(self):
        self.dir_selection_btn.clicked.connect(self.load_image_dir_func)
        self.save_dir_btn.clicked.connect(self.choose_excel_folder)
        self.manual_save_btn.clicked.connect(self.save_csv)
        self.change_image_btn.clicked.connect(self.go_to_image)
        self.main_menu_btn.clicked.connect(self.main_menu)

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