from clilib.util.decorators import deprecated
from clilib.util.dict import SearchableDict, dict_path
from clilib.util.util import SchemaValidator, Util
from pathlib import Path
from clilib.config.config import Config
import re
import json
import yaml


@deprecated("You should use JSONConfigurationFile or YAMLConfigurationFile")
class ConfigLoader:
    def __init__(self, config, fmt="json", keys=None, auto_create=False, schema: dict = None, from_str: bool = False, from_obj: bool = False, schema_optional: bool = True):
        self.logger = Util.configure_logging(name=__name__)
        self.config_file = config
        self.format = fmt
        self.keys = keys
        self.auto_create = auto_create
        self.schema_optional = schema_optional
        self.schema = schema
        if not from_str and not from_obj:
            data = self._load_config()
            if schema is not None:
                self._validate_schema(data)
            if keys:
                self._validate_top_level(data)
            self.config = data
        if from_str:
            self.config_file = None
            data = json.loads(config)
            if schema is not None:
                self._validate_schema(data)
            if keys:
                self._validate_top_level(data)
            self.config = data
        if from_obj:
            self.config_file = None
            if schema is not None:
                self._validate_schema(config)
            if keys:
                self._validate_top_level(config)
            self.config = config

    def _validate_top_level(self, data):
        if len(self.keys.keys()) < 1:
            raise TypeError("Loaded config (%s) has no keys. Required keys are: %s"
                            % (self.config_file, ', '.join(self.keys.keys())))
        for key in self.keys.keys():
            if key not in data:
                raise TypeError("Loaded config (%s) missing required key \"%s\" from key list [%s]"
                                % (self.config_file, key, ', '.join(self.keys.keys())))

    def _validate_schema(self, data):
        if not self.schema_optional:
            for k in self.schema.keys():
                if k not in data:
                    raise TypeError("Missing required key [%s] from keys [%s]" % (k, ", ".join(data.keys())))
        for k, v in data.items():
            if k not in self.schema.keys():
                raise TypeError("Unexpected key [%s] in data" % k)
            ty = self.schema[k]
            if type(v) is not ty:
                raise TypeError("Value of [%s] should be type [%s]" % (k, str(ty.__name__)))
        return True

    def write_config_from_keys(self):
        new_config = {}
        for key, ty in self.keys.items():
            new_config[key] = ty()

        if self.format == "json":
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, ensure_ascii=False, indent=4)
        self.config = new_config

    def _load_config(self):
        if not Path(self.config_file).exists():
            if self.auto_create:
                self.write_config_from_keys()
            else:
                raise FileNotFoundError(self.config_file)

        if self.format == "json":
            with open(self.config_file) as f:
                return json.load(f)
        else:
            return {}

    def reload(self):
        data = self._load_config()
        if self.keys:
            self._validate_top_level(data)
        self.config = data
        return self.get_config()

    def get_config(self):
        return Config(self.config, self.config_file)


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
                if self.__validator is not None:
                    self.__validator.validate(config_data)
                self.__config_data = SearchableDict(config_data)
        except FileNotFoundError as e:
            if self.__auto_create is not None:
                config_data = self.__auto_create.copy()
                if self.__validator is not None:
                    self.__validator.validate(config_data)
                self.__config_data = SearchableDict(config_data)
                self.__config_path.parent.mkdir(parents=True, exist_ok=True)
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
        for k, v in self.__config_data.items():
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
            with open(self._config_path, 'rb') as f:
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
        with open(self._config_path, 'w') as f:
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
