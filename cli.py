import utilities
import time
import click
import logging
import multiprocessing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


handler = logging.FileHandler("syscall-hunter.log")
handler.setLevel(logging.INFO)
logger.addHandler(handler)


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--mrepo",
    required=True,
    type=click.Path(exists=True),
    show_default=True,
    help="[Relative path] File containing a list of repositories to be analysed. This option is mandatory.",
)
@click.option(
    "--compiler",
    required=True,
    type=click.Path(exists=True),
    show_default=True,
    help="Location where the syscall-hunter will look for header files GNU/Linux.",
)
@click.option(
    "--output",
    required=True,
    type=str,
    show_default=True,
    help="[Relative path] Directory where the output files will be created. This option is mandatory.",
)
@click.option(
    "--echo",
    is_flag=True,
    default=True,
    help="Echo the result. Use --no-echo to suppress output.",
)
@click.option("--t", is_flag=True, default=False, help="Activates multiprocessing.")
@click.option(
    "--dev-echo",
    is_flag=True,
    default=True,
    help="Echo debugging information for debugging purposes.",
)
@click.option(
    "--api",
    required=True,
    is_flag=True,
    default=True,
    help="Extracting all the api call from your source code and outputs it in output.txt",
)
def run(mrepo, echo, t, dev_echo, output, compiler, api) -> dict:
    """
    Analyzes a software repository with various options. You need to specify
    the relative path of the repository to be analyzed and the output directory.

    \b
    This CLI tool performs the following steps:
        1.Retrieves a list of all available x86_64 system calls.
        2.Finds and lists all the source files (.c or .cpp) in the given repository.
        3.For each source file, identifies and lists the system calls found in that file.
        4.Searches for header files used in the source files and locates their locations.
        5.identifies which system calls are used in which headers.
        6.finds the line numbers in the source files where each used system call is called.

    \b
    Parameters:
        --mrepo: Path to a file containing a list of repositories to be analyzed.
        --output: The directory where output files will be created (mandatory).
        --database (-d): Specify the database location to fetch the kernel API calls for analysis (default: 'strace_calls.txt').
        --echo: Echo the results (use --no-echo to suppress output).
        --dev-echo: Echo debugging information for debugging purposes.
        --show-c-cpp: Echo the names of all the C or C++ files to be analyzed by syscall hunter in this instance.
        --compiler: Choose the location where the syscall-hunter will look for header files (spd: QNX, spk: GNU/Linux).
        --t: activate multiprocessing.
    \b
    Returns:
        --A files containing the results of the analysis, the f/opt/rta-vrte-linux/3.8.0/sysroots/aarch64-boschdenso-linux/usr/include/
    \b
    Example usage:
        --$ ./syscall_hunter.py  --output=/relative/path//output --mrepo=/relative/path/repo --compiler=/relative/path/compiler
    """
    start_time = time.time()  # Record the start time

    try:
        utilities.clear_or_create_directory(output)
        repo_list = utilities.setup_repository_list(mrepo)

        if not repo_list:
            logger.error(f"* The directory specified MUST have one or more repos.")
            exit(0)

        print(f"* All the files that will be analysed {repo_list}.")

        if t and click.confirm(
            "\n* Running a multiprocess instance will speed up the analysis, but will distort the standard output.\n"
            "  This will not affect the output files. Do you want to continue?"
        ):
            with multiprocessing.Pool() as pool:
                pool.starmap(
                    utilities.repo_analyse,
                    [
                        (repo_name, mrepo, echo, dev_echo, output, compiler)
                        for repo_name in repo_list
                    ],
                )
        else:
            for repo_name in repo_list:
                utilities.repo_analyse(
                    repo_name, mrepo, echo, dev_echo, output, compiler
                )

    except Exception as e:
        logger.error(f"An error occurred in the backend: {e}")

    execution_time = time.time() - start_time
    print(f"Exiting...\nTime elapsed: {execution_time} seconds.")


if __name__ == "__main__":
    "./syscall_hunter.py  --output=./delete --mrepo=./directories --compiler=/opt/rta-vrte-linux/3.8.0/sysroots/aarch64-boschdenso-linux/usr/include/"
    cli_output = run()
