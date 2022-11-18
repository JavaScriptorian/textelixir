def regex_delimiter(string):
    if not string.startswith(r'^'):
        string = fr'^{string}'
    if not string.endswith(r'$'):
        string = fr'{string}$'
    return string