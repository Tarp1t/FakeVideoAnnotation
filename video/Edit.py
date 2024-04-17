import os

# 文件名改为统一格式
def rename_videos_in_folders(root_folder):
    # 遍历根文件夹中的所有子文件夹
    for folder_name in os.listdir(root_folder):
        folder_path = os.path.join(root_folder, folder_name)

        # 检查是否是文件夹
        if os.path.isdir(folder_path):
            # 获取文件夹名称作为新的文件名
            new_file_name = folder_name

            # 遍历文件夹中的所有视频文件
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)

                # 检查文件是否是视频文件
                if os.path.isfile(file_path) and file_name.endswith((".mp4", ".avi", ".mov")):
                    # 构建新的文件名路径
                    new_file_path = os.path.join(folder_path, new_file_name + os.path.splitext(file_name)[1])

                    # 重命名视频文件
                    os.rename(file_path, new_file_path)


if __name__ == "__main__":
    # 根文件夹路径
    root_folder = r"C:\Users\36057\Desktop\covid_video\frame_and_transcript"

    # 调用函数并传入根文件夹路径
    rename_videos_in_folders(root_folder)