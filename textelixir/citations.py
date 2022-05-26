def get_citation(word):
    headers = list(word.keys())
    index_of_word_index = headers.index('word_index')
    citation_headers = headers[0:index_of_word_index+1]
    citation = '/'.join([str(word[i]) for i in citation_headers])
    return citation