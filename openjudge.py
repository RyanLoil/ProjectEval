import json
import logging
import os
import signal

from multiprocessing import Process

from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime

from llm import LLMTest

DRIVER_DICT = {
    'chrome': 'webdriver.Chrome()',
    'edge': 'webdriver.Edge()',
    'firefox': 'webdriver.Firefox()',
}


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
        handler = logging.FileHandler("log/{0}.log".format(datetime.now().strftime("%Y%m%d-%H%M%S")))
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
            d = os.system("pip install " + ",".join(self.requirements))
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

    def get_parameters(self, model: LLMTest, answer, parameter_request):
        '''
        :param model: LLMTest object,
        :param answer:
        :param parameter_request:
        :return:
        '''
        self.logger.info("Requesting parameters from LLM to adapt question.")
        parameter = model.get_parameter(answer,
                                        parameter_request, )  # In GPTTest, the parameter asking is a full answer list of all pages.
        return json.load(parameter)

    # 为测试准备参数


class WebsiteJudge(BaseJudge):
    def __init__(self, requirements, browser_type, website_initiate_command, website_home="http://localhost:8000/"):
        '''

        :param project_answer_list: A parameter list for all the project that is going to be evaluated
        :param requirements: Packages that is required to evaluate(python only).
        :param browser_type: Choose the type of web browser, support chrome, firefox and edge.
        :param website_initiate_command:
        :param website_home:
        '''
        super().__init__(requirements)

        if browser_type not in ['chrome', 'firefox', 'edge']:
            raise Exception('Not a valid browser type')
        try:
            self.logger.info(f"Webdriver {browser_type} Initializing")
            self.driver = eval(DRIVER_DICT[browser_type])
        except Exception as e:
            self.logger.critical(e)

        self.website_initiate_command = website_initiate_command
        self.website_home = website_home  # Default
        self.website_project_process = self.WebsiteProcess()

    class WebsiteProcess(Process):
        def __init__(self):
            Process.__init__(self)

        def run(self):
            d = os.system(self.website_initiate_command)

        def set_website_initiate_command(self, website_initiate_command):
            self.website_initiate_command = website_initiate_command

        def django_shutdown(self):  # TODO 不够优雅，还是通过subprocess来关闭会更好
            result = os.popen('netstat -ano|findstr "8000" ').read().split("\n")  # TODO Django默认8000
            for i in range(len(result)):
                result[i] = result[i].split()
                if len(result[i]) == 5 and result[i][3] == "LISTENING":
                    os.popen("taskkill -pid %s -f" % result[i][4])
                    break

    def preprocess(self):
        self.logger.info("Preprocessing Website Project Test.")
        super().preprocess()
        try:
            os.system("chcp 65001")
            self.website_project_process.set_website_initiate_command(self.website_initiate_command)
            self.website_project_process.start()
            self.website_project_process.join(timeout=1)
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
        self.website_project_process.django_shutdown()
        self.website_project_process.terminate()
        self.website_project_process.join()
        self.website_project_process.close()
        self.driver.close()

    def check(self, test_no, testcode, *args, **kwargs):
        self.logger.info(f"{test_no} starting.")
        super().check(test_no, testcode, *args, **kwargs)
        try:
            namespace = {}
            exec(testcode, namespace)
            function_name = [name for name, value in namespace.items() if callable(value)][0]
            test = namespace[function_name]
            result = test(self.driver, *args, **kwargs)
            if result is not None:
                # Test code will return nothing unless something goes wrong.
                raise Exception(str(test_no) + ': Wrong Answer of ' + str(result))
        except Exception as e:
            self.logger.warning(e)
            return False
        self.logger.info(f"{test_no} passed.")
        return True


class SoftwareJudge(BaseJudge):
    pass


class BatchJudge(BaseJudge):
    pass
