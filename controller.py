import copy
import json
import logging
import os
from datetime import datetime

from llm import GPTTest, LLMTest
from openjudge import WebsiteJudge, BaseJudge

PROJECT_TYPE = {
    'website': WebsiteJudge,
    'software': "",
    'batch': "",
}


class LLMController:
    def __init__(self, question_path: str, model_class: LLMTest, language: dict = None, technical_stack: dict = None,
                 output_path: str = "data/", ):
        '''
        A Example to show how to use LLM answer the question of Project Eval.
        :param question_path: The source data
        :param model_class: The LLM model that you want to use. Check LLMTest in llm.py as a template example.
        :param output_path: The answer from LLM.
        :param language:Restrict format with {"website": "python", "software": "c++", "batch": "basic"}.
        :param technical_stack: Restrict format with {"website": "django", "software": "pygame", "batch": "any"}
        '''

        self.logger = logging.getLogger('LLMController')
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
        answer_dict = {}
        for q in self.question:
            self.logger.info("Answer question {}.".format(q['project_id']))
            language = self.language[q['project_type']] if self.language else q['framework_technical_stack']['language']
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
        output_file_path = self.output_path + self.model.llm + "_" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".json"
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            self.logger.info("Writing to " + output_file_path)
            json.dump(answer_dict, output_file)


class JudgeController:
    def __init__(self, question_path: str, answer_path: str, model_class: LLMTest, ):

        self.logger = logging.getLogger('JudgeController')
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

        try:
            question_list = json.load(open(question_path, 'r', encoding='utf-8'))
            self.question_dict = {q['project_id']: q for q in question_list}
        except Exception as e:
            self.logger.critical("Loading question list failed with error {}".format(e))
            raise Exception("Loading question list failed with error {}".format(e))
        self.testcode = {}
        for t in question_list:
            temp = copy.deepcopy(t)
            self.testcode[temp['project_id']] = temp['testcode']  # Save the testcode for each project
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
        base_dir = "test/" + datetime.now().strftime("%Y%m%d-%H%M%S") + "/" + str(project_id) + "/"
        os.makedirs(base_dir, exist_ok=True)
        for file in self.answer_dict[str(project_id)]:
            file_name =  base_dir + file['path']
            content = file['code']
            last_slash = file_name.rfind("/")
            if last_slash != -1:
                dirpath = file_name[:last_slash]
                if not os.path.isdir(dirpath):
                    os.makedirs(dirpath)
            with open(file_name, 'w', encoding="utf-8") as f:
                f.write(content)
                f.close()

    def evaluate(self):
        total_status = {'total': 0, 'pass': 0, 'failed': 0}
        for project_id in self.question_dict:
            self.logger.info("Evaluating project id {}".format(project_id))
            project = self.question_dict[project_id]
            self.write_answer_to_file(project_id)
            judge: BaseJudge = PROJECT_TYPE[project['project_type']]()
            if not judge.preprocess(project_id):
                self.logger.info("{} scored 0.".format(project_id))
                continue
            try:
                parameter_list = judge.get_parameters(self.model, self.answer_dict[project_id],
                                                      self.question_dict[project_id])
                # parameter = [{"page":"XXX", "function":"[{"function":"XXX", "parameter": [{"name":"XXX", "answer": "your_answer"}, {...}, ...]},...],...]
                parameter = {}
                for page in parameter_list:
                    parameter[page['page']] = {}
                    for function in page["function"]:
                        temp = {p['name']: p['answer'] for p in function['parameter']}
                        parameter[page['page']][function['function']] = function["parameter"]
                del parameter_list
            except Exception as e:
                self.logger.info(f"Get parameters for project id {project_id} failed with exception {e}.")
                self.logger.info("{} scored 0.".format(project_id))
                continue
            pass_count = 0
            n = 0
            index = 0
            for page in self.testcode[project_id]:
                n += len(page['function'])
                total_status['total'] += len(page['function'])
                for function in page['function']:
                    self.logger.info("Evaluating function {}".format(str(project_id) + "_" + str(index)))
                    index += 1
                    try:
                        kwargs = parameter[page['page']][function['function']]
                    except Exception as e:
                        self.logger.info(
                            "Parameter(s) finding was failed in the project_answer_list. Exception {}".format(e))
                        continue
                    if judge.check(str(project_id) + "_" + str(index), function['test'], **kwargs):
                        pass_count += 1
                        self.logger.info("Function {} passed.".format(str(project_id) + "_" + str(index)))
                    else:
                        self.logger.info("Function {} failed.".format(str(project_id) + "_" + str(index)))
            project_score = pass_count / n
            self.logger.info(f"Project id {project_id} scored {project_score}")
            judge.clean()
        self.logger.info("Finished. Report: {}".format(total_status))
        return total_status, total_status['pass'] / total_status['total']
