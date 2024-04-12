import os
import sys
import datetime
from threading import Thread

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon, QGuiApplication, QTextCursor
from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QGridLayout, QLineEdit, QComboBox, QLabel, QFileDialog, QPushButton, QTextEdit, QSpinBox, QDialog, QDialogButtonBox, QMessageBox

import watermark

class MyMainWindow(QMainWindow):
    stage2_needed = Signal(list)

    def __init__(self):
        super().__init__()
        screen = QGuiApplication.primaryScreen().geometry()
        self.setWindowTitle('MiLeicaStyleWatermark')
        self.setFixedSize(int(screen.width()/2.6), int(screen.height()/3))
        icon = QIcon()
        icon.addFile(os.path.join(watermark.ROOT_PATH, "resources", "icons", "watermark.png"))
        self.setWindowIcon(icon)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self._init_ui()
        # self._init_signal()
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
        self.out_quality_input.setValue(80)
        self.central_layout.addWidget(self.out_quality_input, 2, 3, 1, 1)

        # out author label
        self.out_author_label = QLabel(self.central_widget)
        self.out_author_label.setText("照片作者")
        self.central_layout.addWidget(self.out_author_label, 2, 4, 1, 1)

        # out author input
        self.out_author_input = QLineEdit(self.central_widget)
        self.out_author_input.setText("")
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

        self.stage2_needed.connect(self._stage2_event)

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
            self.out_quality_input.setValue(80)
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
        mythread = Thread(target=self._start, args=(in_dir, out_dir, out_format, out_quality, artist), daemon=True)
        mythread.start()
    
    def _change_start_button_event(self):
        self.start_button.setEnabled(True)

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
    
    def _start(self, in_dir: str, out_dir: str, out_format: str, out_quality: int | None, artist: str | None):
        exit_code, ret = self.agent.run(in_dir, out_dir, out_format, out_quality, artist)
        if exit_code == 0:
            print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 添加水印完成!")
            self._change_start_button_event()
        elif exit_code == 1:
            self.stage2_needed.emit(ret)
        elif exit_code == 2:
            self._change_start_button_event()
    
    def _start2(self, files: list, brand: str, model: str, out_dir: str, out_format: str, out_quality: int | None, artist: str | None):
        self.agent.run2(files, brand, model, out_dir, out_format, out_quality, artist)
        self._change_start_button_event()
        print(F"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 添加水印完成!")
    
    def _stage2_event(self, files: list):
        filenames=[]
        for file in files:
            filenames.append(os.path.basename(file))
        if len(filenames) == 1:
            filenames = filenames[0]
        dlg = QMessageBox.question(self, "询问", F"{filenames} 没有exif信息!是否自定义输入照片信息添加水印？")
        if dlg == QMessageBox.Yes:
            self.dlg_ret = []
            new_dlg = CustomDialog(self, self.agent)
            new_dlg.ret.connect(self._get_dlg_ret)
            new_dlg.exec()
            if self.dlg_ret:
                out_dir = self.save_path_display.text()
                out_format = self.out_format_select.currentText()
                out_quality = self.out_quality_input.value()
                artist = self.out_author_input.text()
                self._start2(files, self.dlg_ret[0], self.dlg_ret[1], out_dir, out_format, out_quality, artist)
            else:
                self._change_start_button_event()
        elif dlg == QMessageBox.No:
            self._change_start_button_event()
    
    def _get_dlg_ret(self, ret: list):
        self.dlg_ret = ret

class CustomDialog(QDialog):
    ret = Signal(list)

    def __init__(self, parent, agent: watermark.WaterMarkAgent):
        super().__init__(parent)

        self.setWindowTitle("请选择自定义选项")
        self.agent = agent
        self._init_ui()
        self._init_connect()
    
    def _init_ui(self):
        self.layout = QGridLayout()
        for i in range(3):
            self.layout.setColumnMinimumWidth(i, 1)
            self.layout.setColumnStretch(i, 1)
        self.brand_label = QLabel(self)
        self.brand_label.setText("相机品牌")
        self.layout.addWidget(self.brand_label, 0, 0, 1, 1)

        self.brand = QComboBox(self)
        self.brand.addItem("")
        self.brand.addItems(list(self.agent.records['Camera_records'].keys()))
        self.layout.addWidget(self.brand, 0, 1, 1, 2)

        self.model_label = QLabel(self)
        self.model_label.setText("相机型号")
        self.layout.addWidget(self.model_label, 1, 0, 1, 1)

        self.model = QComboBox(self)
        self.model.addItem("")
        self.layout.addWidget(self.model, 1, 1, 1, 2)

        '''创建一个确认键和取消键'''
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        '''创建对话框按钮'''
        self.buttonBox = QDialogButtonBox(QBtn)
        '''对话框确认信号连接到确认槽函数'''
        self.buttonBox.accepted.connect(self._ok)
        '''对话框取消按钮连接到取消槽函数'''
        self.buttonBox.rejected.connect(self._cancel)
        self.layout.addWidget(self.buttonBox, 2 ,0, 1, 3)

        self.setLayout(self.layout)

    def _init_connect(self):
        self.brand.currentTextChanged.connect(self._update_model_list)
    
    def _update_model_list(self):
        brand = self.brand.currentText()
        if brand != "":
            self.model.clear()
            self.model.addItem("")
            self.model.addItems(self.agent.records['Camera_records'][brand])

    def _ok(self):
        brand = self.brand.currentText()
        model = self.model.currentText()
        if brand != "" and model != "":
            self.ret.emit([brand, model])
            self.done(QDialog.Accepted)
        else:
            self.done(QDialog.Rejected)
    
    def _cancel(self):
        self.done(QDialog.Rejected)

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