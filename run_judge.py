import argparse
import json
import csv
import datetime
import os
from controller import JudgeController
from llm import GPTTest, OllamaTest, GeminiTest
from config import PROJECT_EVAL_DEFAULT_TEST_CASE
from utils import extract_json_files_from_folder

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--dirlist",type=str,required=True, help="The directories that you want to evaluate. The directories must obey the rule of /directory_name/model_name/cascade(direct)/<model>_<timestamp>_level_<level>.json. Official-result is a good example.")
    parser.add_argument("-d", "--dolist",type=str,required=False,default="[]",)
    parser.add_argument("--dolist_para",action="store_true")

    args = parser.parse_args()
    dirlist = json.loads(args.dirlist)
    dolist = set(json.loads(args.dolist))
    dolist_para = args.dolist_para

    # If you are using a NON-ollama model, add your model prefix with its own LLMTestClass in start_with_dict{}, else skip this step.
    start_with_dict = {
        "gpt": GPTTest,
        "gemini": GeminiTest,
    }

    project_id_list = [str(_) for _ in range(1,21)]
    result_output_path = "experiments/"
    file = open(
        result_output_path + f"projecteval-result-{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.csv",
        "w", encoding="utf-8", newline="")

    result_file = csv.DictWriter(
        file, delimiter=",",
        fieldnames=["date", "model", "mode", "timestamp", "level", "passed","failed","executed","score"])
    result_file.writeheader()

    for date in dirlist:
        model_list = os.listdir(os.path.join(result_output_path, date))
        for model in model_list:
            for mode in ("cascade", "direct"):
                dirpath = os.path.join(result_output_path, date, model, mode)
                if not os.path.exists(dirpath):
                    print(f"Skip {dirpath}.")
                    continue
                file_group = extract_json_files_from_folder(dirpath, mode=True)
                for group in file_group:
                    if dolist_para and str(group) not in dolist:
                        continue
                    try:
                        level = int(str(group).split("_")[3])
                        if mode == "cascade" and level == "3":
                            print("Skip cascade level 3")
                            continue
                        tester = JudgeController(question_path="data/project_eval_project.json",
                                                 answer_path=file_group[group]["answer_code_path"],
                                                 model_class=start_with_dict[model.split("-")[0]] if model.split("-")[0] in start_with_dict else OllamaTest,
                                                 parameter_file_path=file_group[group]["answer_parameter_path"],
                                                 llm=model,
                                                 device="GPU-e64683ee-8e58-13f4-b2aa-e88128cc3ef9",
                                                 )

                        tester.logger.info("Start:"+"-".join([date, model, mode, str(level)]))
                        initiate_command = {}
                        requirements = {}

                        # The following block is not within the scope of ProjectEval's selection.
                        # It allows the model to choose the library it likes to use and provide initial commands.
                        # The universality of this part of the code has not been fully tested, so please use and adapt it with caution.
                        for project_id in project_id_list:
                            if project_id not in (str(_) for _ in range(16, 20)):
                                # Website Initial
                                initiate_command[project_id] = [[]]
                                requirements[project_id] = ["django", "matplotlib", "pyperclip", "qrcode", "markdown"]
                            else:
                                # Console initial
                                initiate_command[project_id] = []
                                requirements[project_id] = ["openpyxl", "pandas"]

                        if "startfile" in group:
                            start_file_list = json.load(open(group["startfile"]))
                        else:
                            start_file_list = None
                        score, score_table = tester.evaluate(initiate_command, requirements, project_id_list=project_id_list,
                                        start_file_list=start_file_list)
                        data = {
                            "date": date,
                            "model": model,
                            "mode": mode,
                            "timestamp": str(group).split("_")[1],
                            "level": level,
                            "passed": score["pass"],
                            "failed": PROJECT_EVAL_DEFAULT_TEST_CASE - score["pass"],
                            "executed": score["testcase"] if "testcase" in score else 0,
                            "score": score["pass@1"] if "pass@1" in score else 0,
                        }
                        for key in data:
                            data[key] = str(data[key])
                        result_file.writerow(data)
                        file.flush()
                    except Exception as e:
                        print(e)



