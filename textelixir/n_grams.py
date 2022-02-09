import pandas
class NGrams:
    def __init__(self, elixir, size, group_by, bounds=None, sep=' '):
        self.elixir = elixir[~elixir['pos'].isin(['PUNCT', 'SYM'])]
        self.size = size
        self.group_by = group_by
        self.bounds = bounds
        self.sep = sep
        self.ngram_references = {}
        self.ngrams = self.calculate_ngrams()
        
        

    def calculate_ngrams(self):
        ngram_dict = {}
        # Iterate through each word in the corpus.
        word_count = self.elixir.shape[0]
        for idx in range(0, word_count):
            print(f'\r{idx+1}/{word_count}', end='')
            current_word = self.elixir.iloc[idx]
            if current_word['pos'] not in ['SYM', 'PUNCT']:
                if self.bounds == None:
                    ngram_cluster = self.ngram_cluster(idx, [current_word[self.group_by]])
                else:
                    line_index = int(current_word[self.bounds])
                    ngram_cluster = self.ngram_cluster_bounds(idx, line_index, [current_word[self.group_by]])
                if len(ngram_cluster) == 0:
                    continue
                ngram_string = self.sep.join(ngram_cluster)
                
                # Add the ngram to ngram_dict. Increment its frequency value
                if ngram_string not in ngram_dict:
                    ngram_dict[ngram_string] = 0
                ngram_dict[ngram_string] += 1

                # Get current reference
                current_reference = self.current_reference(idx)
                self.ngram_references[current_reference] = ngram_string
                ibrk = 0

        # End the dynamic printing
        print(f'\n', end='')

        # Sort first by frequency, then by alphabet.
        sorted_ngram_dict = sorted(ngram_dict.items(), key=lambda t: (-t[1], t[0]))
        return sorted_ngram_dict


    def ngram_cluster(self, start_index, cluster_list):
        # Check to see if the cluster_index is already satisfied
        if len(cluster_list) == self.size:
            return cluster_list
        
        # If at the end of the elixir and there aren't enough words, return an empty list.
        is_elixir_empty = start_index + 1 >= self.elixir.shape[0]
        if is_elixir_empty:
            if len(cluster_list) != self.size:
                cluster_list = []
            return cluster_list

        
        word = self.elixir.iloc[start_index+1]
        if word['pos'] not in ['SYM', 'PUNCT']:
            cluster_list.append(word[self.group_by])
        
        # Recursively add words to the cluster list until it's at the right size.
        if len(cluster_list) != self.size and is_elixir_empty == False:
            cluster_list = self.ngram_cluster(start_index+1, cluster_list)

        return cluster_list

    def ngram_cluster_bounds(self, start_index, line_index, cluster_list):
        # Check to see if the cluster_index is already satisfied
        if len(cluster_list) == self.size:
            return cluster_list
        
        # If at the end of the elixir and there aren't enough words, return an empty list.
        is_elixir_empty = start_index + 1 >= self.elixir.shape[0]
        if is_elixir_empty:
            if len(cluster_list) != self.size:
                cluster_list = []
            return cluster_list

        
        word = self.elixir.iloc[start_index+1]
        # Check to see if the word's line_index is the same as the first word in the n-gram
        current_line_index = int(word[self.bounds])
        if current_line_index != line_index:
            if len(cluster_list) != self.size:
                cluster_list = []
            return cluster_list
        
        if word['pos'] not in ['SYM', 'PUNCT']:
            cluster_list.append(word[self.group_by])
        
        # Recursively add words to the cluster list until it's at the right size.
        if len(cluster_list) != self.size and is_elixir_empty == False:
            cluster_list = self.ngram_cluster_bounds(start_index+1, line_index, cluster_list)
        return cluster_list

    def current_reference(self, idx):
        # Grab list of headers
        headers = list(self.elixir.columns.values)
        headers = headers[0:headers.index('word_index')+1]
        reference_values = [str(self.elixir.iloc[idx][i]) for i in headers]
        return '/'.join(reference_values)
        