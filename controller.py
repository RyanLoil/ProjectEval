import copy
import json
import logging
import os
import shutil
import traceback
from datetime import datetime

from llm import GPTTest, LLMTest
from openjudge import WebsiteJudge, BaseJudge
from config import DEFAULT_BROWSER_TYPE

PROJECT_TYPE = {
    'website': WebsiteJudge,
    'software': "",
    'batch': "",
}


class LLMController:
    def __init__(self, question_path: str, model_class: LLMTest, language: dict = None, technical_stack: dict = None,
                 output_path: str = "data/", crush_save_path: str = "data/crash_save/", crush_load_path: str = None):
        '''
        A Example to show how to use LLM answer the question of Project Eval.
        :param question_path: The source data
        :param model_class: The LLM model that you want to use. Check LLMTest in llm.py as a template example.
        :param output_path: The answer from LLM.
        :param language:Restrict format with {"website": "python", "software": "c++", "batch": "basic"}.
        :param technical_stack: Restrict format with {"website": "django", "software": "pygame", "batch": "any"}
        :param crush_save_path: The path to save the dump of answer dict
        :param crush_load_path: if this parameter is NOT None, LLMController will load the give file to continue the task
        '''

        self.logger = logging.getLogger('LLMController')
        self.logger.setLevel(level=logging.DEBUG)
        self.initiate_time = datetime.now().strftime("%Y%m%d-%H%M%S")
        if not self.logger.handlers:
            handler = logging.FileHandler("log/{0}-LLMController.log".format(self.initiate_time))
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            console.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.addHandler(console)
        self.crash_save = crush_save_path + "/{0}-AnswerCrashSave.py".format(self.initiate_time)
        self.crash_load = crush_load_path

        try:
            self.question_list = json.load(open(question_path, 'r', encoding='utf-8'))
        except Exception as e:
            self.logger.critical("Loading question list failed with error {}".format(e))
            raise Exception("Loading question list failed with error {}".format(e))
        self.question = []
        for q in self.question_list:
            temp = copy.deepcopy(q)
            del temp['testcode']
            self.question.append(temp)
        self.model = model_class()
        self.output_path = output_path
        self.language = language
        self.technical_stack = technical_stack

    def run(self, level: int):
        """

        :param level: 1 for natural language description, 2 for natural language checklist, 3 for programming language framework
        :return: A file which is saved in the given directory
        """
        crash_mark = False
        if self.crash_load:
            with open(self.crash_load, "r", encoding="utf-8") as input_file:
                self.logger.info("Loading given crash saved.")
                answer_dict = eval(input_file.read())
                crash_mark = True
                crash_project_id = answer_dict['error_project_id']
                del answer_dict['error_project_id']
            input_file.close()
        else:
            answer_dict = {}
        try:
            for q in self.question:
                if crash_mark:
                    if crash_project_id != q['project_id']:
                        continue
                    else:
                        crash_mark = False
                self.logger.info("Answer question {}.".format(q['project_id']))
                language = self.language[q['project_type']] if self.language else q['framework_technical_stack'][
                    'language']
                technical_stack = self.technical_stack[q['project_type']] if self.technical_stack else \
                    q['framework_technical_stack']['technical_stack']
                if level == 1:
                    # Level 1 uses nl_prompt
                    nl_checklist = self.model.generate_checklist(q['nl_prompt'])
                    framework = self.model.generate_framework(language, technical_stack, nl_checklist)
                elif level == 2:
                    # Level 2 uses nl_checklist
                    nl_checklist = q['nl_checklist']
                    framework = self.model.generate_framework(language, technical_stack, nl_checklist)
                elif level == 3:
                    # Level 3 directly uses framework
                    framework = q['framework']
                else:
                    self.logger.critical("Invalid level number.")
                    raise Exception("Invalid level number.")
                answer = self.model.generate_answer(framework, technical_stack)
                try:
                    if not isinstance(answer, list):  # In the example, LLM will return a python list as answer.
                        raise Exception("Invalid answer format in project {}.".format(q["project_id"]))
                    # answer['project_id'] = q['project_id']
                except Exception as e:
                    self.logger.warning(str(e))
                    continue
                # answer['framework_technical_stack'] = {'language': language, 'technical_stack': technical_stack}
                answer_dict[q['project_id']] = answer
            output_file_path = self.output_path + self.model.llm + "_" + datetime.now().strftime(
                "%Y%m%d-%H%M%S") + ".json"
            with open(output_file_path, "w", encoding="utf-8") as output_file:
                self.logger.info("Writing to " + output_file_path)
                json.dump(answer_dict, output_file)
        except Exception as e:
            print(traceback.format_exc())
            answer_dict["error_project_id"] = q['project_id']
            with open(self.crash_save, "w", encoding="utf-8") as output_file:
                output_file.write(str(answer_dict))
            output_file.close()


class JudgeController:
    def __init__(self, question_path: str, answer_path: str, model_class: LLMTest,
                 parameter_file_path: str = None, parameter_answer_save: str = "data/parameter_answer_save"):

        self.logger = logging.getLogger('JudgeController')
        self.logger.setLevel(level=logging.DEBUG)
        self.initiate_time = datetime.now().strftime("%Y%m%d-%H%M%S")
        if not self.logger.handlers:
            handler = logging.FileHandler("log/{0}-JudgeController.log".format(self.initiate_time))
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            console.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.addHandler(console)
        self.parameter_answer_save = parameter_answer_save
        self.parameter_file_path = parameter_file_path

        try:
            question_list = json.load(open(question_path, 'r', encoding='utf-8'))
            self.question_dict = {q['project_id']: q for q in question_list}
        except Exception as e:
            self.logger.critical("Loading question list failed with error {}".format(e))
            raise Exception("Loading question list failed with error {}".format(e))
        self.testcode = {}
        self.requested_parameter = {}
        for t in question_list:
            temp = copy.deepcopy(t)
            self.testcode[temp['project_id']] = temp['testcode']  # Save the testcode for each project
            temp_2 = copy.deepcopy(t)
            self.requested_parameter[temp['project_id']] = temp_2['testcode']
            for page in self.requested_parameter[temp['project_id']]:
                for function in page['function']:
                    del function['test']
        # testcode = {<pid>:[<testcode list>]
        del question_list
        try:
            self.answer_dict = json.load(open(answer_path, 'r', encoding='utf-8'))
        except Exception as e:
            self.logger.critical("Loading answer list failed with error {}".format(e))
            raise Exception("Loading answer list failed with error {}".format(e))

        self.model = model_class()
        # question_list = {<pid>:{<page>:{<function>:{'function':<function name>, 'parameter':{'name':<parameter name>, 'description': <parameter discription>}, ...}, ...}, ...}
        # in batch project, there is only one page.

    def preprocess(self):
        # For getting parameter and classifying different type of project.
        self.logger.info("Preprocessing.")
        for pid in self.testcode:
            self.question_dict[pid] = {}
            for page in self.testcode[pid]:
                self.question_dict[pid][page['page']] = {}
                for function in page["function"]:
                    temp = copy.deepcopy(function)
                    del temp['test']
                    self.question_dict[pid][page['page']][function['function']] = temp

    # def run(self):
    #     for k in self.project_answer_list:
    #         judge = PROJECT_TYPE[k](self.question_list[k], requirements=["django", ],
    #                                 browser_type="edge", website_initiate_command=None,
    #                                 generation_list_path="data/generation_test.json")
    #         judge.evaluate()
    #
    #         self.logger.info("Evaluating question {}.".format(t['project_id']))
    #         self.logger.debug("Evaluating question {} page {}.".format(t['project_id'], page['page']))

    def write_answer_to_file(self, project_id):
        base_dir = "test/" + datetime.now().strftime("%Y%m%d") + "/" + str(project_id) + "/"

        # Remove the directory if it already exists
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)

        # Create the base directory
        os.makedirs(base_dir)

        # Iterate over files in answer_dict
        for file in self.answer_dict[str(project_id)]:
            # Check if 'file' is None, and create an empty directory if so
            if file['file'] is None:
                empty_dir_path = base_dir + file['path'].replace("./", "")
                os.makedirs(empty_dir_path, exist_ok=True)
                continue

            # Process and write the file
            file_name = base_dir + file['path'].replace("./", "")
            content = file['code']
            last_slash = file_name.rfind("/")

            # Create the directory if it doesn't exist
            if last_slash != -1:
                dirpath = file_name[:last_slash]
                if not os.path.isdir(dirpath):
                    os.makedirs(dirpath)

            # Write the content to the file
            with open(file_name, 'w', encoding="utf-8") as f:
                f.write(content)

        # Handle directory structure if there is only one subdirectory
        if len(os.listdir(base_dir)) == 1:
            base_dir = base_dir + os.listdir(base_dir)[0] + "/"

        return base_dir

    def evaluate(self, initiate_command: dict = None, requirements: dict = None, technical_stack: dict = None,
                 ):
        '''
        :param initiate_command:
        :param requirements:
        :param parameter_file_path:
        :param technical_stack:

        :return:
        '''
        total_status = {'total': 0, 'pass': 0, 'failed': 0, 'score': 0}
        auto_parameter_save_dict = {}
        if self.parameter_file_path:
            # 预加载已生成的parameter
            try:
                parameter_file = open(self.parameter_file_path, 'r', encoding="utf-8")
            except Exception as e:
                self.logger.critical("Loading parameter match failed with error {}".format(e))
                raise Exception("Loading parameter match failed with error {}".format(e))
            exist_parameters = json.load(parameter_file)
        else:
            exist_parameters = None

        for project_id in self.question_dict:
            self.logger.info("Evaluating project id {}".format(project_id))
            project = self.question_dict[project_id]
            # File Writter
            project_root = self.write_answer_to_file(project_id)
            '''
            #TODO 列表
            1.	需要适配参数复用，即参数选择也存在标准答案，此处对应产品经理制作用户手册 √
            2.	Django初始命令的使用，可以使用默认的，也可以使用复用的
            3.	初始命令和requirements的询问也需要做保存
            '''
            if project['project_type'] == 'website':
                # TODO 适配新类预加载
                # Runner
                if initiate_command and project_id in initiate_command:
                    project_initiate_command: [[]] = initiate_command[project_id]
                else:
                    project_initiate_command = None
                if requirements and project_id in requirements:
                    project_requirements = requirements[project_id]
                else:
                    project_requirements = None
                if not project_requirements or not project_initiate_command:
                    # TODO 适配新版本的Judge
                    # Request LLM for requirements and initiate command.
                    competition = self.model.get_information(self.answer_dict[project_id],
                                                             self.question_dict[project_id][
                                                                 "framework_technical_stack"][0][
                                                                 "technical_stack"] if not technical_stack else
                                                             technical_stack[project_id],
                                                             project_root)
                    project_initiate_command: [[]] = competition[
                        "initiate_commands"] if not project_initiate_command else project_initiate_command
                    project_requirements = competition[
                        "requirements"] if not project_requirements else project_requirements

                judge: BaseJudge = PROJECT_TYPE[project['project_type']](project_requirements, DEFAULT_BROWSER_TYPE,
                                                                         project_initiate_command,
                                                                         website_home="http://localhost:8000/")

                # TODO 增加模拟数据载入，这个问题挺棘手的，因为严格意义上它不属于Project的一部分，属于测试工程师的工作，但是我们不能保证所有的框架都有自动化测试，因此可能需要要求LLM提前撰写模拟数据的导入脚本来完成此工作，这似乎是二次询问。

                try:
                    if not judge.preprocess(technical_stack[project_id]["website"] if technical_stack else
                                            self.question_dict[project_id]["framework_technical_stack"][0][
                                                "technical_stack"], initiate_command_list=project_initiate_command,
                                            project_path=project_root):
                        self.logger.info("{} scored 0.".format(project_id))
                        continue
                except Exception as e:
                    self.logger.warning("Preprocessing failed with {}".format(str(e)))
                    self.logger.info("{} scored 0.".format(project_id))
                    continue
            elif project['project_type'] == 'software':
                # TODO software适配
                pass
            else:
                # TODO batch适配
                pass
            try:
                if exist_parameters and project_id in exist_parameters:
                    # 历史Parameter清单复用
                    parameters = exist_parameters[project_id]

                else:
                    # 清单Parameter制作
                    parameter_list = judge.get_parameters(model=self.model, answer=self.answer_dict[project_id],
                                                          technical_stack=
                                                          self.question_dict[project_id]["framework_technical_stack"][
                                                              0][
                                                              "technical_stack"] if not technical_stack else
                                                          technical_stack[project_id],
                                                          parameter_request=self.requested_parameter[project_id])
                    # parameter = [{"page":"XXX", "function":"[{"function":"XXX", "parameter": [{"name":"XXX", "answer": "your_answer"}, {...}, ...]},...],...]
                    parameters = {}
                    for page in parameter_list:
                        parameters[page['page']] = {}
                        for function in page["function"]:
                            # temp = {p['name']: p['answer'] for p in function['parameter']}
                            parameters[page['page']][function['function']] = function["parameter"]
                    auto_parameter_save_dict[project_id] = parameters
                    if type(self.parameter_answer_save) == str:
                        self.parameter_answer_save = open(self.parameter_answer_save
                                                          + "/{0}-ParameterAnswerSave.json".format(self.initiate_time),
                                                          "w", encoding="utf-8")
                    self.parameter_answer_save.seek(0)
                    self.parameter_answer_save.truncate(0)
                    self.parameter_answer_save.write(json.dumps(auto_parameter_save_dict))
                    del parameter_list

            except Exception as e:
                self.logger.info(f"Get parameters for project id {project_id} failed with exception {e}.")
                self.logger.info("{} scored 0.".format(project_id))
                judge.clean()
                continue
            pass_count = 0
            n = 0
            index = 0
            for page in self.testcode[project_id]:
                n += len(page['function'])
                total_status['total'] += len(page['function'])
                for function in page['function']:
                    index += 1
                    self.logger.info("Evaluating function {}".format(
                        str(project_id) + "_" + str(index) + " " + function['function']))
                    try:
                        kwargs = {}
                        for parameter in parameters[page['page']][function['function']]:
                            kwargs[parameter['name']] = parameter['answer']

                    except Exception as e:
                        self.logger.info(
                            "Parameter(s) finding was failed in the project_answer_list. Exception {}".format(e))
                        continue
                    if judge.check(str(project_id) + "_" + str(index), function['test'], **kwargs):
                        pass_count += 1
                        self.logger.info("Function {} passed.".format(str(project_id) + "_" + str(index)))
                    else:
                        self.logger.info("Function {} failed.".format(str(project_id) + "_" + str(index)))
            project_score = (pass_count+1) / (n+1) # 1 for runable
            total_status['total'] += 1
            total_status['score'] += project_score
            total_status['pass'] += (pass_count + 1)
            total_status['failed'] += (n - pass_count)
            self.logger.info(f"Project id {project_id} scored {project_score}")
            judge.clean()
        self.logger.info("Finished. Report: {}".format(total_status))
        return total_status, total_status['pass'] / total_status['total']
