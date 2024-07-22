import logging
import os
from datetime import datetime

from openai import OpenAI

from config import OPEN_AI_KEY

prompt = {
    "generate_checklist": '{nl_prompt}.Give a natural language function checklist from the users\' views using JSON format of [{{"page":"XXX", "function":[{{"function":"XXX", "description"; "YYYY"}}, {{...}}, ...]}}, {{...}}, ...}} with NO other content.',
    "python_generate_framework": 'Based on this checklist {nl_checklist}, give a framework of {technical_stack} also used JSON format of [{{"file":"/example_app/xxx.py","import":["a","b",...], "class":{{"name":"c", "parameter":[{{"name":"XXX", "type":"XXX"}}, {{...}}, ...], "description":"XXXX", "function": [{{"name":"d","parameter":[{{"name":"XXX", "type":"XXX"}}, "variable":[{{"name":"e", "type":"xxx", "description":"xxx"}}, {{...}}, ...], {{...}}, ...], "description":"XXXX", "return_type":"XXX"}}, {{...}}, ...]}}, {{...}}, ...]. If the file is not a python file, the json format should be {{"file": "/example_app/xxx.xx", "description":"XXXX"}}. DO NOT CONTAIN ANY OTHER CONTENTS.',
    "generate_answer": 'Based on this {prompt}, give a {technical_stack} Project to meet the requirement in JSON format of [{"file":"XXX","path":"XXX/XXX", "code":"the_code_in_the_file"},{…},…] with NO other content.',
    "generate_parameter": 'Based on the {technical_stack} project you given which is {answer}, give the parameters of the django project for each test in the {parameter_required}. Return in Json format of [{"page":"XXX", "function":"[{"function":"XXX", "parameter": [{"name":"XXX", "answer": "your_answer"}, {...}, ...]}, {...}, ...], {...}, ...] with NO other content'
}


class LLMTest:
    def __init__(self, llm: str):
        self.llm = llm

        # logger
        self.logger = logging.getLogger(self.__class__.__name__)
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

    def generate_checklist(self, nl_prompt):
        pass

    def generate_framework(self, language, technical_stack, nl_checklist):
        pass

    def generate_answer(self, prompt, technical_stack):
        pass

    def get_parameter(self, answer, technical_stack, parameter_required):
        '''
        Get parameters for the testcode.
        You can override this function to manually provide parameters which are required by the testcode.
        :param answer:
        :param technical_stack:
        :param parameter_required:
        :return: 
        '''
        pass

    def json_to_file(self, answer):
        """
        Transform the answer into files so that the judge can run the project.
        :param answer: The answer should follow the JSON format of [{"file": <filename>, "path": <filepath>, "code": <content>}, {...}, ... ]

        :return: None
        """
        for file in answer:
            filepath = file["path"]
            last_slash = filepath.rfind("/")
            if last_slash != -1:
                dirpath = filepath[:last_slash]
                if not os.path.isdir(dirpath):
                    os.makedirs(dirpath)
            with open(filepath, 'w', encoding="utf-8") as f:
                f.write(file["code"])
                f.close()


class GPTTest(LLMTest):
    def __init__(self, llm="gpt-4o"):
        super(GPTTest, self).__init__(llm)
        self.client = OpenAI(api_key=OPEN_AI_KEY)

    def generate_checklist(self, nl_prompt):
        message = prompt['generate_checklist'].format(nl_prompt=nl_prompt)
        self.logger.debug("Sending:" + message)
        completion = self.client.chat.completions.create(
            model=self.llm,
            messages=[
                {"role": "system",
                 "content": "You are a professional project manager (PM)."},
                {"role": "user",
                 "content": message}
            ]
        )
        self.logger.debug("Received:" + completion.choices[0].message.content)
        return completion

    def generate_framework(self, language, technical_stack, nl_checklist):
        message = prompt[language.lower() + '_generate_framework'].format(nl_checklist=nl_checklist,
                                                                          technical_stack=technical_stack)
        self.logger.debug("Sending:" + message)
        completion = self.client.chat.completions.create(
            model=self.llm,
            messages=[
                {"role": "system",
                 "content": "You are a professional computer framework engineering."},
                {"role": "user",
                 "content": message}
            ]
        )
        self.logger.debug("Received:" + completion.choices[0].message.content)
        return completion

    def generate_answer(self, prompt, technical_stack):
        """
        Generate the answer by using GPT.
        :param prompt: depends on the level chose by user, the prompt can be natural language description, natural language checklist or programming language framework
        :param technical_stack: decided by user
        :return: generated answer in json format
        """
        message = prompt['generate_answer'].format(prompt=prompt, technical_stack=technical_stack)
        self.logger.debug("Sending:" + message)
        completion = self.client.chat.completions.create(
            model=self.llm,
            messages=[
                {"role": "system",
                 "content": "You are a professional computer programmer."},
                {"role": "user",
                 "content": message}
            ]
        )
        self.logger.debug("Received:" + completion.choices[0].message.content)
        return completion

    def get_parameter(self, answer, technical_stack, parameter_required):
        """
        GPT can automatically recognize the request parameter for the test.
        :param answer: the answer that was given by gpt
        :param technical_stack: decided by user in the "generate answer" step
        :param parameter_required: request by the judge
        :return: generated parameters in json format
        """
        message = prompt["generate_parameter"].format(answer=answer, technical_stack=technical_stack,
                                                      parameter_required=parameter_required)
        self.logger.debug("Sending:" + message)
        completion = self.client.chat.completions.create(
            model=self.llm,
            messages=[
                {"role": "system",
                 "content": "You are a professional computer programmer."},
                {"role": "user",
                 "content": message}
            ]
        )
        self.logger.debug("Received:" + completion.choices[0].message.content)
        return completion
