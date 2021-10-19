import re
from .word import Word
from .kwic import KWIC

class SearchResults:
    def __init__(self, elixir, search_string, kwargs):
        self.elixir = elixir
        self.search_string = search_string
        self.kwargs = kwargs
        self.results_indices = self.get_results_indices()
        self.hits = self.get_kwic_lines(before=0, after=0)

        ibrk = 0


    def get_results_indices(self):
        # Determine the search_type: word or phrase
        search_words = self.search_string.split(' ')
        if len(search_words) > 1:
            search_type = 'phrase'
        else:
            search_type = 'word'
        

        if search_type == 'word':
            word_type, search_word = self.get_word_type(self.search_string)
            results_indices = self.filter_elixir(self.search_string, word_type)

        elif search_type == 'phrase':
            for idx, search_word in enumerate(reversed(search_words)):
                word_type, search_word = self.get_word_type(search_word)
                if idx == 0:
                    results_indices = self.filter_elixir(search_word, word_type)
                else:
                    results_indices = [results_index for results_index in results_indices if self.elixir.iloc[results_index-idx][word_type] == search_word]
            
        
        for key, value in self.kwargs.items():
            results_indices = [results_index for results_index in results_indices if self.elixir.iloc[results_index][key] == value]
            ibrk = 0
        
        results_count = len(results_indices)
        print(f'Found {results_count} instances of "{self.search_string}"')
        
        self.search_length = len(search_words)
        return results_indices


    def get_word_type(self, search_word):
        is_pos_search = re.search(r'^/(.+?)/$', search_word)
        if is_pos_search:
            return ('pos', is_pos_search.group(1))
        elif search_word.upper() == search_word:
            return ('lemma', search_word)
        else:
            return ('text', search_word)


    def filter_elixir(self, search_word, word_type):
        results = self.elixir[self.elixir[word_type] == search_word]
        return [result[0] for result in results.iterrows()]

    def kwic_summary(self, before=5, after=5):
        self.get_kwic_lines(before, after)
        
        summary = self.kwic_lines[0:5]
        for i in summary:
            print(i)


    def get_kwic_lines(self, before, after):
        kwic_lines = []
        for results_index in self.results_indices:
            search_hit_indices = [results_index-word_length for word_length in reversed(range(0, self.search_length))]
            search_hits = [self.elixir.iloc[search_hit_index] for search_hit_index in search_hit_indices]
            search_hit_text = ''.join([search_hit['prefix'] + search_hit['text'] for search_hit in search_hits]).strip()
            
            search_before_word_window = self.get_kwic_text_before(before, search_hit_indices[0], [])
            search_after_word_window = self.get_kwic_text_after(after, search_hit_indices[-1], [])

            kwic_string = ''
            
            is_after_first_word = False

            before_arr = []
            hit_arr = []
            after_arr = []


            for i in range(search_before_word_window, search_after_word_window+1):
                w = self.elixir.iloc[i]

                lowest_level_header = self.get_line_index_header()


                line_index = w[lowest_level_header]

                if i < search_hit_indices[0]:
                    before_arr.append(w)
                elif i > search_hit_indices[-1]:
                    after_arr.append(w)
                else:
                    hit_arr.append(w)
                

                is_after_first_word = True
                last_line_index = w[lowest_level_header]

            kwic_lines.append(before_arr, hit_arr, after_arr)
            ibrk = 0
        return KWIC(kwic_lines)

    def get_line_index_header(self):
        headers = list(self.elixir.columns.values)
        return headers[headers.index('word_index')-1]
        ibrk = 0

    def get_kwic_text_before(self, before, start_index, indices_list):
        if start_index-1 < 0:
            indices_list = indices_list[::-1]
            return indices_list[0]
        word = self.elixir.iloc[start_index-1]
        if word['pos'] not in ['SYM', 'PUNCT']:
            indices_list.append(start_index-1)
        
        if len(indices_list) < before:
            self.get_kwic_text_before(before, start_index-1, indices_list)

        indices_list = indices_list[::-1]
        if len(indices_list) > 1:
            return indices_list[0]
        # If before == 0, then just return the start_index.
        return start_index


    def get_kwic_text_after(self, after, start_index, indices_list):
        if start_index+1 >= self.elixir.shape[0]:
            return indices_list[-1]
        word = self.elixir.iloc[start_index+1]
        if word['pos'] not in ['SYM', 'PUNCT']:
            indices_list.append(start_index+1)
        
        if len(indices_list) < after:
            self.get_kwic_text_after(after, start_index+1, indices_list)

        if len(indices_list) > 1:
            return indices_list[-1]
        # If after == 0, then just return the start_index
        return start_index