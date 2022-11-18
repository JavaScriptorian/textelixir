import pandas

def get_metadata(basename, table_name, **kwargs):
    # pos
    key = list(kwargs.keys())[0]
    # [ 'SYM', 'PUNCT', 'SPACE' ]
    value = list(kwargs.values())[0]
    # word.tsv
    metadata = pandas.read_csv(f'{basename}/{table_name}.tsv', sep='\t', escapechar='\\', index_col=None, header=0, keep_default_na=False, na_values=[])
    if isinstance(value, list):
        filtered_metadata = metadata[metadata[key].isin(value[0])]
    else:
        filtered_metadata = metadata[metadata[key] == value]
    return filtered_metadata['index'].to_list()
