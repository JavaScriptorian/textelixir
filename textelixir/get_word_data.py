import pandas

def get_word_data(basename, word_types):
    word_metadata = pandas.read_csv(f'{basename}/word.tsv', sep='\t', escapechar='\\', index_col=None, header=0, keep_default_na=False, na_values=[])
    word_metadata[word_types] = word_metadata[word_types].astype(str) 
    return word_metadata.set_index('index').to_dict()