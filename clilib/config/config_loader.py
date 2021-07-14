from clilib.util.util import Util
from pathlib import Path
from clilib.config.config import Config
import json


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
