import re

# Use jsonpath-like path on dictionary to get result 
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