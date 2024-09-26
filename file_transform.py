import os
import json


def get_files(directory):
    """
    Get all files in the given directory recursively.
    :param directory: The root directory to start from.
    :return: List of file paths.
    """
    files_list = []
    for root, _, files in os.walk(directory):
        if root.split("/")[-1] == "migrations":
            continue
        for file in files:
            if file.split('.')[-1] == 'sqlite3':
                continue
            file_path = os.path.join(root, file)
            files_list.append(file_path)
    return files_list


def file_to_json(file_path, base_directory):
    """
    Convert a file's content into a JSON-compatible format.
    :param file_path: Path to the file.
    :param base_directory: The base directory to determine the relative path.
    :return: Dictionary representing the file's information.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        print(file_path, " is not a valid file.")
        return None

    relative_path = os.path.relpath(file_path, base_directory)

    return {
        "file": os.path.basename(file_path),
        "path": relative_path.replace("\\", "/"),
        "code": code
    }


def project_to_json(directory):
    """
    Convert an entire project directory into a JSON structure.
    :param directory: The root directory of the project.
    :return: List of dictionaries representing each file.
    """
    files = get_files(directory)
    result = []
    for file in files:
        json_str = file_to_json(file, directory)
        if json_str:
            result.append(json_str)
    return result


def save_json(data, output_file):
    """
    Save the JSON data to a file.
    :param data: The JSON data to save.
    :param output_file: The output file path.
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


if __name__ == "__main__":
    all_project_directory = "test/20240925-人工修正/"  # Set your project directory here
    output_file = "data/操作版本/answer-4.json"
    json_data = {}
    index = 4
    for directory in os.listdir(all_project_directory):
        if int(directory) < index:
            continue
        if len(os.listdir(os.path.join(all_project_directory, directory))) == 1:
            project_directory = os.path.join(all_project_directory, directory) + "/" + \
                                os.listdir(os.path.join(all_project_directory, directory))[0]
        else:
            project_directory = os.path.join(all_project_directory, directory)
        json_data[str(index)] = project_to_json(project_directory)
        index += 1
    save_json(json_data, output_file)

    print(f"Project files saved to {output_file}")
