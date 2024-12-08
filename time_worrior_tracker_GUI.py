import sys
import subprocess
import json
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
    QDialog,
    QLineEdit,
    QLabel,
    QScrollArea,
    QTextEdit,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette, QColor, QFont


class TimeWarriorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TimeWarrior GUI (WSL)")

        # Initialize storage files
        self.config_file = "~/.timewarrior_gui_config.json"
        self.interval_info_file = "~/.timewarrior_gui_interval_info.json"

        # Check TimeWarrior installation and create directories
        if not self.check_timewarrior():
            sys.exit(1)

        self.deleted_tags = self.load_deleted_tags()
        self.interval_info = self.load_interval_info()

        # Initialize tracking variables
        self.current_task = None
        self.is_tracking = False

        self.init_ui()
        self.apply_dark_theme()
        self.load_tasks()

        # Timer for updating tracking duration display
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_tracking_duration)
        self.update_timer.start(1000)  # Update every second

    def check_timewarrior(self):
        """Check if TimeWarrior is installed and accessible in WSL"""
        try:
            # First ensure the directory structure exists
            if not self.ensure_data_directory():
                return False

            # Then check TimeWarrior installation
            result = subprocess.run(
                ["wsl", "timew", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            if result.returncode != 0:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("TimeWarrior Not Found in WSL")
                msg.setInformativeText(
                    "Please make sure TimeWarrior is installed in your WSL distribution.\n"
                    "You can install it using:\n"
                    "sudo apt-get update\n"
                    "sudo apt-get install timewarrior"
                )
                msg.setWindowTitle("Installation Required")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
                return False

            return True

        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error Checking TimeWarrior")
            msg.setInformativeText(f"Error: {str(e)}")
            msg.setWindowTitle("Error")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return False

    def ensure_data_directory(self):
        """Ensure TimeWarrior data directory exists in WSL"""
        try:
            # Create directories in WSL environment
            create_dirs_command = """
            mkdir -p ~/.timewarrior/data
            mkdir -p ~/.timewarrior/extensions
            touch ~/.timewarrior/timewarrior.cfg
            """

            result = subprocess.run(
                ["wsl", "bash", "-c", create_dirs_command],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            if result.returncode != 0:
                QMessageBox.warning(
                    self, "Error", f"Failed to create directories: {result.stderr}"
                )
                return False

            return True

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to initialize TimeWarrior directory structure: {str(e)}",
            )
            return False

    def run_timew_command(self, args):
        """Run a TimeWarrior command through WSL with proper error handling"""
        try:
            return subprocess.run(
                ["wsl", "timew"] + args,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Command Error",
                f"Error running TimeWarrior command in WSL: {str(e)}\n"
                f"Command: timew {' '.join(args)}",
            )
            return None

    def load_deleted_tags(self):
        """Load the list of deleted tags from config file in WSL"""
        try:
            # Check if config file exists in WSL
            check_file = subprocess.run(
                ["wsl", "test", "-f", self.config_file], capture_output=True
            )

            if check_file.returncode == 0:
                # File exists, read it
                result = subprocess.run(
                    ["wsl", "cat", self.config_file],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                if result.returncode == 0:
                    return set(json.loads(result.stdout).get("deleted_tags", []))
            return set()
        except Exception as e:
            print(f"Error loading config: {e}")
            return set()

    def save_deleted_tags(self):
        """Save the current list of deleted tags to config file in WSL"""
        try:
            config = {"deleted_tags": list(self.deleted_tags)}
            config_json = json.dumps(config)

            # Save to file in WSL
            save_command = f"echo '{config_json}' > {self.config_file}"
            result = subprocess.run(
                ["wsl", "bash", "-c", save_command],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            if result.returncode != 0:
                print(f"Error saving config: {result.stderr}")

        except Exception as e:
            print(f"Error saving config: {e}")

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Main layout
        main_layout = QHBoxLayout()

        # Left layout for project and task list
        left_layout = QVBoxLayout()

        # Create tree widget for projects and tasks
        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabel("Projects and Tasks")
        self.project_tree.setStyleSheet(
            """
            QTreeWidget {
                background-color: #2c2f33;
                color: white;
                font-size: 14px;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:selected {
                background-color: #7289da;
            }
            """
        )
        self.project_tree.itemClicked.connect(self.select_task)
        left_layout.addWidget(self.project_tree)

        # Add project and task buttons
        button_layout = QHBoxLayout()

        add_project_btn = QPushButton("Add Project")
        add_project_btn.setStyleSheet(
            "font-size: 18px; padding: 10px; background-color: #7289da; color: #FFFFFF;"
        )
        add_project_btn.clicked.connect(self.add_project)
        button_layout.addWidget(add_project_btn)

        add_task_btn = QPushButton("Add Task")
        add_task_btn.setStyleSheet(
            "font-size: 18px; padding: 10px; background-color: #43b581; color: #FFFFFF;"
        )
        add_task_btn.clicked.connect(self.add_task)
        button_layout.addWidget(add_task_btn)

        delete_btn = QPushButton("Delete Selected")
        delete_btn.setStyleSheet(
            "font-size: 18px; padding: 10px; background-color: #ff5c5c; color: #FFFFFF;"
        )
        delete_btn.clicked.connect(self.delete_selected)
        button_layout.addWidget(delete_btn)

        left_layout.addLayout(button_layout)

        # Right layout for interval display and tracking controls
        right_layout = QVBoxLayout()

        # Timer display
        self.timer_label = QLabel("No active tracking")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet(
            "font-size: 24px; padding: 10px; color: #FFFFFF;"
        )
        right_layout.addWidget(self.timer_label)

        # Start/Stop button
        self.start_stop_btn = QPushButton("Start")
        self.start_stop_btn.setStyleSheet(
            "font-size: 18px; padding: 10px; background-color: #43b581; color: #FFFFFF;"
        )
        self.start_stop_btn.clicked.connect(self.start_stop_tracking)
        self.start_stop_btn.setEnabled(False)
        right_layout.addWidget(self.start_stop_btn)

        # Logger label
        self.logger_label = QLabel("Select a task to view intervals.")
        self.logger_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.logger_label.setStyleSheet("color: white; font-size: 14px;")
        self.logger_label.setWordWrap(True)

        # Scroll area for logger
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.addWidget(self.logger_label)
        scroll_area.setWidget(scroll_content)

        right_layout.addWidget(scroll_area)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)

        main_widget.setLayout(main_layout)

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(33, 37, 43))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(42, 45, 50))
        palette.setColor(QPalette.AlternateBase, QColor(33, 37, 43))
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(54, 57, 63))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.Highlight, QColor(88, 101, 242))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        self.setPalette(palette)

    def load_tasks(self):
        """Load existing projects and tasks from TimeWarrior"""
        try:
            # Get all tags from TimeWarrior
            result = self.run_timew_command(["tags"])
            if result and result.stdout:
                tags = result.stdout.strip().split("\n")
                self.project_tree.clear()

                # Build project-task structure
                project_dict = {}
                for tag in tags:
                    tag = tag.strip()
                    if tag and not tag.startswith("Tracking"):
                        if tag in self.deleted_tags:
                            continue  # Skip deleted tags
                        if "-" in tag:
                            project_name, task_tag = tag.split("-", 1)
                            project_dict.setdefault(project_name, set()).add(task_tag)
                        else:
                            # Project without tasks
                            project_dict.setdefault(tag, set())

                # Populate the tree widget
                for project_name, task_tags in project_dict.items():
                    project_item = QTreeWidgetItem([project_name])
                    for task_tag in task_tags:
                        task_item = QTreeWidgetItem([task_tag])
                        project_item.addChild(task_item)
                    self.project_tree.addTopLevelItem(project_item)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load tasks: {str(e)}")

    def load_task_info(self):
        """Load task extra information from metadata file in WSL"""
        try:
            # Check if task info file exists in WSL
            check_file = subprocess.run(
                ["wsl", "test", "-f", self.task_info_file], capture_output=True
            )

            if check_file.returncode == 0:
                # File exists, read it
                result = subprocess.run(
                    ["wsl", "cat", self.task_info_file],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                if result.returncode == 0:
                    return json.loads(result.stdout)
            return {}
        except Exception as e:
            print(f"Error loading task info: {e}")
            return {}

    def save_task_info(self):
        """Save the task extra information to metadata file in WSL"""
        try:
            task_info_json = json.dumps(self.task_info)
            # Save to file in WSL
            save_command = f"echo '{task_info_json}' > {self.task_info_file}"
            result = subprocess.run(
                ["wsl", "bash", "-c", save_command],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            if result.returncode != 0:
                print(f"Error saving task info: {result.stderr}")

        except Exception as e:
            print(f"Error saving task info: {e}")

    def add_task(self):
        """Add a new task under a selected project"""
        selected_item = self.project_tree.currentItem()
        if not selected_item:
            QMessageBox.warning(
                self, "No Project Selected", "Please select a project to add a task."
            )
            return

        if selected_item.parent():
            # If a task is selected, get its parent project
            project_item = selected_item.parent()
        else:
            project_item = selected_item

        project_name = project_item.text(0)

        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Task")
        dialog.setStyleSheet(
            """
            QDialog {
                background-color: #2c2f33;
            }
            QLabel {
                color: white;
                font-size: 14px;
                padding: 5px;
            }
            QLineEdit {
                padding: 5px;
                font-size: 14px;
                background-color: #36393f;
                color: white;
                border: 1px solid #1a1c1e;
            }
            QPushButton {
                font-size: 14px;
                padding: 8px 16px;
                background-color: #7289da;
                color: white;
                border: none;
            }
        """
        )

        layout = QVBoxLayout()

        # Task tag input
        task_label = QLabel("Task Tag (required):")
        task_input = QLineEdit()
        layout.addWidget(task_label)
        layout.addWidget(task_input)

        button_layout = QHBoxLayout()
        ok_button = QPushButton("Add")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)

        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec_() == QDialog.Accepted:
            task_tag = task_input.text().strip()

            if not task_tag:
                QMessageBox.warning(self, "Error", "Task Tag is required!")
                return

            full_tag = f"{project_name}-{task_tag}"

            # Remove from deleted tags if it was previously deleted
            if full_tag in self.deleted_tags:
                self.deleted_tags.remove(full_tag)
                self.save_deleted_tags()

            # Add tag to TimeWarrior by starting and stopping an interval
            self.run_timew_command(["start", full_tag])
            self.run_timew_command(["stop"])

            # Add task to the project in the tree
            task_item = QTreeWidgetItem([task_tag])
            project_item.addChild(task_item)
            project_item.setExpanded(True)

    def edit_task(self):
        """Edit properties of an existing task or interval"""
        selected_item = self.project_tree.currentItem()
        if not selected_item:
            QMessageBox.warning(
                self, "No Selection", "Please select a task or interval to edit."
            )
            return

        # Determine if it's a task or project
        if not selected_item.parent():
            # Editing a project (we can implement project editing if needed)
            QMessageBox.information(
                self, "Edit Project", "Editing projects is not supported."
            )
            return
        else:
            task_name = selected_item.text(0)
            project_name = selected_item.parent().text(0)
            full_tag = f"{project_name}-{task_name}"

            # Get intervals for this task
            export_result = self.run_timew_command(["export"])
            if export_result and export_result.stdout:
                intervals = json.loads(export_result.stdout)
                relevant_intervals = [
                    interval
                    for interval in intervals
                    if full_tag in interval.get("tags", [])
                ]

                if not relevant_intervals:
                    QMessageBox.information(
                        self, "No Intervals", "No intervals found for this task."
                    )
                    return

                # Let the user select an interval to edit
                interval_choices = {
                    f"ID {interval.get('id')} | {interval.get('start')} - {interval.get('end')}": interval
                    for interval in relevant_intervals
                }

                interval_dialog = QDialog(self)
                interval_dialog.setWindowTitle("Select Interval to Edit")
                interval_dialog.setStyleSheet(
                    """
                    QDialog {
                        background-color: #2c2f33;
                    }
                    QLabel {
                        color: white;
                        font-size: 14px;
                        padding: 5px;
                    }
                    QComboBox {
                        padding: 5px;
                        font-size: 14px;
                        background-color: #36393f;
                        color: white;
                        border: 1px solid #1a1c1e;
                    }
                    QPushButton {
                        font-size: 14px;
                        padding: 8px 16px;
                        background-color: #7289da;
                        color: white;
                        border: none;
                    }
                """
                )

                layout = QVBoxLayout()
                label = QLabel("Select an interval to edit:")
                interval_combo = QComboBox()
                interval_combo.addItems(interval_choices.keys())
                layout.addWidget(label)
                layout.addWidget(interval_combo)

                button_layout = QHBoxLayout()
                ok_button = QPushButton("Edit")
                cancel_button = QPushButton("Cancel")
                button_layout.addWidget(ok_button)
                button_layout.addWidget(cancel_button)
                layout.addLayout(button_layout)

                interval_dialog.setLayout(layout)

                ok_button.clicked.connect(interval_dialog.accept)
                cancel_button.clicked.connect(interval_dialog.reject)

                if interval_dialog.exec_() == QDialog.Accepted:
                    selected_text = interval_combo.currentText()
                    selected_interval = interval_choices[selected_text]
                    self.edit_interval(selected_interval)
            else:
                QMessageBox.warning(self, "Error", "Failed to retrieve intervals.")

    def select_task_or_project(self, item):
        """Display intervals and extra information for the selected project or task"""
        if not item:
            return

        # If it's a project
        if not item.parent():
            project_name = item.text(0)
            self.current_task = project_name
            self.display_intervals_for_project(project_name)
        # If it's a task
        else:
            task_name = item.text(0)
            project_name = item.parent().text(0)
            full_tag = f"{project_name}-{task_name}"
            self.current_task = full_tag
            self.display_intervals_for_tag(full_tag)

        # Enable the Start/Stop button
        self.start_stop_btn.setEnabled(True)
        self.check_tracking_status()

    def select_task(self, item):
        """Display intervals for the selected task or project"""
        if not item:
            return

        if item.parent():
            # It's a task
            task_tag = item.text(0)
            project_name = item.parent().text(0)
            self.current_task = f"{project_name}-{task_tag}"

            self.display_intervals_for_tag(self.current_task)

            # Enable the Start/Stop button
            self.start_stop_btn.setEnabled(True)
            self.check_tracking_status()
        else:
            # It's a project
            self.current_task = item.text(0)
            self.display_intervals_for_project(self.current_task)

            # Disable the Start/Stop button for projects
            self.start_stop_btn.setEnabled(False)

    def add_project(self):
        """Add a new project"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Project")
        dialog.setStyleSheet(
            """
            QDialog {
                background-color: #2c2f33;
            }
            QLabel {
                color: white;
                font-size: 14px;
                padding: 5px;
            }
            QLineEdit {
                padding: 5px;
                font-size: 14px;
                background-color: #36393f;
                color: white;
                border: 1px solid #1a1c1e;
            }
            QPushButton {
                font-size: 14px;
                padding: 8px 16px;
                background-color: #7289da;
                color: white;
                border: none;
            }
        """
        )

        layout = QVBoxLayout()

        # Project name input
        project_label = QLabel("Project Name (required):")
        project_input = QLineEdit()
        layout.addWidget(project_label)
        layout.addWidget(project_input)

        button_layout = QHBoxLayout()
        ok_button = QPushButton("Add")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)

        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec_() == QDialog.Accepted:
            project_name = project_input.text().strip()

            if not project_name:
                QMessageBox.warning(self, "Error", "Project Name is required!")
                return

            # Remove from deleted tags if it was previously deleted
            if project_name in self.deleted_tags:
                self.deleted_tags.remove(project_name)
                self.save_deleted_tags()

            # Add project to TimeWarrior by starting and stopping an interval
            self.run_timew_command(["start", project_name])
            self.run_timew_command(["stop"])

            # Add project to tree
            project_item = QTreeWidgetItem([project_name])
            self.project_tree.addTopLevelItem(project_item)

    def delete_selected(self):
        """Delete selected project or task"""
        selected_item = self.project_tree.currentItem()
        if not selected_item:
            QMessageBox.warning(
                self, "No Selection", "Please select a project or task to delete."
            )
            return

        if selected_item.parent():
            # It's a task
            task_tag = selected_item.text(0)
            project_name = selected_item.parent().text(0)
            full_tag = f"{project_name}-{task_tag}"

            confirm = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete the task '{task_tag}' in project '{project_name}'?\nThis will hide all intervals associated with this task.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if confirm == QMessageBox.Yes:
                # Add task to deleted tags
                self.deleted_tags.add(full_tag)
                self.save_deleted_tags()

                # Remove from tree
                index = selected_item.parent().indexOfChild(selected_item)
                selected_item.parent().takeChild(index)
                self.logger_label.setText("Select a task to view intervals.")
                self.start_stop_btn.setEnabled(False)
        else:
            # It's a project
            project_name = selected_item.text(0)

            confirm = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete the project '{project_name}'?\nThis will hide all intervals associated with this project and its tasks.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if confirm == QMessageBox.Yes:
                # Add project and its tasks to deleted tags
                self.deleted_tags.add(project_name)
                for i in range(selected_item.childCount()):
                    task_item = selected_item.child(i)
                    task_tag = task_item.text(0)
                    full_tag = f"{project_name}-{task_tag}"
                    self.deleted_tags.add(full_tag)
                self.save_deleted_tags()

                # Remove from tree
                index = self.project_tree.indexOfTopLevelItem(selected_item)
                self.project_tree.takeTopLevelItem(index)
                self.logger_label.setText("Select a task to view intervals.")
                self.start_stop_btn.setEnabled(False)

    def start_stop_tracking(self):
        """Start or stop tracking for the selected task"""
        if not self.current_task or "-" not in self.current_task:
            QMessageBox.warning(
                self, "No Task Selected", "Please select a task to track."
            )
            return

        if self.is_tracking:
            self.stop_tracking()
        else:
            self.start_tracking()

    def start_tracking(self):
        """Start tracking time for the current task"""
        result = self.run_timew_command(["start", self.current_task])
        if result and result.returncode == 0:
            self.is_tracking = True
            self.start_stop_btn.setText("Stop")
            self.start_stop_btn.setStyleSheet(
                "font-size: 18px; padding: 10px; background-color: #ff5c5c; color: #FFFFFF;"
            )
            self.timer_label.setText("Tracking...")
        else:
            QMessageBox.warning(self, "Error", "Failed to start tracking.")
    
    def stop_tracking(self):
        """Stop tracking time"""
        result = self.run_timew_command(["stop"])
        if result and result.returncode == 0:
            self.is_tracking = False
            self.start_stop_btn.setText("Start")
            self.start_stop_btn.setStyleSheet(
                "font-size: 18px; padding: 10px; background-color: #43b581; color: #FFFFFF;"
            )
            self.timer_label.setText("No active tracking")

            # Get the ID of the last interval
            interval_id = self.get_last_interval_id()
            if interval_id:
                # Prompt for extra information
                self.prompt_for_interval_info(interval_id)

            # Refresh intervals display
            self.display_intervals_for_tag(self.current_task)
        else:
            QMessageBox.warning(self, "Error", "Failed to stop tracking.")

    def update_tracking_duration(self):
        """Update the timer label with the current tracking duration"""
        if self.is_tracking:
            # Get the current active tracking information
            result = self.run_timew_command([])
            if result and result.stdout:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "Tracking" in line:
                        # Extract the duration from the line
                        parts = line.split()
                        if len(parts) >= 2:
                            duration = parts[1]
                            self.timer_label.setText(f"Tracking: {duration}")
                        break
        else:
            self.timer_label.setText("No active tracking")

    def check_tracking_status(self):
        """Check if the current task is being tracked"""
        result = self.run_timew_command([])
        if result and result.stdout:
            if self.current_task in result.stdout:
                self.is_tracking = True
                self.start_stop_btn.setText("Stop")
                self.start_stop_btn.setStyleSheet(
                    "font-size: 18px; padding: 10px; background-color: #ff5c5c; color: #FFFFFF;"
                )
            else:
                self.is_tracking = False
                self.start_stop_btn.setText("Start")
                self.start_stop_btn.setStyleSheet(
                    "font-size: 18px; padding: 10px; background-color: #43b581; color: #FFFFFF;"
                )
        else:
            self.is_tracking = False
            self.start_stop_btn.setText("Start")
            self.start_stop_btn.setStyleSheet(
                "font-size: 18px; padding: 10px; background-color: #43b581; color: #FFFFFF;"
            )

    def load_interval_info(self):
        """Load interval extra information from metadata file in WSL"""
        try:
            # Check if interval info file exists in WSL
            check_file = subprocess.run(
                ["wsl", "test", "-f", self.interval_info_file], capture_output=True
            )

            if check_file.returncode == 0:
                # File exists, read it
                result = subprocess.run(
                    ["wsl", "cat", self.interval_info_file],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                if result.returncode == 0:
                    return json.loads(result.stdout)
            return {}
        except Exception as e:
            print(f"Error loading interval info: {e}")
            return {}

    def save_interval_info(self):
        """Save the interval extra information to metadata file in WSL"""
        try:
            interval_info_json = json.dumps(self.interval_info)
            # Save to file in WSL
            save_command = f"echo '{interval_info_json}' > {self.interval_info_file}"
            result = subprocess.run(
                ["wsl", "bash", "-c", save_command],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            if result.returncode != 0:
                print(f"Error saving interval info: {result.stderr}")

        except Exception as e:
            print(f"Error saving interval info: {e}")

    def edit_interval(self, interval):
        """Edit properties of a specific interval"""
        interval_id = str(interval.get("id"))
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Interval ID {interval_id}")
        dialog.setStyleSheet(
            """
            QDialog {
                background-color: #2c2f33;
            }
            QLabel {
                color: white;
                font-size: 14px;
                padding: 5px;
            }
            QLineEdit, QTextEdit, QDateTimeEdit {
                padding: 5px;
                font-size: 14px;
                background-color: #36393f;
                color: white;
                border: 1px solid #1a1c1e;
            }
            QPushButton {
                font-size: 14px;
                padding: 8px 16px;
                background-color: #7289da;
                color: white;
                border: none;
            }
        """
        )

        layout = QVBoxLayout()

        # Start time
        start_label = QLabel("Start Time:")
        start_time_edit = QDateTimeEdit()
        start_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        start_time = QDateTime.fromString(
            interval.get("start").replace("T", " ").split("Z")[0], "yyyy-MM-dd HH:mm:ss"
        )
        start_time_edit.setDateTime(start_time)
        layout.addWidget(start_label)
        layout.addWidget(start_time_edit)

        # End time
        end_label = QLabel("End Time:")
        end_time_edit = QDateTimeEdit()
        end_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        end_time = QDateTime.fromString(
            interval.get("end").replace("T", " ").split("Z")[0], "yyyy-MM-dd HH:mm:ss"
        )
        end_time_edit.setDateTime(end_time)
        layout.addWidget(end_label)
        layout.addWidget(end_time_edit)

        # Tags
        tags_label = QLabel("Tags (comma-separated):")
        tags_input = QLineEdit()
        tags_input.setText(", ".join(interval.get("tags", [])))
        layout.addWidget(tags_label)
        layout.addWidget(tags_input)

        # Extra information
        extra_info_label = QLabel("Extra Information:")
        extra_info_input = QTextEdit()
        extra_info_input.setFixedHeight(100)
        existing_info = self.interval_info.get(interval_id, "")
        extra_info_input.setPlainText(existing_info)
        layout.addWidget(extra_info_label)
        layout.addWidget(extra_info_input)

        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)

        save_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec_() == QDialog.Accepted:
            # Get updated values
            new_start = start_time_edit.dateTime().toString("yyyy-MM-ddTHH:mm:ssZ")
            new_end = end_time_edit.dateTime().toString("yyyy-MM-ddTHH:mm:ssZ")
            new_tags = [
                tag.strip() for tag in tags_input.text().split(",") if tag.strip()
            ]
            extra_info = extra_info_input.toPlainText().strip()

            # Modify the interval using timew modify
            modify_command = [
                "modify",
                f"@{interval_id}",
                f"start:{new_start}",
                f"end:{new_end}",
            ] + new_tags

            result = self.run_timew_command(modify_command)
            if result and result.returncode == 0:
                # Update extra information
                self.interval_info[interval_id] = extra_info
                self.save_interval_info()

                QMessageBox.information(
                    self, "Success", "Interval updated successfully."
                )

                # Refresh display
                if "-" in self.current_task:
                    self.display_intervals_for_tag(self.current_task)
                else:
                    self.display_intervals_for_project(self.current_task)
            else:
                QMessageBox.warning(self, "Error", "Failed to modify interval.")

    def display_intervals_for_project(self, project_name):
        """Display intervals for the selected project"""
        try:
            # Get all intervals associated with the project and its tasks
            export_result = self.run_timew_command(["export"])
            if export_result and export_result.stdout:
                intervals = json.loads(export_result.stdout)
                relevant_intervals = [
                    interval
                    for interval in intervals
                    if any(
                        (tag == project_name or tag.startswith(f"{project_name}-"))
                        and tag not in self.deleted_tags
                        for tag in interval.get("tags", [])
                    )
                ]

                display_text = ""

                if relevant_intervals:
                    # Include interval extra information
                    for interval in relevant_intervals:
                        interval_id = str(interval.get("id"))
                        interval_extra_info = self.interval_info.get(interval_id, "")
                        if interval_extra_info:
                            interval["extra_info"] = interval_extra_info

                    # Display intervals in JSON format
                    formatted_json = json.dumps(relevant_intervals, indent=4)
                    display_text += f"<b>Intervals:</b>\n{formatted_json}"
                else:
                    display_text += f"No intervals found for project '{project_name}'."

                self.logger_label.setText(display_text)
            else:
                self.logger_label.setText(
                    f"No intervals found for project '{project_name}'."
                )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load intervals: {str(e)}")
            self.logger_label.setText("")

    def get_last_interval_id(self):
        """Retrieve the ID of the most recent interval"""
        try:
            export_result = self.run_timew_command(["export"])
            if export_result and export_result.stdout:
                intervals = json.loads(export_result.stdout)
                if intervals:
                    # Assuming the last interval is the most recent one
                    last_interval = intervals[-1]
                    return str(last_interval.get("id"))
            return None
        except Exception as e:
            print(f"Error retrieving last interval ID: {e}")
            return None

    def prompt_for_interval_info(self, interval_id):
        """Prompt the user to enter extra information for an interval"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Interval Extra Information")
        dialog.setStyleSheet(
            """
            QDialog {
                background-color: #2c2f33;
            }
            QLabel {
                color: white;
                font-size: 14px;
                padding: 5px;
            }
            QTextEdit {
                padding: 5px;
                font-size: 14px;
                background-color: #36393f;
                color: white;
                border: 1px solid #1a1c1e;
            }
            QPushButton {
                font-size: 14px;
                padding: 8px 16px;
                background-color: #7289da;
                color: white;
                border: none;
            }
        """
        )

        layout = QVBoxLayout()

        info_label = QLabel("Enter extra information for this interval:")
        info_input = QTextEdit()
        info_input.setFixedHeight(100)
        layout.addWidget(info_label)
        layout.addWidget(info_input)

        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Skip")
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)

        save_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec_() == QDialog.Accepted:
            extra_info = info_input.toPlainText().strip()
            if extra_info:
                self.interval_info[interval_id] = extra_info
                self.save_interval_info()

    def display_intervals_for_tag(self, tag):
        """Display intervals and extra information for a specific tag"""
        try:
            # Get all intervals associated with the tag
            export_result = self.run_timew_command(["export"])
            if export_result and export_result.stdout:
                intervals = json.loads(export_result.stdout)
                relevant_intervals = [
                    interval
                    for interval in intervals
                    if tag in interval.get("tags", [])
                ]

                display_text = ""

                if relevant_intervals:
                    # Include interval extra information
                    for interval in relevant_intervals:
                        interval_id = str(interval.get("id"))
                        interval_extra_info = self.interval_info.get(interval_id, "")
                        if interval_extra_info:
                            interval["extra_info"] = interval_extra_info

                    # Display intervals in JSON format
                    formatted_json = json.dumps(relevant_intervals, indent=4)
                    display_text += f"<b>Intervals:</b>\n{formatted_json}"
                else:
                    display_text += f"No intervals found for task '{tag}'."

                self.logger_label.setText(display_text)
            else:
                self.logger_label.setText(f"No intervals found for task '{tag}'.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load intervals: {str(e)}")
            self.logger_label.setText("")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set application-wide font
    font = QFont()
    font.setPointSize(10)
    app.setFont(font)

    window = TimeWarriorGUI()
    window.show()
    sys.exit(app.exec_())
