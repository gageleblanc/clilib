from asyncio import subprocess
from clilib.util.logging import Logging
from clilib.builders.app import EasyCLI
from pathlib import Path
import subprocess
import distutils.core
import shutil
import json
import os


class WheelUtils:
    """
    Various utilities for inspecting python projects
    """
    def __init__(self, debug: bool = False, working_directory: str = None):
        """
        :param debug: Add additional debugging output
        :param working_directory: Directory of project to inspect. Default is the same directory this script is run from.
        """
        if working_directory is None:
            working_directory = os.getcwd()
        self.working_directory = Path(working_directory)
        self.logger = Logging("WheelUtils", debug=debug).get_logger()
        setup_path = self.working_directory.joinpath("setup.py")
        self._setup = distutils.core.run_setup(str(setup_path))

    def build_archive(self, python_executable: str = None, pip_executable: str = None):
        """
        Build archive of current project and it's requirements, installable locally without internet.
        :param python_executable: Python executable to use for building wheel. Default is python3
        :param pip_executable: Path to pip executable. Default is pip3.
        """
        output_path = self.working_directory.joinpath("dist")
        self.build_wheel(python_executable)
        self.fetch_requirements(output=str(output_path), pip_executable=pip_executable)
        archive_path = self.working_directory.joinpath("%s_with_requirements" % self._setup.get_name())
        self.logger.info("Creating archive at [%s.zip]" % str(archive_path))
        shutil.make_archive(str(archive_path), 'zip', str(output_path))

    def build_wheel(self, python_executable: str = None):
        """
        Build wheel from setup.py in working directory
        :param python_executable: Python executable to use for building wheel. Default is python3
        """
        if python_executable is None:
            python_executable = "python3"
        self.logger.info("Building wheel from setup.py ...")
        command = [python_executable, "setup.py", "bdist_wheel"]
        self.logger.debug("Running command: [%s]" % " ".join(command))
        subprocess.run(command, cwd=str(self.working_directory))

    def fetch_requirements(self, output: str = None, pip_executable: str = None):
        """
        Fetch install requirements to specified output directory.
        :param output: Directory to output downloaded requirements to. Default is ./reqs
        :param pip_executable: Path to pip executable. Default is pip3.
        """
        if pip_executable is None:
            pip_executable = "pip3"
        if output is None:
            output = self.working_directory.joinpath("reqs")
        else:
            output = Path(output)
            output.mkdir(exist_ok=True, parents=True)
        for req in self._setup.install_requires:
            self.logger.info("Attempting to download [%s] with pip" % req)
            command = [pip_executable, "download", req, "--dest", str(output)]
            self.logger.debug("Pip command: [%s]" % " ".join(command))
            subprocess.run(command, cwd=str(self.working_directory))

    def show_requirements(self):
        """
        Return install requirements as json
        """
        print(json.dumps(self._setup.install_requires))


def cli():
    EasyCLI(WheelUtils)
