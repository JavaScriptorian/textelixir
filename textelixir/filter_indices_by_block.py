import itertools
def filter_indices_by_block(results, block_num):
    filtered_indices = []
    for search_word, result_list in results.items():
        filtered_indices.extend([indices for indices in result_list if (indices[0] >= block_num*1000000 and indices[0] < (block_num*1000000) + 1000000)])
    filtered_indices.sort()
    return list(k for k,_ in itertools.groupby(filtered_indices))
