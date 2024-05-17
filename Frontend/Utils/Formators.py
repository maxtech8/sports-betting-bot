import re


def reformat_name(name):
    # Replace all non-alphanumeric characters (excluding the separators) with a space
    name = re.sub(r'[^\w\s,.]', '', name)

    # Split the string by any occurrence of the separators (space, comma, period)
    words = re.split(r'[ ,.]+', name)

    # Keep only alphanumeric characters in each word, convert to lowercase
    clean_words = [''.join(char for char in word if char.isalnum()).lower() for word in words]

    # Filter out any empty strings resulting from words being all non-alphanumeric
    clean_words = [word for word in clean_words if word]

    return '&'.join(clean_words)[:10]
