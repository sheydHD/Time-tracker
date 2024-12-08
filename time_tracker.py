import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QInputDialog,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QGridLayout,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette, QColor
import datetime
import os

# Get the directory of the .exe file (or script if run as Python script)
base_dir = (
    os.path.dirname(sys.executable)
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))
)

db_path = os.path.join(base_dir, "tasks.db")


class Task:
    def __init__(self, name):
        self.name = name
        self.time_logs = []  # List of tuples (start_time, end_time)
        self.current_start_time = None

    def start(self):
        if not self.current_start_time:
            self.current_start_time = datetime.datetime.now()

    def stop(self):
        if self.current_start_time:
            end_time = datetime.datetime.now()
            self.time_logs.append((self.current_start_time, end_time))
            self.current_start_time = None

    def total_time(self, period="all"):
        total = datetime.timedelta()
        now = datetime.datetime.now()

        for start, end in self.time_logs:
            if period == "day" and start.date() != now.date():
                continue
            if period == "week" and start.isocalendar()[1] != now.isocalendar()[1]:
                continue
            if period == "month" and start.month != now.month:
                continue
            total += end - start
        return total


class TimeTrackerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Time Tracker")
        self.showFullScreen()
        self.tasks = {}
        self.current_task = None

        self.init_db()
        self.init_ui()
        self.apply_dark_theme()

        QApplication.instance().aboutToQuit.connect(self.save_state_on_close)

    def init_db(self):
        # Connect to the database using the dynamically created db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS time_logs (
                id INTEGER PRIMARY KEY,
                task_id INTEGER,
                start_time TEXT,
                end_time TEXT,
                duration TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        """
        )
        self.conn.commit()

    def init_ui(self):
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Layouts
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Task List and Buttons
        self.task_list = QListWidget()
        self.task_list.setStyleSheet(
            "font-size: 18px; padding: 10px; background-color: #2c2f33; color: #FFFFFF;"
        )
        self.task_list.itemClicked.connect(self.select_task)
        left_layout.addWidget(self.task_list)

        add_task_btn = QPushButton("Add Task")
        add_task_btn.setStyleSheet(
            "font-size: 18px; padding: 10px; background-color: #7289da; color: #FFFFFF;"
        )
        add_task_btn.clicked.connect(self.add_task)
        left_layout.addWidget(add_task_btn)

        modify_task_btn = QPushButton("Modify Task Name")
        modify_task_btn.setStyleSheet(
            "font-size: 18px; padding: 10px; background-color: #7289da; color: #FFFFFF;"
        )
        modify_task_btn.clicked.connect(self.modify_task_name)
        left_layout.addWidget(modify_task_btn)

        delete_task_btn = QPushButton("Delete Selected")
        delete_task_btn.setStyleSheet(
            "font-size: 18px; padding: 10px; background-color: #7289da; color: #FFFFFF;"
        )
        delete_task_btn.clicked.connect(self.delete_selected_tasks)
        left_layout.addWidget(delete_task_btn)

        exit_btn = QPushButton("Exit")
        exit_btn.setStyleSheet(
            "font-size: 18px; padding: 10px; background-color: #ff5c5c; color: #FFFFFF;"
        )
        exit_btn.clicked.connect(self.close)
        left_layout.addWidget(exit_btn)

        left_layout.addStretch()
        left_layout.setStretch(0, 1)
        left_layout.setStretch(1, 0)
        left_layout.setStretch(2, 0)
        left_layout.setStretch(3, 0)
        left_layout.setStretch(4, 0)

        # Task Timer and Details
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setAlignment(Qt.AlignLeft)
        self.timer_label.setStyleSheet(
            "font-size: 48px; padding: 10px; color: #FFFFFF;"
        )
        right_layout.addWidget(self.timer_label)

        self.start_stop_btn = QPushButton("Start")
        self.start_stop_btn.setStyleSheet(
            "font-size: 24px; padding: 10px; background-color: #43b581; color: #FFFFFF;"
        )
        self.start_stop_btn.clicked.connect(self.start_stop_timer)
        right_layout.addWidget(self.start_stop_btn)

        self.task_name_label = QLabel("Select a task")
        self.task_name_label.setAlignment(Qt.AlignLeft)
        self.task_name_label.setStyleSheet(
            "font-size: 24px; padding: 10px; color: #FFFFFF;"
        )
        right_layout.addWidget(self.task_name_label)

        # Log Panel with Labels
        log_content_widget = QWidget()
        log_content_layout = QVBoxLayout(log_content_widget)
        log_content_layout.setAlignment(
            Qt.AlignTop
        )  # Ensure content starts from the top

        header_layout = QGridLayout()
        start_header = QLabel("Start Time")
        start_header.setStyleSheet("font-size: 18px; padding: 5px; color: #FFFFFF;")
        end_header = QLabel("End Time")
        end_header.setStyleSheet("font-size: 18px; padding: 5px; color: #FFFFFF;")
        duration_header = QLabel("Duration")
        duration_header.setStyleSheet("font-size: 18px; padding: 5px; color: #FFFFFF;")
        action_header = QLabel("Action")
        action_header.setStyleSheet("font-size: 18px; padding: 5px; color: #FFFFFF;")
        header_layout.addWidget(start_header, 0, 0)
        header_layout.addWidget(end_header, 0, 1)
        header_layout.addWidget(duration_header, 0, 2)
        header_layout.addWidget(action_header, 0, 3)
        log_content_layout.addLayout(header_layout)

        self.details_time_logs_label = QGridLayout()
        self.details_time_logs_label.setAlignment(Qt.AlignTop)  # Align logs to the top
        time_logs_widget = QWidget()
        time_logs_widget.setLayout(self.details_time_logs_label)
        log_content_layout.addWidget(time_logs_widget)

        log_scroll = QScrollArea()
        log_scroll.setWidgetResizable(True)
        log_scroll.setWidget(log_content_widget)
        right_layout.addWidget(log_scroll)

        # Total Time Label
        self.total_time_label = QLabel("Total Time: 00:00:00")
        self.total_time_label.setStyleSheet(
            "font-size: 18px; padding: 10px; color: #FFFFFF;"
        )
        right_layout.addWidget(self.total_time_label)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 3)

        main_widget.setLayout(main_layout)

        # Timer to update the elapsed time
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        self.load_tasks()
        self.start_stop_btn.setEnabled(True)  # Enable start button by default

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(33, 37, 43))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(42, 45, 50))
        palette.setColor(QPalette.AlternateBase, QColor(33, 37, 43))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(54, 57, 63))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(88, 101, 242))
        palette.setColor(QPalette.Highlight, QColor(88, 101, 242))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        self.setPalette(palette)

    def save_state_on_close(self):
        """Ensure any running task is logged with an end time when the app closes."""
        if self.current_task and self.current_task.current_start_time:
            # Stop the task with the current time as the end time
            end_time = datetime.datetime.now()
            task_id = next(
                (tid for tid, task in self.tasks.items() if task == self.current_task),
                None,
            )

            if task_id:
                start_time = self.current_task.current_start_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                duration = str(end_time - self.current_task.current_start_time).split(
                    "."
                )[0]

                # Update the database
                self.cursor.execute(
                    "UPDATE time_logs SET end_time = ?, duration = ? WHERE task_id = ? AND start_time = ? AND end_time IS NULL",
                    (
                        end_time.strftime("%Y-%m-%d %H:%M:%S"),
                        duration,
                        task_id,
                        start_time,
                    ),
                )
                self.conn.commit()
            self.current_task.stop()

    def add_task(self):
        text, ok = QInputDialog.getText(self, "Add Task", "Task Name:")
        if not ok:
            return  # The user canceled the dialog, do nothing
        if not text.strip():
            QMessageBox.warning(self, "Error", "Task name cannot be empty.")
            return

        # Insert task into database
        self.cursor.execute("INSERT INTO tasks (name) VALUES (?)", (text,))
        self.conn.commit()
        task_id = self.cursor.lastrowid

        # Add task to dictionary and UI list
        self.tasks[task_id] = Task(text)
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, task_id)
        self.task_list.addItem(item)

        # Automatically select the new task
        self.task_list.setCurrentItem(item)
        self.select_task(item)

    def load_tasks(self):
        self.cursor.execute("SELECT id, name FROM tasks")
        rows = self.cursor.fetchall()
        for task_id, name in rows:
            self.tasks[task_id] = Task(name)
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, task_id)
            self.task_list.addItem(item)

    def select_task(self, item):
        task_id = item.data(Qt.UserRole)
        self.current_task = self.tasks[task_id]
        self.task_name_label.setText(self.current_task.name)
        self.start_stop_btn.setEnabled(True)
        self.update_task_details(task_id)

    def update_task_details(self, task_id):
        self.cursor.execute(
            "SELECT id, start_time, end_time, duration FROM time_logs WHERE task_id = ?",
            (task_id,),
        )
        rows = self.cursor.fetchall()
        total_time = datetime.timedelta()
        # Clear previous logs
        for i in reversed(range(self.details_time_logs_label.count())):
            item = self.details_time_logs_label.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        # Update logs with new data
        for row_idx, (log_id, start_time, end_time, duration) in enumerate(rows):
            start_label = QLabel(start_time)
            start_label.setStyleSheet("font-size: 18px; padding: 5px; color: #FFFFFF;")
            end_label = QLabel(end_time if end_time else "In Progress")
            end_label.setStyleSheet("font-size: 18px; padding: 5px; color: #FFFFFF;")
            duration_label = QLabel(duration if duration else "...")
            duration_label.setStyleSheet(
                "font-size: 18px; padding: 5px; color: #FFFFFF;"
            )
            self.details_time_logs_label.addWidget(start_label, row_idx, 0)
            self.details_time_logs_label.addWidget(end_label, row_idx, 1)
            self.details_time_logs_label.addWidget(duration_label, row_idx, 2)
            if end_time:  # Only add delete button if the log entry is complete
                delete_button = QPushButton("Delete")
                delete_button.setStyleSheet(
                    "font-size: 18px; padding: 5px; background-color: #ff5c5c; color: #FFFFFF;"
                )
                delete_button.clicked.connect(
                    lambda checked, log_id=log_id: self.delete_log_entry(log_id)
                )
                self.details_time_logs_label.addWidget(delete_button, row_idx, 3)
            if end_time:
                start_dt = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                end_dt = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                total_time += end_dt - start_dt
        self.total_time_label.setText(f"Total Time: {str(total_time)}")

    def delete_log_entry(self, log_id):
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this log entry?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            # Delete the log entry from the database
            self.cursor.execute("DELETE FROM time_logs WHERE id = ?", (log_id,))
            self.conn.commit()
            # Refresh the task details
            task_id = next(
                (tid for tid, task in self.tasks.items() if task == self.current_task),
                None,
            )
            self.update_task_details(task_id)

    def modify_task_name(self):
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self, "No Task Selected", "Please select a task to modify."
            )
            return

        item = selected_items[0]
        task_id = item.data(Qt.UserRole)
        current_name = self.tasks[task_id].name

        new_name, ok = QInputDialog.getText(
            self, "Modify Task Name", "New Task Name:", text=current_name
        )
        if not ok or not new_name.strip():
            return  # The user canceled the dialog or entered an empty name

        # Update task name in the database
        self.cursor.execute(
            "UPDATE tasks SET name = ? WHERE id = ?", (new_name, task_id)
        )
        self.conn.commit()

        # Update task name in the UI
        self.tasks[task_id].name = new_name
        item.setText(new_name)
        self.task_name_label.setText(new_name)

    def delete_selected_tasks(self):
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self, "No Task Selected", "Please select tasks to delete."
            )
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_items)} selected task(s)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            for item in selected_items:
                task_id = item.data(Qt.UserRole)
                if self.current_task and task_id == task_id:
                    self.stop_current_task()
                self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                self.cursor.execute(
                    "DELETE FROM time_logs WHERE task_id = ?", (task_id,)
                )
                self.conn.commit()
                self.task_list.takeItem(self.task_list.row(item))
                del self.tasks[task_id]

            # Clear the details in the UI since the selected task(s) are deleted
            self.current_task = None
            self.task_name_label.setText("Select a task")
            self.timer_label.setText("00:00:00")
            self.total_time_label.setText("Total Time: 00:00:00")

            # Clear all the log details displayed in the layout
            for i in reversed(range(self.details_time_logs_label.count())):
                item = self.details_time_logs_label.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()

            # Disable the Start/Stop button as there's no task selected anymore
            self.start_stop_btn.setText("Start")
            self.start_stop_btn.setEnabled(False)

    def start_stop_timer(self):
        if self.current_task is None:
            # No task is selected
            # Check if "Daily task" exists
            daily_task_id = None
            for task_id, task in self.tasks.items():
                if task.name == "Daily task":
                    daily_task_id = task_id
                    break
            if daily_task_id is None:
                # Create "Daily task"
                self.cursor.execute(
                    "INSERT INTO tasks (name) VALUES (?)", ("Daily task",)
                )
                self.conn.commit()
                daily_task_id = self.cursor.lastrowid
                self.tasks[daily_task_id] = Task("Daily task")
                item = QListWidgetItem("Daily task")
                item.setData(Qt.UserRole, daily_task_id)
                self.task_list.addItem(item)
            else:
                # Find the QListWidgetItem corresponding to daily_task_id
                item = None
                for index in range(self.task_list.count()):
                    temp_item = self.task_list.item(index)
                    if temp_item.data(Qt.UserRole) == daily_task_id:
                        item = temp_item
                        break
            # Select the task
            self.task_list.setCurrentItem(item)
            self.select_task(item)

        if self.current_task.current_start_time:
            # Stop the timer
            self.stop_current_task()
        else:
            # Start the timer
            self.current_task.start()
            self.timer.start(1000)
            self.start_stop_btn.setText("Stop")
            self.log_session_start()  # Log that the session has started
        self.update_timer()

    def stop_current_task(self):
        if self.current_task and self.current_task.current_start_time:
            # Stop the timer
            self.current_task.stop()
            self.timer.stop()
            self.start_stop_btn.setText("Start")

            # Save stop time to database
            task_id = next(
                (tid for tid, task in self.tasks.items() if task == self.current_task),
                None,
            )
            start_time = self.current_task.time_logs[-1][0].strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            end_time = self.current_task.time_logs[-1][1].strftime("%Y-%m-%d %H:%M:%S")
            duration = str(
                self.current_task.time_logs[-1][1] - self.current_task.time_logs[-1][0]
            ).split(".")[0]
            self.cursor.execute(
                "UPDATE time_logs SET end_time = ?, duration = ? WHERE task_id = ? AND start_time = ? AND end_time IS NULL",
                (end_time, duration, task_id, start_time),
            )
            self.conn.commit()
            self.update_task_details(task_id)  # Refresh the task details immediately

    def update_timer(self):
        if self.current_task and self.current_task.current_start_time:
            elapsed = datetime.datetime.now() - self.current_task.current_start_time
            self.timer_label.setText(str(elapsed).split(".")[0])
        else:
            self.timer_label.setText("00:00:00")

    def log_session_start(self):
        task_id = next(
            (tid for tid, task in self.tasks.items() if task == self.current_task), None
        )
        start_time = self.current_task.current_start_time.strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO time_logs (task_id, start_time, end_time, duration) VALUES (?, ?, ?, ?)",
            (task_id, start_time, None, None),
        )
        self.conn.commit()
        self.update_task_details(task_id)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimeTrackerApp()
    window.show()
    sys.exit(app.exec_())
