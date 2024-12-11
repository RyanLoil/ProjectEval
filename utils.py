import shutil
import os

import cv2
from selenium.webdriver.common.by import By
from Levenshtein import distance as levenshtein_distance
import runpy
import io
from contextlib import redirect_stdout, redirect_stderr

from config import IMAGE_SIMILARITY_THRESHOLD


def selenium_find_minimum_ancestor(driver, source_tag, check_by, check_text):
    """
    a selenium function that finds the minimum ancestor for a given tag
    :param driver: selenium driver, usually used self.driver in the project eval
    :param source_tag:
    :param check_by:
    :param check_text:
    :return:
    """
    counter = 5
    tag = source_tag
    while counter > 0:
        try:
            tag.find_element(check_by, check_text)
            break
        except Exception:
            tag = tag.find_element(By.XPATH, "./ancestor::*[1]")
            counter -= 1
            continue
    if counter == 0:
        raise AssertionError('No minimum ancestor found')
    return tag

def copy_file(src: str, dst: str) -> None:
    """
    Copy a file from src to dst.

    :param src: Source file path
    :param dst: Destination file path or directory
    :raises FileNotFoundError: If the src file does not exist
    :raises IsADirectoryError: If the src is a directory
    :raises PermissionError: If the program lacks permission to read src or write to dst
    """
    try:
        # Check if src exists
        if not os.path.isfile(src):
            raise FileNotFoundError(f"Source file not found: {src}")

        # If dst is a directory, construct full destination path
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))

        # Copy file
        shutil.copy2(src, dst)
        print(f"File copied successfully from {src} to {dst}")
    except Exception as e:
        print(f"Error: {e}")

def rename_file(src: str, dst: str) -> None:
    """
    Rename a file in the same folder or to a new folder.

    :param src: Source file path
    :param dst: Destination file path (new name or new path)
    :raises FileNotFoundError: If the src file does not exist
    :raises PermissionError: If the program lacks permission to rename the file
    """
    try:
        os.rename(src, dst)
        # print(f"File renamed successfully from {src} to {dst}")
    except Exception as e:
        raise e

def run_entry(path: str) -> tuple[str, str]:
    """
    Capture all stdout and stderr, including logger outputs written to console.

    :param module_name: Module to run using runpy
    :return: Tuple containing captured stdout and stderr
    """
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    try:
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            runpy.run_path(path, run_name="__main__")
        return_value = (stdout_buffer.getvalue(), stderr_buffer.getvalue())
    except Exception as e:
        return_value = (str(e), str(e))
    finally:
        stdout_buffer.seek(0)
        stderr_buffer.seek(0)


    return return_value


def string_similarity(str1, str2):
    """
    计算两个字符串的相似性，基于 Levenshtein 距离。

    :param str1: 第一个字符串
    :param str2: 第二个字符串
    :return: 相似性分数（0 到 1 之间），1 表示完全相同，0 表示完全不同
    """
    max_len = max(len(str1), len(str2))
    if max_len == 0:  # 防止除以零
        return 1.0
    dist = levenshtein_distance(str1, str2)
    similarity = 1 - dist / max_len
    return similarity


def calculate_histogram_similarity(image1, image2):
    image1 = cv2.imread(image1)
    image2 = cv2.imread(image2)
    # 使用ORB提取特征
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(image1, None)
    kp2, des2 = orb.detectAndCompute(image2, None)

    # 匹配特征
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)

    # 计算匹配率
    similarity = len(matches) / min(len(kp1), len(kp2))
    return similarity > IMAGE_SIMILARITY_THRESHOLD
