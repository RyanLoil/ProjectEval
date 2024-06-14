import copy
import os, json
from datetime import datetime

from openai import OpenAI
from config import OPEN_AI_KEY
import logging

prompt = {
    "check_list_generation": '{nl_prompt}.Just give a natural language function checklist from the users\' views using JSON format of [{{"page":"XXX", "function":[{{"function":"XXX", "description"; "YYYY", "required":true / false}}, {{...}}, ...], "required": true / false}}, {{...}}, ...}} with NO other content.',
    "python_framework_generation": 'Based on this checklist {nl_checklist}, give a framework of {technical_stack} also used JSON format of [{{"file":"/example_app/xxx.py","import":["a","b",...], "class":{{"name":"c", "parameter":[{{"name":"XXX", "type":"XXX"}}, {{...}}, ...], "description":"XXXX", "function": [{{"name":"d","parameter":[{{"name":"XXX", "type":"XXX"}}, "variable":[{{"name":"e", "type":"xxx", "description":"xxx"}}, {{...}}, ...], {{...}}, ...], "description":"XXXX", "return_type":"XXX"}}, {{...}}, ...]}}, {{...}}, ...] include the unnecessary functions. If the file is not a python file, the json format should be {{"file": "/example_app/xxx.xx", "description":"XXXX"}}. DO NOT CONTAIN ANY OTHER CONTENTS.',
    "website_test_generation": 'Based on this checklist {nl_checklist}, give a selenium test code for each functions in JSON format of [{{"page":"XXX", "function":[{{"function":"XXX", "test": "your_test_code", "parameter": [{{"name":"test_url", "description": "the url for test"}}, {{"name":"weight_input_box_id", "description":"the input box component id of the weight"}}, {{...}}, ...]}}, {{...}}, ...}} with NO other content.',
}


class DataGenerator:
    def __init__(self, input_file: str, output_file: str, llm, ):
        """
        For data automation generation.
        :param input_file: A JSON file path, see data/generation.json as example.
        :param output_file: output file path.
        :param llm: we used openai gpt model as our automation generation model.
        """
        with open(input_file) as file:
            self.input_data = json.load(file)
        file.close()
        self.output_file = output_file
        self.client = OpenAI(api_key=OPEN_AI_KEY)
        self.llm = llm

        # logger
        self.logger = logging.getLogger('DataGenerator')
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

    def generate(self):
        output = []
        for data in self.input_data:
            self.logger.info("Generating project id {0}".format(data['project_id']))
            generated_data = copy.deepcopy(data)
            nl_prompt = data['nl_prompt']

            # nl_checklist generate
            try:
                nl_checklist = self.checklist_generate(nl_prompt).choices[0].message.content.replace("```json",
                                                                                                     "").replace("```",
                                                                                                                 "")
                nl_checklist = json.loads(nl_checklist)
            except Exception as e:
                self.logger.warning(
                    "Project id {project_id}: checklist generation error {e}".format(project_id=data["project_id"],
                                                                                     e=str(e)))
                continue
            framework_list = []
            for framework_para in data['framework_technical_stack']:
                try:
                    framework = self.framework_generate(framework_para["language"], nl_checklist,
                                                        framework_para["technical_stack"]).choices[
                        0].message.content.replace("```json", "").replace("```", "")
                    framework = json.loads(framework)
                except Exception as e:
                    self.logger.warning(
                        "Project id {project_id}: framework {language} {technical_stack} generation error {e}".format(
                            project_id=data["project_id"], language=framework_para["language"],
                            technical_stack=framework_para["technical_stack"], e=str(e)))
                    continue
                framework = {"content": framework, "language": framework_para["language"],
                             "technical_stack": framework_para["technical_stack"]}
                framework_list.append(framework)
            try:
                testcode = self.test_generate(data["project_type"], str(nl_checklist)).choices[
                    0].message.content.replace("```json", "").replace("```", "")
                testcode = json.loads(testcode)
            except Exception as e:
                self.logger.warning(
                    "Project id {project_id}: test generation error {e}".format(
                        project_id=data["project_id"], e=str(e)))

            generated_data["nl_checklist"] = nl_checklist
            generated_data["framework"] = framework_list
            generated_data["testcode"] = testcode
            output.append(generated_data)
        with open(self.output_file, "w", encoding="utf-8") as output_file:
            self.logger.info("Writing to " + self.output_file)
            json.dump(output, output_file)

    def checklist_generate(self, nl_prompt: str):
        message = prompt['check_list_generation'].format(nl_prompt=nl_prompt)
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

    def framework_generate(self, language: str, nl_checklist: str, technical_stack: str):
        message = prompt[language.lower() + '_framework_generation'].format(nl_checklist=nl_checklist,
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

    def test_generate(self, project_type: str, nl_checklist: str):
        message = prompt[project_type + "_test_generation"].format(nl_checklist=nl_checklist)
        self.logger.debug("Sending:" + message)
        completion = self.client.chat.completions.create(
            model=self.llm,
            messages=[
                {"role": "system",
                 "content": "You are a professional computer programming tester."},
                {"role": "user",
                 "content": message}
            ]
        )
        self.logger.debug("Received:" + completion.choices[0].message.content)
        return completion


dg = DataGenerator(input_file="data/generation.json", output_file="data/generation_test.json", llm='gpt-4o')
dg.generate()
