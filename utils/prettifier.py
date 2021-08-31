PRINT_PRETTY_INDENT = '  '

def is_dict(it):
    return isinstance(it, dict)

def is_list(it):
    return isinstance(it, list)

def is_non_primitive(it):
    return hasattr(it, '__dict__')

def is_str(it):
    return isinstance(it, str)

class GeneralCache:
    def __init__(self):
        self.items = {}

    def add(self, it):
        self.items[id(it)] = it
        return id(it)

    def index_of(self, it):
        if id(it) in self.items:
            return id(it)
        return None

def print_dict_contents(it, indent):
    print('{')

    for key, value in it.items():
        print(f'{indent}{PRINT_PRETTY_INDENT}{key}:', end=' ')
        print_pretty(value, indent + PRINT_PRETTY_INDENT)

    print(indent + '}')

def print_list_contents(it, indent):
    print('[')

    for value in it:
        print(indent + PRINT_PRETTY_INDENT, end='')
        print_pretty(value, indent + PRINT_PRETTY_INDENT)

    print(indent + ']')

def print_pretty(it, indent='', cache=GeneralCache(), show_ids=True):
    cache_id = cache.index_of(it)
    is_new = cache_id is None

    if is_new and is_non_primitive(it):
       cache_id = cache.add(it)

    if is_non_primitive(it):
        print(type(it).__name__, end=' ')

        if show_ids:
            new_prefix = ''

            if is_new:
                new_prefix = '+'

            print(f'@{new_prefix}{cache_id}', end=' ')

    if is_new:
        if is_list(it):
            print_list_contents(it, indent)
        elif is_dict(it):
            print_dict_contents(it, indent)
        elif is_non_primitive(it):
            print_dict_contents(it.__dict__, indent)
        elif is_str(it):
            print(f'"{it}"')
        else:
            print(it)
    else:
        print('[cached]')
