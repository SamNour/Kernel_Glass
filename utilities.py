import subprocess
import re
import time
import os
import shutil
import pprint
import utilities
from query_sys import (
    x86_64_syscalls,
    find_c_cpp_files,
    syscall_hunter,
    searching_for_syscalls_in_headers,
    header_hunter,
    FOUND_SYSCALLS,
)
import click
import sys
import logging
from query_api import main as run_query_api


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


handler = logging.FileHandler("syscall-hunter.log")
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def execute_shell_locate_cmd(cmd):
    results = set()  # Initialize an empty set to store the results
    try:
        result = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if result.returncode == 0:
            output_string = result.stdout
            # Split the output into lines and add them to the set
            results.update(output_string.splitlines())
        else:
            error_message = result.stderr
            print("Error:", error_message)
    except Exception as e:
        print("An error occurred:", str(e))
    return results


import re


def grep_exact(word_to_find, file_path):
    result = {}
    try:
        with open(file_path, "r") as file:
            for line_number, line in enumerate(file, 1):
                # Exclude lines starting with " or /*
                if (
                    not line.strip().startswith('"')
                    and not line.strip().startswith("/*")
                    and not line.strip().startswith("*")
                    and not line.strip().startswith("//")
                ):
                    if re.search(rf"\b{re.escape(word_to_find)}\b", line):
                        result[line_number] = line.strip()
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")

    return result


def find_line_number_in_c_cpp(c_cpp, syscall):
    res = {}
    if not c_cpp:
        print("Not found")
        return
    if isinstance(c_cpp, set):
        for file in c_cpp:
            output = grep_exact(syscall, file)
            if output:
                result_str = f"{syscall} is found in file {file}"
                res[result_str] = output

    elif isinstance(c_cpp, set):
        output = grep_exact(syscall, c_cpp)
        if output:
            result_str = f"{syscall} is found in file {c_cpp}"
            res[result_str] = output
    return res


def pretty_dots(sentence, num_dots):
    print(sentence, end="", flush=True)
    for _ in range(num_dots):
        print(".", end="", flush=True)
        time.sleep(0.1)
    print()


def clear_or_create_directory(output):
    os.system("rm *.log")
    if os.path.exists(output):
        shutil.rmtree(output)
        os.mkdir(output)
        print(f"* Directory '{output}' cleared and recreated.")
    else:
        os.mkdir(output)
        print(f"* Directory '{output}' created.")


def setup_repository_list(mrepo) -> list:
    repo_list = []
    for d in os.listdir(mrepo):
        if os.path.isdir(os.path.join(mrepo, d)):
            repo_list.append(d)
    return repo_list


"TODO: FIX ME! "


def paths(output, repo_name):
    path_header = os.path.join(output, f"Headers_{repo_name}.txt")
    path_syscall_perfile = os.path.join(
        output, f"syscalls_per_file_output_{repo_name}.txt"
    )

    path_find_lines = os.path.join(output, f"line_number_output_{repo_name}.txt")
    path_echo = os.path.join(output, f"user_output_{repo_name}.txt")
    path_api = os.path.join(output, f"api_output_{repo_name}.txt")
    return path_header, path_syscall_perfile, path_find_lines, path_echo, path_api


def repo_analyse(repo_name, mrepo, echo, dev_echo, output, compiler):
    repo_output_folder = os.path.join(
        output, os.path.basename(repo_name).replace(" ", "_")
    )
    os.mkdir(repo_output_folder)
    print(f"os.mkdir{repo_output_folder}")
    repo_path = os.path.join(mrepo, repo_name)
    (
        path_header,
        path_syscall_perfile,
        path_find_lines,
        path_echo,
        path_api,
    ) = utilities.paths(output, repo_name)
    path_header = path_header.replace(" ", "_")
    path_echo = path_echo.replace(" ", "_")
    path_find_lines = path_find_lines.replace(" ", "_")
    path_syscall_perfile = path_syscall_perfile.replace(" ", "_")
    path_api = path_api.replace(" ", "_")

    print(f"* Path of the repository being analysed {repo_path}.")
    if os.path.exists(repo_path):
        print("xxxxxxxxxx")
        run_query_api(path_api, repo_output_folder)
        # print(f"os.system(mv {path_api} {repo_output_folder}")
        # os.system(f"mv {path_api} {repo_output_folder}")

        repo_name = os.path.basename(repo_path)
        print(f"* Repository currently analysed {repo_path}.")

        # Create file paths
        utilities.pretty_dots("* Fetching required Information.", 2)
        utilities.pretty_dots(
            f"* Creating {output} directory containing all the debuggin Information.", 3
        )
        all_x86_64_syscalls, all_c_cpp_files = x86_64_syscalls(), find_c_cpp_files(
            repo_path
        )
        headers = header_hunter(all_c_cpp_files)
        # ! find_c_cpp_files(),

        tmp_lst = []

        with click.progressbar(
            all_c_cpp_files,
            label="Finding c and cpp files",
            length=len(all_c_cpp_files),
        ) as bar:
            for files in bar:
                tmp_lst.append(files)
        print(f"* All C/CPP files found. ")
        pprint.pprint(tmp_lst)
        if echo:
            tmp_lst = []
            logger.info("Finding which syscall is found in which header...")

            with open(path_echo, "a") as file:
                syscalls_headers_dict = searching_for_syscalls_in_headers(
                    all_x86_64_syscalls, header_hunter(all_c_cpp_files), compiler
                )
                pprint.pprint(syscalls_headers_dict, file)
                print(f"os.system(mv {path_echo} {repo_output_folder}")
                os.system(f"mv {path_echo} {repo_output_folder}")
        if dev_echo:
            logger.info("\r* Working hard, please be patient!")
            tmp_lst = []

            with click.progressbar(syscalls_headers_dict.keys()) as bar:
                for key in bar:
                    tmp_lst.append(
                        utilities.find_line_number_in_c_cpp(all_c_cpp_files, key)
                    )

            headers = header_hunter(all_c_cpp_files)
            with open(path_header, "w") as file:
                pprint.pprint(headers, file)
            print(f"os.system(mv {path_header} {repo_output_folder}")
            os.system(f"mv {path_header} {repo_output_folder}")
            for files in all_c_cpp_files:
                syscall_hunter(all_x86_64_syscalls, files)
                sys.stdout.write(f"[  ] System calls found in the  {files}         ")
                sys.stdout.flush()
                sys.stdout.write(f"\r[OK] System calls found in the  {files} \n")
                sys.stdout.flush()
                with open(path_syscall_perfile, "a") as file:
                    file.write("\n")
                    pprint.pprint(
                        f"        #######################################################",
                        file,
                    )
                    pprint.pprint(f"System calls found in the  {files}", file)
                    pprint.pprint(
                        f"""      ########################################################""",
                        file,
                    )
                    file.write("\n")
                    pprint.pprint(FOUND_SYSCALLS, file)
                FOUND_SYSCALLS.clear()
            print(f"os.system(mv {path_syscall_perfile} {repo_output_folder}")

            os.system(f"mv {path_syscall_perfile} {repo_output_folder}")

            with open(path_find_lines, "w") as file:
                pprint.pprint(tmp_lst, file)
                # pprint.pprint(tmp_lst)
            print(f"os.system(mv {path_find_lines} {repo_output_folder}")
            os.system(f"mv {path_find_lines} {repo_output_folder}")
            logger.info(f"User information is saved in {repo_output_folder}")
            logger.info(
                f"Information about which API calls are in specific C/C++ files is saved in {repo_output_folder}"
            )
            logger.info(
                f"Header names in the C/C++ files are saved in {repo_output_folder}"
            )
            logger.info(
                f"Developer debugging information is saved in {repo_output_folder}"
            )
        else:
            logger.error(f"No data found in {repo_path}")
