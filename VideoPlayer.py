from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtMultimediaWidgets import QVideoWidget
import subprocess
import json
from GUI import Ui_MainWindow
from convertAudio import RequestApi
from myVideoWidget import myVideoWidget
import sys
import cv2

from aip import AipOcr

import os
import json
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定中文字体为黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示为方块的问题

from collections import Counter


class AnnotationWindow(QWidget):
    def __init__(self, text_content,file_name):
        super().__init__()
        self.setWindowTitle("标注窗口")
        self.setGeometry(400, 400, 800, 600)
        self.setWindowIcon(QIcon("resources/images/mannuate.png"))

        layout = QVBoxLayout()
        self.file_name = file_name
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(text_content)
        layout.addWidget(self.text_edit)

        self.btn_noun = QPushButton("名词")
        self.btn_noun.clicked.connect(lambda: self.select_triple("n"))
        self.btn_noun.setIcon(QIcon("resources/images/word.png"))
        layout.addWidget(self.btn_noun)

        self.btn_verb = QPushButton("动词")
        self.btn_verb.clicked.connect(lambda: self.select_triple("v"))
        self.btn_verb.setIcon(QIcon("resources/images/action.png"))
        layout.addWidget(self.btn_verb)

        self.btn_property = QPushButton("属性")
        self.btn_property.clicked.connect(lambda: self.select_triple("f"))
        self.btn_property.setIcon(QIcon("resources/images/judge.png"))
        layout.addWidget(self.btn_property)

        # 添加标注类别选择下拉框
        self.label_category = QLabel("选择标注类别:")
        layout.addWidget(self.label_category)
        self.combo_category = QComboBox()
        self.combo_category.addItems(["政治", "经济", "健康", "娱乐", "社会"])
        layout.addWidget(self.combo_category)

        # 添加显示文本长度的标签
        self.label_length = QLabel()
        layout.addWidget(self.label_length)

        self.btn_save = QPushButton("完成标注并保存")
        self.btn_save.clicked.connect(self.save_and_close)
        layout.addWidget(self.btn_save)
        self.setLayout(layout)

        # 添加统计词频的按钮
        self.btn_word_frequency = QPushButton("统计词频并绘制图像")
        self.btn_word_frequency.clicked.connect(self.calculate_and_plot_word_frequency)
        layout.addWidget(self.btn_word_frequency)

        # 添加 Matplotlib 图像显示区域
        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.setLayout(layout)
        # 更新文本长度显示
        self.update_text_length()

        # 初始化存储标注文本的变量
        self.noun_text = ""
        self.verb_text = ""
        self.property_text = ""

    def select_triple(self, category):
            selected_text = self.text_edit.textCursor().selectedText()
            if selected_text:
                cursor = self.text_edit.textCursor()
                text_to_insert = f"<{category}>{selected_text}</{category}>"  # 包含标签的文本
                cursor.insertText(text_to_insert)

                # 获取光标位置
                position = cursor.position()
                # 移动光标到文本末尾
                cursor.movePosition(QTextCursor.End)
                # 设置新的光标位置
                cursor.setPosition(position)
                # 将新的光标应用到文本编辑器
                self.text_edit.setTextCursor(cursor)
        # 根据选择的标注类型存储文本
            if category == "n":
                self.noun_text += selected_text + "\n"
            elif category == "v":
                self.verb_text += selected_text + "\v"
            elif category == "f":
                self.property_text += selected_text + "\f"

    def update_text_length(self):
        text_length = len(self.text_edit.toPlainText())
        self.label_length.setText(f"文本长度: {text_length} 字符")

    def save_and_close(self):
        text_content = self.text_edit.toPlainText()
        selected_category = self.combo_category.currentText()
        selected_category_index = self.combo_category.currentIndex()
        text_length = len(text_content)
        # 获取文本文件的上一层文件夹路径
        parent_folder = os.path.dirname(os.path.dirname(os.path.abspath(self.file_name)))
        output_folder = os.path.join(parent_folder, "annotation_Json")
        origin_folder = os.path.dirname(os.path.abspath(self.file_name))
        # 创建 annotation_Json 文件夹
        os.makedirs(output_folder, exist_ok=True)
        # 构建输出文件路径
        folder_name = os.path.basename(os.path.dirname(self.file_name))
        file_name = os.path.splitext(os.path.basename(self.file_name))[0]
        output_file = os.path.join(output_folder, f"{folder_name}_{file_name}_Json.json")
        # 确保目录存在，如果不存在则创建它
        if not os.path.exists(output_folder):
            print(f"Creating directory: {output_folder}")
            os.makedirs(output_folder)

        print(f"Saving file to: {output_file}")

        # 保存原始文本
        original_text_file = os.path.join(origin_folder, f"{os.path.splitext(os.path.basename(self.file_name))[0]}.txt")
        with open(original_text_file, "w", encoding="utf-8") as orig_f:
            orig_f.write(text_content)

        # 保存标注信息到 JSON 文件
        noun_text_list = self.noun_text.strip().split('\n')
        verb_text_list = self.verb_text.strip().split('\n')
        property_text_list = self.property_text.strip().split('\n')

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "category": selected_category,
                "category_index": selected_category_index,
                "text_length": text_length,
                "annotated_text": text_content.replace("<n>", "").replace("</n>", "").replace("<v>", "").replace("</v>",
                                                                                                                 "").replace(
                    "<f>", "").replace("</f>", ""),
                "noun_text": noun_text_list,
                "verb_text": verb_text_list,
                "property_text": property_text_list
            }, f, ensure_ascii=False, indent=4)
        self.close()

    def calculate_and_plot_word_frequency(self):
        # 获取 annotation_Json 文件夹路径
        parent_folder = os.path.dirname(os.path.dirname(os.path.abspath(self.file_name)))
        annotation_folder = os.path.join(parent_folder, "annotation_Json")

        # 遍历 annotation_Json 文件夹中的所有文件
        for filename in os.listdir(annotation_folder):
            if filename.endswith(".json"):
                # 构建完整的文件路径
                annotation_file = os.path.join(annotation_folder, filename)
                with open(annotation_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 提取名词和动词文本
                noun_text = " ".join(data["noun_text"])
                verb_text = " ".join(data["verb_text"])

                # 统计名词和动词的词频
                noun_counter = Counter(noun_text.split())
                verb_counter = Counter(verb_text.split())

                # 绘制词频图像
                self.ax.bar(noun_counter.keys(), noun_counter.values(), color='b', alpha=0.5, label='名词')
                self.ax.bar(verb_counter.keys(), verb_counter.values(), color='r', alpha=0.5, label='动词')
                self.ax.set_xlabel("词汇")
                self.ax.set_ylabel("词频")
                self.ax.set_title("词频统计")
                self.ax.legend()

                # 更新图像显示
                self.canvas.draw()

class myMainWindow(Ui_MainWindow, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon("C:/Users/36057/Desktop/fakeVideoAnnotation_PyQt/resources/images/shipinbiaozhu.png"))
        self.setWindowTitle("Fake-Video-Annotation")
        self.menu_bar = self.menuBar()
        self.view_menu = self.menu_bar.addMenu("数据统计")
        # 添加显示数据的动作
        self.show_data_action = QAction("查看数据", self)
        self.show_data_action.triggered.connect(self.show_data)
        self.view_menu.addAction(self.show_data_action)
        # 百度API相关设置
        APP_ID = '56769275'
        API_KEY = 'qN3OAq4kTCCGqMNTaeKWdD4T'
        SECRET_KEY = 'qnLTsp4k54USOvgswdPwI5vqtq6EIaFb'
        self.client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
        self.Text_listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.audio_listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.Video_listWidget.setSelectionMode(QAbstractItemView.MultiSelection)  # 开启多选框模式
        self.sld_video_pressed = False  # 判断当前进度条识别否被鼠标点击
        self.videoFullScreen = False  # 判断当前widget是否全屏
        self.videoFullScreenWidget = myVideoWidget()  # 创建一个全屏的widget
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.wgt_video)  # 视频播放输出的widget，就是上面定义的
        self.btn_open.clicked.connect(self.openVideoFile)  # 打开视频文件按钮
        self.btn_play.clicked.connect(self.playVideo)  # play
        self.btn_stop.clicked.connect(self.pauseVideo)  # pause
        self.player.positionChanged.connect(self.changeSlide)  # change Slide
        self.videoFullScreenWidget.doubleClickedItem.connect(self.videoDoubleClicked)  # 双击响应
        self.wgt_video.doubleClickedItem.connect(self.videoDoubleClicked)  # 双击响应
        self.sld_video.setTracking(False)
        self.sld_video.sliderReleased.connect(self.releaseSlider)
        self.sld_video.sliderPressed.connect(self.pressSlider)
        self.sld_video.sliderMoved.connect(self.moveSlider)  # 进度条拖拽跳转
        self.sld_video.ClickedValue.connect(self.clickedSlider)  # 进度条点击跳转
        self.sld_audio.valueChanged.connect(self.volumeChange)  # 控制声音播放
        self.btn_upload_video.clicked.connect(self.upload_video)  # 选取视频文件
        self.uploaded_files = []  # 存储展示选择的视频文件名称
        self.btn_extract_text.clicked.connect(self.extract_text_from_video)  # 视频转文本
        self.frame_time_edit.setText("3")  # 设定默认帧时间为3秒
        self.btn_convert_video_to_audio.clicked.connect(self.convert_video_to_audio)  # 视频转音频
        self.btn_convert_audio_to_text.clicked.connect(self.convert_audio_to_text)  # 音频转文本
        self.Video_listWidget.itemDoubleClicked.connect(self.openSelectedFile)  # 点击列表文件即可打开
        self.audio_listWidget.itemDoubleClicked.connect(self.openSelectedFile)
        self.Text_listWidget.itemDoubleClicked.connect(self.openSelectedFile)
        self.btn_Annotation.clicked.connect(self.show_Annotation_window)
        self.btn_clear_videos.clicked.connect(self.clear_videos)
        self.btn_clear_audios.clicked.connect(self.clear_audios)
        self.btn_clear_texts.clicked.connect(self.clear_texts)
        # 保存视频、音频和文本的路径列表
        self.video_paths = []
        self.audio_paths = []
        self.text_paths = []

    def clear_videos(self):
        selected_items = self.Video_listWidget.selectedItems()
        for item in selected_items:
            self.Video_listWidget.takeItem(self.Video_listWidget.row(item))

    def clear_audios(self):
        selected_items = self.audio_listWidget.selectedItems()
        for item in selected_items:
            self.audio_listWidget.takeItem(self.audio_listWidget.row(item))

    def clear_texts(self):
        selected_items = self.Text_listWidget.selectedItems()
        for item in selected_items:
            self.Text_listWidget.takeItem(self.Text_listWidget.row(item))

    def show_data(self):
        video_count = len(self.video_paths)
        total_duration = sum(self.calculate_video_duration(path) for path in self.video_paths)
        average_duration = total_duration / video_count if video_count > 0 else 0

        total_text_count = sum(self.calculate_text_count(path) for path in self.text_paths)
        average_text = total_text_count / len(self.text_paths) if len(self.text_paths) > 0 else 0

        QMessageBox.information(self, "Data",
                                f"已标注的视频数量：{video_count}\n"
                                f"平均视频时长：{average_duration}秒\n"
                                f"提取的文本平均数量：{average_text}")

    def calculate_video_duration(self, file_path):
        video = cv2.VideoCapture(file_path)
        duration = video.get(cv2.CAP_PROP_FRAME_COUNT) / video.get(cv2.CAP_PROP_FPS)
        video.release()
        return duration

    def calculate_text_count(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            text_count = len(file.read().split())
        return text_count

    def show_Annotation_window(self):
        selected_items = self.Text_listWidget.selectedItems()
        if selected_items:
            for item in selected_items:
                file_path = item.text()
                with open(file_path, "r", encoding="utf-8") as file:
                    text_content = file.read()
                    Annotation_window = AnnotationWindow(text_content, file_path)
                    Annotation_window.show()

    # 打开选中的文件
    def openSelectedFile(self, item: QListWidgetItem):
        # 获取选中的文件路径
        file_path = item.text()
        # 打开文件
        if os.path.exists(file_path):
            os.startfile(file_path)  # 在Windows系统中打开文件
        else:
            QMessageBox.warning(self, "File Not Found", f"The file {file_path} does not exist.")

    # 操作成功返回简单的消息框机制
    def operation_successful_popup(self):
        msg = QMessageBox()
        msg.setWindowTitle("Success")
        msg.setText("操作成功")
        msg.setIcon(QMessageBox.Information)
        msg.exec_()

    # 曾经提取过的视频读入成功返回消息框
    def show_last_annotation_popup(self):
        msg = QMessageBox()
        msg.setWindowTitle("Success")
        msg.setText("上次提取信息已加载")
        msg.setIcon(QMessageBox.Information)
        msg.exec_()

    def convert_audio_to_text(self):
        selected_items = self.audio_listWidget.selectedItems()
        if selected_items:
            for selected_item in selected_items:
                file_path = selected_item.text()
                self.audio_to_text(file_path)

    def audio_to_text(self, file_path):
        api = RequestApi(appid="609c45ef", secret_key="ec26bac5dba71c1d419310ce2e01f649", upload_file_path=file_path)
        file = api.all_api_request()
        self.Text_listWidget.addItem(file)
        self.operation_successful_popup()

    def check_frame_folder(self, video_file):
        video_folder = os.path.dirname(video_file)
        video_name = os.path.splitext(os.path.basename(video_file))[0]
        frame_folder = os.path.join(video_folder, video_name + "_frames")
        if os.path.exists(frame_folder):
            text_files = [file for file in os.listdir(frame_folder) if file.endswith(".txt")]
            if text_files:
                for text_file in text_files:
                    self.Text_listWidget.addItem(os.path.join(frame_folder, text_file))
                return True
        return False

    def upload_video(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "Video Files (*.mp4 *.avi)")
        if files:
            for file in files:
                if not self.check_frame_folder(file):
                    self.uploaded_files.append(file)
                    self.Video_listWidget.addItem(file)
                    self.video_paths += [os.path.join(file)]
                    self.operation_successful_popup()
                else:
                    self.show_last_annotation_popup()

    def extract_text_from_video(self, video_file):
        frame_time = int(self.frame_time_edit.text())
        selected_items = self.Video_listWidget.selectedItems()
        if selected_items:
            for item in selected_items:
                file_path = item.text()
                self.extract_text(file_path, frame_time)

    def convert_video_to_audio(self):
        selected_items = self.Video_listWidget.selectedItems()
        if selected_items:
            for item in selected_items:
                file_path = item.text()
                self.extract_Audio(file_path)

    def extract_Audio(self, file_path):
        # 构建新文件夹路径
        folder_name = os.path.splitext(os.path.basename(file_path))[0] + "_audio"
        audio_folder = os.path.join(os.path.dirname(file_path), folder_name)
        # 构建音频文件路径
        audio_file = os.path.join(audio_folder, os.path.splitext(os.path.basename(file_path))[0] + ".wav")
        os.makedirs(audio_folder, exist_ok=True)  # 创建存储音频文件的文件夹（如果不存在）
        # 构建 ffmpeg 命令
        command = ["ffmpeg", "-i", file_path, "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-y", audio_file]
        subprocess.call(command)  # 调用 ffmpeg 进行视频到音频的转换
        self.audio_listWidget.addItem(audio_file)  # 将生成的音频文件添加到列表中
        self.operation_successful_popup()  # 显示操作成功提示框

    def extract_text(self, file_path, frame_time):
        capture = cv2.VideoCapture(file_path)
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

        if frame_time == 0:
            self.extract_whole_video(file_path)  # 如果帧时间为0，则提取视频的全部文本
        else:
            self.extract_frames_and_text(file_path, capture, total_frames, frame_time)  # 否则根据时间帧提取帧和文本
        capture.release()

    def extract_whole_video(self, video_path):
        frame_folder = os.path.splitext(video_path)[0] + "_frames"
        os.makedirs(frame_folder, exist_ok=True)
        capture = cv2.VideoCapture(video_path)
        while capture.isOpened():
            ret, frame = capture.read()
            if not ret:
                break
            cv2.imwrite(os.path.join(frame_folder, f"frame_{int(capture.get(cv2.CAP_PROP_POS_FRAMES))}.jpg"), frame)
        capture.release()

        # OCR识别
        for filename in os.listdir(frame_folder):
            if filename.endswith(".jpg"):
                image_path = os.path.join(frame_folder, filename)
                extracted_text = self.perform_ocr(image_path)
                # 识别的文本信息保存到文件中去
                text_file_path = os.path.splitext(image_path)[0] + "_text.txt"
                with open(text_file_path, "w", encoding="utf-8") as text_file:
                    text_file.write(extracted_text)

    def extract_frames_and_text(self, video_path, capture, total_frames, frame_time):
        frame_folder = os.path.splitext(video_path)[0] + "_frames"
        os.makedirs(frame_folder, exist_ok=True)
        frame_count = 0
        while capture.isOpened():
            ret, frame = capture.read()
            if not ret:
                break
            current_time = int(capture.get(cv2.CAP_PROP_POS_MSEC)) / 1000
            if current_time >= frame_time * frame_count:
                cv2.imwrite(os.path.join(frame_folder, f"frame_{frame_count}.jpg"), frame)
                frame_count += 1
        capture.release()

        # 对每张图片进行OCR识别
        for filename in os.listdir(frame_folder):
            if filename.endswith(".jpg"):
                image_path = os.path.join(frame_folder, filename)
                extracted_text = self.perform_ocr(image_path)
                # 将识别到的文本信息保存到文件中
                text_file_path = os.path.splitext(image_path)[0] + "_text.txt"
                # 将描述视频帧的文本信息保存到文件中
                with open(text_file_path, "w", encoding="utf-8") as text_file:
                    text_file.write(extracted_text)
                self.Text_listWidget.addItem(text_file_path)
        self.operation_successful_popup()

    # OCR文本识别
    def perform_ocr(self, image_path):
        with open(image_path, 'rb') as fp:
            image = fp.read()
        # 调用百度API进行OCR识别
        options = {}
        options['language_type'] = "CHN_ENG"
        options['detect_direction'] = "true"
        options['detect_language'] = "true"
        options['probability'] = "false"
        result = self.client.basicGeneral(image, options)
        extracted_text = ""
        for word in result['words_result']:
            extracted_text += word['words'] + "\n"
            print(word['words'])
        return extracted_text

    def volumeChange(self, position):
        volume = round(position / self.sld_audio.maximum() * 100)
        print("vlume %f" % volume)
        self.player.setVolume(volume)
        self.lab_audio.setText("volume:" + str(volume) + "%")

    def clickedSlider(self, position):
        if self.player.duration() > 0:  # 开始播放后才允许进行跳转
            video_position = int((position / 100) * self.player.duration())
            self.player.setPosition(video_position)
            self.lab_video.setText("%.2f%%" % position)
        else:
            self.sld_video.setValue(0)

    def moveSlider(self, position):
        self.sld_video_pressed = True
        if self.player.duration() > 0:  # 开始播放后才允许进行跳转
            video_position = int((position / 100) * self.player.duration())
            self.player.setPosition(video_position)
            self.lab_video.setText("%.2f%%" % position)

    def pressSlider(self):
        self.sld_video_pressed = True
        print("pressed")

    def releaseSlider(self):
        self.sld_video_pressed = False

    def changeSlide(self, position):
        if not self.sld_video_pressed:  # 进度条被鼠标点击时不更新
            self.vidoeLength = self.player.duration() + 0.1
            self.sld_video.setValue(round((position / self.vidoeLength) * 100))
            self.lab_video.setText("%.2f%%" % ((position / self.vidoeLength) * 100))

    def openVideoFile(self):
        self.player.setMedia(QMediaContent(QFileDialog.getOpenFileUrl()[0]))  # 选取视频文件
        self.player.play()  # 播放视频
        print(self.player.availableMetaData())

    def playVideo(self):
        self.player.play()

    def pauseVideo(self):
        self.player.pause()

    def videoDoubleClicked(self, text):

        if self.player.duration() > 0:  # 开始播放后才允许进行全屏操作
            if self.videoFullScreen:
                self.player.setVideoOutput(self.wgt_video)
                self.videoFullScreenWidget.hide()
                self.videoFullScreen = False
            else:
                self.videoFullScreenWidget.show()
                self.player.setVideoOutput(self.videoFullScreenWidget)
                self.videoFullScreenWidget.setFullScreen(1)
                self.videoFullScreen = True


if __name__ == '__main__':
    # QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    video_gui = myMainWindow()
    video_gui.show()
    sys.exit(app.exec_())
