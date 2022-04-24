import json
import logging
from pathlib import Path


class Logging:
    """
    Set up and return a logging object based on given arguments
    """
    def __init__(self, log_name: str, log_desc: str = None, log_fmt: str = '[%(asctime)s][%(name)s][%(levelname)8s] - %(message)s', console_log: bool = True, file_log: bool = False, file_log_location: str = "/var/log", file_log_mode: str = 'a+', app_name: str = None, debug: bool = False, logging_level: str = None):
        """
        :param log_name: Name of log
        :param log_desc: Optional description to include after log name
        :param log_fmt: Optional format to specify for logging output.
        :param console_log: Output logging to console. Default is True
        :param file_log: Output logging to file. Default is False
        :param file_log_location: Optional location of file log. Default is /var/log. This is only relevant if file_log is True
        :param file_log_mode: Optional file mode to open logfile as. Default is a+. This is only relevant if file_log is True
        :param app_name: Optional value used to determine logging configuration location. If left unset, it is generated based on log name and log description.
        :param debug: Enable debugging. Default is false.
        """
        self.name = log_name
        self.logging_level = logging_level
        if self.logging_level is not None:
            if isinstance(self.logging_level, str):
                self.logging_level = self.logging_level.upper()
            else:
                # Should probably just gracefully handle this instead of throwing exception
                # raise TypeError("logging_level must be a string")
                self.logging_level = None
        if log_desc is not None:
            self.name = "%s][%s" % (log_name, log_desc)
        if app_name is not None:
            self._app_name = app_name
        else:
            self._app_name = self.name.lower().replace("][", "_")
        self._debug = debug
        self._log_suffix = log_desc
        self._log_dir = Path(file_log_location)
        path_name = self.name.replace("][", "/")
        self._log_filename = self._log_dir.joinpath("%s.log" % path_name)
        if file_log:
            self._log_filename.parent.mkdir(exist_ok=True, parents=True)
        self._logger = logging.getLogger(self.name)
        if not self._logger.hasHandlers():
            self._logger.setLevel(logging.INFO)
            self._config = self._get_logging_config()
            if self._config is not None:
                if "debug" in self._config:
                    self._debug = self._config["debug"]
                if "log_dir" in self._config:
                    self._log_dir = Path(self._config["log_dir"])
                    self._log_filename = self._log_dir.joinpath("%s.log" % self.name)
                if "log_to_file" in self._config:
                    file_log = self._config["log_to_file"]
                if "console_log" in self._config:
                    console_log = self._config["console_log"]
            self._log_formatter = logging.Formatter(fmt=log_fmt)
            self._log_file_mode = file_log_mode
            if console_log:
                self._configure_console_handler()
            if file_log:
                self._configure_file_handler()

    def get_logger(self):
        """
        Return logging object from configuration passed to init.
        :return: Logger
        """
        return self._logger

    def _get_logging_config(self):
        global_config_path = Path("/etc/clilib/config").joinpath(self._app_name).joinpath("logging.json")
        user_config_path = Path.home().joinpath(".config").joinpath("clilib").joinpath(self._app_name).joinpath("logging.json")
        config = {}

        if global_config_path.exists():
            with open(str(global_config_path)) as gc:
                config.update(json.loads(gc.read()))

        if user_config_path.exists():
            with open(str(user_config_path)) as uc:
                config.update(json.loads(uc.read()))

        return config

    def _configure_console_handler(self):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self._log_formatter)
        if self._debug:
            self._logger.setLevel(logging.DEBUG)
            console_handler.setLevel(logging.DEBUG)
        if self.logging_level:
            self._logger.setLevel(getattr(logging, self.logging_level))
            console_handler.setLevel(getattr(logging, self.logging_level))
        self._logger.addHandler(console_handler)

    def _configure_file_handler(self):
        file_handler = logging.FileHandler(self._log_filename, self._log_file_mode)
        file_handler.setFormatter(self._log_formatter)
        self._logger.addHandler(file_handler)

    # needs to be staticmethod so that its used before logging is initialized 
    @staticmethod
    def add_logging_level(levelName, levelNum = (logging.DEBUG - 1), methodName = None):
        """
        https://stackoverflow.com/a/35804945/14578858
        Comprehensively adds a new logging level to the `logging` module and the
        currently configured logging class.

        `levelName` becomes an attribute of the `logging` module with the value
        `levelNum`. `methodName` becomes a convenience method for both `logging`
        itself and the class returned by `logging.getLoggerClass()` (usually just
        `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
        used.

        To avoid accidental clobberings of existing attributes, this method will
        raise an `AttributeError` if the level name is already an attribute of the
        `logging` module or if the method name is already present 

        Example
        -------
        >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
        >>> logging.getLogger(__name__).setLevel("TRACE")
        >>> logging.getLogger(__name__).trace('that worked')
        >>> logging.trace('so did this')
        >>> logging.TRACE
        5

        """
        if not methodName:
            methodName = levelName.lower()

        if hasattr(logging, levelName):
            raise AttributeError('{} already defined in logging module'.format(levelName))
        if hasattr(logging, methodName):
            raise AttributeError('{} already defined in logging module'.format(methodName))
        if hasattr(logging.getLoggerClass(), methodName):
            raise AttributeError('{} already defined in logger class'.format(methodName))

        # This method was inspired by the answers to Stack Overflow post
        # http://stackoverflow.com/q/2183233/2988730, especially
        # http://stackoverflow.com/a/13638084/2988730
        def logForLevel(self, message, *args, **kwargs):
            if self.isEnabledFor(levelNum):
                self._log(levelNum, message, args, **kwargs)
        def logToRoot(message, *args, **kwargs):
            logging.log(levelNum, message, *args, **kwargs)

        logging.addLevelName(levelNum, levelName)
        setattr(logging, levelName, levelNum)
        setattr(logging.getLoggerClass(), methodName, logForLevel)
        setattr(logging, methodName, logToRoot)
