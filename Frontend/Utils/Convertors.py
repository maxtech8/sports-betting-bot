import dill


def function_to_bytes(my_function):
    return dill.dumps(my_function)


def bytes_to_function(retrieved_function_bytes):
    return dill.loads(retrieved_function_bytes)

