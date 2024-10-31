import calendar
import csv
import json
import logging
import os
import signal
import string
import subprocess
import sys
import time
import traceback
import threading

from time import sleep

import pyperclip
import selenium
from selenium import webdriver
from selenium.webdriver.support import ui
from selenium.webdriver.common.by import By
from datetime import datetime

import utils
from config import ENCODE_FORMAT
from llm import LLMTest

DRIVER_DICT = {
    'chrome': 'webdriver.Chrome()',
    'edge': 'webdriver.Edge()',
    'firefox': 'webdriver.Firefox()',
}

selenium_util_function = [
    """
    
    """,
]


class BaseJudge:
    def __init__(self, requirements: list[str], ):
        '''

        :param project_answer_list: Required. The list that llm provided according to the code and checklist
        :param requirements: Optional. The list of required pakages that LLM used in code generation
        :param generation_list_path: Optional. The generation path, usually 'data/generation_list.json', but we actually divided into three different types.
        '''
        # logger
        self.logger = logging.getLogger('Judge')
        self.logger.setLevel(level=logging.DEBUG)
        if not self.logger.handlers:
            handler = logging.FileHandler("log/{0}-Judge.log".format(datetime.now().strftime("%Y%m%d-%H%M%S")))
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            console.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.addHandler(console)

        self.requirements = requirements

        # self.logger.info("Loading generation list...")
        # try:
        #     self.generation_list = json.load(open(generation_list_path, 'r', encoding='utf-8'))
        # except Exception as e:
        #     self.logger.critical("Loading generation list failed with error {}".format(e))
        #     raise Exception("Loading generation list failed with error {}".format(e))

    def environment_initiate(self):
        if not self.requirements:
            # No additional requirements.
            return True
        self.logger.info("Install required pakages.")
        try:
            d = os.system("pip install " + " ".join(self.requirements))
            if d != 0:
                raise Exception("Install required pakages failed with return code: " + str(d))
        except Exception as e:
            self.logger.critical(e)
            return False
        return True

    def preprocess(self, *args, **kwargs):
        # 启动测试环境
        if not self.environment_initiate():
            raise Exception("Environment installation failed.")
        pass

    def clean(self):
        # 清理之前的运行环境
        pass

    def check(self, test_no, testcode, *args, **kwargs):
        # 测试核心函数
        pass

    def get_parameters(self, model: LLMTest, answer, technical_stack, parameter_request):
        '''
        :param model: LLMTest object,
        :param answer:
        :param parameter_request:
        :return:
        '''
        self.logger.info("Requesting parameters from LLM to adapt question.")
        parameters = model.get_parameter(answer, technical_stack,
                                         parameter_request)  # In GPTTest, the parameter asking is a full answer list of all pages.
        return parameters

    # 为测试准备参数


class WebsiteJudge(BaseJudge):
    def __init__(self, requirements, browser_type, project_root,
                 website_home="http://localhost:8000/"):
        '''
        :param requirements: Packages that is required to evaluate(python only).
        :param browser_type: Choose the type of web browser, support chrome, firefox and edge.
        :param website_home:
        '''
        super().__init__(requirements)

        if browser_type not in ['chrome', 'firefox', 'edge']:
            raise Exception('Not a valid browser type')
        try:
            self.logger.info(f"Webdriver {browser_type} Initializing")
            self.driver = eval(DRIVER_DICT[browser_type])
            self.driver.set_page_load_timeout(3)
        except Exception as e:
            self.logger.critical(e)

        # self.website_initiate_command = website_initiate_command
        self.website_project_root = project_root
        self.website_home = website_home  # Default
        # self.website_project_process = self.WebsiteProcess()

    # class WebsiteProcess(Process):
    #     def __init__(self):
    #         Process.__init__(self)
    #
    #     def run(self):
    #         d = os.system(self.website_initiate_command)
    #
    #     def set_website_initiate_command(self, website_initiate_command):
    #         self.website_initiate_command = website_initiate_command
    #
    #     def django_shutdown(self):  # 不够优雅，还是通过subprocess来关闭会更好
    #         result = os.popen('netstat -ano|findstr "8000" ').read().split("\n")
    #         for i in range(len(result)):
    #             result[i] = result[i].split()
    #             if len(result[i]) == 5 and result[i][3] == "LISTENING":
    #                 os.popen("taskkill -pid %s -f" % result[i][4])
    #                 break

    class DjangoServer:
        def __init__(self, project_path, logger,
                     venv_path: str = os.path.abspath(".").replace("\\", "/") + "/.venv/"):  # TODO 移除绝对路径交给用户
            '''
            For a python environments, the venv_path should be the ProjectEval's venv path which should be more convenient

            :param project_path:
            :param logger:
            :param venv_path:
            '''
            self.venv_path = venv_path
            self.project_path = project_path
            self.process = None
            self.logger = logger
            self.stdout_file = open("log/{0}-Project-Normal.log".format(
                datetime.now().strftime("%Y%m%d-%H%M%S")), "a", encoding="utf-8")
            self.stderr_file = open("log/{0}-Project-Error.log".format(
                datetime.now().strftime("%Y%m%d-%H%M%S")), "a", encoding="utf-8")
            self.project_id = project_path.split("/")[-1] if project_path.split("/")[-1] else project_path.split("\\")[
                -1]
            self.stdout_file.write("=============Project {}===============".format(self.project_id))
            self.stderr_file.write("=============Project {}===============".format(self.project_id))

        def get_activate_script(self):
            activate_script = os.path.join(self.venv_path, 'Scripts', 'python.exe')
            if not os.path.exists(activate_script):
                raise FileNotFoundError(f"Virtual environment activation script not found: {activate_script}")
            return activate_script

        def initiate_command(self, initiate_command_list: [[]]):
            '''
            :param initiate_command_list: list for initiate command. A list for each command which is the command parameter for python. Example:[['manage.py', 'makemigrations']]
            :return: None
            '''
            for initiate_command in initiate_command_list:
                process = subprocess.Popen([self.get_activate_script(), *initiate_command], cwd=self.project_path,
                                           shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                           creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

                process.wait(15)
                process.terminate()

        def start(self):

            self.process = subprocess.Popen([self.get_activate_script(), "manage.py", "runserver"],
                                            cwd=self.project_path,
                                            shell=True,
                                            stdout=self.stdout_file, # PIPE会被阻塞如果日志太多
                                            stderr=self.stderr_file, # PIPE会被阻塞如果日志太多
                                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)  # 必须要提供CREATE_NEW_PROCESS_GROUP，否则会杀掉所有进程
            # err = self.process.stderr.read().decode(ENCODE_FORMAT)
            # if err:
            #     self.logger.warning(err)
            self.logger.info("Django server started with PID:" + str(self.process.pid))

        def stop(self):
            if self.process and self.process.poll() is None:
                self.process.send_signal(signal.CTRL_BREAK_EVENT)  # 唯一的办法解决所有问题
            else:
                self.logger.info("Django server is not running.")
            self.stdout_file.close()
            self.stderr_file.close()

    WEBSITE_SERVER_MANAGER = {
        'Django': DjangoServer,
        # All other kinds of website server should be created in this way.
    }

    def preprocess(self, technical_stack, initiate_command_list, *args, **kwargs):
        '''

        :param initiate_command_list:
        :param technical_stack:
        :param args: For the subprocesss.
        :param kwargs: For the subprocesss.
        :param initiate_command_list: The command for running project. For django, "manage.py makemigrations" and "manage.py migrate" will be its initiate commands.
        :return:
        '''
        os.system("chcp 65001")
        self.logger.info("Preprocessing Website Project Test.")
        # TODO Django一般不自动创建Manage.py
        super().preprocess()
        try:
            self.subprocess = WebsiteJudge.WEBSITE_SERVER_MANAGER[technical_stack](logger=self.logger, *args, **kwargs)
            self.subprocess.initiate_command(initiate_command_list)
            self.subprocess.start()
        except Exception as e:
            self.logger.critical(e)
            return False

        try:
            self.driver.get(self.website_home)
        except Exception as e:
            self.logger.critical(e)
            return False
        return True

    def clean(self):
        # self.website_project_process.django_shutdown()
        # self.website_project_process.terminate()
        # self.website_project_process.join()
        # self.website_project_process.close()
        self.subprocess.stop()
        self.driver.close()

    def check(self, test_no, testcode, *args, **kwargs):
        def timeout():
            self.driver.execute_script("window.stop()")
            raise TimeoutError("Test execution exceeded the time limit.")

        self.logger.info(f"{test_no} starting.")
        super().check(test_no, testcode, *args, **kwargs)
        try:
            namespace = {"By": By(), "time": time, "pyperclip": pyperclip, "string": string,
                         'ui': ui, 'os': os, 'csv': csv, 'utils': utils, 'datetime': datetime,
                         'calendar': calendar
                         }  # TODO Namespace中其它库文件将会是需要处理的问题
            callable_default_package = {name for name in namespace.keys()}
            exec(testcode, namespace)
            function_name = [name for name, value in namespace.items() if callable(value) and name not in callable_default_package][0]
            test = namespace[function_name]
            try:
                timer = threading.Timer(3, timeout)  # Set timeout limit (in seconds)
                timer.start()
                result = test(self.driver, *args, **kwargs)
            except AssertionError as e:
                result = e
                self.logger.warning(f"Assertion Error: {str(e)}\nTestcase failed.")
            except TimeoutError as e:
                result = "time out"
                self.logger.warning(f"Timeout Error: {str(e)}")
            finally:
                timer.cancel()
            if result is not None:
                # Test code will return nothing unless something goes wrong.
                raise Exception(str(test_no) + ': Wrong Answer of ' + str(result))
            sleep(0.3)
        except Exception as e:
            self.logger.warning(str(e))
            if not str(e).strip():
                self.logger.warning(traceback.format_exc())
            return False

        self.logger.info(f"{test_no} passed.")
        return True


class SoftwareJudge(BaseJudge):
    pass


class BatchJudge(BaseJudge):
    pass
