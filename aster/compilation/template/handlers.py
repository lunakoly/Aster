def take(position):
    def take(nodes):
        return nodes[position]
    return take

# No `string_create`, because any
# token is a string.

def string_append(nodes):
    return nodes[0] + nodes[1]

def list_create(nodes):
    return nodes[0] + nodes[1]

def list_append(position):
    def append(nodes):
        nodes[0].values.append(nodes[position])
        return nodes[0]
    return append
