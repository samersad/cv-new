import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter import ttk
import face_recognition
import cv2
import os
import pickle
import numpy as np
import csv
from datetime import datetime
from PIL import Image, ImageTk  # combbddddddddddddddddddd

from openpyxl import Workbook
from tkinter import filedialog

def export_attendance_to_excel():
    if not os.path.exists(ATTENDANCE_FILE):
        messagebox.showinfo("Export", "No attendance records found.")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance Report"
    ws.append(["Username", "Timestamp"])

    with open(ATTENDANCE_FILE, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            ws.append(row)

    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if file_path:
        wb.save(file_path)
        messagebox.showinfo("Export", f"Attendance exported to:\n{file_path}")


# === إعداد المسارات ===
KNOWN_FACES_DIR = 'known_faces'
ENCODINGS_FILE = 'face_encodings.pkl'
USERS_CSV_FILE = 'users.csv'
ATTENDANCE_FILE = 'attendance_report.csv'

# إنشاء مجلدات عند الحاجة
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

# تحميل الوجوه المسجلة
if os.path.exists(ENCODINGS_FILE):
    with open(ENCODINGS_FILE, 'rb') as f:
        known_face_encodings, known_usernames = pickle.load(f)
else:
    known_face_encodings = []
    known_usernames = []

# === متغيرات المستخدم الحالي ===
current_user = None
current_role = None

# === دوال النظام ===

def register_user():
    username = simpledialog.askstring("Register", "Enter new username:")
    if not username:
        return

    role = simpledialog.askstring("Role", "Enter role (admin/user):", initialvalue="user")
    if role not in ("admin", "user"):
        messagebox.showerror("Error", "Invalid role. Choose 'admin' or 'user'.")
        return

    cap = cv2.VideoCapture(0)
    messagebox.showinfo("Info", "Position your face and press 's' to capture.")

    while True:
        ret, frame = cap.read()
        cv2.imshow("Register - Press 's' to save", frame)

        if cv2.waitKey(1) & 0xFF == ord('s'):
            face_locations = face_recognition.face_locations(frame)
            if len(face_locations) != 1:
                messagebox.showerror("Error", "Ensure exactly one face is visible.")
                continue

            face_encoding = face_recognition.face_encodings(frame, face_locations)[0]
            known_face_encodings.append(face_encoding)
            known_usernames.append(username)

            with open(ENCODINGS_FILE, 'wb') as f:
                pickle.dump((known_face_encodings, known_usernames), f)

            user_folder = os.path.join(KNOWN_FACES_DIR, username)
            os.makedirs(user_folder, exist_ok=True)
            image_path = os.path.join(user_folder, f"{username}.jpg")
            cv2.imwrite(image_path, frame)

            # حفظ الصلاحية في ملف CSV
            with open(USERS_CSV_FILE, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([username, role])

            messagebox.showinfo("Success", f"{username} ({role}) registered.")
            break
        # سجل من قام بالتسجيل ومتى
        with open('registration_log.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([username, role, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    
    cap.release()
    cv2.destroyAllWindows()

def view_registration_log():

    if not os.path.exists('registration_log.csv'):
        messagebox.showinfo("Registration Log", "No registration records found.")
        return

    log_window = tk.Toplevel(app)
    log_window.title("Registration Log")
    log_window.geometry("500x300")

    text = tk.Text(log_window, wrap='word')
    text.pack(expand=True, fill='both')

    with open('registration_log.csv', mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            text.insert('end', f"Username: {row[0]}, Role: {row[1]}, Time: {row[2]}\n")
def view_attendance_log():
    if not os.path.exists(ATTENDANCE_FILE):
        messagebox.showinfo("Attendance Log", "No attendance records found.")
        return

    attendance_window = tk.Toplevel(app)
    attendance_window.title("Attendance Log")
    attendance_window.geometry("500x300")

    text = tk.Text(attendance_window, wrap='word')
    text.pack(expand=True, fill='both')

    with open(ATTENDANCE_FILE, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            text.insert('end', f"Name: {row[0]}, Time: {row[1]}\n")

def login_user():
    global current_user, current_role

    cap = cv2.VideoCapture(0)
    messagebox.showinfo("Info", "Looking for face... Press 'q' to stop.")

    success = False
    while True:
        ret, frame = cap.read()
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        face_locations = face_recognition.face_locations(small_frame)
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

            if matches:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    user = known_usernames[best_match_index]
                    current_user = user

                    # استخراج الصلاحية من users.csv
                    current_role = "user"
                    if os.path.exists(USERS_CSV_FILE):
                        with open(USERS_CSV_FILE, mode='r') as file:
                            reader = csv.reader(file)
                            for row in reader:
                                if row[0] == user:
                                    current_role = row[1]
                                    break

                    # إذا كان المستخدم admin نطلب كلمة المرور
                    if current_role == "admin":
                        password = simpledialog.askstring("Admin Login", "Enter admin password:", show='*')
                        if password != "123":
                            messagebox.showerror("Error", "Incorrect admin password!")
                            current_user = None
                            current_role = None
                            cap.release()
                            cv2.destroyAllWindows()
                            return
                            
                    messagebox.showinfo("Access Granted", f"Welcome {user}!\nRole: {current_role}")
                    success = True
                    break

        cv2.imshow("Login", frame)
        if success or cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if current_role == "admin":
        show_admin_button()
def delete_user():
    if current_role != "admin":
        messagebox.showerror("Error", "Only admins can delete users.")
        return

    username_to_delete = simpledialog.askstring("Delete User", "Enter the username of the user to delete:")
    if not username_to_delete:
        return

    # قراءة ملف CSV للبحث عن المستخدم ودوره
    user_found = False
    is_admin = False
    users = []

    if os.path.exists(USERS_CSV_FILE):
        with open(USERS_CSV_FILE, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                users.append(row)
                if row[0] == username_to_delete:
                    user_found = True
                    if row[1] == "admin":
                        is_admin = True

    if not user_found:
        messagebox.showerror("Error", f"User '{username_to_delete}' not found.")
        return

    if is_admin:
        messagebox.showerror("Error", "You cannot delete an admin user.")
        return

    # حذف من قائمة الوجوه إن وُجد
    if username_to_delete in known_usernames:
        index = known_usernames.index(username_to_delete)
        del known_usernames[index]
        del known_face_encodings[index]

        with open(ENCODINGS_FILE, 'wb') as f:
            pickle.dump((known_face_encodings, known_usernames), f)

    # تحديث ملف CSV بدون المستخدم
    users = [user for user in users if user[0] != username_to_delete]

    with open(USERS_CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(users)

    # حذف مجلد صور المستخدم
    user_folder = os.path.join(KNOWN_FACES_DIR, username_to_delete)
    if os.path.exists(user_folder):
        for filename in os.listdir(user_folder):
            file_path = os.path.join(user_folder, filename)
            os.remove(file_path)
        os.rmdir(user_folder)

    messagebox.showinfo("Success", f"User '{username_to_delete}' has been deleted.")
    if current_role != "admin":
        messagebox.showerror("Error", "Only admins can delete users.")
        return

    username_to_delete = simpledialog.askstring("Delete User", "Enter the username of the user to delete:")
    if not username_to_delete:
        return

    # حذف من ملف الوجوه
    if username_to_delete in known_usernames:
        index = known_usernames.index(username_to_delete)
        del known_usernames[index]
        del known_face_encodings[index]

        with open(ENCODINGS_FILE, 'wb') as f:
            pickle.dump((known_face_encodings, known_usernames), f)

    # حذف من ملف CSV
    users = []
    with open(USERS_CSV_FILE, mode='r') as file:
        reader = csv.reader(file)
        users = [row for row in reader]

    users = [user for user in users if user[0] != username_to_delete]

    with open(USERS_CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(users)

    # حذف الصور من مجلد الوجوه
    user_folder = os.path.join(KNOWN_FACES_DIR, username_to_delete)
    if os.path.exists(user_folder):
        for filename in os.listdir(user_folder):
            file_path = os.path.join(user_folder, filename)
            os.remove(file_path)
        os.rmdir(user_folder)

    messagebox.showinfo("Success", f"User {username_to_delete} has been deleted.")
def show_admin_button():
    admin_button = ttk.Button(app, text="admin_dashboard  ",image=admin_dashboard_icon,compound="left", command=admin_dashboard, style="TButton").pack(pady=10)

    delete_button = ttk.Button(app, text="delete users ",image=delete_users_icon, compound="left",command=delete_user, style="TButton").pack(pady=10)

    log_button = ttk.Button(app, text="Registration Log",image=Registration_Log_icon, compound="left", command=view_registration_log, style="TButton").pack(pady=10)

    attendance_log_button = ttk.Button(app, text="Attendance Log",image=Attendance_Log_icon, compound="left", command=view_attendance_log, style="TButton").pack(pady=10)

    export_excel_button = ttk.Button(app, text="Export Attendance to Excel", command=export_attendance_to_excel,style="TButton").pack(pady=10)



def admin_dashboard():
    messagebox.showinfo("admin_dashboard", f"wellcome {current_user} (Admin)\n You can perform administrative tasks here.")


def detect_team_members():
    cap = cv2.VideoCapture(0)
    messagebox.showinfo("Team Detection", "Detecting team members... Press 'q' to stop.")
    present_members = set()

    while True:
        ret, frame = cap.read()
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        face_locations = face_recognition.face_locations(small_frame)
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)

        names_in_frame = []

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            name = "Unknown"

            if matches:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_usernames[best_match_index]
                    present_members.add(name)

            names_in_frame.append(name)

        for (top, right, bottom, left), name in zip(face_locations, names_in_frame):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0) if name != "Unknown" else (0, 0, 255), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        cv2.imshow("Team Members Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if present_members:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(ATTENDANCE_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            for member in present_members:
                writer.writerow([member, timestamp])

        messagebox.showinfo("Detected", f"Team Members Present:\n{', '.join(present_members)}\n\nSaved to attendance_report.csv")
    else:
        messagebox.showinfo("Detected", "No team members detected.")


# === الواجهة الرسومية ===

app = tk.Tk()
app.title("Face Recognition System")
app.geometry("400x400")  # زيادة حجم نافذة التطبيق
app.configure(bg="#F0F0FF")

# إضافة أيقونات للأزرار مع تكبير حجم الأيقونات
login_icon = Image.open("login.png")
login_icon = login_icon.resize((40, 40))    
login_icon = ImageTk.PhotoImage(login_icon)

register_icon = Image.open("register.png")
register_icon = register_icon.resize((40, 40))  
register_icon = ImageTk.PhotoImage(register_icon)

attendance_icon = Image.open("attendance.png")
attendance_icon = attendance_icon.resize((40, 40))  
attendance_icon = ImageTk.PhotoImage(attendance_icon)

exit_icon = Image.open("exit.png")
exit_icon = exit_icon.resize((40, 40))  
exit_icon = ImageTk.PhotoImage(exit_icon)

admin_dashboard_icon = Image.open("administrator.png")
admin_dashboard_icon = admin_dashboard_icon.resize((40, 40))  
admin_dashboard_icon = ImageTk.PhotoImage(admin_dashboard_icon)

delete_users_icon = Image.open("delete.png")
delete_users_icon = delete_users_icon.resize((40, 40))  
delete_users_icon = ImageTk.PhotoImage(delete_users_icon)


Registration_Log_icon = Image.open("registration-log.png")
Registration_Log_icon = Registration_Log_icon.resize((40, 40))  
Registration_Log_icon = ImageTk.PhotoImage(Registration_Log_icon)

Attendance_Log_icon = Image.open("attendance-log.png")
Attendance_Log_icon = Attendance_Log_icon.resize((40, 40))  
Attendance_Log_icon = ImageTk.PhotoImage(Attendance_Log_icon)
# تحسين الأزرار باستخدام ttk
tk.Label(app, text="Face Recognition System", font=("Arial", 16, "bold"), bg="#F0F0FF", fg="black").pack(pady=20)

ttk.Button(app, text="Login with Face", image=login_icon, compound="left", command=login_user, style="TButton").pack(pady=10)
ttk.Button(app, text="Register New User", image=register_icon, compound="left", command=register_user, style="TButton").pack(pady=10)
ttk.Button(app, text="Team Attendance", image=attendance_icon, compound="left", command=detect_team_members, style="TButton").pack(pady=10)
ttk.Button(app, text="Exit", image=exit_icon, compound="left", command=app.quit, style="TButton").pack(pady=10)  

app.mainloop()
