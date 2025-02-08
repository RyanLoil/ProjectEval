import logging, os, signal, subprocess, time, threading, traceback
import calendar, csv, string, openpyxl
import runpy
import shutil
import sys
from time import sleep

import pandas
import pyperclip
import select
from selenium.webdriver.support import ui
from selenium.webdriver.common.by import By
from datetime import datetime
from selenium import webdriver
from func_timeout import func_set_timeout, FunctionTimedOut, func_timeout

import utils
from config import VENV_PATH, STRING_SIMILARITY_THRESHOLD, TIMEOUT_LIMIT, IO_WAIT, LOG_PATH
from llm import LLMTest

DRIVER_DICT = {
    'chrome': 'webdriver.Chrome()',
    'edge': 'webdriver.Edge()',
    'firefox': 'webdriver.Firefox()',
}


class BasePythonManager:
    def __init__(self, project_id, project_path, logger):
        '''
        For a python environments, the venv_path should be the ProjectEval's venv path which should be more convenient

        :param project_path:
        :param logger:
        :param venv_path:
        '''
        self.venv_path = VENV_PATH
        self.project_path = project_path
        self.process = None
        self.logger = logger
        self.start_command: list[str] = []

        self.stdout_file = open(f"{LOG_PATH}/{self.logger.start_time}-Project-Normal.log", "a", encoding="utf-8")
        self.stderr_file = open(f"{LOG_PATH}/{self.logger.start_time}-Project-Error.log", "a", encoding="utf-8")
        self.project_id = project_id
        self.stdout_file.write("=============Project {}===============\n".format(self.project_id))
        self.stderr_file.write("=============Project {}===============\n".format(self.project_id))

    def get_activate_script(self):
        activate_script = os.path.join(self.venv_path, 'Scripts', 'python.exe')
        if not os.path.exists(activate_script):
            raise FileNotFoundError(f"Virtual environment activation script not found: {activate_script}")
        return activate_script

    def initiate_command(self, initiate_command_list: [[]]):
        '''
        :param initiate_command_list: list for initiate command. A list for each command which is the command parameter for python. Example:[['manage.py', 'makemigrations']].
        Or use [[['manage.py', 'createsuperuser'], ["Test","abc@example.com","abc12345","abc12345"]], ...] to run further command in a single shell.
        :return: None
        '''
        for initiate_command in initiate_command_list:
            process = subprocess.Popen([self.get_activate_script(), *initiate_command], cwd=self.project_path,
                                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

            process.wait(10)
            process.terminate()

    def start(self):
        self.process = subprocess.Popen([self.get_activate_script(), *self.start_command],
                                        cwd=self.project_path,
                                        shell=True,
                                        stdout=self.stdout_file,  # PIPE会被阻塞如果日志太多
                                        stderr=self.stderr_file,  # PIPE会被阻塞如果日志太多
                                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)  # 必须要提供CREATE_NEW_PROCESS_GROUP，否则会杀掉所有进程
        # err = self.process.stderr.read().decode(ENCODE_FORMAT)
        # if err:
        #     self.logger.warning(err)
        self.logger.info(f"{self.__class__.__name__} started with PID: {str(self.process.pid)}")

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.send_signal(signal.CTRL_BREAK_EVENT)  # 唯一的办法解决所有问题
        else:
            self.logger.info(f"{self.__class__.__name__} is not running.")
        self.stdout_file.close()
        self.stderr_file.close()


class BaseJudge:
    def __init__(self, project_id, requirements: list[str]):
        '''

        :param project_answer_list: Required. The list that llm provided according to the code and checklist
        :param requirements: Optional. The list of required pakages that LLM used in code generation
        :param generation_list_path: Optional. The generation path, usually 'data/generation_list.json', but we actually divided into three different types.
        '''
        # logger
        self.logger = logging.getLogger('Judge')
        self.logger.setLevel(level=logging.DEBUG)
        if not self.logger.handlers:
            self.logger.start_time = datetime.now().strftime("%Y%m%d-%H%M%S")
            handler = logging.FileHandler(f"{LOG_PATH}/{self.logger.start_time}-Judge.log", encoding="utf-8")
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            console.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.addHandler(console)

        self.requirements = requirements
        self.status = False
        self.project_id = project_id
        self.subprocess = None
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
            self.logger.critical(f"Environment initiate exception:{e}")
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
    def __init__(self, project_id, requirements, browser_type, project_root,
                 website_home="http://localhost:8000/"):
        '''
        :param requirements: Packages that is required to evaluate(python only).
        :param browser_type: Choose the type of web browser, support chrome, firefox and edge.
        :param website_home:
        '''
        super().__init__(project_id, requirements)

        if browser_type not in ['chrome', 'firefox', 'edge']:
            raise Exception('Not a valid browser type')
        try:
            self.logger.info(f"Webdriver {browser_type} Initializing")
            self.driver = eval(DRIVER_DICT[browser_type])
            self.driver.set_page_load_timeout(3)
        except Exception as e:
            self.logger.critical(f"WebsiteJudge initiate exception: {e}")

        # self.website_initiate_command = website_initiate_command
        self.website_project_root = project_root
        self.website_home = website_home  # Default
        # self.website_project_process = self.WebsiteProcess()

    class DjangoServer(BasePythonManager):
        def __init__(self, project_id, project_path, logger):
            super().__init__(project_id, project_path, logger)
            self.start_command = ["manage.py", "runserver"]

        def initiate_command(self, initiate_command_list: [[]]):
            '''
            Notice: if the initiate_command_list is not set, it will automatically run the default Django command, and add superuser named "Admin" with password "abc#12345"
            :param initiate_command_list: the initiate command list that are given by user or LLM.
            :return: None
            '''
            if initiate_command_list == [[]] or not initiate_command_list:
                initiate_command_list = [["manage.py", "makemigrations"],
                                         ["manage.py", "migrate"],
                                         ]  # ["manage.py", "createsuperuser", "--username", "Admin", "--email",  "abc@example.com", "--noinput"]
                super().initiate_command(initiate_command_list)
                # Create Superuser
                process = subprocess.Popen([self.get_activate_script(), "manage.py", "shell"], cwd=self.project_path,
                                           text=True,
                                           shell=True, stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                                           )
                process.communicate(input="\n".join([
                    "from django.contrib.auth.models import User",
                    "u = User(username='Admin')",
                    # ProjectEval Django Standard Admin User. Username: Admin, Password: abc#12345
                    "u.set_password('abc#12345')",
                    "u.is_superuser = True",
                    "u.is_staff = True",
                    "u.is_active = True",
                    "u.save()",
                    "",
                ]), timeout=10)
                process.kill()
            else:
                super().initiate_command(initiate_command_list)

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
            self.subprocess = WebsiteJudge.WEBSITE_SERVER_MANAGER[technical_stack](project_id=self.project_id,
                                                                                   logger=self.logger, *args, **kwargs)
            self.subprocess.initiate_command(initiate_command_list)
            self.subprocess.start()
            self.status = True
        except Exception as e:
            self.logger.critical(f"Subprocess initiate exception:{e}")
            self.subprocess.stop()
            return False

        try:
            self.driver.get(self.website_home)
        except Exception as e:
            self.logger.critical(f"Website home visit exception:{e}")
            self.subprocess.stop()
            return False
        return True

    def clean(self):
        try:
            self.subprocess.stop()
            self.driver.close()
        except Exception as e:
            self.logger.info(f"Clean exception:{e}")
        self.status = False

    def check(self, test_no, testcode, *args, **kwargs):
        self.logger.info(f"{test_no} starting.")
        super().check(test_no, testcode, *args, **kwargs)
        try:
            namespace = {"By": By(), "time": time, "pyperclip": pyperclip, "string": string,
                         'ui': ui, 'os': os, 'csv': csv, 'utils': utils, 'datetime': datetime,
                         'calendar': calendar
                         }  # TODO Namespace中其它库文件将会是需要处理的问题
            callable_default_package = {name for name in namespace.keys()}
            exec(testcode, namespace)
            function_name = \
                [name for name, value in namespace.items() if callable(value) and name not in callable_default_package][
                    0]
            test = namespace[function_name]
            try:
                result = func_timeout(TIMEOUT_LIMIT, test, args=(self.driver, *args), kwargs=kwargs)
            except AssertionError as e:
                result = e
                self.logger.warning(f"Assertion Error: {str(e)}\nTestcase failed.")
            except FunctionTimedOut as e:
                result = "timeout"
                self.logger.warning(f"Timeout Error: {str(e)}")
            except Exception as e:
                result = "runtime error"
                self.logger.warning(f"Testcode runtime exception: {e}")
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
    # TODO Software adaption
    pass


class BatchJudge(BaseJudge):
    def __init__(self, project_id, requirements, project_root):
        super().__init__(project_id, requirements)

        self.project_root = project_root

    class FileManager(BasePythonManager):
        def __init__(self, project_id, project_path, logger, start_file):
            super().__init__(project_id, project_path, logger)
            self.initial_status = False
            self.start_file = start_file

        def initiate_command(self, initiate_command_list: [[]]):
            """
            copy all material files from source path to project path
            :param initiate_command_list: From basic python manager,
            :return:
            """
            super().initiate_command(initiate_command_list)
            material_path = "data/material/"
            self.logger.info(f"Copy material files from {material_path} to {self.project_path}.")
            for file_name in os.listdir(material_path):
                if file_name.startswith(f"{self.project_id}-"):
                    shutil.copyfile(os.path.join(material_path, file_name), os.path.join(self.project_path, file_name))
                    self.logger.debug(f"{file_name} copied.")
            time.sleep(IO_WAIT)

        def start(self):
            # File Batch no needs of subprocess
            pass

    class ConsoleManager(BasePythonManager):
        def __init__(self, project_id, project_path, logger, start_file):
            super().__init__(project_id, project_path, logger)
            self.initial_status = True
            self.start_command = [start_file, ]
            self.stdout_file_path = "output.txt"
            self.stdout_tell = 0

        # class ReaderWithTimeout: # Failed, as readline will get one more line when it is timeout.
        #     """Helper class for threaded reading with timeout."""
        #     def __init__(self, pipe):
        #         self.pipe = pipe
        #         self.line = None
        #         self.done = threading.Event()
        #
        #     def read_line(self):
        #         try:
        #             temp = self.pipe.readline()
        #             self.line = temp if temp.strip() is None else temp.strip()
        #         finally:
        #             self.done.set()
        #
        # def read_with_timeout(self, pipe, timeout=1):
        #     """Read a line from process.stdout with timeout."""
        #     reader = self.ReaderWithTimeout(pipe)
        #     thread = threading.Thread(target=reader.read_line)
        #     thread.start()
        #     thread.join(timeout=timeout)
        #     if reader.done.is_set():
        #         return reader.line
        #     else:
        #         self.logger.debug(f"Timeout of {timeout} seconds exceeded while waiting for output.")
        #         return "EOF"

        def start(self):
            self.process = subprocess.Popen(
                [self.get_activate_script(), *self.start_command],
                cwd=self.project_path,
                stdin=subprocess.PIPE,
                stdout=open(self.project_path + self.stdout_file_path, "a", encoding="utf-8"),
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            if not self.process:
                raise RuntimeError("Failed to start the BashCrawl script.")
            self.logger.info(f"{self.__class__.__name__} started with PID: {str(self.process.pid)}")
            # time.sleep(1)
            # self.logger.debug(f"Empty output at first:{self.read_with_timeout(self.process.stdout)}") #

        def read_output(self):
            # output_lines = []
            # counter = 0
            # while counter < 100:  # Prevent infinite loops
            #     try:
            #         line = self.read_with_timeout()
            #         if line == "EOF":
            #             # End of output
            #             break
            #         if not line:
            #             line = ""
            #         self.logger.debug("Got line: " + line)  # Log to logger
            #         self.stdout_file.write("Got line: " + line + "\n")  # Write to stdout log
            #         self.stdout_file.flush()
            #         output_lines.append(line)
            #         if ">>>" in line or "$ " in line:  # Adjust based on your script's prompt
            #             break
            #     except Exception as e:
            #         self.logger.warning(f"Read output exception: {e}")
            #         break
            #     counter += 1
            # return output_lines # Failed, as readline will get one more line when it is timeout.
            output_lines = []
            time.sleep(0.1)
            with open(self.stdout_file_path, "r", encoding="utf-8") as f:
                # f.seek(0, 2)  # Move to the end of the file
                current_pos = self.stdout_tell

                # Wait for the first output
                counter = 0
                line = None
                while counter <= 100 and not line:
                    f.seek(current_pos)
                    line = f.readline()
                    time.sleep(0.1)
                self.logger.debug("Got line: " + line)  # Log to logger
                output_lines.append(line)
                current_pos = f.tell()

                while True:
                    f.seek(current_pos)  # Ensure we read from the last known position
                    line = f.readline()
                    if line:
                        self.logger.debug("Got line: " + line)  # Log to logger
                        output_lines.append(line)
                        # 检查是否为终止标志
                        if ">>>" in line or "$ " in line:  # 根据实际的脚本提示符调整
                            break
                    else:
                        break
                    current_pos = f.tell()
                self.stdout_tell = f.tell()
                f.close()
            return output_lines

        def poll(self):
            return self.process.poll()

        def send_command(self, command: str) -> str:
            """
            Send a command to the BashCrawl script and capture the output.

            :param command: Command to send to the script.
            :return: Output from the script.
            """

            # Send command
            self.logger.debug(f"Sending command: {command}")
            self.stdout_file.write(f"{datetime.today().isoformat()} Sending command: {command}\n")
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
            sleep(0.1)

            # Read output until the prompt or EOF
            output_lines = self.read_output()
            self.stdout_file.write(f"{datetime.today().isoformat()} Got output:\n")
            self.stdout_file.write("".join(output_lines))

            # Capture errors from stderr
            # stderr_line = self.read_with_timeout(self.process.stderr)
            # if stderr_line and stderr_line != "EOF":
            #     self.logger.error(stderr_line.strip())
            #     self.stderr_file.write(stderr_line)
            #     self.stderr_file.flush()

            return "".join(output_lines)

    BATCH_MANAGER = {
        'None': ConsoleManager,
        'Openpyxl': FileManager,
        'Statsmodels': FileManager,
        'Matplotlib': FileManager,
    }

    def preprocess(self, technical_stack, initiate_command_list, *args, **kwargs):
        os.system("chcp 65001")
        self.logger.info("Preprocessing Batch Project Test.")
        super().preprocess()
        try:
            self.subprocess = BatchJudge.BATCH_MANAGER[technical_stack](project_id=self.project_id, logger=self.logger,
                                                                        *args, **kwargs)
            self.subprocess.initiate_command(initiate_command_list)
            self.subprocess.start()
            self.status = self.subprocess.initial_status

            return True
        except Exception as e:
            self.logger.critical(f"Preprocess exception: {e}")
            return False

    def check(self, test_no, testcode, *args, **kwargs):
        def timeout(process):
            if process:
                process.poll()
            raise TimeoutError("Test execution exceeded the time limit.")

        self.logger.info(f"{test_no} starting.")
        super().check(test_no, testcode, *args, **kwargs)
        try:
            namespace = {"time": time, "pyperclip": pyperclip, "string": string, "pd": pandas,
                         'os': os, 'csv': csv, 'utils': utils, 'datetime': datetime, 'openpyxl': openpyxl,
                         'runpy': runpy, 'threshold': STRING_SIMILARITY_THRESHOLD, '_subprocess': self.subprocess,
                         # 'func_set_timeout': func_set_timeout,
                         }  # TODO Namespace中其它库文件将会是需要处理的问题
            callable_default_package = {name for name in namespace.keys()}
            # testcode = f"@func_set_timeout({TIMEOUT_LIMIT})\n"+testcode
            # testcode = testcode+"\n\ttime.sleep(5)\n"
            exec(testcode, namespace)
            function_name = \
                [name for name, value in namespace.items() if callable(value) and name not in callable_default_package][
                    0]
            test = namespace[function_name]
            try:
                local_path = os.getcwd()
                os.chdir(self.project_root)
                result = func_timeout(TIMEOUT_LIMIT, test, args=args, kwargs=kwargs)
            except AssertionError as e:
                result = e
                self.logger.warning(f"Assertion Error: {str(e)}. Testcase failed.")
            except FunctionTimedOut as e:
                result = "timeout"
                self.logger.warning(f"Timeout Error: {str(e)}")
            except Exception as e:
                result = "runtime error"
                self.logger.warning(f"Testcode Runtime exception: {e}")
            finally:
                os.chdir(local_path)
                # timer.cancel()
            if result is not None:
                # Test code will return nothing unless something goes wrong.
                raise Exception(str(test_no) + ': Wrong answer of ' + str(result))
        except Exception as e:
            self.logger.warning(f"Testcode check exception: {e}")
            if not str(e).strip():
                self.logger.warning(traceback.format_exc())
            return False

        self.logger.info(f"{test_no} passed.")
        return True

    def clean(self):
        self.subprocess.stop()
        self.status = False
