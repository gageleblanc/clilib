import json


class Config(dict):
    def __init__(self, d, path):
        self.__dict__ = d
        self.path = path

    def write_config(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.__dict__, f, ensure_ascii=False, indent=4)

    def reload(self):
        with open(self.path) as f:
            self.__dict__ = json.load(f)

    def get_dict(self):
        return self.__dict__
