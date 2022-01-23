import re

# Use jsonpath-like path on dictionary to get result
from typing import Any


def dict_path(d: dict, path: str):
    """
    Traverses given dictionary and returns result based on given path
    :param d: Dictionary to traverse
    :param path: Path used to return result
    """
    for key in path.split("."):
        if not key:
            continue
        li = re.findall(r'[(\d+)]', key)
        if len(li) > 0:
            k = key.split("[")[0]
            if not isinstance(d.get(k), list):
                raise TypeError("Value for key %s is not a list" % k)
            l = d.get(k)
            d = l[int(li[0])]
        else:
            d = d.get(key, None)
        if d is None:
            raise IndexError("Given dictionary does not contain path: %s (key: %s)" % (path, key))
    return d


class SearchableDict(dict):
    def search_path(self, path):
        """
        Traverses given dictionary and returns result based on given path
        :param path: Path used to return result
        """
        d = self
        for key in path.split("."):
            if not key:
                continue
            li = re.findall(r'[(\d+)]', key)
            if len(li) > 0:
                k = key.split("[")[0]
                if not isinstance(d.get(k), list):
                    raise TypeError("Value for key %s is not a list" % k)
                l = d.get(k)
                d = l[int(li[0])]
            else:
                d = d.get(key, None)
            if d is None:
                raise IndexError("Given dictionary does not contain path: %s (key: %s)" % (path, key))
        return d

    def get_path(self, path: str, default: Any = None):
        """
        Return value from dictionary based on path
        :param path: Path to retrieve
        :param default: Default value to return if path does not exist
        :return:
        """
        try:
            value = self.search_path(path)
        except IndexError:
            value = default
        return value

    def set_path(self, path: str, value: Any):
        """
        Set value of given path
        :param path: Path to set
        :param value: Value to set for given path
        :return:
        """
        d = self
        path_parts = path.split(".")
        destination = path_parts.pop()
        for key in path_parts:
            if not key:
                continue
            li = re.findall(r'[(\d+)]', key)
            if len(li) > 0:
                k = key.split("[")[0]
                if not isinstance(d.get(k), list):
                    raise TypeError("Value for key %s is not a list" % k)
                l = d.get(k)
                d = l[int(li[0])]
            else:
                n = d.get(key, None)
                if n is None:
                    d[key] = SearchableDict()
                d = d.get(key)
            if d is None:
                raise IndexError("Given dictionary does not contain path: %s (key: %s)" % (path, key))
        d[destination] = value
