def extract_callback_data(data: str):
    params = data.split("$")[-1]
    return params.split("_")
