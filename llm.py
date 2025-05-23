import json
import logging
import os
import re
import time
from datetime import datetime

from openai import OpenAI
from google import genai
from config import OPENAI_KEY, GOOGLE_AI_KEY
from prompt import prompt


class LLMTest:
    def __init__(self, llm: str, *args, **kwargs):
        self.llm = llm

        # logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(level=logging.DEBUG)
        if not self.logger.handlers:
            handler = logging.FileHandler("log/{0}-LLM.log".format(datetime.now().strftime("%Y%m%d-%H%M%S")),encoding="utf-8")
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            console.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.addHandler(console)

    def send_message(self, message, role_message):
        pass

    def generate_checklist(self, nl_prompt):
        pass

    def generate_skeleton(self, language, technical_stack, nl_checklist):
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

    def get_information(self, answer, technical_stack, project_root):
        '''
        Get any information that may use for the project judge.
        NOTE: initiate command will always be requested in this function. However, we do recommend that give the initiate command manually as most of the LLM can't do it correctly
        You can override this function to manually provide parameters which are required by the testcode.
        :param answer:
        :param technical_stack:
        :param project_root:
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

    @staticmethod
    def parse(rsp, pattern: str = r"```json(.*)```"):
        match = re.search(pattern, rsp, re.DOTALL)
        code_text = match.group(1) if match else rsp
        return code_text




class GPTTest(LLMTest):
    def __init__(self, llm="gpt-4o", *args, **kwargs):
        super(GPTTest, self).__init__(llm, *args, **kwargs)
        self.client = OpenAI(api_key=OPENAI_KEY)

    def send_message(self, message, role_message):
        self.logger.debug("Sending:" + message)
        completion = self.client.chat.completions.create(
            model=self.llm,
            messages=[
                {"role": "system",
                 "content": role_message},
                {"role": "user",
                 "content": message}
            ]
        )
        self.logger.debug("Received:" + completion.choices[0].message.content)
        return completion

    def completion_to_dict(self, answer):
        s = answer.choices[0].message.content
        try:
            return json.loads(LLMTest.parse(s))
        except Exception as e:
            self.logger.debug(f"Completion to dict failed by using pattern ```json(.*)```: {e}")
        try:
            return json.loads(LLMTest.parse(s, pattern=r"```json\n(\[.*?\])\n\```"))
        except Exception as e:
            self.logger.debug(f"Completion to dict failed by using pattern ```json\\n(\\[.*?\\])\\n``` : {e}")
        try:
            return json.loads(s)
        except Exception as e:
            self.logger.debug(f"Completion to dict failed directly: {e}")
            self.logger.debug("Completion to dict: trying replace \\")
            s = s.replace("\\", "\\\\")
            return s

    def generate_checklist(self, nl_prompt):
        message = prompt[self.__class__.__name__]['generate_checklist'].format(nl_prompt=nl_prompt)
        completion = self.send_message(message, "You are a professional project manager (PM).")
        return self.completion_to_dict(completion)

    def generate_skeleton(self, language, technical_stack, nl_checklist):
        message = prompt[self.__class__.__name__][language.lower() + '_generate_skeleton'].format(
            nl_checklist=nl_checklist,
            technical_stack=technical_stack)
        completion = self.send_message(message, "You are a professional computer program architect.")
        return self.completion_to_dict(completion)

    def generate_answer(self, description, technical_stack):
        """
        Generate the answer by using GPT.
        :param description: depends on the level chose by user, the prompt can be natural language description, natural language checklist or programming language framework
        :param technical_stack: decided by user
        :return: generated answer in json format
        """
        message = prompt[self.__class__.__name__]['generate_answer'].format(description=description,
                                                                            technical_stack=technical_stack if technical_stack else "")
        completion = self.send_message(message, "You are a professional computer programmer.")
        return self.completion_to_dict(completion)

    def get_parameter(self, answer, technical_stack, parameter_required):
        """
        GPT can automatically recognize the request parameter for the test.
        :param answer: the answer that was given by gpt
        :param technical_stack: decided by user in the "generate answer" step
        :param parameter_required: request by the judge
        :return: generated parameters in json format
        """
        message = prompt[self.__class__.__name__]["generate_parameter"].format(answer=answer,
                                                                               technical_stack=technical_stack if technical_stack else "",
                                                                               parameter_required=parameter_required)
        completion = self.send_message(message, "You are a professional computer programmer.")
        return self.completion_to_dict(completion)

    def get_information(self, answer, technical_stack, project_root):
        """
        GPT can automatically recognize the initial command, requirements and other necessary information.
        :param answer:
        :param technical_stack:
        :return: message
        """
        message = prompt[self.__class__.__name__]["generate_information"].format(answer=answer,
                                                                                 technical_stack=technical_stack if technical_stack else "",
                                                                                 project_root=project_root)
        completion = self.send_message(message, "You are a professional computer programmer.")
        return self.completion_to_dict(completion)

    def get_start_file(self, answer, technical_stack, project_root):
        """
        GPT can automatically recognize the entry point of a console project.
        :param answer:
        :param technical_stack:
        :param project_root:
        :return: message
        """
        message = prompt[self.__class__.__name__]["generate_entry_point"].format(answer=answer,
                                                                                 technical_stack=technical_stack if technical_stack else "",
                                                                                 project_root=project_root)
        completion = self.send_message(message, "You are a professional computer programmer.")
        return self.completion_to_dict(completion)

    def mask_skeleton(self, answer):
        """
        as masker need to describe the using method of
        :param answer:
        :return:
        """
        message = prompt[self.__class__.__name__]['mask_framework'].format(answer=answer)
        completion = self.send_message(message, "You are a professional computer program architect.")
        return self.completion_to_dict(completion)


class LlamaTest(GPTTest):
    def __init__(self, llm="llama3.2", device: str = "", *args, **kwargs):
        '''
        This llama test class is created base on Ollama. Ollama supports OpenAI pattern.
        :param llm: any model that Ollama supports can use in this class.
        :param device: If you want to use other GPU rather than GPU:0, set the UUID in this param. Check the UUID by using "nvidia-smi -L".
        '''
        super(LlamaTest, self).__init__(llm)
        if device:
            os.environ['CUDA_VISIBLE_DEVICES'] = device
        os.environ[
            'NO_PROXY'] = "localhost,127.0.0.1"  # Ollama didn't fit the proxy settings which will lead to 502 error.
        self.client = OpenAI(
            base_url='http://localhost:11434/v1/',
            api_key="llama"  # Required but ignored
        )
        del os.environ['NO_PROXY']
        if device:
            del os.environ['CUDA_VISIBLE_DEVICES']

class GeminiTest(GPTTest):
    def __init__(self, llm="gemini-1.5-flash",  *args, **kwargs):
        super(GeminiTest, self).__init__(llm)
        self.client = genai.Client(api_key=GOOGLE_AI_KEY)

    def send_message(self, message, role_message):
        self.logger.debug("Sending:" + message)
        completion = self.client.models.generate_content(
            model=self.llm,
            contents = message,
        )
        self.logger.debug("Received:" + completion.text)
        time.sleep(1)
        return completion

    def completion_to_dict(self, answer):
        s = answer.text
        try:
            return json.loads(LLMTest.parse(s))
        except Exception as e:
            self.logger.debug(f"Completion to dict failed by using pattern ```json(.*)```: {e}")
        try:
            return json.loads(LLMTest.parse(s, pattern=r"```json\n(\[.*?\])\n\```"))
        except Exception as e:
            self.logger.debug(f"Completion to dict failed by using pattern ```json\\n(\\[.*?\\])\\n``` : {e}")
        try:
            return json.loads(s)
        except Exception as e:
            self.logger.debug(f"Completion to dict failed directly: {e}")
            self.logger.debug("Completion to dict: trying replace \\")
            s = s.replace("\\", "\\\\")
            return s