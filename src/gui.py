import os
import sys
import datetime

from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtGui import QIcon, QGuiApplication, QTextCursor
from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QGridLayout, QLineEdit, QComboBox, QLabel, QFileDialog, QPushButton, QTextEdit, QSpinBox

import watermark

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        screen = QGuiApplication.primaryScreen().geometry()
        self.setWindowTitle('MiLeicaStyleWatermark')
        self.setFixedSize(int(screen.width()/3), int(screen.height()/3))
        icon = QIcon()
        icon.addFile(os.path.join(watermark.ROOT_PATH, "resources", "icons", "watermark.png"))
        self.setWindowIcon(icon)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self._init_ui()
        self._connect()
        self.agent = watermark.WaterMarkAgent()

        self.stream = Stream()
        self.stream.stream_update.connect(self._write_log_info)
        sys.stdout = self.stream
        sys.stderr = self.stream

        self.stream_update_state = 0
        print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] MiLeicaStyleWatermark start!")

    def _init_ui(self):
        cols = 7
        self.central_layout = QGridLayout(self.central_widget)
        self.central_widget.setLayout(self.central_layout)

        for i in range(cols):
            self.central_layout.setColumnMinimumWidth(i, 1)
            self.central_layout.setColumnStretch(i, 1)

        # images path display
        self.images_path_display = QLineEdit(self.central_widget)
        self.images_path_display.setReadOnly(True)
        self.central_layout.addWidget(self.images_path_display, 0, 0, 1, 6)

        # images path select button
        self.images_path_select_button = QPushButton(self.central_widget)
        self.images_path_select_button.setText("照片文件夹")
        self.central_layout.addWidget(self.images_path_select_button, 0, 6, 1, 1)

        # save path display
        self.save_path_display = QLineEdit(self.central_widget)
        self.save_path_display.setReadOnly(True)
        self.save_path_display.setText(watermark.DEFAULT_OUT_DIR.replace("\\", "/"))
        self.central_layout.addWidget(self.save_path_display, 1, 0, 1, 6)

        # save path button 
        self.save_path_button = QPushButton(self.central_widget)
        self.save_path_button.setText("保存文件夹")
        self.central_layout.addWidget(self.save_path_button, 1, 6, 1, 1)

        # out format label
        self.out_format_label = QLabel(self.central_widget)
        self.out_format_label.setText("输出照片格式")
        self.central_layout.addWidget(self.out_format_label, 2, 0, 1, 1)

        # out format select
        self.out_format_select = QComboBox(self.central_widget)
        self.out_format_select.addItems(watermark.SUPPORT_OUT_FORMAT)
        self.central_layout.addWidget(self.out_format_select, 2, 1, 1, 1)

        # out quality label
        self.out_quality_label = QLabel(self.central_widget)
        self.out_quality_label.setText("输出照片质量")
        self.central_layout.addWidget(self.out_quality_label, 2, 2, 1, 1)

        # out quality input
        self.out_quality_input = QSpinBox(self.central_widget)
        self.out_quality_input.setMinimum(1)
        self.out_quality_input.setMaximum(100)
        self.out_quality_input.setValue(85)
        self.central_layout.addWidget(self.out_quality_input, 2, 3, 1, 1)

        # out author label
        self.out_author_label = QLabel(self.central_widget)
        self.out_author_label.setText("照片作者")
        self.central_layout.addWidget(self.out_author_label, 2, 4, 1, 1)

        # out author input
        self.out_author_input = QLineEdit(self.central_widget)
        self.central_layout.addWidget(self.out_author_input, 2, 5, 1, 1)

        # start button 
        self.start_button = QPushButton(self.central_widget)
        self.start_button.setText("Start")
        self.central_layout.addWidget(self.start_button, 2, 6, 1, 1)

        # log display
        self.log_display = QTextEdit(self.central_widget)
        self.log_display.setReadOnly(True)
        self.central_layout.addWidget(self.log_display, 3, 0, 6, 7)

    def _connect(self):
        self.images_path_select_button.clicked.connect(self._select_images_path_event)
        self.save_path_button.clicked.connect(self._select_save_path_event)
        self.out_format_select.currentTextChanged.connect(self._out_format_change_event)
        self.start_button.clicked.connect(self._start_event)

    def _select_images_path_event(self):
        filepath = QFileDialog.getExistingDirectory(self.central_widget, dir=watermark.DESKTOP_PATH)
        if filepath != "":
            self.images_path_display.setText(filepath)
        
    def _select_save_path_event(self):
        filepath = QFileDialog.getExistingDirectory(self.central_widget, dir=watermark.DESKTOP_PATH)
        if filepath != "":
            self.save_path_display.setText(filepath)
    
    def _out_format_change_event(self):
        current_format = self.out_format_select.currentText()
        if current_format == 'jpg':
            self.out_quality_input.setValue(85)
            self.out_quality_input.setReadOnly(False)
        elif current_format == 'png':
            self.out_quality_input.setValue(100)
            self.out_quality_input.setReadOnly(True)

    def _start_event(self):
        self.start_button.setEnabled(False)
        in_dir = self.images_path_display.text()
        out_dir = self.save_path_display.text()
        out_format = self.out_format_select.currentText()
        out_quality = self.out_quality_input.value()
        artist = self.out_author_input.text()
        self._worker_thread = QThread(self)
        self._worker = MyWorker(self.agent,in_dir, out_dir, out_format, out_quality, artist)
        self._worker.moveToThread(self._worker_thread)
        self._worker.end.connect(self._change_start_button_event)
        self._worker_thread.started.connect(self._worker.run)
        self._worker_thread.start()
    
    def _change_start_button_event(self):
        self.start_button.setEnabled(True)
        print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 添加水印完成!")

    def _write_log_info(self, text: str):
        log_cursor = self.log_display.textCursor()
        log_cursor.movePosition(QTextCursor.End)
        if text.endswith("\n"):
            self.stream_update_state = 0
        else:
            if self.stream_update_state == 1:
                log_cursor.select(QTextCursor.BlockUnderCursor)
                log_cursor.removeSelectedText()
            self.stream_update_state = 1

        log_cursor.insertText(text)
        self.log_display.setTextCursor(log_cursor)
        self.log_display.ensureCursorVisible()
    
class MyWorker(QObject):
    end = Signal(str)

    def __init__(self, agent: watermark.WaterMarkAgent, in_dir: str, out_dir: str, out_format: str, out_quality: int | None, artist: str | None) -> None:
        super().__init__()
        self.agent = agent
        self.in_dir = in_dir
        self.out_dir = out_dir
        self.out_format = out_format
        self.out_quality = out_quality
        self.artist = artist
    
    def run(self):
        self.agent.run(self.in_dir, self.out_dir, self.out_format, self.out_quality, self.artist)
        self.end.emit("end")

class Stream(QObject):
    stream_update = Signal(str)

    def write(self, text: str):
        self.stream_update.emit(text)

if __name__ == "__main__":
    # app = QApplication(sys.argv)
    app = QApplication()
    win = MyMainWindow()
    win.show()
    app.exec()