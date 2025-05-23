"""
This is all the prompt that is using in ProjectEval.
We are welcome that you edit any of them to get higher scores.
"""

CLOSE_SOURCE = {
    "generate_checklist": '{nl_prompt}.Give a natural language function checklist from the users\' views '
                          'using JSON format as [{{"page":"XXX", "function":[{{"function":"XXX", "description"; "YYYY"}}, {{...}}, ...]}}, {{...}}, ...}} with NO additional content, instruction or summary.',
    "python_generate_skeleton": 'Based on this checklist {nl_checklist}, give a framework of {technical_stack} '
                                 'also used JSON format of [{{"file":"xxx.py","path":"somepath/somedir/xxx.py","code":"the_skeleton"}}, {{...}}, ...]. '
                                 'DO NOT CONTAIN ANY OTHER CONTENTS.',
    "generate_answer": 'Based on this {description}, give a {technical_stack} Project of its all files (including the essential files to run the project) to meet the requirement '
                       'in JSON format of [{{"file":"answer.something","path":"somepath/somedir/answer.something", "code":"the_code_in_the_file"}},{{...}},...] with NO other content. Recommend adding an id attribute to each HTML element and adding classes for them too.',
    "generate_parameter": 'Based on the {technical_stack} project you given which is {answer}, give the required parameters\' values of the django project for each test in the {parameter_required}. '
                          'Return in Json format of [{{"page":"XXX", "function":"[{{"function":"XXX", "parameter": [{{"name":"XXX", "answer": "your_answer_parameter"}}, {{...}}, ...]}}, {{...}}, ...], {{...}}, ...] with NO other content and DO NOT CHANGE THE KEYS OF JSON. '
                          'For example, the requested parameter name is \'test_url\' and the answer may be \'http://localhost:8000/\'.',
    "generate_information": 'Based on the {technical_stack} project you given which is {answer}, assume that all files and environments have been created in root {project_root}, '
                            'and projects and apps have been created, give the run commands, homepage\'s url and requirements of the {technical_stack} project, '
                            'return in JSON format of {{"initiate_commands": [["manage.py","makemigrations"],["manage.py","migrate"],[XXX,YYY],...], "requirements": [XXXX, YYYY]}} NO additional content, instruction or summary',
    "generate_entry_point": 'Based on the {technical_stack} project you given which is {answer}, '
                            'assume that all files and environments have been created in root {project_root}, find the entry file to run the project. '
                            'ONLY return the path such as "example/run.py" with NO additional content, instruction or summary.Do NOT add root path into the answer, but only the relative path.',
    "mask_framework": 'You are tasked with standardizing code project files into a structured format. Here are the files that need to be structured: {answer}. Follow these specific steps:\n\n1. **Input Structure**:  \n   Each project is a list of dictionary where:  \n   - The each dictionary represents a file.  \n   - Each dictionary contains:\n     - "file": the filename.\n     - "path": the file path.\n     - "code": the code content.\n\n2. **Standardization Rules**:  \n   Each project must follow this format:  \n   - **File Content**: The code must have clearly defined placeholder functions with docstrings describing their purpose.  \n   - **Consistent Sections**: Include these sections in order:  \n     - Python:\n\t\t- Import statements  \n\t\t- File paths or global variables  \n\t\t- Function definitions (each with docstrings, if there is no docstrings, make one)  \n\t\t- (Optional) main() function or entry point (if __name__ == "__main__")  \n\t - HTML:\n\t\t- <head> tag and its content\n\t\t- <body> tag WITHOUT its content and replace the content with comment of docstrings describing the content purpose.\n   - **Retained Files**: The following type of files should remain UNCHANGE:\n     - Django default files like: migrations, wsgi, asgi, manage, settings.\n\t - Python default files like: __init__\n   - **Removing Sections**:\n\t - All other contents that are NOT in the Consistent Sections or Retained Files include "return" and "pass" sentence and its parameter\n\t - DO NOT remove any contents that are mentioned in the Consistent Sections or Retained Files\n3. **Output Structure**:  \n   Maintain the input format but with all projects standardized similarly to Example Output belowed. Ensure the code style, comments, and placeholders are clean and consistent across all projects.\n\n4. **Specific Adjustments**:  \n   - Replace incomplete or inconsistent docstrings with meaningful placeholders like:  \n     \npython\n     """\n     Brief description of the function\'s purpose.\n     """\n  \n   - Ensure imports are grouped logically at the top.  \n   - Use consistent naming conventions for variables, file paths, and methods.  \n   - Retain project-specific logic while ensuring stylistic consistency.\n\n5. **Example Output**:  \n   Here\'s the desired structure for any given project:  \n   \njson\n[\n       {{\n         "file": "file_name.py",\n         "path": "file_name.py",\n         "code": "import module\n\n# Global variables\ninput_file = "input_file.xlsx"\noutput_file = "output_file.xlsx"\n\ndef function_name():\n    """\n    Brief description of function.\n    """\n    pass\n\ndef main():\n    """\n    Main execution function.\n    """\n    pass\n\nif __name__ == "__main__":\n    main()"\n       }},\n\t   {{\n\t   ...\n\t   }},\n\t   ...\n]\n'
    }

prompt = {
    "GPTTest": CLOSE_SOURCE,
    "GeminiTest": CLOSE_SOURCE,
    "LlamaTest": {
        "generate_checklist": '{nl_prompt}.Give a natural language function checklist from the users\' views. '
                              'Only return as a JSON object which template is [{{"page":"XXX", "function":[{{"function":"XXX", "description"; "YYYY"}}, {{...}}, ...]}}, {{...}}, ...}} with NO other content. '
                              'Respond only with natural language valid JSON. Do not write an introduction or summary.',
        "python_generate_skeleton": 'Based on this checklist {nl_checklist}, give a framework of {technical_stack}.'
                                     'Only return as a JSON object which template is [{{"file":"xxx.py","path":"somepath/somedir/xxx.py","code":"the_skeleton"}}, {{...}}, ...]. '
                                     'If the file is not a python file, the json format should be {{"file": "/example_app/xxx.xx", "description":"XXXX"}}. DO NOT CONTAIN ANY OTHER CONTENTS. '
                                     'Respond only with valid JSON. Do not write an introduction or summary.',
        "generate_answer": 'Based on this {description}, give a {technical_stack} Project of its all files (including the essential files to run the project) to meet the requirement.'
                           'Only return as a JSON object which template is [{{"file":"answer.something","path":"somepath/somedir/answer.something", "code":"the_code_in_the_file"}},{{…}},…] with NO other content. '
                           'Respond only with valid JSON. Do not write an introduction or summary. '
                           'Recommend adding an id attribute to each HTML element and adding classes for them too.',
        "generate_parameter": 'Based on the {technical_stack} project you given which is {answer}, give the required parameters\' values of the django project for each test in the {parameter_required}. '
                              'Return as a JSON object which template is [{{"page":"XXX", "function":"[{{"function":"XXX", "parameter": [{{"name":"XXX", "answer": "your_answer_parameter"}}, {{...}}, ...]}}, {{...}}, ...], {{...}}, ...] with NO other content and DO NOT CHANGE THE KEYS OF JSON. '
                              'For example, the requested parameter name is \'test_url\' and the answer may be \'http://localhost:8000/\'. '
                              'Respond only with valid JSON. Do not write an introduction or summary.',
        "generate_information": 'Based on the {technical_stack} project you given which is {answer}, assume that all files and environments have been created in root {project_root}, '
                                'and projects and apps have been created, give the run commands, homepage\'s url and requirements of the {technical_stack} project. '
                                'Only return as a JSON object which template is {{"initiate_commands": [["manage.py","makemigrations"],["manage.py","migrate"],[XXX,YYY],...], "requirements": [XXXX, YYYY]}} with NO other content. '
                                'Respond only with valid JSON. Do not write an introduction or summary.',
        "generate_entry_point": 'Based on the {technical_stack} project you given which is {answer}, '
                                'assume that all files and environments have been created in root {project_root}, find the entry file to run the project. '
                                'ONLY return the path such as "example/run.py" with NO other content. Do NOT add root path into the answer, but only the relative path.'
                                'Do NOT write an introduction or summary.'
    },

}
