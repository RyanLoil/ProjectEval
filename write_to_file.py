import json
import os
import shutil


def _to_file(file_name: str, content: str):
    last_slash = file_name.rfind("/")
    if last_slash != -1:
        dirpath = file_name[:last_slash]
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)
    with open(file_name, 'w', encoding="utf-8") as f:
        f.write(content)
        f.close()


def write_to_file(data_path: str, output_path: str):
    data = json.load(open(data_path, 'r', encoding="utf-8"))
    for source in data:
        if os.path.exists(output_path + source + "/"):
            shutil.rmtree(output_path + source + "/")
        os.makedirs(output_path + source + "/")
        for file in data[source]:
            _to_file(output_path + source + "/" + file['path'], file['code'])

if __name__ == '__main__':
    data_path = 'data/操作版本/skeletongpt-4o_20250122-215803.json'
    output_path = 'test/project_2/'
    write_to_file(data_path, output_path)