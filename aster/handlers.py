from .synthetic import create_accessor

handlers_cache = {}

def take(position):
    cache_key = ('take', position)

    if cache_key in handlers_cache:
        return handlers_cache[cache_key]

    def inner(nodes):
        return nodes[position]

    handlers_cache[cache_key] = inner
    return inner

result = create_accessor(take)

# No `string_create`, because any
# token is a string.

def string_append(results):
    return results[0] + results[1]

def list_create(results):
    return results[0] + results[1]

def list_append(position):
    cache_key = ('list_append', position)

    if cache_key in handlers_cache:
        return handlers_cache[cache_key]

    def append(results):
        results[0].values.append(results[position])
        return results[0]

    handlers_cache[cache_key] = append
    return append
