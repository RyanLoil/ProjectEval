prompt = {
    "GPTTest":{
    "generate_checklist": '{nl_prompt}.Give a natural language function checklist from the users\' views '
                          'using JSON format as [{{"page":"XXX", "function":[{{"function":"XXX", "description"; "YYYY"}}, {{...}}, ...]}}, {{...}}, ...}} with NO additional content, instruction or summary.',
    "python_generate_framework": 'Based on this checklist {nl_checklist}, give a framework of {technical_stack} '
                                 'also used JSON format of [{{"file":"/example_app/xxx.py","import":["a","b",...], "class":{{"name":"c", "parameter":[{{"name":"XXX", "type":"XXX"}}, {{...}}, ...], "description":"XXXX", "function": [{{"name":"d","parameter":[{{"name":"XXX", "type":"XXX"}}, "variable":[{{"name":"e", "type":"xxx", "description":"xxx"}}, {{...}}, ...], {{...}}, ...], "description":"XXXX", "return_type":"XXX"}}, {{...}}, ...]}}, {{...}}, ...]. '
                                 'If the file is not a python file, the json format should be {{"file": "/example_app/xxx.xx", "description":"XXXX"}}. DO NOT CONTAIN ANY OTHER CONTENTS.',
    "generate_answer": 'Based on this {description}, give a {technical_stack} Project of its all files (including the essential files to run the project) to meet the requirement '
                       'in JSON format of [{{"file":"answer.something","path":"somepath/somedir/answer.something", "code":"the_code_in_the_file"}},{{…}},…] with NO other content.',
    "generate_parameter": 'Based on the {technical_stack} project you given which is {answer}, give the required parameters\' values of the django project for each test in the {parameter_required}. '
                          'Return in Json format of [{{"page":"XXX", "function":"[{{"function":"XXX", "parameter": [{{"name":"XXX", "answer": "your_answer_parameter"}}, {{...}}, ...]}}, {{...}}, ...], {{...}}, ...] with NO other content and DO NOT CHANGE THE KEYS OF JSON. '
                          'For example, the requested parameter name is \'test_url\' and the answer may be \'http://localhost:8000/\'.',
    "generate_information": 'Based on the {technical_stack} project you given which is {answer}, assume that all files and environments have been created in root {project_root}, '
                            'and projects and apps have been created, give the run commands, homepage\'s url and requirements of the {technical_stack} project, '
                            'return in JSON format of {{"initiate_commands": [["manage.py","makemigrations"],["manage.py","migrate"],[XXX,YYY],...] ,"homepage":"http://XXX.YYY/", "requirements": [XXXX, YYYY]}} NO additional content, instruction or summary',
    "generate_entry_point": 'Based on the {technical_stack} project you given which is {answer}, '
                            'assume that all files and environments have been created in root {project_root}, find the entry file to run the project. '
                            'ONLY return the path such as "example/run.py" with NO additional content, instruction or summary.'
    },
    "LlamaTest": {
        "generate_checklist": '{nl_prompt}.Give a natural language function checklist from the users\' views. '
                              'Only return as a JSON object which template is [{{"page":"XXX", "function":[{{"function":"XXX", "description"; "YYYY"}}, {{...}}, ...]}}, {{...}}, ...}} with NO other content. '
                              'Respond only with natural language valid JSON. Do not write an introduction or summary.',
        "python_generate_framework": 'Based on this checklist {nl_checklist}, give a framework of {technical_stack}.'
                                     'Only return as a JSON object which template is [{{"file":"/example_app/xxx.py","import":["a","b",...], "class":{{"name":"c", "parameter":[{{"name":"XXX", "type":"XXX"}}, {{...}}, ...], "description":"XXXX", "function": [{{"name":"d","parameter":[{{"name":"XXX", "type":"XXX"}}, "variable":[{{"name":"e", "type":"xxx", "description":"xxx"}}, {{...}}, ...], {{...}}, ...], "description":"XXXX", "return_type":"XXX"}}, {{...}}, ...]}}, {{...}}, ...]. '
                                     'If the file is not a python file, the json format should be {{"file": "/example_app/xxx.xx", "description":"XXXX"}}. DO NOT CONTAIN ANY OTHER CONTENTS. '
                                     'Respond only with valid JSON. Do not write an introduction or summary.',
        "generate_answer": 'Based on this {description}, give a {technical_stack} Project of its all files (including the essential files to run the project) to meet the requirement.'
                           'Only return as a JSON object which template is [{{"file":"answer.something","path":"somepath/somedir/answer.something", "code":"the_code_in_the_file"}},{{…}},…] with NO other content. '
                           'Respond only with valid JSON. Do not write an introduction or summary.',
        "generate_parameter": 'Based on the {technical_stack} project you given which is {answer}, give the required parameters\' values of the django project for each test in the {parameter_required}. '
                              'Return as a JSON object which template is [{{"page":"XXX", "function":"[{{"function":"XXX", "parameter": [{{"name":"XXX", "answer": "your_answer_parameter"}}, {{...}}, ...]}}, {{...}}, ...], {{...}}, ...] with NO other content and DO NOT CHANGE THE KEYS OF JSON. '
                              'For example, the requested parameter name is \'test_url\' and the answer may be \'http://localhost:8000/\'. '
                              'Respond only with valid JSON. Do not write an introduction or summary.',
        "generate_information": 'Based on the {technical_stack} project you given which is {answer}, assume that all files and environments have been created in root {project_root}, '
                                'and projects and apps have been created, give the run commands, homepage\'s url and requirements of the {technical_stack} project. '
                                'Only return as a JSON object which template is {{"initiate_commands": [["manage.py","makemigrations"],["manage.py","migrate"],[XXX,YYY],...] ,"homepage":"http://XXX.YYY/", "requirements": [XXXX, YYYY]}} with NO other content. '
                                'Respond only with valid JSON. Do not write an introduction or summary.',
        "generate_entry_point": 'Based on the {technical_stack} project you given which is {answer}, '
                                'assume that all files and environments have been created in root {project_root}, find the entry file to run the project. '
                                'ONLY return the path such as "example/run.py" with NO other content. '
                                'Do not write an introduction or summary.'
    },

}
