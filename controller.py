import copy
import json
import logging
import os
import shutil
import time
import traceback
from datetime import datetime

from llm import GPTTest, LLMTest
from openjudge import WebsiteJudge, BatchJudge, BaseJudge
from config import DEFAULT_BROWSER_TYPE, IO_WAIT, PROJECT_EVAL_DEFAULT_TEST_CASE, LOG_PATH, \
    PROJECT_EVAL_DEFAULT_TEST_DIR, PROJECT_EVAL_DEFAULT_EXPERIMENT_DIR, RUN_DATE


# from indicator import sentence_transformer_calc, codebleu_calc, levenshtein_calc

def sentence_transformer_calc(*args, **kwargs):
    from indicator import sentence_transformer_calc
    return sentence_transformer_calc(*args, **kwargs)

def codebleu_calc(*args, **kwargs):
    from indicator import codebleu_calc
    return codebleu_calc(*args, **kwargs)

def levenshtein_calc(*args, **kwargs):
    from indicator import levenshtein_calc
    return levenshtein_calc(*args, **kwargs)

PROJECT_TYPE = {
    'website': WebsiteJudge,
    'software': "",
    'batch': BatchJudge,
    'console': BatchJudge,
}


class BaseController:
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(level=logging.DEBUG)
        self.initiate_time = datetime.now().strftime("%Y%m%d-%H%M%S")
        if not self.logger.handlers:
            os.makedirs(os.path.dirname(f"{LOG_PATH}/{RUN_DATE}/"), exist_ok=True)
            handler = logging.FileHandler(f"{LOG_PATH}/{RUN_DATE}/{self.initiate_time}-{self.__class__.__name__}.log",
                                          encoding="utf-8")
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            console.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.addHandler(console)


class LLMController(BaseController):
    def __init__(self, question_path: str, model_class: type(LLMTest), llm: str, language: dict = None,
                 technical_stack: dict = None,
                 device: str = "",
                 output_path: str = "data/", crush_save_path: str = "data/crash_save/", crush_load_path: str = None,
                 parameter_generate: bool = False,
                 information_generate: bool = False,
                 start_file_generate: bool = False,
                 ):
        '''
        Controller to use LLM answering the question of Project Eval.
        :param question_path: The source data
        :param model_class: The LLM model that you want to use. Check LLMTest in llm.py as a template example.
        :param output_path: The answer from LLM.
        :param language:Restrict format with {"website": "python", "software": "c++", "batch": "basic"}.
        :param technical_stack: Restrict format with {"website": "django", "software": "pygame", "batch": "any"}
        :param crush_save_path: The path to save the dump of answer dict
        :param crush_load_path: if this parameter is NOT None, LLMController will load the give file to continue the task
        '''
        super().__init__()

        self.crash_save = crush_save_path + "/{0}-AnswerCrashSave.py".format(self.initiate_time)
        self.crash_load = crush_load_path

        try:
            question_list = json.load(open(question_path, 'r', encoding='utf-8'))
        except Exception as e:
            self.logger.critical("Loading question list failed with error {}".format(e))
            raise Exception("Loading question list failed with error {}".format(e))
        self.question = []
        self.requested_parameter, self.testcode = JudgeController.requested_parameter_and_testcode(question_list)
        del self.testcode
        for q in question_list:
            temp = copy.deepcopy(q)
            del temp['testcode']
            self.question.append(temp)
        self.model = model_class(llm=llm, device=device)
        self.output_path = output_path
        self.language = language
        self.technical_stack = technical_stack
        self.parameter_generate = parameter_generate
        self.information_generate = information_generate
        self.start_file_generate = start_file_generate
        if self.parameter_generate:
            self.project = json.load(open(question_path, 'r', encoding='utf-8'))

    LEVEL_DICT = {
        1: "nl_prompt",
        2: "nl_checklist",
        3: "skeleton",
    }

    def _dump_file(self, data, output_file_path):
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            self.logger.info("Writing to " + output_file_path)
            json.dump(data, output_file)

    def run(self, level: int, cascade: bool = False):
        """
        Execute the test.
        :param level: 1 for natural language description, 2 for natural language checklist, 3 for programming language skeleton
        :param cascade: Generated answer level by level. True for cascade, False for no cascade
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
        nl_checklist_dict = {}
        skeleton_dict = {}
        parameter_dict = {}
        information_dict = {}
        start_file_dict = {}
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        try:
            for q in self.question:
                project_id = q['project_id']
                if crash_mark:
                    if crash_project_id != project_id:
                        continue
                    else:
                        crash_mark = False
                self.logger.info("Answer question {}.".format(project_id))
                language = self.language[q['project_type']] if self.language else q['framework_technical_stack'][
                    'language']
                technical_stack = self.technical_stack[q['project_type']] if self.technical_stack else \
                    q['framework_technical_stack'][0]['technical_stack']
                if cascade:
                    if level == 1:
                        # Level 1 uses nl_prompt
                        nl_checklist = self.model.generate_checklist(q['nl_prompt'])
                        nl_checklist_dict[project_id] = nl_checklist
                        skeleton = self.model.generate_skeleton(language, technical_stack, nl_checklist)
                        skeleton_dict[project_id] = skeleton
                    elif level == 2:
                        # Level 2 uses nl_checklist
                        nl_checklist = q['nl_checklist']
                        skeleton = self.model.generate_skeleton(language, technical_stack, nl_checklist)
                        skeleton_dict[project_id] = skeleton
                    elif level == 3:
                        # Level 3 directly uses skeleton
                        skeleton = q['skeleton']
                    else:
                        self.logger.critical("Invalid level number.")
                        raise Exception("Invalid level number.")
                    final_prompt = skeleton

                    if level == 1:
                        output_file_path = f"{self.output_path}{self.model.llm}_{timestamp}_level_{level}_nl_checklist.json".replace(":","-")
                        self._dump_file(nl_checklist_dict, output_file_path)
                    if level <= 2:
                        output_file_path = f"{self.output_path}{self.model.llm}_{timestamp}_level_{level}_skeleton.json".replace(":","-")
                        self._dump_file(skeleton_dict, output_file_path)

                else:
                    final_prompt = q[self.LEVEL_DICT[level]]
                answer = self.model.generate_answer(final_prompt, technical_stack)

                try:
                    if not isinstance(answer, list):  # In the example, LLM will return a python list as answer.
                        raise Exception("Invalid answer format in project {}.".format(q["project_id"]))
                    # answer['project_id'] = project_id
                except Exception as e:
                    self.logger.warning(str(e))
                    continue
                # answer['framework_technical_stack'] = {'language': language, 'technical_stack': technical_stack}

                answer_dict[project_id] = answer
                output_file_path = f"{self.output_path}{self.model.llm}_{timestamp}_level_{level}.json".replace(":","-")
                self._dump_file(answer_dict, output_file_path)

                if self.parameter_generate:
                    parameter = self.model.get_parameter(answer, technical_stack, self.requested_parameter[project_id])
                    parameter_dict[project_id] = parameter
                    output_file_path = f"{self.output_path}{self.model.llm}_{timestamp}_level_{level}_parameter.json".replace(":","-")
                    self._dump_file(parameter_dict, output_file_path)

                project_root = PROJECT_EVAL_DEFAULT_TEST_DIR + str(project_id) + "/"
                if self.information_generate:
                    information = self.model.get_information(answer, technical_stack, project_root)
                    information_dict[project_id] = information
                    output_file_path = f"{self.output_path}{self.model.llm}_{timestamp}_level_{level}_information.json".replace(":","-")
                    self._dump_file(information_dict, output_file_path)

                if self.start_file_generate:
                    start_file = self.model.get_start_file(answer, technical_stack, project_root)
                    start_file_dict[project_id] = start_file
                    output_file_path = f"{self.output_path}{self.model.llm}_{timestamp}_level_{level}_startfile.json".replace(":","-")
                    self._dump_file(start_file_dict, output_file_path)


        except Exception as e:
            print(traceback.format_exc())
            answer_dict["error_project_id"] = project_id
            with open(self.crash_save, "w", encoding="utf-8") as output_file:
                output_file.write(str(answer_dict))
            output_file.close()


class MaskerController(BaseController):
    def __init__(self, answer_path: str, model_class: type(LLMTest), output_path: str, llm: str, device: str = ""):
        super(MaskerController, self).__init__()
        try:
            self.answer_dict = json.load(open(answer_path, 'r', encoding='utf-8'))
        except Exception as e:
            self.logger.critical("Loading answer list failed with error {}".format(e))
            raise Exception("Loading answer list failed with error {}".format(e))
        self.model = model_class(llm=llm, device=device)
        self.output_path = output_path
        self.skeleton = {}

    def run(self):
        try:
            for project_id in self.answer_dict:
                skeleton = self.model.mask_skeleton(self.answer_dict[project_id])
                self.skeleton[project_id] = skeleton
            output_file_path = self.output_path + "skeleton" + self.model.llm + "_" + datetime.now().strftime(
                "%Y%m%d-%H%M%S") + ".json"
            with open(output_file_path, "w", encoding="utf-8") as output_file:
                self.logger.info("Writing to " + output_file_path)
                json.dump(self.skeleton, output_file)
        except Exception as e:
            self.logger.critical(str(e))


class JudgeController(BaseController):
    @staticmethod
    def requested_parameter_and_testcode(question_list):
        requested_parameter = {}
        testcode = {}
        for t in question_list:
            temp = copy.deepcopy(t)
            testcode[temp['project_id']] = temp['testcode']  # Save the testcode for each project
            temp_2 = copy.deepcopy(t)
            requested_parameter[temp['project_id']] = temp_2['testcode']
            for page in requested_parameter[temp['project_id']]:
                for function in page['function']:
                    del function['test']
        return requested_parameter, testcode

    def __init__(self, question_path: str, answer_path: str, model_class: type(LLMTest),
                 parameter_file_path: str = None, parameter_answer_save: str = "data/parameter_answer_save",
                 llm: str = None, device: str = None):
        '''
        :param question_path: the question path.
        :param answer_path:
        :param model_class:
        :param parameter_file_path:
        :param parameter_answer_save:
        '''
        super().__init__()
        self.parameter_answer_save = parameter_answer_save
        self.parameter_file_path = parameter_file_path

        try:
            question_list = json.load(open(question_path, 'r', encoding='utf-8'))
            self.question_dict = {q['project_id']: q for q in question_list}
        except Exception as e:
            self.logger.critical("Loading question list failed with error {}".format(e))
            raise Exception("Loading question list failed with error {}".format(e))
        self.requested_parameter, self.testcode = self.requested_parameter_and_testcode(question_list)

        # testcode = {<pid>:[<testcode list>]
        del question_list
        try:
            self.answer_dict = json.load(open(answer_path, 'r', encoding='utf-8'))
        except Exception as e:
            self.logger.critical("Loading answer list failed with error {}".format(e))
            raise Exception("Loading answer list failed with error {}".format(e))

        self.model = model_class(llm=llm, device=device)
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
        base_dir = PROJECT_EVAL_DEFAULT_TEST_DIR + str(project_id) + "/"
        try:
            # Remove the directory if it already exists
            if os.path.exists(base_dir):
                shutil.rmtree(base_dir)

            # Create the base directory
            os.makedirs(base_dir)
            while not os.path.exists(base_dir):
                # prevent IO problem
                continue

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
            if len(os.listdir(base_dir)) == 1 and len(os.listdir(base_dir)[0].split(".")) == 1:
                base_dir = base_dir + os.listdir(base_dir)[0] + "/"
            time.sleep(IO_WAIT)
            return base_dir
        except Exception as e:
            self.logger.critical("Writing answer files failed with error {}".format(e))
            return base_dir

    def evaluate(self, initiate_command: dict = None, requirements: dict = None, technical_stack: dict = None,
                 project_id_list: list = None, start_file_list: dict = None,
                 ):
        '''
        :param initiate_command:
        :param requirements:
        :param technical_stack:
        :param project_id_list:
        :param start_file_list:
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
        project_score_table = []
        for project_id in self.question_dict if project_id_list is None else project_id_list:
            project_score_table_row = {
                "project_id": project_id,
                "pass": 0,
                "testcase": len(self.testcode[project_id])
            }
            project_score_table.append(project_score_table_row)
            try:
                self.logger.info("Evaluating project id {}".format(project_id))
                project = self.question_dict[project_id]
                if project_id not in self.answer_dict:
                    self.logger.warning("Project id {} does not exist, skip. Score 0.".format(project_id))
                    continue
                # File Writer
                project_root = self.write_answer_to_file(project_id)
                '''
                #TODO
                1.	Initial command and requirements' query also need to be saved.
                '''
                # Runner
                if initiate_command and project_id in initiate_command:
                    project_initiate_command: [[]] = initiate_command[project_id]
                else:
                    project_initiate_command = None
                if requirements and project_id in requirements:
                    project_requirements = requirements[project_id]
                else:
                    project_requirements = None
                if project['project_type'] == 'website':
                    if not project_requirements or not project_initiate_command:
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
                    # Judge Initial
                    judge: BaseJudge = PROJECT_TYPE[project['project_type']](project_id, project_requirements,
                                                                             DEFAULT_BROWSER_TYPE,
                                                                             project_initiate_command,
                                                                             website_home="http://localhost:8000/")

                    try:
                        preprocess_result = judge.preprocess(technical_stack[project_id]["website"] if technical_stack else
                                                             self.question_dict[project_id]["framework_technical_stack"][0][
                                                                 "technical_stack"],
                                                             initiate_command_list=project_initiate_command,
                                                             project_path=project_root)
                        if not preprocess_result:
                            self.logger.warning(f"Preprocessing failed with {preprocess_result}.")
                            self.logger.info("{} scored 0.".format(project_id))
                            continue
                    except Exception as e:
                        self.logger.warning(f"Preprocessing failed with {str(e)}")
                        self.logger.info("{} scored 0.".format(project_id))
                        continue
                elif project['project_type'] == 'software':
                    # TODO software
                    pass
                else:
                    # Batch or Console
                    if not start_file_list or project_id not in start_file_list:
                        start_file = self.model.get_start_file(self.answer_dict[project_id],
                                                               self.question_dict[project_id][
                                                                   "framework_technical_stack"][0][
                                                                   "technical_stack"] if not technical_stack else
                                                               technical_stack[project_id],
                                                               project_root)
                    else:
                        start_file = start_file_list[project_id]

                    judge: BaseJudge = PROJECT_TYPE[project['project_type']](project_id, project_requirements,
                                                                             project_root, )
                    try:
                        preprocess_result = judge.preprocess(technical_stack[project_id]["batch"] if technical_stack else
                                                             self.question_dict[project_id]["framework_technical_stack"][0][
                                                                 "technical_stack"],
                                                             initiate_command_list=project_initiate_command,
                                                             project_path=project_root, start_file=start_file)
                        if not preprocess_result:
                            self.logger.warning(f"Preprocessing failed with {preprocess_result}.")
                            self.logger.info("{} scored 0.".format(project_id))
                            continue
                    except Exception as e:
                        self.logger.warning(f"Preprocessing failed with {str(e)}")
                        self.logger.info("{} scored 0.".format(project_id))
                        continue
                try:
                    if exist_parameters and project_id in exist_parameters:
                        # Reuse parameters
                        parameter_list = exist_parameters[project_id]

                    else:
                        # Get parameters
                        parameter_list = judge.get_parameters(model=self.model, answer=self.answer_dict[project_id],
                                                              technical_stack=
                                                              self.question_dict[project_id]["framework_technical_stack"][
                                                                  0][
                                                                  "technical_stack"] if not technical_stack else
                                                              technical_stack[project_id],
                                                              parameter_request=self.requested_parameter[project_id])
                        # parameter = [{"page":"XXX", "function":"[{"function":"XXX", "parameter": [{"name":"XXX", "answer": "your_answer"}, {...}, ...]},...],...]

                        auto_parameter_save_dict[project_id] =  parameter_list
                        if type(self.parameter_answer_save) == str:
                            self.parameter_answer_save = open(self.parameter_answer_save
                                                              + "/{0}-ParameterAnswerSave.json".format(self.initiate_time),
                                                              "w", encoding="utf-8")
                        self.parameter_answer_save.seek(0)
                        self.parameter_answer_save.truncate(0)
                        self.parameter_answer_save.write(json.dumps(auto_parameter_save_dict))


                except Exception as e:
                    self.logger.warning(f"Get parameters for project id {project_id} failed with exception {e}.")
                    self.logger.info("{} scored 0.".format(project_id))
                    judge.clean()
                    continue

                try:
                    if type(parameter_list) == list:
                        parameters = {}
                        for page in parameter_list:
                            parameters[page['page']] = {}
                            for function in page["function"]:
                                # temp = {p['name']: p['answer'] for p in function['parameter']}
                                parameters[page['page']][function['function']] = function["parameter"]
                        del parameter_list
                    else:
                        parameters = parameter_list
                except Exception as e:
                    self.logger.warning(f"Get parameters for project id {project_id} failed with exception {e}.")
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
                        try:
                            if judge.check(str(project_id) + "_" + str(index), function['test'], **kwargs):
                                pass_count += 1
                                self.logger.info("Function {} passed.".format(str(project_id) + "_" + str(index)))
                            else:
                                self.logger.info("Function {} failed.".format(str(project_id) + "_" + str(index)))
                        except Exception as e:
                            self.logger.info("Function {} failed.".format(str(project_id) + "_" + str(index)) + "Error: {}".format(e))
                project_score = (pass_count + 1) / (n + 1)  # 1 for runable
                project_score_table_row["pass"] = pass_count + 1
                total_status['total'] += 1
                total_status['score'] += project_score
                total_status['pass'] += (pass_count + 1)
                total_status['failed'] += (n - pass_count)
                self.logger.info(f"Project id {project_id} scored {project_score}")
                judge.clean()
            except Exception as e:
                self.logger.critical(f"Error:{e} | Traceback:{traceback.format_exc()}")
            if judge.status:
                judge.clean()
        total_status['testcase'] = total_status['total']
        total_status['total'] = PROJECT_EVAL_DEFAULT_TEST_CASE
        if len(project_id_list) == 20:
            # ProjectEval Standard
            total_status['pass@1'] = total_status['pass'] / PROJECT_EVAL_DEFAULT_TEST_CASE
        self.logger.info("Finished. Report: {}".format(total_status))
        return total_status, project_score_table #, total_status['pass'] / (total_status['total'] if total_status['total'] > 0 else 1)


class IndicatorController(BaseController):
    """
    This controller is for all 4 objective indicators.
    """

    def __init__(self,verbose_name, answer_checklist_path: str, answer_skeleton_path: str, answer_code_path: str,
                 answer_parameter_path: str,
                 reference_project_path: str, reference_code_path: str, reference_parameter_path: str,
                 report_file_path: str = None                 ):
        super().__init__()
        self.answer_checklist = json.load(
            open(answer_checklist_path, "r", encoding="utf-8")) if answer_checklist_path else None
        self.answer_skeleton = json.load(
            open(answer_skeleton_path, "r", encoding="utf-8")) if answer_skeleton_path else None

        self.answer_code = json.load(open(answer_code_path, "r", encoding="utf-8")) if answer_code_path else None
        self.answer_parameter = json.load(
            open(answer_parameter_path, "r", encoding="utf-8")) if answer_parameter_path else None

        self.reference_project = json.load(open(reference_project_path, "r", encoding="utf-8"))
        self.reference_code = json.load(open(reference_code_path, "r", encoding="utf-8"))
        self.reference_parameter = json.load(open(reference_parameter_path, "r", encoding="utf-8"))
        self._test_data = {
            "checklist": {},
            "skeleton": {},
            "code": {},
            "parameter": {},
        }
        self._reference_data = {
            "checklist": {},
            "skeleton": {},
            "code": {},
            "parameter": self.reference_parameter,
        }
        self.verbose_name = verbose_name
        self.standard_checklist_and_skeleton_processing()
        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        if not report_file_path:
            report_file_path = PROJECT_EVAL_DEFAULT_EXPERIMENT_DIR + f"/{verbose_name}-{self.timestamp}-objective_indicators_reports.txt"
        self.report_file = open(report_file_path, "w", encoding="utf-8")

    def standard_checklist_and_skeleton_processing(self):
        try:
            for project in self.reference_project:
                self._reference_data["checklist"][project["project_id"]] = []
                for page in project["nl_checklist"]:
                    for function in page["function"]:
                        self._reference_data["checklist"][project["project_id"]].append(
                            page["page"] + "||" + function["function"] + "||" + function["description"])

                self._reference_data["skeleton"][project["project_id"]] = []
                for file in project["skeleton"]:
                    self._reference_data["skeleton"][project["project_id"]].append(file['code'])

                self._reference_data["code"][project["project_id"]] = []
                for file in self.reference_code[project["project_id"]]:
                    self._reference_data["code"][project["project_id"]].append(file['code'])

            if self.answer_checklist:
                for checklist in self.answer_checklist:
                    self._test_data["checklist"][checklist] = []
                    for page in self.answer_checklist[checklist]:
                        try:
                            for function in page["function"]:
                                self._test_data["checklist"][checklist].append(
                                    page["page"] + "||" + function["function"] + "||" + function["description"])
                        except Exception as e:
                            self.logger.warning(f"Failed to load function list of project:{checklist} with file {page} on error {e}")

            if self.answer_skeleton:
                for skeleton in self.answer_skeleton:
                    self._test_data["skeleton"][skeleton] = []
                    for file in self.answer_skeleton[skeleton]:
                        try:
                            self._test_data["skeleton"][skeleton].append(file['code'])
                        except Exception as e:
                            self.logger.warning(f"Failed to load skeleton list of project:{skeleton} with file {file} on error {e}")

            if self.answer_code:
                for code in self.answer_code:
                    self._test_data["code"][code] = []
                    for file in self.answer_code[code]:
                        try:
                            self._test_data["code"][code].append(file['code'])
                        except Exception as e:
                            self.logger.warning(f"Failed to load code list of project:{code} with file {file} on error {e}")


            for project_id in self.answer_parameter:
                self._test_data["parameter"][project_id] = {}
                for page in self.answer_parameter[project_id]:
                    try:
                        self._test_data["parameter"][project_id][page["page"]] = {}
                        for function in page["function"]:
                            # temp = {p['name']: p['answer'] for p in function['parameter']}
                            self._test_data["parameter"][project_id][page["page"]][function['function']] = function[
                                "parameter"]
                    except Exception as e:
                        self.logger.warning(f"Failed to load parameter list of project:{project_id} with parameter {page} on error {e}")

        except Exception as e:
            self.logger.critical(f"Initial failed:{e}")

    def run(self, project_id_list: list[str], checklist: bool = True, skeleton: bool = True, code: bool = True,
            parameter: bool = True):
        score = {
            "checklist": 0 if checklist else None,
            "skeleton": 0 if skeleton else None,
            "code": 0 if code else None,
            "parameter": 0 if parameter else None,
        }
        report = {
            "assignment": {
                "checklist": {},
                "skeleton": {},
                "code": {},
                "parameter": {}
            }
        }
        score_table = []
        for project_id in project_id_list:
            score_table_row = {
                "project_id": project_id,
                "checklist": 0 if checklist else None,
                "skeleton": 0 if skeleton else None,
                "code": 0 if code else None,
                "parameter": 0 if parameter else None,
            }
            score_table.append(score_table_row)
            self.logger.info(f"Processing project {project_id}.")
            if checklist and self.answer_checklist and project_id in self.answer_checklist:
                self.logger.info(f"Checklist on project {project_id}.")
                try:
                    best_score, assignment = sentence_transformer_calc(self._test_data["checklist"][project_id],
                                                                       self._reference_data["checklist"][project_id])
                    report["assignment"]["checklist"][project_id] = assignment
                    score["checklist"] += best_score
                    score_table_row["checklist"] = best_score
                    self.logger.info(f"Checklist score on project {project_id}: {best_score}")
                except Exception as e:
                    self.logger.critical(f"Failed to calculate checklist:{e}")

            if skeleton and self.answer_skeleton and project_id in self.answer_skeleton and self.answer_skeleton[project_id]:
                self.logger.info(f"Skeleton on project {project_id}.")
                try:
                    best_score, assignment = codebleu_calc(self._test_data["skeleton"][project_id],
                                                           self._reference_data["skeleton"][project_id],
                                                           language=self.reference_project[int(project_id) - 1][
                                                               "framework_technical_stack"][0][
                                                               "language"].lower())
                    report["assignment"]["skeleton"][project_id] = assignment
                    score["skeleton"] += best_score
                    score_table_row["skeleton"] = best_score
                    self.logger.info(f"Skeleton score on project {project_id}: {best_score}")
                except Exception as e:
                    self.logger.critical(f"Failed to calculate skeleton:{e}")

            if code and self.answer_code and project_id in self.answer_code and self.answer_code[project_id]:
                self.logger.info(f"Code on project {project_id}.")
                try:
                    best_score, assignment = codebleu_calc(self._test_data["code"][project_id],
                                                           self._reference_data["code"][project_id],
                                                           language=self.reference_project[int(project_id) - 1][
                                                               "framework_technical_stack"][0][
                                                               "language"].lower())
                    report["assignment"]["code"][project_id] = assignment
                    score["code"] += best_score
                    score_table_row["code"] = best_score
                    self.logger.info(f"Code score on project {project_id}: {best_score}")
                except Exception as e:
                    self.logger.critical(f"Failed to calculate code:{e}")

            if parameter and self.answer_parameter and project_id in self.answer_parameter:
                self.logger.info(f"Parameter on project {project_id}.")
                try:
                    best_score, similarities = levenshtein_calc(self._test_data["parameter"][project_id],
                                                                self._reference_data["parameter"][project_id])
                    report["assignment"]["parameter"][project_id] = similarities
                    score["parameter"] += best_score
                    score_table_row["parameter"] = best_score
                    self.logger.info(f"Parameter score on project {project_id}: {best_score}")
                except Exception as e:
                    self.logger.critical(f"Failed to calculate parameter:{e}")

        for key in score:
            if score[key] is not None:
                score[key] = round(float(score[key]), 6)
        self.logger.info(f"{self.verbose_name} Sum:{score}")
        self.report_file.write("Sum:"+json.dumps(score)+"\n")
        for key in score:
            if score[key] is not None:
                score[key] = str(round(score[key] / len(project_id_list), 4) * 100) + "%"
        self.logger.info(f"{self.verbose_name} Average:{score}")
        self.report_file.write("Average:" + json.dumps(score)+"\n")
        self.report_file.write(str(report))
        return score, score_table


class CaseStudyController(BaseController):
    def __init__(self, cot_log_path, llm, device, model_class:LLMTest, output_file_path, n):
        super().__init__()
        self.cot_log = open(cot_log_path, "r",encoding="utf-8").read()
        self.model:LLMTest = model_class(llm=llm, device=device)
        self.n = n
        self.output_file = open(output_file_path, "w", encoding="utf-8")

    def run(self):
        message = f"Here is the log what you have reasoned.\n ```log\n  {self.cot_log}  \n```Return your FULL chain of thought of reasoning each step in the log. DO NOT summary the output."
        role_message = "You are GPT-4o"
        count = 0
        while count < self.n:
            print(f"Start:{count}")
            text = self.model.send_message(message, role_message)
            print(f"Finished: {text.choices[0].message.content}")
            self.output_file.write(f"======Count {count+1}======")
            self.output_file.write(text.choices[0].message.content)
            count += 1

