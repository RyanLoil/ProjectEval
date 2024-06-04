import os, json

prompt = {
    "check_list_generation": 'Just give a natural language function checklist from the users\' views using JSON format of [{"page":"XXX", "function":[{"function":"XXX", "description"; "YYYY", "required":true / false}, {...}, ...], "required": true / false}, {...}, ...} with NO other content',
    "django_framework_generation": 'Based on this checklist, give a framework of Django also used JSON format of [{"file":"/example_app/xxx.py","import":["a","b",...], "class":{"name":"c", "parameter":[{"name":"XXX", "type":"XXX"}, {...}, ...], "description":"XXXX", "function": [{"name":"d","parameter":[{"name":"XXX", "type":"XXX"}, "variable":[{"name":"e", "type":"xxx", "description":"xxx"}, {...}, ...], {...}, ...], "description":"XXXX", "return_type":"XXX"}, {...}, ...]}, {...}, ...] include the unnecessary functions with NO other content. If the file is not a python file, the json format should be {"file": "/example_app/xxx.xx", "description":"XXXX"}'
    ""
}

class DataGenerator:
    def __init__(self, input_file:str, output_file:str, llm, ):
        """
        For data automation generation.
        :param input_file: A JSON file path, see /data/generation.json as example.
        :param output_file: output file path.
        :param llm: we used openai gpt model as our automation generation model.
        """
        with open(input_file) as file:
            self.input_data = json.load(file)
        file.close()
        self.output_file = output_file

    def generate(self):
        pass

    def checklist_generation(self):
        pass

    def framework_generation(self):
        pass

    def test_generation(self):
        pass
