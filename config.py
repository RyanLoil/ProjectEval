import configparser
import os
from datetime import datetime

configs = configparser.ConfigParser()
configs.read("config.ini")

PROJECT_EVAL_DEFAULT_TEST_CASE = 284
PROJECT_EVAL_DEFAULT_TEST_DIR = "test/" + datetime.now().strftime("%Y%m%d") + "/"
PROJECT_EVAL_DEFAULT_EXPERIMENT_DIR = "experiments/" + datetime.now().strftime("%Y%m%d") + "/"
PROJECT_EVAL_DEFAULT_DATA_PATH = "data/project_eval_project.json"
PROJECT_EVAL_DEFAULT_ANSWER_PATH = "data/project_eval_answer.json"
PROJECT_EVAL_DEFAULT_PARAMETER_PATH = "data/project_eval_parameter.json"

OPEN_AI_KEY = configs["Default"]['OPEN_AI_KEY']
GOOGLE_AI_KEY = configs["Default"]['GOOGLE_AI_KEY']
DEFAULT_BROWSER_TYPE = configs["Default"]['DEFAULT_BROWSER_TYPE']
ENCODE_FORMAT = configs["Default"]['ENCODE_FORMAT']
VENV_PATH = eval(configs["Default"]['VENV_PATH'])
STRING_SIMILARITY_THRESHOLD = float(configs["Default"]['STRING_SIMILARITY_THRESHOLD'])
IMAGE_SIMILARITY_THRESHOLD = float(configs["Default"]['IMAGE_SIMILARITY_THRESHOLD'])
TIMEOUT_LIMIT = float(configs["Default"]['TIMEOUT_LIMIT'])
IO_WAIT = float(configs["Default"]['IO_WAIT'])
LOG_PATH = configs["Default"]["LOG_PATH"]
