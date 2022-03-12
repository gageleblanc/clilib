from clilib.util.decorators import deprecated
from clilib.util.dict import SearchableDict, dict_path
from clilib.util.util import SchemaValidator, Util
from pathlib import Path
from clilib.config.config import Config
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


class JSONConfigurationFile:
    def __init__(self, config_path: str, schema: dict = None, schema_strict: bool = False, auto_create: dict = None, write_on_set: bool = False):
        """
        Load JSON configuration file from disk, use auto_create if not None and file does not exist.
        :param config_path: Path to configuration file
        :param schema: Validation schema for validating loaded config. This is optional
        :param schema_strict: Schema validation is strict, failing if keys are missing from loaded config
        :param auto_create: Dictionary of defaults for auto creation, or None
        :param write_on_set: Boolean value which tells object whether to write to disk when a value in the config is changed.
        """
        self.__config_path = Path(config_path)
        self.__schema = schema
        self.__config_data = SearchableDict()
        self.__schema_strict = schema_strict
        self.__validator = None
        self.__auto_create = auto_create
        self.__write_on_set = write_on_set
        if self.__schema is not None:
            self.__validator = SchemaValidator(self.__schema, schema_strict)
        self._load_file()

    def __call__(self, path: str):
        return self.__config_data.get_path(path)

    def __getitem__(self, item):
        return self.__config_data.get_path(item)

    def __setitem__(self, item, value):
        config_data = SearchableDict(self.__config_data.copy())
        config_data.set_path(item, value)
        if self.__validator is not None:
            self.__validator.validate(config_data)
        self.__config_data = config_data
        if self.__write_on_set:
            self.write()

    def _load_file(self):
        try:
            with open(self.__config_path, 'rb') as f:
                config_data = json.load(f)
                if self.__validator is not None:
                    self.__validator.validate(config_data)
                self.__config_data = SearchableDict(config_data)
        except FileNotFoundError as e:
            if self.__auto_create is not None:
                config_data = self.__auto_create.copy()
                if self.__validator is not None:
                    self.__validator.validate(config_data)
                self.__config_data = SearchableDict(config_data)
                self.write()
            else:
                raise e

    def write(self):
        with open(self.__config_path, 'w') as f:
            json.dump(self.__config_data, f)


class YAMLConfigurationFile:

    class NoAliasDumper(yaml.SafeDumper):
        def ignore_aliases(self, data):
            return True

    def __init__(self, config_path: str, schema: dict = None, schema_strict: bool = False, auto_create: dict = None, write_on_set: bool = False):
        """
        Load YAML configuration file from disk, use auto_create if not None and file does not exist.
        :param config_path: Path to configuration file
        :param schema: Validation schema for validating loaded config. This is optional
        :param schema_strict: Schema validation is strict, failing if keys are missing from loaded config
        :param auto_create: Dictionary of defaults for auto creation, or None
        :param write_on_set: Boolean value which tells object whether to write to disk when a value in the config is changed.
        """
        self.__config_path = Path(config_path)
        self.__schema = schema
        self.__config_data = SearchableDict()
        self.__schema_strict = schema_strict
        self.__validator = None
        self.__auto_create = auto_create
        self.__write_on_set = write_on_set
        if self.__schema is not None:
            self.__validator = SchemaValidator(self.__schema, schema_strict)
        self._load_file()

    def __call__(self, path: str):
        return self.__config_data.get_path(path)

    def __getitem__(self, item):
        return self.__config_data.get_path(item)

    def __setitem__(self, item, value):
        config_data = SearchableDict(self.__config_data.copy())
        config_data.set_path(item, value)
        if self.__validator is not None:
            self.__validator.validate(config_data)
        self.__config_data = config_data
        if self.__write_on_set:
            self.write()

    def _load_file(self):
        try:
            with open(self.__config_path, 'rb') as f:
                config_data = yaml.safe_load(f)
                if self.__validator is not None:
                    self.__validator.validate(config_data)
                self.__config_data = SearchableDict(config_data)
        except FileNotFoundError as e:
            if self.__auto_create is not None:
                config_data = self.__auto_create.copy()
                if self.__validator is not None:
                    self.__validator.validate(config_data)
                self.__config_data = SearchableDict(config_data)
                self.write()
            else:
                raise e

    def write(self):
        with open(self.__config_path, 'wb') as f:
            f.write(yaml.dump(self.__config_data, Dumper=YAMLConfigurationFile.NoAliasDumper))
