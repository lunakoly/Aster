def collect_symbol_groups(container):
    return {it[3:]: container[it] for it in container if it.startswith('is_')}
