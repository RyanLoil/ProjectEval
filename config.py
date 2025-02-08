import configparser
import os

configs = configparser.ConfigParser()
configs.read("config.ini")

OPEN_AI_KEY = configs["Default"]['OPEN_AI_KEY']
DEFAULT_BROWSER_TYPE = configs["Default"]['DEFAULT_BROWSER_TYPE']
ENCODE_FORMAT = configs["Default"]['ENCODE_FORMAT']
VENV_PATH = eval(configs["Default"]['VENV_PATH'])
STRING_SIMILARITY_THRESHOLD = float(configs["Default"]['STRING_SIMILARITY_THRESHOLD'])
IMAGE_SIMILARITY_THRESHOLD = float(configs["Default"]['IMAGE_SIMILARITY_THRESHOLD'])
TIMEOUT_LIMIT = float(configs["Default"]['TIMEOUT_LIMIT'])