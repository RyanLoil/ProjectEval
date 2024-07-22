import copy
import json
import logging
from datetime import datetime

from llm import GPTTest, LLMTest
from openjudge import WebsiteJudge

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

        self.logger = logging.getLogger('Controller')
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
                answer = eval(answer)  # In the example, LLM will return a python dictionary as answer.
                if type(answer) != dict:
                    raise Exception("Invalid answer format in project {}.".format(q["project_id"]))
                answer['project_id'] = q['project_id']
            except Exception as e:
                self.logger.warning(str(e))
                continue
            answer['framework_technical_stack'] = {'language': language, 'technical_stack': technical_stack}
            answer_dict[q['project_id']] = answer
        output_file_path = self.output_path + self.model.llm + "_" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".json"
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            self.logger.info("Writing to " + output_file_path)
            json.dump(answer_dict, output_file)


class JudgeController:
    def __init__(self, question_path: str, answer_path: str, model_class: LLMTest, ):

        self.logger = logging.getLogger('Controller')
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
            self.testcode_list = json.load(open(question_path, 'r', encoding='utf-8'))
        except Exception as e:
            self.logger.critical("Loading question list failed with error {}".format(e))
            raise Exception("Loading question list failed with error {}".format(e))
        self.testcode = []
        for t in self.testcode_list:
            temp = copy.deepcopy(t)
            del temp['nl_prompt'], temp['nl_checklist'], temp['framework']
            self.testcode.append(temp)

        try:
            self.answer_dict = json.load(open(answer_path, 'r', encoding='utf-8'))
        except Exception as e:
            self.logger.critical("Loading answer list failed with error {}".format(e))
            raise Exception("Loading answer list failed with error {}".format(e))

        self.model = model_class()
        self.project_parameter_request_list = {
            'website': {},
            'software': {},
            'batch': {},
        }
        self.project_answer_list = {
            'website': {},
            'software': {},
            'batch': {},
        }

    def preprocess(self):
        # For getting parameter and classifying different type of project.
        self.logger.info("Preprocessing.")

        for t in self.testcode:
            for page in t:
                for function in page:
                    del function['test']
            self.project_parameter_request_list[t['project_type']][t['project_id']] = t

        self.logger.info("Requesting parameters from LLM to adapt question.")
        for k in self.project_parameter_request_list:
            for pid in self.project_parameter_request_list[k]:
                parameter = self.model.get_parameter(self.answer_dict[pid],
                                                     self.project_parameter_request_list[k][pid], )
                self.project_answer_list[k][pid] = parameter

    def run(self):
        for k in self.project_answer_list:
            judge = PROJECT_TYPE[k](self.project_parameter_request_list[k], requirements=["django", ],
                                    browser_type="edge", website_initiate_command=None,
                                    generation_list_path="data/generation_test.json")
            judge.evaluate()

            self.logger.info("Evaluating question {}.".format(t['project_id']))
            self.logger.debug("Evaluating question {} page {}.".format(t['project_id'], page['page']))


