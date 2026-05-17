import os
import shutil


def clear_pycache():
    """清除当前目录下任何位置的__pycache__文件夹"""

    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            shutil.rmtree(os.path.join(root, "__pycache__"))


if __name__ == "__main__":
    clear_pycache()
    print("__pycache__清除完成")
