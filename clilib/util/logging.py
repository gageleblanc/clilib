import json
import logging
from pathlib import Path
from clilib.config.config_loader import ConfigLoader


class Logging:
    def __init__(self, log_name: str, log_desc: str = None, log_fmt: str = '[%(asctime)s][%(name)s]LOGDESC[%(levelname)8s] - %(message)s', console_log: bool = True, file_log: bool = False, file_log_location: str = "/var/log", file_log_mode: str = 'a+', debug: bool = False):
        self.name = log_name
        self._debug = debug
        self._log_suffix = log_desc
        self._log_dir = Path(file_log_location)
        self._log_filename = self._log_dir.joinpath("%s.log" % self.name)
        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(logging.INFO)
        self._config = self._get_logging_config()
        if self._config is not None:
            if "debug" in self._config.get_dict():
                self._debug = self._config.debug
            if "log_dir" in self._config.get_dict():
                self._log_dir = self._config.log_dir
            if "log_to_file" in self._config.get_dict():
                file_log = self._config.log_to_file
            if "console_log" in self._config.get_dict():
                console_log = self._config.console_log
        if log_desc is not None:
            self._format = log_fmt.replace("LOGDESC", "[%s]" % log_desc)
        else:
            self._format = log_fmt.replace("LOGDESC", "")
        self._log_formatter = logging.Formatter(fmt=self._format)
        self._log_file_mode = file_log_mode
        if console_log:
            self._configure_console_handler()
        if file_log:
            self._configure_file_handler()

    def get_logger(self):
        return self._logger

    def _get_logging_config(self):
        global_config_path = Path("/etc/clilib/config/logging.json")
        user_config_path = Path.home().joinpath(".config").joinpath("clilib").joinpath("logging.json")
        global_config = {}
        user_config = {}
        try:
            with open(str(global_config_path)) as gc:
                global_config = json.loads(gc.read())
        except Exception as e:
            if self._debug:
                self._logger.warning("Skipping global logging config due to error: %s" % str(e))
        try:
            with open(str(user_config_path)) as uc:
                user_config = json.loads(uc.read())
        except Exception as e:
            if self._debug:
                self._logger.warning("Skipping user logging config due to error: %s" % str(e))
        try:
            config = ConfigLoader(config={**global_config, **user_config}, schema={"debug": bool, "log_to_file": bool, "log_dir": str, "console_log": bool}, from_obj=True).get_config()
        except Exception as e:
            config = None
            if self._debug:
                self._logger.warning("Skipping logging config due to error: %s" % str(e))

        return config

    def _configure_console_handler(self):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self._log_formatter)
        if self._debug:
            self._logger.setLevel(logging.DEBUG)
            console_handler.setLevel(logging.DEBUG)
        self._logger.addHandler(console_handler)

    def _configure_file_handler(self):
        file_handler = logging.FileHandler(self._log_filename, self._log_file_mode)
        file_handler.setFormatter(self._log_formatter)
        self._logger.addHandler(file_handler)
