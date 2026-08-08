
def list_to_tuple_recursive(li: list):
    return tuple(list_to_tuple_recursive(child) if isinstance(child, list) else child for child in li)