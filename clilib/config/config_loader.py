from clilib.util.decorators import deprecated
from clilib.util.dict import SearchableDict, dict_path
from clilib.util.util import SchemaValidator, Util
from pathlib import Path
from clilib.config.config import Config
import re
import json
import yaml


class ConfigurationFile:
    """
    Configuration File base class
    """
    def __init__(self, config_path: str, schema: dict = None, schema_strict: bool = False, auto_create: dict = None, write_on_set: bool = False):
        """
        Load a configuration file from a path.
        :param config_path: Path to configuration file
        :param schema: Validation schema for validating loaded config. This is optional
        :param schema_strict: Schema validation is strict, failing if keys are missing from loaded config
        :param auto_create: Dictionary of defaults for auto creation, or None
        :param write_on_set: Boolean value which tells object whether to write to disk when a value in the config is changed.
        """
        self.path = Path(config_path)
        self._config_data = SearchableDict()
        self._schema = schema
        self._schema_strict = schema_strict
        self._validator = None
        self._auto_create = auto_create
        self._write_on_set = write_on_set
        if self._schema is not None:
            self._validator = SchemaValidator(self._schema, self._schema_strict)
        self._load_file()

    def _load_config(self):
        raise NotImplementedError("You must implement this method")

    def __call__(self, path: str):
        return self._config_data.get_path(path)

    def __contains__(self, item):
        return item in self._config_data

    def __getitem__(self, item):
        return self._config_data.get_path(item)

    def __setitem__(self, item, value):
        config_data = SearchableDict(self._config_data.copy())
        config_data.set_path(item, value)
        if self._validator is not None:
            self._validator.validate(config_data)
        self._config_data = config_data
        if self._write_on_set:
            self.write()
    
    def __delitem__(self, key):
        if key in self._config_data:
            del self._config_data[key]
            if self._write_on_set:
                self.write()

    def reload(self):
        self._load_config()

    def write(self):
        raise NotImplementedError("You must implement this method")


class INIConfigurationFile(ConfigurationFile):
    """
    Load INI configuration file from disk, use auto_create if not None and file does not exist. Note that writing configuration files with this
    class will not retain comments.
    :param config_path: Path to configuration file
    :param schema: Validation schema for validating loaded config. This is optional
    :param schema_strict: Schema validation is strict, failing if keys are missing from loaded config
    :param auto_create: Dictionary of defaults for auto creation, or None
    :param write_on_set: Boolean value which tells object whether to write to disk when a value in the config is changed.
    """

    def _parse_file(self, file_data):
        data_lines = file_data.splitlines()
        current_section = None
        parsed_data = SearchableDict()
        for line in data_lines:
            if re.match(r"^;.*|^#.*", line):
                continue
            elif re.match(r"^\[([a-zA-Z0-9\._]*)\]", line):
                section_name = re.findall(r"^\[([a-zA-Z0-9\._]*)\]", line)
                if len(section_name) > 0:
                    new_current_section = section_name[0]
                    if new_current_section.startswith("."):
                        current_section = "%s.%s" % (current_section, new_current_section)
                    else:
                        current_section = new_current_section
            else:
                if current_section is not None:
                    key_value = re.findall(r"^([a-zA-Z0-9_]*)\s+=\s+(.*)", line)
                    if len(key_value) > 0:
                        key = key_value[0][0]
                        value = key_value[0][1]
                        path = "%s.%s" % (current_section, key)
                        parsed_data.set_path(path, value)
                else:
                    key_value = re.findall(r"^([a-zA-Z0-9_]*)\s+=\s+(.*)", line)
                    if len(key_value) > 0:
                        key = key_value[0][0]
                        value = key_value[0][1]
                        parsed_data.set_path(key, value)
        return parsed_data

    def _load_file(self):
        try:
            with open(self.path, 'rb') as f:
                config_data = f.read().decode()
                config_data = self._parse_file(config_data)
                if self._validator is not None:
                    self._validator.validate(config_data)
                self._config_data = SearchableDict(config_data)
        except FileNotFoundError as e:
            if self._auto_create is not None:
                config_data = self._auto_create.copy()
                if self._validator is not None:
                    self._validator.validate(config_data)
                self._config_data = SearchableDict(config_data)
                self._config_path.parent.mkdir(parents=True, exist_ok=True)
                self.write()
            else:
                raise e

    def _dump_dict(self, data: dict):
        output = ""
        for k, v in data.items():
            if isinstance(v, dict):
                output += "[.%s]\n" % k
                output += self._dump_dict(v)
            elif isinstance(v, (str, int, float)):
                output += "%s = %s\n" % (k, v)
            else:
                raise TypeError("Unsupported type %s" % type(v))
        return output

    def dump(self):
        """
        Dump configuration to file
        """
        final = ""
        for k, v in self._config_data.items():
            if isinstance(v, dict):
                final += "[%s]\n" % k
                final += self._dump_dict(v)
            elif isinstance(v, (str, int, float)):
                new_final = "%s = %s\n" % (k, str(v))
                new_final += final
                final = new_final
            else:
                raise TypeError("Unsupported ini value type: %s" % type(v))
        return final

    def write(self):
        with open(self.path, 'w') as f:
            final_data = self.dump()
            f.write(final_data)


class JSONConfigurationFile(ConfigurationFile):
    """
    Load JSON configuration file from disk, use auto_create if not None and file does not exist.
    :param config_path: Path to configuration file
    :param schema: Validation schema for validating loaded config. This is optional
    :param schema_strict: Schema validation is strict, failing if keys are missing from loaded config
    :param auto_create: Dictionary of defaults for auto creation, or None
    :param write_on_set: Boolean value which tells object whether to write to disk when a value in the config is changed.
    """
    def _load_file(self):
        try:
            with open(self.path, 'rb') as f:
                config_data = json.load(f)
                if self._validator is not None:
                    self._validator.validate(config_data)
                self._config_data = SearchableDict(config_data)
        except FileNotFoundError as e:
            if self.__auto_create is not None:
                config_data = self.__auto_create.copy()
                if self._validator is not None:
                    self._validator.validate(config_data)
                self._config_data = SearchableDict(config_data)
                self._config_path.parent.mkdir(parents=True, exist_ok=True)
                self.write()
            else:
                raise e

    def write(self):
        with open(self.path, 'w') as f:
            json.dump(self._config_data, f)


class YAMLConfigurationFile(ConfigurationFile):
    """
    Load YAML configuration file from disk, use auto_create if not None and file does not exist.
    :param config_path: Path to configuration file
    :param schema: Validation schema for validating loaded config. This is optional
    :param schema_strict: Schema validation is strict, failing if keys are missing from loaded config
    :param auto_create: Dictionary of defaults for auto creation, or None
    :param write_on_set: Boolean value which tells object whether to write to disk when a value in the config is changed.
    """
    class NoAliasDumper(yaml.SafeDumper):
        def ignore_aliases(self, data):
            return True

    def _load_file(self):
        try:
            with open(self.path, 'rb') as f:
                config_data = yaml.safe_load(f)
                if self._validator is not None:
                    self._validator.validate(config_data)
                self._config_data = SearchableDict(config_data)
        except FileNotFoundError as e:
            if self._auto_create is not None:
                config_data = self._auto_create.copy()
                if self._validator is not None:
                    self._validator.validate(config_data)
                self._config_data = SearchableDict(config_data)
                self._config_path.parent.mkdir(parents=True, exist_ok=True)
                self.write()
            else:
                raise e

    def write(self):
        with open(self.path, 'w') as f:
            f.write(yaml.dump(dict(self._config_data), Dumper=YAMLConfigurationFile.NoAliasDumper))
