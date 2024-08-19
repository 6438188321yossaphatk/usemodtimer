import sys
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, QSizePolicy, QGridLayout,QMessageBox,
                             QVBoxLayout, QHBoxLayout, QComboBox, QTableWidget, QTableWidgetItem, QSpacerItem, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPalette, QBrush, QColor,QFont
import sys
import math
import time
import os

#2320 x 840
class ScoreboardApp(QWidget):
    FONT_SIZE = 20
    DEFAULT_ROW_HEIGHT = 160  # Default row height
    ROUND_COLUMNS = ['R1', 'R2']
    COLUMN_WIDTHS = [90, 140, 270, 180, 180, 120, 140, 180, 180, 120, 140, 120]
    COLUMN_WIDTHS = [110, 160, 300, 220, 220, 120, 140, 220, 220, 120, 140, 120]

    #COLUMN_WIDTHS = [70, 100, 270, 150, 130, 100, 100, 150, 130, 100, 100, 150]
    FONT_STRETCH = 30
    
    HEADERS = [
        'Rank', 'Team Code', 'Team Name', 'R1 Time', 'R1 Time_Score', 'R1 Score', 'R1 Medal',
        'R2 Time', 'R2 Time_Score', 'R2 Score', 'R2 Medal', 'Total'
    ]
    
    def __init__(self):
        super().__init__()
        self.team_rows = {}
        self.team_data = {}
        self.round2_input_entered = False

        self.header_to_index = {header: index for index, header in enumerate(self.HEADERS)}
        self.initUI()
        self.load_team_data()
        self.populate_scoreboard()
        self.time_scores = {round_prefix: {} for round_prefix in self.ROUND_COLUMNS}
        # Connect the cell change signal to the slot
        self.scoreboard_table.cellChanged.connect(self.on_cell_changed)

    def initUI(self):
        self.setWindowTitle('Scoreboard App')
        self.setGeometry(100, 100, 2000, 840)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Background settings
        self.background_label = QLabel(self)
        self.background_label.setGeometry(0, 0, 1200, 700)
        self.update_background_image()

        # Container for inputs
        self.input_container = QWidget()
        self.input_container.setFixedHeight(int(self.height() * 0.17))
        self.create_inputs()

        self.main_layout = QVBoxLayout()
        # Horizontal layout for input and description
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.input_container)

        # Description box styling
        description_label = QLabel(self.create_score_description())
        description_label.setStyleSheet("""
            QLabel {color: black;font-size: 18px;padding: 2px;border: 1px solid #ccc;
                border-radius: 15px;background-color: rgba(255, 255, 255, 0.95);margin-left: 15px;margin-right: 15px;
            }""")
        description_label.setWordWrap(True)
        description_label.setFixedWidth(450)

        h_layout.addStretch()  # Stretch to push description to the right
        h_layout.addWidget(description_label, alignment=Qt.AlignRight)

        self.main_layout.addLayout(h_layout)

        # Scoreboard table
        self.scoreboard_table = QTableWidget()
        self.scoreboard_table.setColumnCount(len(self.HEADERS))
        self.scoreboard_table.setHorizontalHeaderLabels(self.HEADERS)
        self.scoreboard_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        for i, width in enumerate(self.COLUMN_WIDTHS):
            self.scoreboard_table.setColumnWidth(i, width)

        # Set uniform row heights
        self.set_uniform_row_height(self.DEFAULT_ROW_HEIGHT)

        # Styling for table headers
        header_font = QFont("Helvetica", 20)  # Removed QFont.Bold to remove bold effect
        header = self.scoreboard_table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setFont(header_font)
        header.setStyleSheet("QHeaderView::section {background-color: rgba(255, 255, 255, 0.95); border: 1px solid #ccc; padding: 1px; color: black;}")  # Reduced border thickness
        
        
        self.main_layout.addItem(QSpacerItem(0, 10, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.main_layout.addWidget(self.scoreboard_table)
        self.main_layout.setStretch(0, 0)
        #self.main_layout.setStretch(1, 1)
        self.setLayout(self.main_layout)

    def create_inputs(self):
        styles = {
            "black_text": "color: black;",
            "input_field": """
                QLineEdit {color: black;background-color: rgba(255, 255, 255, 0.9);border: 1px solid #ccc;
                    border-radius: 5px; padding: 3px; font-size: 20px;  /* Adjust font size here */
                }
                QLineEdit:focus { border-color: #66afe9; outline: none;}
            """,
            "label": "QLabel {color: black; padding: 5px; font-size: 16px;}",
            "button": """
                QPushButton { color: black; background-color: rgba(255, 255, 255, 0); border: 1px solid #ccc; border-radius: 1px; padding: 2px 5px; /* Adjust padding here */
                }
                QPushButton:hover {background-color: rgba(200, 200, 200, 0.5);}
            """
        }

        widgets = {
            "round_label": QLabel('Round:'),
            "round_combo": QComboBox(),
            "team_code_label": QLabel('Code:'),
            "team_code_input": QLineEdit(),
            "team_name_label": QLabel('Name:'),
            "team_name_display": QLabel(),
            "score_label": QLabel('Score:'),
            "score_input": QLineEdit(),
            "time_label": QLabel('Time :'),
            "time_input": QLineEdit(),
            "add_button": QPushButton('Add'),
            "save_button": QPushButton('Save')  # Add Save button
        }

        for widget, style in {
            widgets["round_label"]: styles["label"],
            widgets["team_code_label"]: styles["label"],
            widgets["team_name_label"]: styles["label"],
            widgets["score_label"]: styles["label"],
            widgets["time_label"]: styles["label"],
            widgets["team_code_input"]: styles["input_field"],
            widgets["score_input"]: styles["input_field"],
            widgets["time_input"]: styles["input_field"],
            widgets["team_name_display"]: styles["black_text"] + "background-color: transparent; padding: 5px;",
            widgets["add_button"]: styles["button"],
            widgets["save_button"]: styles["button"]  # Style the Save button
        }.items():
            widget.setStyleSheet(style)

        self.team_code_input = widgets["team_code_input"]
        self.team_name_display = widgets["team_name_display"]
        self.round_combo = widgets["round_combo"]
        self.score_input = widgets["score_input"]
        self.time_input = widgets["time_input"]

        widgets["round_combo"].addItems(['Round 1', 'Round 2'])
        widgets["round_combo"].setFixedSize(120, 30)
        widgets["round_combo"].setStyleSheet(styles["black_text"] + "background-color: white; border-radius: 5px; padding: 5px;")
        widgets["team_code_input"].setFixedSize(120, 30)
        widgets["team_code_input"].textChanged.connect(self.auto_fill_team_name)
        widgets["team_name_display"].setFixedSize(200, 30)
        widgets["score_input"].setFixedSize(100, 30)
        widgets["time_input"].setFixedSize(100, 30)
        widgets["add_button"].clicked.connect(self.add_to_scoreboard)
        widgets["save_button"].clicked.connect(self.save_to_excel)  # Connect Save button

        for widget in [widgets["team_code_input"], widgets["score_input"], widgets["time_input"]]:
            widget.returnPressed.connect(self.add_to_scoreboard)

        grid_layout = QGridLayout()
        layout_data = [
            (widgets["round_label"], 0, 0), (widgets["round_combo"], 0, 1),
            (widgets["team_code_label"], 1, 0), (widgets["team_code_input"], 1, 1),
            (widgets["team_name_label"], 2, 0), (widgets["team_name_display"], 2, 1),
            (widgets["score_label"], 0, 2), (widgets["score_input"], 0, 3),
            (widgets["time_label"], 1, 2), (widgets["time_input"], 1, 3),
            (widgets["add_button"], 2, 3)
        ]
        for widget, row, col in layout_data:
            grid_layout.addWidget(widget, row, col, Qt.AlignLeft)

        # Add a spacer between the Add and Save buttons
        spacer = QSpacerItem(5, 0, QSizePolicy.Minimum, QSizePolicy.Fixed)
        grid_layout.addItem(spacer, 2, 4)

        # Add the Save button
        grid_layout.addWidget(widgets["save_button"], 2, 3, Qt.AlignRight)

        grid_layout.setHorizontalSpacing(1)
        grid_layout.setVerticalSpacing(10)
        grid_layout.setContentsMargins(1, 10, 15, 1)

        self.input_container.setLayout(grid_layout)
        self.input_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.input_container.setFixedSize(450, 130)  # Adjusted size to accommodate the new button


    def create_score_description(self):
        # Returns a description of the medal distribution criteria with further reduced vertical spacing
        description = (
            "<b>Medal Distribution Score Criteria:</b>"
            "<div style='margin-top: 8px; line-height: 5em;'>🥇 Gold Medal: combined score >= 80"
            "<div style='margin-top: 5px; line-height: 5em;'>🥈 Silver Medal: combined score of 70-79 "
            "<div style='margin-top: 5px; line-height: 5em;'>🥉 Bronze Medal: combined score of 60-69 "
        )
        return description

    def resizeEvent(self, event):
        self.update_background_image()
        total_height = self.height()
        scoreboard_height = self.scoreboard_table.geometry().height()
        remaining_height = total_height - scoreboard_height
        input_container_height = max(remaining_height * 0.15, 120)  # Ensure a minimum height of 150px
        self.input_container.setFixedHeight(int(input_container_height))

    def update_background_image(self):
        oImage = QImage("cbt.jpg")
        sImage = oImage.scaled(self.size(), Qt.IgnoreAspectRatio)
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(sImage))
        self.setPalette(palette)

    def load_team_data(self):
        try:
            self.data_frame = pd.read_excel('recheckscoreboard.xlsx', engine='openpyxl')
        except Exception as e:
            print(f"Error loading team data: {e}")

    def populate_scoreboard(self):
        if self.data_frame.empty:
            print("Data frame is empty")  # Debugging statement
            return

        self.scoreboard_table.setRowCount(0)
        self.scoreboard_table.setColumnCount(0)
        font = QFont("Helvetica", self.FONT_SIZE, self.FONT_STRETCH)
        self.scoreboard_table.setFont(font)

        # Set column headers 
        self.scoreboard_table.setColumnCount(len(self.data_frame.columns))
        self.scoreboard_table.setHorizontalHeaderLabels(self.data_frame.columns)

        for row_idx in range(len(self.data_frame)):
            self.scoreboard_table.insertRow(row_idx)
            for col_idx, col_name in enumerate(self.data_frame.columns):
                cell_value = self.data_frame.iloc[row_idx, col_idx]
                if pd.notna(cell_value):
                    if isinstance(cell_value, float) and cell_value.is_integer():
                        cell_value = str(int(cell_value))
                    else:
                        cell_value = str(cell_value)
                else:
                    cell_value = ''

                item = QTableWidgetItem(cell_value)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(font)
                item.setForeground(QBrush(QColor("black")))  # Set text color to black
                self.scoreboard_table.setItem(row_idx, col_idx, item)

                if col_name == 'Team Code':
                    team_code = cell_value
                    self.team_rows[team_code] = row_idx  # Populate team_rows dictionary

            self.scoreboard_table.setRowHeight(row_idx, self.DEFAULT_ROW_HEIGHT)
        self.scoreboard_table.setStyleSheet("QTableWidget::item { background-color: #FDF3E7; padding-top: 10px; padding-bottom: 10px; }")

    def add_to_scoreboard(self):
        round_selected = self.round_combo.currentText()
        team_code_number = self.team_code_input.text()

        # Convert the input to float first, then to int
        try:
            team_code_number = int(float(team_code_number))
        except ValueError:
            QMessageBox.warning(self, 'Invalid Input', 'The team code number entered is invalid.')
            return
        
        team_code = f"CRB{team_code_number:02d}"
        score = self.score_input.text()
        time = self.time_input.text()

        formatted_time = self.format_time_input(time)
        if team_code not in self.team_rows:
            print("Team code not found in team_rows")  # Debugging statement
            QMessageBox.warning(self, 'Invalid Team Code', 'The team code entered is invalid.')
            return

        row_position = self.team_rows[team_code]
        round_column_map = {
            'Round 1': 'R1 Time',
            'Round 2': 'R2 Time'
        }
        round_column = self.header_to_index.get(round_column_map.get(round_selected, ''), -1)

        if round_selected == 'Round 2':
            self.round2_input_entered = True

        if self.round2_input_entered and round_selected == 'Round 1':
            QMessageBox.warning(self, 'Edit Disabled', 'You cannot edit Round 1 after entering Round 2.')
            return

        self.scoreboard_table.blockSignals(True)
        
        items = {
            round_column: QTableWidgetItem(formatted_time),
            round_column + 2: QTableWidgetItem(score),
            round_column + 1: QTableWidgetItem(''),
            round_column + 3: QTableWidgetItem('')
        }

        font = QFont("Helvetica", self.FONT_SIZE, self.FONT_STRETCH)
        
        for col, item in items.items():
            item.setTextAlignment(Qt.AlignCenter)
            item.setFont(font)
            self.scoreboard_table.setItem(row_position, col, item)

        combine_round12_col = self.header_to_index.get('Total', -1)
        if combine_round12_col != -1:
            combine_round12 = self.calculate_combine_round12(row_position)
            combine_round12_item = QTableWidgetItem(str(combine_round12))
            combine_round12_item.setTextAlignment(Qt.AlignCenter)
            combine_round12_item.setFont(font)
            self.scoreboard_table.setItem(row_position, combine_round12_col, combine_round12_item)

        # self.update_rankings()

        # Apply stylesheet to set text color to black
        self.scoreboard_table.setStyleSheet("""
            QTableWidget::item {
                background-color: #FDF3E7;
                color: black;  /* Set text color to black */
                padding-top: 10px;
                padding-bottom: 10px;
            }
            QTableWidget QTableCornerButton::section {
                background-color: #FDF3E7;  /* Match corner button background color */
            }
        """)

        self.scoreboard_table.blockSignals(False)


        self.update_rankings()

        # Apply stylesheet to set text color to black
        self.scoreboard_table.setStyleSheet("""
            QTableWidget::item {
                background-color: #FDF3E7;
                color: black;  /* Set text color to black */
                padding-top: 10px;
                padding-bottom: 10px;
            }
            QTableWidget QTableCornerButton::section {
                background-color: #FDF3E7;  /* Match corner button background color */
            }
        """)

        self.scoreboard_table.blockSignals(False)

    def set_uniform_row_height(self, height):
        for row in range(self.scoreboard_table.rowCount()):
            self.scoreboard_table.setRowHeight(row, height)

    def auto_fill_team_name(self):
        team_code = f"CRB{self.team_code_input.text().strip().zfill(2)}"
        if team_code in self.team_rows:
            row_position = self.team_rows[team_code]
            team_name_item = self.scoreboard_table.item(row_position, self.header_to_index['Team Name'])
            if team_name_item:
                self.team_name_display.setText(team_name_item.text())
            else:
                self.team_name_display.setText('')
        else:
            self.team_name_display.setText('')
        self.team_name_display.setStyleSheet("QLabel { color: black; font-size: 17px; }")

    

    def format_time_input(self, time_str):
        parts = time_str.split(':')
        if len(parts) == 1: return f"{parts[0]}:00:00"
        elif len(parts) == 2:return f"{parts[0]}:{parts[1]}:00"
        elif len(parts) == 3:return f"{parts[0]}:{parts[1]}:{parts[2]}"
        return time_str

    def parse_time(self, time_str):
        parts = time_str.split(':')
        try:
            if len(parts) == 1: return int(parts[0]) * 60000
            elif len(parts) == 2: return int(parts[0]) * 60000 + int(parts[1]) * 1000
            elif len(parts) == 3: return int(parts[0]) * 60000 + int(parts[1]) * 1000 + int(parts[2])
        except ValueError: pass
        return float('inf')


    def save_to_excel(self):
        # Open a file dialog to select where to save the Excel file
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Scoreboard to Excel",
            "",
            "Excel Files (*.xlsx);;All Files (*)",
            options=options
        )

        if not file_path:
            # If no file path is selected, return
            QMessageBox.warning(self, 'Save Error', 'No file path was selected.')
            return
        
        # Ensure the file has the correct extension
        if not file_path.endswith('.xlsx'):
            file_path += '.xlsx'

        # Convert QTableWidget to a pandas DataFrame
        num_rows = self.scoreboard_table.rowCount()
        num_cols = self.scoreboard_table.columnCount()
        headers = [self.scoreboard_table.horizontalHeaderItem(i).text() for i in range(num_cols)]
        data = []

        for row in range(num_rows):
            row_data = []
            for col in range(num_cols):
                item = self.scoreboard_table.item(row, col)
                row_data.append(item.text() if item is not None else '')
            data.append(row_data)

        df = pd.DataFrame(data, columns=headers)

        try:
            # Save DataFrame to Excel file
            df.to_excel(file_path, index=False)
            QMessageBox.information(self, 'Saved', f'Scoreboard saved to {file_path}')
        except Exception as e:
            QMessageBox.critical(self, 'Save Error', f'An error occurred while saving the file: {e}')


    def on_cell_changed(self, row, col):
        round_prefix = next((prefix for prefix in self.ROUND_COLUMNS if col == self.header_to_index.get(f'{prefix} Time')), None)

        if self.round2_input_entered and round_prefix == 'R1':
            QMessageBox.warning(self, 'Edit Disabled', 'You cannot edit Round 1 after entering Round 2.')
            return

        self.update_rankings()


    def update_round_time_scores(self, round_prefix):
        time_score_col_index = self.header_to_index.get(f"{round_prefix} Time_Score")
        score_col_index = self.header_to_index.get(f"{round_prefix} Score")
        
        if time_score_col_index is None or score_col_index is None:
            print(f"No column found for {round_prefix} Time_Score or {round_prefix} Score")
            return

        times = []
        input_order = {}
        zero_time_teams = []

        # Collect all times and their input order for teams with a score of 100
        for row in range(self.scoreboard_table.rowCount()):
            score_item = self.scoreboard_table.item(row, score_col_index)
            if score_item and score_item.text().isdigit() and int(score_item.text()) == 100:
                time_str = self.scoreboard_table.item(row, time_score_col_index - 1).text() if self.scoreboard_table.item(row, time_score_col_index - 1) else ''
                if time_str:
                    try:
                        time_value = self.parse_time(time_str)
                        team_code = self.scoreboard_table.item(row, self.header_to_index['Team Code']).text()
                        timestamp = time.time()
                        input_order[team_code] = (timestamp, row)
                        if time_value == 0:
                            zero_time_teams.append((team_code, row))
                        else:
                            times.append((team_code, time_value, row))
                    except (ValueError, AttributeError) as e:
                        print(f"Error parsing time for row {row}: {e}")

        if not times and not zero_time_teams:
            # Clear scores if no valid times
            for row in range(self.scoreboard_table.rowCount()):
                self.scoreboard_table.setItem(row, time_score_col_index, QTableWidgetItem(''))
            return

        # Sort times based on time value and then by input time
        sorted_times = sorted(times, key=lambda x: (x[1], input_order[x[0]][0]), reverse=True)

        # Determine scoring logic based on round
        if round_prefix == 'R1':
            max_score = 10
            score_step = 1
        elif round_prefix == 'R2':
            max_score = 30
            score_step = 3
        else:
            print(f"Unknown round_prefix {round_prefix}")
            return

        last_non_zero_time_score = max_score - (min(len(sorted_times), 10) - 1) * score_step if len(sorted_times) > 0 else max_score - 9 * score_step
        scores = {}

        # Assign scores for top 10 teams
        for rank, (team_code, _, row) in enumerate(sorted_times):
            if rank < 10:
                score = max_score - rank * score_step
                scores[team_code] = score
                item = QTableWidgetItem(str(score))
                item.setFont(QFont("Helvetica", self.FONT_SIZE, self.FONT_STRETCH))
                item.setForeground(QBrush(QColor("black")))
                self.scoreboard_table.setItem(row, time_score_col_index, item)
            else:
                break

        # Assign the lowest score of non-zero time teams to zero-time teams in the top 10
        for team_code, row in zero_time_teams:
            if len(scores) < 10:
                scores[team_code] = last_non_zero_time_score - score_step
                item = QTableWidgetItem(str(last_non_zero_time_score - score_step))
                item.setFont(QFont("Helvetica", self.FONT_SIZE, self.FONT_STRETCH))
                item.setForeground(QBrush(QColor("black")))
                self.scoreboard_table.setItem(row, time_score_col_index, item)
            else:
                break
        # Clear scores for teams not in the top 10
        for row in range(self.scoreboard_table.rowCount()):
            team_code = self.scoreboard_table.item(row, self.header_to_index['Team Code']).text()
            if team_code not in scores:
                self.scoreboard_table.setItem(row, time_score_col_index, QTableWidgetItem(''))


    def update_rankings(self):
        # Temporarily disconnect the signal to prevent recursion
        self.scoreboard_table.blockSignals(True)

        # Update time scores for each round independently based on their specific columns
        for round_prefix in self.ROUND_COLUMNS:
            if self.header_to_index.get(f"{round_prefix} Time") is not None:
                self.update_round_time_scores(round_prefix)

        # If there is a Total column, update its value
        combine_round12_col = self.header_to_index.get('Total')
        if combine_round12_col is not None:
            for row in range(self.scoreboard_table.rowCount()):
                combine_round12 = self.calculate_combine_round12(row)
                self.scoreboard_table.setItem(row, combine_round12_col, QTableWidgetItem(str(combine_round12)))

        # Update rankings for each round
        for round_score_col in ['R1 Score', 'R2 Score']:
            self.rank_and_assign_medals_for_round(self.header_to_index[round_score_col])

        self.update_overall_ranking()  # Update overall ranking based on the combined scores
        self.reorder_rows_by_rank()  # Reorder rows by their rank

        # Reconnect the signal after changes are made
        self.scoreboard_table.blockSignals(False)



    def update_overall_ranking(self):
        # Temporarily block signals to prevent recursion
        self.scoreboard_table.blockSignals(True)

        team_scores = []
        for row in range(self.scoreboard_table.rowCount()):
            total_score = sum(int(float(self.scoreboard_table.item(row, self.header_to_index[col_name]).text() or 0))
                            for col_name in ['R1 Score', 'R2 Score']
                            if self.header_to_index.get(col_name) is not None and self.scoreboard_table.item(row, self.header_to_index[col_name]))

            total_time_score = sum(int(float(self.scoreboard_table.item(row, self.header_to_index[col_name]).text() or 0))
                                for col_name in ['R1 Time_Score', 'R2 Time_Score']
                                if self.header_to_index.get(col_name) is not None and self.scoreboard_table.item(row, self.header_to_index[col_name]))

            total_time = sum(self.parse_time(self.scoreboard_table.item(row, self.header_to_index[col_name]).text() or '0:00:00')
                            for col_name in ['R1 Time', 'R2 Time']
                            if self.header_to_index.get(col_name) is not None and self.scoreboard_table.item(row, self.header_to_index[col_name]))

            combined_total = float(total_score) + float(total_time_score)
            team_scores.append((row, combined_total, total_time))

        # Sort teams by combined total score and then by total time
        team_scores.sort(key=lambda x: (x[1], -x[2]), reverse=True)
        rank_col = self.header_to_index.get('Rank')
        if rank_col is not None:
            # Assign ranks based on the sorted order
            for rank, (row, _, _) in enumerate(team_scores):
                self.scoreboard_table.setItem(row, rank_col, QTableWidgetItem(str(rank + 1)))

        # Reconnect the signal after changes are made
        self.scoreboard_table.blockSignals(False)



    def reorder_rows_by_rank(self):
        # Temporarily block signals to prevent recursion
        self.scoreboard_table.blockSignals(True)

        # Collect current data
        row_data = [(row, [self.scoreboard_table.item(row, col).text() if self.scoreboard_table.item(row, col) else ""
                        for col in range(self.scoreboard_table.columnCount())])
                    for row in range(self.scoreboard_table.rowCount())]

        # Sort rows by rank
        rank_col = self.header_to_index['Rank']
        row_data.sort(key=lambda x: int(x[1][rank_col]))

        # Rebuild the table based on the sorted rows
        new_team_rows = {}
        for new_row, (old_row, data) in enumerate(row_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)  # Set alignment to center
                item.setFont(QFont("Helvetica", self.FONT_SIZE,self.FONT_STRETCH))  # Apply the font to the item
                self.scoreboard_table.setItem(new_row, col, item)
            # Update the team_rows mapping with the new row positions
            team_code_col = self.header_to_index['Team Code']
            team_code = self.scoreboard_table.item(new_row, team_code_col).text()
            new_team_rows[team_code] = new_row

        self.team_rows = new_team_rows

        # Reconnect signals after processing
        self.scoreboard_table.blockSignals(False)

    ######################################################################################################################################################

    def calculate_combine_round12(self, row):
        try:
            round_columns = ['R1 Score', 'R1 Time_Score', 'R2 Score', 'R2 Time_Score']
            combined_score = 0
            for col in round_columns:
                item = self.scoreboard_table.item(row, self.header_to_index[col])
                if item is not None:
                    text = item.text()
                    # Check if text can be converted to a number
                    if text.replace('-', '').replace('.', '').isdigit():
                        combined_score += float(text)

            # Convert to int to remove decimal point
            combined_score = int(combined_score)

            return combined_score if combined_score != 0 else ' '

        except Exception as e:
            print(f"Error in calculate_combine_round12: {e}")
            return ' '


    def rank_and_assign_medals_for_round(self, round_column):
        self.scoreboard_table.blockSignals(True)

        combined_scores = []
        for row in range(self.scoreboard_table.rowCount()):
            try:
                score_item = self.scoreboard_table.item(row, round_column)
                time_score_item = self.scoreboard_table.item(row, round_column - 1)
                time_item = self.scoreboard_table.item(row, round_column - 2)

                score = int(score_item.text()) if score_item and score_item.text() else 0
                time_score = int(time_score_item.text()) if time_score_item and time_score_item.text() else 0
                time = self.parse_time(time_item.text()) if time_item and time_item.text() else float('inf')
                
                combined_score = score + time_score
                combined_scores.append((row, combined_score, time))
            except Exception:
                combined_scores.append((row, -1, float('inf')))

        # Filter valid scores
        valid_scores = [cs for cs in combined_scores if cs[1] >= 0]
        # Sort by combined score and then by time
        valid_scores.sort(key=lambda x: (x[1], x[2]))

        for rank, (row, combined_score, _) in enumerate(valid_scores):
            medal_col = round_column + 1
            self.assign_medal(row, combined_score, rank + 1, medal_col)

        self.scoreboard_table.blockSignals(False)



    def assign_medal(self, row, combined_score, rank, medal_col):
        self.scoreboard_table.blockSignals(True)
        score_item = self.scoreboard_table.item(row, medal_col - 1)
        medal = '-'

        if score_item and score_item.text():  # Check if there is a score
            try:
                score_value = float(score_item.text())
                if score_value >= 80:
                    medal = '🥇'  # Gold medal
                elif score_value >= 70:
                    medal = '🥈'  # Silver medal
                elif score_value >= 60:
                    medal = '🥉'  # Bronze medal
            except ValueError:
                pass  # Handle cases where score is not a number
        
        # Create a QTableWidgetItem for the medal
        item = QTableWidgetItem(medal)
        font = QFont()
        font.setPointSize(self.FONT_SIZE)
        item.setFont(font)
        self.scoreboard_table.setItem(row, medal_col, item)
        self.scoreboard_table.blockSignals(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    scoreboard_app = ScoreboardApp()
    scoreboard_app.show()
    sys.exit(app.exec_())
