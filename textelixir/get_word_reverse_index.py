import pandas
from .filter_chunk import *
# def get_word_reverse_index(filename, punct_word_ids, text_filter, filter_regex):
#     index = []
#     elixir = pandas.read_csv(filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=1000000, keep_default_na=False, na_values=[])
#     for block_num, chunk in enumerate(elixir):
#         # Filter out punctuation
#         chunk = chunk[~chunk['word'].isin(punct_word_ids)]
#         # Add optional filters to the chunk
#         chunk = filter_chunk(chunk, text_filter, filter_regex)
        
#         index.extend(list(chunk.index.values))
#     return {idx: i for idx, i in enumerate(index)}     

def get_word_reverse_index(filename, punct_word_ids, text_filter, filter_regex):
    reverse_index = []
    elixir = pandas.read_csv(filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=1000000, keep_default_na=False, na_values=[])
    for block_num, chunk in enumerate(elixir):
        # Filter out punctuation
        chunk = chunk[~chunk['word'].isin(punct_word_ids)]
        # Add optional filters to the chunk
        chunk = filter_chunk(chunk, text_filter, filter_regex)
        
        reverse_index.extend(list(chunk['word']))
    return {idx: i for idx, i in enumerate(reverse_index)}   