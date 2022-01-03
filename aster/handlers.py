from codegen import wrap_matmul

def take(position):
    def take(nodes):
        return nodes[position]
    return take

result = wrap_matmul(take)

# No `string_create`, because any
# token is a string.

def string_append(results):
    return results[0] + results[1]

def list_create(results):
    return results[0] + results[1]

def list_append(position):
    def append(results):
        results[0].values.append(results[position])
        return results[0]
    return append