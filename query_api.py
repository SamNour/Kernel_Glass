from collections import deque
from pygments.lexers import CLexer, CppLexer
from pygments.token import Name
import subprocess
import re
import os
from tqdm import tqdm
import click


API_CALLS = []

def get_c_cpp_files(root_dir):
    c_files = []
    cpp_files = []

    for dirpath, _, filenames in os.walk(
            root_dir
            ):
        for filename in filenames:
            if filename.endswith(".c"):
                c_files.append(os.path.join(dirpath, filename))
            elif filename.endswith(".cpp"):
                cpp_files.append(os.path.join(dirpath, filename))
    return c_files if c_files else cpp_files


def extract_functions_from_code(code, language):
    lexer = CppLexer() if language == "C++" else CLexer()
    tokens = lexer.get_tokens(code)
    functions = [tok[1] for tok in tokens if tok[0] in Name]
    functions_1 = [tok[1] for tok in tokens if tok[0] == Name.Function]
    return list(set(functions).union(set(functions_1)))


def remove_items(test_list, items):
    res = list(filter((items).__ne__, test_list))
    return res


def get_false_pos() -> list():
    command = r"grep -Pzo '\^\^ \w+\nSymbol Definitions:\n\nSymbol References:\n\nDocumented in:\n' /home/nos1abt/py-test/output.txt"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    f_pos = output.decode()
    if error:
        print(f"Error: {error}")
    else:
        pattern = r"\^\^ (\w+)"
        matches = re.findall(pattern, f_pos)
        # pprint.pprint(matches) # for debugging purposes
        return matches


def API_Calls_hunter(language):
    MACROS = []
    functions = []
    macro_pattern = re.compile(r"#define\s+(\w+)")
    functions
    for file in get_c_cpp_files("./repos/"):
        fdata = open(file, "r").read()
        matches = macro_pattern.findall(fdata)
        MACROS.extend(matches)
        functions.extend(extract_functions_from_code(fdata, language))

    MACROS = set(MACROS)
    functions = set(functions)
    with open("output.txt", "w") as file:
        for item in functions:
            if item not in MACROS:
                command = f"echo ^^ {item} ; /usr/local/elixir/query.py v4.10 ident {item} {language} ;  echo \n"
                subprocess.run(command, shell=True, stdout=file)


def remove_pattern_from_list(lst) -> list():
    i = 0
    FP = get_false_pos()
    for index, _ in enumerate(FP):
        FP[index] = f"^^ {FP[index]}\n"

    while i < len(lst) - 1:
        if (
            lst[i] == "Symbol References:\n"
            and lst[i + 1] == "\n"
            or lst[i] == "Symbol Definitions:\n"
            and lst[i + 1] == "\n"
            or lst[i] == "Documented in:\n"
            and lst[i + 1] == "\n"
        ):
            del lst[i : i + 2]
        elif lst[i] in FP:
            del lst[i : i + 1]
        else:
            i += 1
    return lst


def replace_lines_in_file(filename, path_api_output, repo_output_folder):
    with open(filename, "r") as file:
        lines = file.readlines()
        remove_pattern_from_list(lines)
    with open(path_api_output, "w") as file:
        file.writelines(lines)
    os.system(f"mv {path_api_output} {repo_output_folder}")



# def extract_api_calls_pos(path_api_output, repo_output_folder):
#     fpath = repo_output_folder +"/" + os.path.basename(path_api_output)

#     print(  fpath, "yyyyyyyyyyyyyyyyyyyyyyyyyyy")
    

#     with open(f'{fpath}', 'r') as file:
#         lines = file.readlines()
#         for item in lines:
#             if item.startswith("^^"):
#                 item = item.replace("^^", "")
#                 item = item.replace("\n", "")
#                 API_CALLS.append(item)
#     with open(f"{fpath}_APICALLS", "w") as file:
#         for i in API_CALLS:
#             file.write(i + "\n")
#     print(f"os.system(mv {path_api_output}_APICALLS {repo_output_folder}")
#     print(f"{path_api_output} ---------- {repo_output_folder} ---- {path_api_output}_APICALLS")

#     os.system(f"mv {API_CALLS} {repo_output_folder}")
#     return API_CALLS


# bsp-veth-linux/./delete/api_output_bsp-veth-linux.txt'
# os.path.basename(path_api_output) = bsp-veth-linux/
# repo_output_folder = ./delete/api_output_bsp-veth-linux.txt
def extract_words_and_types(repo_output_folder, path_api_output):
    output_dir = repo_output_folder.split("/")[1]
    file_name =  repo_output_folder.split("/")[2]
    fpath = output_dir +"/" + os.path.basename(path_api_output) + "/" + file_name
    print(  fpath, "yyyyyyyyyyyyyyyyyyyyyyyyyyy")

    with open(fpath, 'r') as file:
        lines = file.readlines()

    result = []
    word = None
    types = []
    for line in lines:
        if line.startswith("^^"):
            if word is not None:
                result.append((word, types))
            word = line.split("^^")[1].strip()
            types = set()
        else:
            type_match = re.search(r'type: (\w+)', line)
            if type_match:
                types.add(type_match.group(1))
    if word is not None:
        result.append((word, types))

    api_call_set_path = output_dir +"/" + os.path.basename(path_api_output) + "/" +  "APICALLS.txt"

    with open(f"{api_call_set_path}", 'w') as file:
        for i in result:
            file.write(str(i) + '\n')
    return result

def filer_final_api_calls( repo_output_folder, filter, api_list):
    api_call_set_path = repo_output_folder+ "/" +  "APICALLS_Filter.txt"

    with open(f"{api_call_set_path}", 'w') as file:
        for i in api_list:
            if 'function' in i[1]:
                file.write(str(i) + '\n')


def main(path_api_output, repo_output_folder):
    # print(path_api_output, repo_output_folder)
    # exit(0)
    with click.progressbar(length=1, label='Running API_Calls_hunter') as bar:
        API_Calls_hunter("C")
        bar.update(1)

    with click.progressbar(length=1, label='Running get_false_pos') as bar:
        get_false_pos()
        bar.update(1)

    with click.progressbar(
        length=1, 
        label='Running replace_lines_in_file') as bar:
        replace_lines_in_file("output.txt", path_api_output, repo_output_folder)
        bar.update(1)
    
    l = extract_words_and_types(
        path_api_output, 
        repo_output_folder)
    
    filer_final_api_calls(
        repo_output_folder, 
        "function", 
        l)

    os.system("rm output.txt")

# main()