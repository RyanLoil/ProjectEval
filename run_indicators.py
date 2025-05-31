import argparse
import csv
import datetime
import json
import os

from config import PROJECT_EVAL_DEFAULT_ANSWER_PATH, PROJECT_EVAL_DEFAULT_DATA_PATH, PROJECT_EVAL_DEFAULT_PARAMETER_PATH
from controller import IndicatorController
from utils import extract_json_files_from_folder

parser = argparse.ArgumentParser()
parser.add_argument("-r", "--dirlist", type=str, required=True,
                    help="The directories that you want to evaluate. The directories must obey the rule of /directory_name/model_name/cascade(direct)/<model>_<timestamp>_level_<level>.json. Official-result is a good example.")
parser.add_argument("-d", "--dolist", type=str, required=False, default="[]", )
parser.add_argument("--dolist_para", action="store_true")

args = parser.parse_args()
dirlist = json.loads(args.dirlist)
dolist = set(json.loads(args.dolist))
dolist_para = args.dolist_para

result_output_path = "experiments/"
file = open(result_output_path + f"objective-indicators-result-{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.csv", "w", encoding="utf-8", newline="")
result_file = csv.DictWriter(
    file, delimiter=",",
    fieldnames=["date", "model", "mode", "timestamp", "level", "checklist", "skeleton", "code", "parameter"])
result_file.writeheader()
for date in dirlist:
    model_list = os.listdir(os.path.join(result_output_path, date))
    for model in model_list:
        for mode in ("cascade", "direct"):
            dirpath = os.path.join(result_output_path, date, model, mode)
            if not os.path.exists(dirpath):
                print(f"Directory {dirpath} doesn't exist. Skipping.")
                continue

            file_group = extract_json_files_from_folder(dirpath)
            for group in file_group:
                timestamp = str(group).split("_")[1]
                level = int(str(group).split("_")[3])
                controller = IndicatorController(
                    verbose_name=str(group),
                    reference_code_path=PROJECT_EVAL_DEFAULT_ANSWER_PATH,
                    reference_project_path=PROJECT_EVAL_DEFAULT_DATA_PATH,
                    reference_parameter_path=PROJECT_EVAL_DEFAULT_PARAMETER_PATH,
                    report_file_path=result_output_path + f"/{date}/{model}/{mode}/{str(group)}-{timestamp}-objective_indicators_reports.txt",
                    **file_group[group]
                )
                controller.logger.info(f"Start {group}.")
                score, score_table = controller.run([f"{_}" for _ in range(1, 21)],
                                       checklist=True if level==1 and mode=="cascade" else False,
                                       skeleton=True if level<=2 and mode=="cascade" else False,
                                       )
                data = {
                    "date": date,
                    "model": model,
                    "mode": mode,
                    "timestamp": timestamp,
                    "level": level,
                    **score,
                }
                for key in data:
                    data[key] = str(data[key])
                result_file.writerow(data)
                file.flush()