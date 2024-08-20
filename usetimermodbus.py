import sys
from PyQt5.QtWidgets import (QMainWindow, QApplication,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QSpinBox,QMessageBox,QGroupBox,QDialog,QDialogButtonBox,QLineEdit,QGridLayout,QSizePolicy,QSpacerItem
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QByteArray
from PyQt5.QtGui import QPixmap
import random
import pandas as pd
import threading, time,os
from pymodbus.client import ModbusTcpClient
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR"] = "1"

class AddTimeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Time")
        self.setLayout(QVBoxLayout())

        self.init_input_spinboxes()
        self.init_buttons()

    def init_input_spinboxes(self):
        labels_and_ranges = [
            ("Minutes:", 59),
            ("Seconds:", 59),
            ("Milliseconds:", 9)
        ]
        self.spinboxes = []

        for label_text, max_value in labels_and_ranges:
            self.add_spinbox_row(label_text, max_value)
#
    def add_spinbox_row(self, label_text, max_value):
        row_layout = QHBoxLayout()
        row_layout.addWidget(QLabel(label_text))
        spinbox = QSpinBox()
        spinbox.setRange(0, max_value)
        self.spinboxes.append(spinbox)
        row_layout.addWidget(spinbox)
        self.layout().addLayout(row_layout)

    def init_buttons(self):
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout().addWidget(button_box)

    def get_additional_time(self):
        minutes, seconds, milliseconds = [sb.value() for sb in self.spinboxes]
        total_milliseconds = (minutes * 60 + seconds) * 1000 + milliseconds
        return total_milliseconds


class RenameTeamDialog(QDialog):
    team_code_changed = pyqtSignal(str)

    def __init__(self, parent=None, current_code=""):
        super().__init__(parent)
        self.setWindowTitle("Rename Team Code")
        self.layout = QVBoxLayout(self)

        self.label = QLabel("Enter new team code:")
        self.layout.addWidget(self.label)

        self.code_input = QLineEdit(current_code)
        self.layout.addWidget(self.code_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_new_code(self):
        return self.code_input.text()

    def accept(self):
        new_code = self.get_new_code()
        self.team_code_changed.emit(new_code)
        super().accept()

from PyQt5.QtCore import pyqtSignal, QObject

class AutoShopTimers(QObject):
    complete_timer_signal = pyqtSignal(int)  # Signal to indicate timer completion
    def __init__(self, team_widgets):
        super().__init__()  # Initialize the QObject part
        self.client = None
        self.modbus_host = '192.168.1.75'
        self.modbus_port = 502
        self.team_widgets = team_widgets
        self.timers = {
            200: self.team_widgets[0],
            202: self.team_widgets[1],
            204: self.team_widgets[2],
            206: self.team_widgets[3],
            208: self.team_widgets[4]
        }
        self.completed_addresses = set()  # Track completed addresses
        # Connect the signal to the slot
        self.complete_timer_signal.connect(self.handle_timer_completion)
        # Start a separate thread to listen for Modbus signals
        threading.Thread(target=self.modbus_listener, daemon=True).start()

    def connect_to_modbus(self):
        try:
            self.client = ModbusTcpClient(self.modbus_host, port=self.modbus_port)
            if not self.client.connect():
                print(f"Failed to connect to Modbus server at {self.modbus_host}:{self.modbus_port}")
                self.client = None
            else:
                print(f"Connected to Modbus server at {self.modbus_host}:{self.modbus_port}")
        except Exception as e:
            print(f"Error connecting to Modbus server: {e}")
            self.client = None

    def handle_timer_completion(self, address):
        if address in self.timers:
            self.timers[address].complete_timer()
            print(f"Timer completed for widget associated with address {address}")

    def modbus_listener(self):
        while True:
            if self.client is None or not self.client.is_socket_open():
                print("Attempting to reconnect to Modbus server...")
                self.connect_to_modbus()
                if self.client is None:
                    print("Reconnection failed, retrying in 5 seconds...")
                    time.sleep(5)
                    continue

            for address in list(self.timers.keys()):  # Iterate over a copy of the keys
                if address in self.completed_addresses:
                    continue  # Skip addresses that have already received the complete signal

                try:
                    response = self.client.read_holding_registers(address, 1)
                    if response.isError():
                        print(f"Error reading Modbus register at address {address}")
                    else:
                        value = response.registers[0]
                        print(f"Modbus listener signal from address {address}: {value}")
                        if value == 1:  # Adjust the condition as needed
                            self.complete_timer_signal.emit(address)
                            self.completed_addresses.add(address)  # Mark address as completed
                except Exception as e:
                    print(f"Error reading Modbus data: {e}")
                    self.client.close()  # Close the client to force reconnection
                    self.client = None
                    break  # Exit loop to retry connection

            time.sleep(0.4)  # Check every 0.4 seconds



# class AutoShopTimers:
#     def __init__(self, team_widgets):
#         self.client = ModbusTcpClient('192.168.1.75', port=502)  # Replace with PLC's IP and port
#         self.team_widgets = team_widgets
#         self.timers = {
#             200: self.team_widgets[0],
#             202: self.team_widgets[1],
#             204: self.team_widgets[2],
#             206: self.team_widgets[3],
#             208: self.team_widgets[4]
#         }
#         self.completed_addresses = set()  # Track completed addresses
#         # Start a separate thread to listen for Modbus signals
#         threading.Thread(target=self.modbus_listener, daemon=True).start()

#     def modbus_listener(self):
#         while True:
#             for address in list(self.timers.keys()):  # Iterate over a copy of the keys
#                 if address in self.completed_addresses:
#                     continue  # Skip addresses that have already received the complete signal
                
#                 response = self.client.read_holding_registers(address, 1)
#                 if response.isError():
#                     print(f"Error reading Modbus register at address {address}")
#                 else:
#                     value = response.registers[0]
#                     print(f"Modbus listener signal from address {address}: {value}")
#                     if value == 1:  # Adjust the condition as needed
#                         self.timers[address].complete_timer()
#                         print(f"Sent signal to complete timer for widget associated with address {address}")
#                         self.completed_addresses.add(address)  # Mark address as completed

#             time.sleep(0.4)  # Check every 0.2 seconds


class TWidgetBase(QGroupBox):
    def __init__(self, title):
        super().__init__()
        self.setTitle(title)
        self.time_left = 0
        self.initial_time = 0
        self.additional_time_left = 0
        self.complete = False
        self.paused = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        
        self.start_button = self.create_button("Start", self.toggle_timer)
        self.reset_button = self.create_button("Reset", self.reset_timer)
        self.add_time_button = self.create_button("Add Time", self.add_time_dialog)


        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.layout)
        self.setStyleSheet(
            """
            QGroupBox {background-color: #FDF3E7; color: #424242; border: 2px solid #FFA726; border-radius: 10px; padding: 1px; }
            QLabel { color: #424242; }
            """
        )
        #timer display
        self.timer_display = QLabel("00:00:0", alignment=Qt.AlignCenter)
        self.timer_display.setStyleSheet(
            """
            QLabel { font-size: 240px; font-weight: bold; color: #FF7043; background-color: #FDF3E7; text-align: center; padding: 0; font-family: 'Roboto Mono', monospace; letter-spacing: -1px; }
            """
        )
        #Addition team timer display:
        self.additional_time_display = QLabel("+00:00:0")
        self.additional_time_display.setStyleSheet(
            """font-size: 25px; font-weight: 2px; color: red; font-family: 'Courier New', monospace; letter-spacing: -2px;"""
        )

    def create_button(self, text, callback, width=100):
        button = QPushButton(text)
        button.clicked.connect(callback)
        button.setFixedWidth(width)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setStyleSheet(
            """
            QPushButton { color: #424242; background-color: #FFE0B2; border: 1px solid #ccc; padding: 5px; font-size: 16px; border-radius: 9px; }
            QPushButton:hover { background-color: #FFCC80; border-color: #bbb; }
            """
        )
        return button

    # def toggle_timer(self):
    #     if self.paused:
    #         if self.time_left > 0:
    #             self.timer.start(100)
    #         elif self.additional_time_left > 0:
    #             self.timer.start(100)
            
    #         self.start_button.setText("Pause")
    #     else:
    #         self.timer.stop()
    #         self.start_button.setText("Resume")
    #     self.paused = not self.paused

    def toggle_timer(self):
        if self.paused:
            if self.time_left > 0 or self.additional_time_left > 0:
                self.timer.start(100)
            
            self.start_button.setText("Pause")
            self.start_button.setStyleSheet(
            """
            QPushButton { color: #424242; background-color: #FFE0B2; border: 1px solid #ccc; padding: 5px; font-size: 16px; border-radius: 9px; }
            QPushButton:hover { background-color: #FFCC80; border-color: #bbb; }
            """
        )
            # self.start_button.setStyleSheet("background-color: red; color: white;")
        else:
            self.timer.stop()
            self.start_button.setText("Resume")
            self.start_button.setStyleSheet(
            """
            QPushButton { color: #424242; background-color: red; border: 1px solid #ccc; padding: 5px; font-size: 16px; border-radius: 9px; }
            QPushButton:hover { background-color: #FFCC80; border-color: #bbb; }
            """
        )
        self.paused = not self.paused


    def reset_timer(self):
        self.timer.stop()
        self.time_left = 0
        self.additional_time_left = 0
        self.update_display()
        self.start_button.setText("Start")
        self.paused = True
        self.complete = False

    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 100
            self.update_display()
            if self.time_left <= 0:
                self.time_left = 0
        elif self.additional_time_left > 0:
            self.additional_time_left -= 100
            self.update_display()
            if self.additional_time_left <= 0:
                self.additional_time_left = 0
        else:
            self.timer.stop()
            self.start_button.setText("Start")
            self.paused = True
            

    def update_display(self):
        minutes = self.time_left // 1000 // 60
        seconds = (self.time_left // 1000) % 60
        milliseconds = (self.time_left % 1000) // 100
        self.timer_display.setText(f"{minutes:02d}:{seconds:02d}:{milliseconds:01d}")

        # Update additional time display
        additional_minutes = self.additional_time_left // 1000 // 60
        additional_seconds = (self.additional_time_left // 1000) % 60
        additional_milliseconds = (self.additional_time_left % 1000) // 100
        self.additional_time_display.setText(f"+{additional_minutes:02d}:{additional_seconds:02d}:{additional_milliseconds:01d}")
    
        
    def add_time_dialog(self):
        dialog = AddTimeDialog(self)
        if dialog.exec_():
            self.additional_time = dialog.get_additional_time()
            # Initialize total additional time if it does not exist
            if not hasattr(self, 'total_additional_time_set'):
                self.total_additional_time_set = 0
            # Update additional time and cumulative total
            self.additional_time_left += self.additional_time
            self.total_additional_time_set += self.additional_time
            self.update_display()
    


class TeamTimerWidget(TWidgetBase):
    def __init__(self, team_number, team_code, teams_df):
        super().__init__(f"Station #{team_number}")
        self.team_number = team_number
        self.teams_df = teams_df
        self.team_code = team_code  # Initialize team_code
        self.team_name = self.get_team_name_from_code(team_code)  # Initialize team_name
        self.additional_time_left = 0
        self.total_additional_time_set = 0
        self.init_ui()  # Initialize the UI components

    def init_ui(self):
        team_info_layout = QVBoxLayout()
        
        # Team Code Label
        self.team_code_label = QLabel(f"{self.team_code}")
        self.team_code_label.setStyleSheet(
            """font-size: 24px; font-weight: bold; color: #424242; background-color: none;"""
        )
        team_info_layout.addWidget(self.team_code_label, alignment=Qt.AlignCenter)

        # Team Name Label
        self.team_name_label = QLabel(self.wrap_text(self.team_name))
        self.team_name_label.setWordWrap(True)
        self.team_name_label.setStyleSheet(
            """font-size: 24px; font-weight: bold; color: #424242; background-color: none;"""
        )
        team_info_layout.addWidget(self.team_name_label, alignment=Qt.AlignCenter)
        
        # Add team info layout
        self.layout.addLayout(team_info_layout)
        self.layout.addStretch(1)

        # Timer Display
        self.timer_display.setStyleSheet(
            """font-size: 70px; font-weight: bold; color: #FF7043; font-family: 'Courier New', monospace; letter-spacing: -8px;"""
        )
        self.timer_display.setFixedWidth(250)
        self.layout.addWidget(self.timer_display, alignment=Qt.AlignCenter)
        
        self.layout.addWidget(self.additional_time_display, alignment=Qt.AlignCenter)
        self.layout.addItem(QSpacerItem(0, 30, QSizePolicy.Expanding, QSizePolicy.Fixed))

        # Row 1 Buttons (Start and Reset)
        row1_buttons_layout = QHBoxLayout()
        row1_buttons_layout.addWidget(self.start_button)
        row1_buttons_layout.addWidget(self.reset_button)
        self.layout.addLayout(row1_buttons_layout)
        
        # Row 2 Buttons (Add Time and Rename)
        row2_buttons_layout = QHBoxLayout()
        self.rename_button = self.create_button("Rename", self.rename_team_dialog)
        row2_buttons_layout.addWidget(self.add_time_button)
        row2_buttons_layout.addWidget(self.rename_button)
        
        # Vertical Layout for Buttons
        team_button_vertical_layout = QVBoxLayout()
        team_button_vertical_layout.addLayout(row2_buttons_layout)
   
        # Complete Button
        self.complete_button = self.create_button("Complete", self.complete_timer, 250)
        self.complete_button.setStyleSheet(
            """
            QPushButton { color: white; background-color: grey; border: 1px solid #ccc; padding: 5px; font-size: 16px; border-radius: 10px; }
            QPushButton:hover { background-color: green; border-color: #bbb; }
            """
        )
        self.complete_button.setFixedHeight(60)
        team_button_vertical_layout.addWidget(self.complete_button, alignment=Qt.AlignBottom)
        self.layout.addLayout(team_button_vertical_layout)

    def complete_timer(self):
        print("TeamCode:", self.team_code," | Team:", self.team_name)
        super().complete_timer() 

    def wrap_text(self, text):
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            if len(' '.join(current_line)) > 20:
                lines.append(' '.join(current_line[:-1]))
                current_line = [word]
        lines.append(' '.join(current_line))

        # Join lines with <br> and wrap in a center-aligned div
        return '<div style="text-align:center;">' + '<br>'.join(lines) + '</div>'


    def rename_team_dialog(self):
        dialog = RenameTeamDialog(self, self.team_code)
        dialog.team_code_changed.connect(self.update_team_code)
        dialog.exec_()

    def update_team_code(self, new_code):
        self.set_team_code(new_code)

    def get_team_name_from_code(self, team_code):
        team_name_row = self.teams_df[self.teams_df['team code'] == team_code]
        if not team_name_row.empty:
            return team_name_row.iloc[0]['team name']
        else:
            return "Unknown Team"

    def set_team_code(self, team_code):
        self.team_code = team_code
        self.team_name = self.get_team_name_from_code(team_code)
        self.team_code_label.setText(f"{self.team_code}")
        self.team_name_label.setText(self.wrap_text(self.team_name))
    
    def complete_timer(self):
        self.timer.stop()
        self.start_button.setText("Start")
        self.paused = True
        self.complete_button.setStyleSheet(
            """
            QPushButton { color: white; background-color: green; border: 1px solid #ccc; padding: 5px; font-size: 16px; border-radius: 10px; }
            QPushButton:hover { background-color: green; border-color: #bbb; }
            """
        )
        self.start_button.setStyleSheet(
            """
            QPushButton { color: #424242; background-color: #FFE0B2; border: 1px solid #ccc; padding: 5px; font-size: 16px; border-radius: 9px; }
            QPushButton:hover { background-color: #FFCC80; border-color: #bbb; }
            """
        )

        elapsed_main_time = self.initial_time - self.time_left
        # Calculate total additional time set
        total_additional_seconds = self.total_additional_time_set // 1000

        # Calculate actual additional time used
        actual_additional_time_used = total_additional_seconds - (self.additional_time_left// 1000)
        actual_additional_seconds = actual_additional_time_used % 60

        # Calculate total time used combined with the main time
        total_time_used = (elapsed_main_time// 1000) + actual_additional_time_used
        total_minutes = total_time_used // 60
        total_seconds = total_time_used % 60

        # Print the results
        print("TeamCode:", self.team_code," | Team:", self.team_name)
        print(f"Main Timer time use =  {elapsed_main_time // 1000 // 60:02}:{(elapsed_main_time // 1000) % 60:02}")
        print(f"Total Additional Time Set: {total_additional_seconds // 60:02}:{total_additional_seconds % 60:02}")
        print(f"Actual Additional Time Used: {actual_additional_seconds // 60:02}:{actual_additional_seconds % 60:02}")
        print(f"Total Time Used =  {total_minutes:02} min {total_seconds:02} sec")

        # Reset the additional time left after calculation
        self.additional_time_left = 0
        self.complete = True
    
    
    def reset_timer(self) :
        super().reset_timer()
        self.complete_button.setStyleSheet(
            """
            QPushButton { color: white; background-color: grey; border: 1px solid #ccc; padding: 5px; font-size: 16px; border-radius: 10px; 
            }
            QPushButton:hover { background-color: gray; border-color: #bbb; 
            }"""
        )
    
    def update_display(self):
        super().update_display()
        # Update additional time display
        additional_minutes = self.additional_time_left // 1000 // 60
        additional_seconds = (self.additional_time_left // 1000) % 60
        additional_milliseconds = (self.additional_time_left % 1000) // 100
        self.additional_time_display.setText(f"+{additional_minutes:02d}:{additional_seconds:02d}:{additional_milliseconds:01d}")



class MainTimerWidget(TWidgetBase):
    def __init__(self):
        super().__init__("Main Timer")
        self.setTitle("Main Timer")
        self.init_ui()
        

    def init_ui(self):
        self.timer_display.setFixedSize(1000, 240) #main timer display
        self.layout.addWidget(self.timer_display, alignment=Qt.AlignCenter)

        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignCenter)
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.reset_button)
        buttons_layout.addWidget(self.add_time_button)
        self.layout.addLayout(buttons_layout)

        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)


    def add_time_dialog(self):
        dialog = AddTimeDialog(self)
        if dialog.exec_():
            self.additional_time = dialog.get_additional_time()
            # Update additional time and cumulative total
            self.time_left += self.additional_time
            self.update_display()

class TeamTimersApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Team Timers App")
        self.init_ui()
        self.auto_shop_timers = AutoShopTimers(self.team_widgets)
        # Restore the state when initializing
        self.restore_state()

    def closeEvent(self, event):
        # Save state securely before closing
        self.save_state()
        super().closeEvent(event)

    def save_state(self):
        # Save the window state to a file
        try:
            with open("app_state.txt", "w") as f:
                f.write(self.saveState().toHex().data().decode('utf-8'))
            print("State saved successfully.")
        except Exception as e:
            print(f"Error saving state: {e}")

    def restore_state(self):
        # Restore the window state from a file
        try:
            with open("app_state.txt", "r") as f:
                state = QByteArray.fromHex(f.read().encode('utf-8'))
                self.restoreState(state)
            print("State restored successfully.")
        except Exception as e:
            print(f"Error restoring state: {e}")

    def init_ui(self):
        self.setWindowTitle("Team Timers")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowOpacity(1)

        self.central_widget = QWidget()  # Create a central widget
        self.setCentralWidget(self.central_widget)  # Set the central widget

        self.layout = QHBoxLayout(self.central_widget)  # Set layout on central widget

        self.init_content_widget()
        self.init_circle_widget()

        self.layout.addWidget(self.content_widget)
        self.layout.addWidget(self.circle_widget)

        self.background_label = QLabel(self.central_widget)
        self.background_label.setPixmap(QPixmap("nncb.jpg"))
        self.background_label.setScaledContents(True)
        self.background_label.lower()

    def init_content_widget(self):
        self.content_widget = QWidget()  # Initialize the content widget
        self.content_layout = QVBoxLayout(self.content_widget)  # Create a layout for the content widget
        # Add content to content_widget using self.content_layout
        # Example:
        # self.content_layout.addWidget(QLabel("Content Here"))

    def init_circle_widget(self):
        self.circle_widget = QWidget()  # Initialize the circle widget
        self.circle_layout = QVBoxLayout(self.circle_widget)  # Create a layout for the circle widget
        # Add content to circle_widget using self.circle_layout
        # Example:
        # self.circle_layout.addWidget(QLabel("Circle Here"))


    def init_content_widget(self):
        self.content_layout = QVBoxLayout()
        self.content_layout.addItem(QSpacerItem(50, 170, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.main_control_group = QGroupBox()

        self.main_control_layout = QHBoxLayout()  # Changed to QHBoxLayout for horizontal stacking
        self.main_control_group.setLayout(self.main_control_layout)
        self.main_control_group.setStyleSheet(
            "QGroupBox { background-color: #FDF3E7; color: black; border: 2px solid #FFA726; padding: 2px }"
        )

        self.main_timer_widget = MainTimerWidget()
        self.main_timer_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_timer_widget.setStyleSheet(
            "QGroupBox { background-color: #FDF3E7; color: black; border: none; padding: 6px }"
        )

        self.control_layout = QVBoxLayout()
        self.toggle_stop_resume_button = QPushButton("Start All")
        self.toggle_stop_resume_button.clicked.connect(self.toggle_stop_resume)
        self.toggle_stop_resume_button.setStyleSheet(
            "QPushButton { font-size: 20px; font-weight: bold; background-color: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 8px; } QPushButton:hover { background-color: #218838; }")
        self.control_layout.addWidget(self.toggle_stop_resume_button)

        self.reset_all_button = QPushButton("Reset All")
        self.reset_all_button.clicked.connect(self.reset_all_timers)
        self.reset_all_button.setStyleSheet(
            "QPushButton { font-size: 20px; font-weight: bold; background-color: #ffc107; color: white; border: none; padding: 10px 20px; border-radius: 8px; } QPushButton:hover { background-color: #e0a800; }")
        self.control_layout.addWidget(self.reset_all_button)

        self.set_same_time_button = QPushButton("Set Same Time")
        self.set_same_time_button.clicked.connect(self.set_same_time)
        self.set_same_time_button.setStyleSheet(
            "QPushButton { font-size: 20px; font-weight: bold; background-color: #6c757d; color: white; border: none; padding: 10px 20px; border-radius: 8px; } QPushButton:hover { background-color: #5a6268; }")
        self.control_layout.addWidget(self.set_same_time_button)

        self.control_group = QGroupBox()
        self.control_group.setTitle("Control Panel")

        self.control_group.setLayout(self.control_layout)
        self.control_group.setStyleSheet(
            "QGroupBox { background-color: #FDF3E7; color: black; border: none; padding: 6px }"
        )
        self.control_group.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.main_control_layout.addWidget(self.main_timer_widget)
        self.main_control_layout.addWidget(self.control_group)  # Add control_group directly to main_control_layout

        self.content_layout.addWidget(self.main_control_group)

        self.teams_layout = QHBoxLayout()
        self.teams_layout.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        self.team_widgets = []

        self.excel_file_path = 'cobotoo.xlsx'
        self.teams_df = pd.read_excel(self.excel_file_path)
        team_codes = ['CRB01', 'CRB02', 'CRB03', 'CRB04', 'CRB05']
        for team_number, code in enumerate(team_codes, 1):
            self.add_team(team_number, code)

        self.content_layout.addLayout(self.teams_layout)

        self.content_widget = QWidget()
        self.content_widget.setLayout(self.content_layout)
        self.content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


    def init_circle_widget(self):
        self.circle_layout = QVBoxLayout()
        self.circles = []

        # Add spacer item at the top
        self.circle_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Fixed))

        # Loop to create circles
        for i in range(3):
            circle = QLabel()
            circle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            circle.setMinimumSize(100, 100)  # Ensure circles are never too small
            circle.setStyleSheet(
                """
                QLabel {background-color: #cccccc; border-radius: 50px; font-size: 65px; font-weight: bold; color: black; border: 6px solid white;}
                """
            )
            circle.setAlignment(Qt.AlignCenter)
            self.circles.append(circle)

            # Add circle to main layout with left alignment
            self.circle_layout.addWidget(circle, alignment=Qt.AlignCenter)

            # Add vertical spacing between circles
            if i < 2:  self.circle_layout.addItem(QSpacerItem(10, 200, QSizePolicy.Expanding, QSizePolicy.Fixed))
            # Add vertical spacing between circles
            if i==2: self.circle_layout.addItem(QSpacerItem(10, 150, QSizePolicy.Expanding, QSizePolicy.Fixed))

        # Add randomize button with spacer item
        self.randomize_button = QPushButton("Randomize")
        self.randomize_button.clicked.connect(self.randomize_circles)
        self.randomize_button.setStyleSheet(
            "QPushButton { font-size: 15px; font-weight: bold; background-color: #007bff; color: white; border: none; padding: 10px 30px; border-radius: 10px; } QPushButton:hover { background-color: #0056b3; }")
        self.circle_layout.addWidget(self.randomize_button, alignment=Qt.AlignCenter)
        # Set up circle widget
        self.circle_widget = QWidget()
        self.circle_widget.setLayout(self.circle_layout)
        self.circle_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Specify exact size policy
        self.circle_widget.setFixedSize(320, 1000)  # Specify exact fixed size

    def resizeEvent(self, event):
        self.background_label.resize(event.size())
        super().resizeEvent(event)

    def add_team(self, team_number, team_code):
        team_widget = TeamTimerWidget(team_number, team_code, self.teams_df)
        team_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.teams_layout.addWidget(team_widget)
        self.team_widgets.append(team_widget)
        
    def keyPressEvent(self, event):
        key = event.key()
        if key in range(Qt.Key_1, Qt.Key_6):  # Qt.Key_1 is 49, Qt.Key_5 is 53
            index = key - Qt.Key_1  # Converts Qt.Key_1 to 0, Qt.Key_2 to 1, etc.
            if 0 <= index < len(self.team_widgets):
                self.team_widgets[index].toggle_timer()
                event.accept()
        else:
            super().keyPressEvent(event)

    def toggle_stop_resume(self):
        if self.toggle_stop_resume_button.text() == "Start All":
            self.start_all_timers()
            self.toggle_stop_resume_button.setText("Pause All")
        else:
            self.pause_all_timers()
            self.toggle_stop_resume_button.setText("Start All")


    # def start_all_timers(self):
    #     if self.main_timer_widget.paused:
    #         self.main_timer_widget.toggle_timer()
    #     for widget in self.team_widgets:
    #         if widget.paused:
    #             if widget.paused and widget.complete==True:
    #                 pass
    #             else:
    #                 widget.toggle_timer()

    def start_all_timers(self):
        if self.main_timer_widget.paused:
            self.main_timer_widget.toggle_timer()
        for widget in self.team_widgets:
            if widget.paused:
                widget.toggle_timer()

    def pause_all_timers(self):
        if not self.main_timer_widget.paused:
            self.main_timer_widget.toggle_timer()
        for widget in self.team_widgets:
            if not widget.paused:
                widget.toggle_timer()

    def reset_all_timers(self):
        self.main_timer_widget.reset_timer()
        for widget in self.team_widgets:
            widget.reset_timer()

    def set_same_time(self):
        base_time = self.main_timer_widget.time_left
        for widget in self.team_widgets:
            widget.time_left = base_time
            widget.initial_time = base_time
            widget.paused = True
            widget.start_button.setText("Start")
            widget.update_display()
            
    def randomize_circles(self):
        numbers = list(range(1, 4))
        random.shuffle(numbers)
        for i, circle in enumerate(self.circles):
            circle.setText(str(numbers[i]))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = TeamTimersApp()
    main_win.show()
    sys.exit(app.exec_())