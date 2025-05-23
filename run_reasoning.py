from datetime import datetime
import os
from controller import LLMController
from llm import GPTTest, LlamaTest, GeminiTest

# 1.Add any model you like using mode_dict. The boolean value means that it is [True/False] that the model is a coding model.
model_dict = {
    # "gpt-4o": False,
    # "gemma2": False,
    # "codegemma": True,
    # "gemma3": False,
    "gemma3:27b": False,
}

# 2. Set the input file path. Default is "data/project_eval_project.json"
file_path = "data/project_eval_project.json"

# 3. If you are using a NON-ollama model, add your model prefix with its own LLMTestClass in start_with_dict{}, else skip this step.
start_with_dict = {
    "gpt": GPTTest,
    "gemini": GeminiTest
}

# 4.Set your test times.
test_times = 5

# 5.Set if you want to test cascade or direct. [True] means only cascade, [False] means only direct, [True, False] means both.
cascade_settings = [True, False]

# 6.Set your GPU UUID. If you don't know it or you want to use default GPU or you are using a non-local API, leave it blank.
GPU_UUID = "GPU-e64683ee-8e58-13f4-b2aa-e88128cc3ef9"

# Enjoy it. It will default save in experiments/<today>-<times>/<model_name>/.
if __name__ == '__main__':
    for counter in range(test_times):
        for cascade in cascade_settings:

            for model in model_dict:
                save_path = f"experiments/{datetime.now().strftime('%Y%m%d')}-{counter+1}/{model.replace(":","-")}/{'cascade' if cascade else 'direct'}/"

                if not os.path.exists(save_path):
                    os.makedirs(save_path)

                tester = LLMController(
                    question_path=file_path,
                    model_class=start_with_dict[model.split("-")[0]] if model.split("-")[0] in start_with_dict else LlamaTest,
                    llm=model,
                    device=GPU_UUID,
                    language={"website": "python", "software": "python", "batch": "python", "console": "python"},
                    technical_stack={"website": "Django", "software": "pygame", "batch": "none", "console": "none"},
                    output_path=save_path,
                    parameter_generate=True,
                    information_generate=True,
                    start_file_generate=True,
                )
                start_level = 3 if model_dict[model] else 1
                for level in range(start_level,4):
                    tester.run(level, cascade=cascade)