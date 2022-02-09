import pandas
class NGrams:
    def __init__(self, filename, size, group_by, bounds=None, sep=' ', punct_pos='', chunk_num=0):
        # self.elixir = elixir[~elixir['pos'].isin(['PUNCT', 'SYM'])]
        self.filename = filename
        self.size = size
        self.group_by = group_by
        self.bounds = bounds
        self.sep = sep
        self.punct_pos = punct_pos
        self.chunk_num = chunk_num
        self.ngram_references = {}
        self.ngrams = self.calculate_ngrams()
        
    def calculate_ngrams(self):
        ngram_dict = {}
        self.elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=10000, keep_default_na=False)
        # word_tracking will contain each words. Once it hits correct size or end of sentence, then reset the words.
        word_tracking = []
        current_citation = ''
        # Iterate through each chunk of the elix file.
        for block_num, chunk in enumerate(self.elixir):
            print(f'\rN-Gram Progress: {round((block_num+1)/self.chunk_num*100, 2)}%', end='')
            # Iterate through each word in the chunk.
            for w in chunk.to_dict('records'):
                # Check to see if the word is punctuation.
                if w['pos'] in self.punct_pos:
                    continue
                # Get the citation (location) of the word.
                citation = self.get_citation(chunk, w)
                # If the citation is not the same as the current_citation, then we've hit a new sentence.
                # Words should not be in an ngram from different sentences.
                if citation != current_citation:
                    word_tracking = []
                    current_citation = citation
                # Append the next word to word_tracking
                word_tracking.append(w[self.group_by])
                
                if len(word_tracking) == self.size:
                    full_ngram = self.sep.join(word_tracking)
                    if full_ngram not in ngram_dict:
                        ngram_dict[full_ngram] = 0
                    ngram_dict[full_ngram] += 1
                    # Pop the first word in word_tracking in preparation for the next word.
                    word_tracking.pop(0)
        
        sorted_ngram_dict = sorted(ngram_dict.items(), key=lambda t: (-t[1], t[0]))
        return sorted_ngram_dict

    def get_citation(self, chunk, word):
        headers = list(chunk.columns.values)
        index_of_word_index = headers.index('word_index')
        citation_headers = headers[0:index_of_word_index]
        citation = '/'.join([str(word[i])for i in citation_headers])
        return citation
        