import pandas
import re

from .kwic import KWIC
from .collocates import Collocates
from .sentences import Sentences
from .vocabdist import VocabDist
from .getwords import get_previous_word

class SearchResults:
    def __init__(self, filename, search_string, word_count, **kwargs):
        # Parse kwargs
        self.punct_pos = kwargs['punct_pos']
        self.verbose = kwargs['verbose']
        self.text_filter = kwargs['text_filter']
        # Check for regex within text_filter
        if self.text_filter and 'is_regex' in self.text_filter:
            self.filter_regex = self.text_filter['is_regex']
            del self.text_filter['is_regex']
        else:
            self.filter_regex = False
        self.regex = kwargs['regex']
        self.search_string = search_string
        self.wildcard = self.check_string_for_wildcards()
        self.filename = filename
        self.word_count = word_count    # Total words in corpus
        # If the search_string is just one string, then get the results_indices for that word.
        if isinstance(search_string, str):     
            self.results_indices = self.get_results_indices()
        elif isinstance(search_string, list):
            self.results_totals = self.get_results_indices()

    def check_string_for_wildcards(self):
        return True if ('*' in self.search_string or '?' in self.search_string) and self.regex == False else False

    def get_results_indices(self):
        # Determine the search_type: word or phrase
        if isinstance(self.search_string, str):
            search_words = self.search_string.split(' ')
        elif isinstance(self.search_string, list):
            search_words = self.search_string[0].split(' ')

        # Set Search Type 'word' || phrase
        search_type = 'phrase' if len(search_words) > 1 else 'word'

        if search_type == 'word':
            word_type, search_word = self.get_word_type(self.search_string) if isinstance(self.search_string, str) else self.get_word_type(self.search_string[0])
            results_indices = self.filter_elixir(self.search_string, word_type)

        elif search_type == 'phrase':
            for idx, search_word in enumerate(reversed(search_words)):
                # Parse ~##~ as partial match operator
                if re.search(r'^~(\d+)~$', search_word):
                    distance = int(re.search(r'^~(\d+)~$', search_word).group(1))
                    continue

                word_type, search_word = self.get_word_type(search_word)
                if idx == 0:
                    results_indices = self.filter_elixir(search_word, word_type)
                    # Set default distance to 1.
                    distance = 1
                else:
                    self.elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=10000)
                    new_indices = []
                    for block_num, chunk in enumerate(self.elixir):
                        # Get the list of the current results indices based on the block number.
                        curr_indices = self.filter_indices_by_block(results_indices, block_num)               

                        for curr_index in curr_indices:
                            curr_block_num, word_index = curr_index[0].split(':')
                            curr_block_num = int(curr_block_num)
                            word_index = int(word_index)

                            if curr_block_num != block_num:
                                raise Exception(f'The current block num {curr_block_num} is not the same as block num {block_num}')

                            last_chunk = last_chunk if block_num != 0 else None
                            
                            # Get previous words
                            previous_words = get_previous_word(last_chunk, chunk, block_num, word_index, distance)
                            
                            # Filter those previous words for good hits.
                            good_hit = None
                            for y in previous_words:
                                for key, value in y.items():
                                    if len(word_type) > 1:
                                        w1, w2 = re.split(r'(?<!\\)_', search_word)
                                        wt1, wt2 = word_type
                                        if value[wt1] == w1 and value[wt2] == w2:
                                            good_hit = key
                                            continue
                                    else:
                                        if value[word_type[0]] == search_word:
                                            good_hit = key # 8:120
                                            continue
                            if good_hit is not None:
                                phrase_result = (good_hit, *curr_index)
                                new_indices.append(phrase_result)
                        # Save the last chunk.
                        last_chunk = chunk
                    # Reset distance to 1
                    results_indices = new_indices
                    distance = 1
        
        # Get count of how many results found.
        self.results_count = 0
        for index in results_indices:
            if isinstance(self.search_string, str):
                self.results_count += 1
            elif isinstance(self.search_string, list):
                self.results_count += results_indices[index]

        if self.verbose:
            print(f'Found {self.results_count} instances of "{self.search_string}"')
        

        return results_indices


    def get_word_type(self, search_word):
        search_type_list = []

        # Separate the search_word by any underscores.
        # Must check for an escape backslash before the underscore.
        search_word_split = re.split(r'(?<!\\)_', search_word)
        for idx, sw in enumerate(search_word_split):
            if idx == 0:
                if re.search(r'^/(.+?)/$', sw):
                    search_type_list.append('pos')
                elif search_word.upper() == search_word:
                    search_type_list.append('lemma')
                else:
                    search_type_list.append('lower')
            else:
                search_type_list.append('pos')
        
        return (search_type_list, search_word)



    def filter_elixir(self, search_word, word_type):
        # Initialize a list or dictionary depending on the type of search.
        if isinstance(search_word, str):
            results = []
        elif isinstance(search_word, list):
            results = {}
        self.elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=10000)
        for block_num, chunk in enumerate(self.elixir):
            chunk = chunk.applymap(str)
            chunk = self.filter_chunk(chunk)
            # Normal Search Handle
            if isinstance(search_word, str):
                # Split search word by its handle and remove any // around a POS.
                word_specs = [re.sub(r'^/(.+?)/$', r'\1', w) for w in re.split(r'(?<!\\)_', search_word)]
                for wt_idx, wt in enumerate(word_type):
                    if wt_idx == 0:
                        # POSITIVE REGEX HANDLER
                        if self.regex:
                            value = word_specs[wt_idx]
                            found_words = chunk[chunk[wt].str.match(value)]
                        # POSITIVE WILDCARD HANDLER
                        elif self.wildcard:
                            value = word_specs[wt_idx].replace('*', '.*').replace('?', '.')
                            found_words = chunk[chunk[wt].str.match(value, na=False)]
                        # POSITIVE EXACT MATCH HANDLER
                        else:
                            value = word_specs[wt_idx]
                            found_words = chunk[chunk[wt] == value]
                    else:
                        # POSITIVE REGEX HANDLER
                        if self.regex:
                            value = word_specs[wt_idx]
                            found_words = found_words[chunk[wt].str.match(value)]
                        # POSITIVE WILDCARD HANDLER
                        elif self.wildcard:
                            value = word_specs[wt_idx].replace('*', '.*').replace('?', '.')
                            found_words = found_words[chunk[wt].str.match(value)]
                        # POSITIVE EXACT MATCH HANDLER
                        else:
                            value = word_specs[wt_idx]
                            found_words = found_words[found_words[wt] == value]
                for word in found_words.to_dict('index'):
                    find_index = word-(block_num*10000)
                    results.append((f'{block_num}:{find_index}',))
            
            # Collocates Handler
            elif isinstance(search_word, list):
                for word in search_word:
                    word_specs = [re.sub(r'^/(.+?)/$', r'\1', w) for w in re.split(r'(?<!\\)_', word)]
                    # TODO: HANLDE WILDCARDS HERE
                    for wt_idx, wt in enumerate(word_type):
                        found_words = chunk[chunk[wt] == word_specs[wt_idx]] if wt_idx == 0 else found_words[found_words[wt] == word_specs[wt_idx]]
                    if word not in results:
                        results[word] = 0
                    results[word] += len(found_words)

        return results

    # Filters the results_indices list to get only the word citations with the same block number.
    def filter_indices_by_block(self, results_indices, block_num):
        filtered_indices = []
        for index in results_indices:
            curr_block_num, word_num = index[-1].split(':')
            if int(curr_block_num) == block_num:
                filtered_indices.append(index)
        return filtered_indices

    # Filters the chunk based on optional filters.
    def filter_chunk(self, chunk):
        if self.text_filter == None:
            return chunk
        elif isinstance(self.text_filter, dict):
            filter_index = 0
            for key, value in self.text_filter.items():
                # Change value:string to value:list
                if isinstance(value, str):
                    value_list = [value]
                elif isinstance(value, list):
                    value_list = value

                self.filter_wildcard = True if ('*' in value or '?' in value) and (self.filter_regex == False) else False
                
                for value in value_list:
                    # If it's the first filter being applied.
                    if filter_index == 0:
                        # Look for everything excluding this one item.
                        if value.startswith('!'):
                            value = value[1:]
                            # NEGATIVE REGEX HANDLER
                            if self.filter_regex:
                                new_chunk = chunk[~chunk[key].str.match(value)]
                            # NEGATIVE WILDCARD HANDLER
                            elif self.filter_wildcard:
                                value = value.replace('*', '.*').replace('?', '.')
                                new_chunk = chunk[~chunk[key].str.match(value)]
                            # NEGATIVE EXACT MATCH HANDLER
                            else:
                                new_chunk = chunk[chunk[key] != value]
                            
                        # Look for everything including this item.
                        else:
                            # POSITIVE REGEX HANDLER
                            if self.filter_regex:
                                new_chunk = chunk[chunk[key].str.match(value)]
                            # POSITIVE WILDCARD HANDLER
                            elif self.filter_wildcard:
                                value = value.replace('*', '.*').replace('?', '.')
                                new_chunk = chunk[chunk[key].str.match(value)]
                            # POSITIVE EXACT MATCH HANDLER
                            else:
                                new_chunk = chunk[chunk[key] == value]
                    # If it's not the first filter being applied.
                    else:
                        if value.startswith('!'):
                            value = value[1:]
                            if new_chunk.shape[0] > 0:
                                ibrk = 0
                            # NEGATIVE REGEX HANDLER
                            if self.filter_regex:
                                new_chunk = new_chunk[~new_chunk[key].str.match(value)]
                            # NEGATIVE WILDCARD HANDLER
                            elif self.filter_wildcard:
                                value = value.replace('*', '.*').replace('?', '.')
                                new_chunk = new_chunk[~new_chunk[key].str.match(value)]
                            # NEGATIVE EXACT MATCH HANDLER
                            else:
                                new_chunk = new_chunk[new_chunk[key] != value]
                        else:
                            # POSITIVE REGEX HANDLER
                            if self.filter_regex:
                                new_chunk = new_chunk[new_chunk[key].str.match(value)]
                            elif self.wildcard:
                                pass
                            # EXACT MATCH HANDLER
                            else:
                                new_chunk = new_chunk[new_chunk[key] == value]
                    filter_index += 1
            return new_chunk
        elif isinstance(self.text_filter, list):
            pass
            # TODO: This is where a user could input ['Book of Mormon/1 Nephi/1/1'] to specify exact citation filtering.

    ### VOCABULARY DISTRIBUTION HANDLER
    def vocab_distribution(self, **kwargs):
        group_by = kwargs['group_by'] if 'group_by' in kwargs else 0
        return VocabDist(self.filename, group_by, self.results_indices, self.punct_pos, self.search_string)

    ### KWIC LINES HANDLER
    def kwic_lines(self, before=5, after=5, group_by='lower'):
        return KWIC(self.filename, self.results_indices, before=before, after=after, group_by=group_by, search_string=self.search_string, punct_pos=self.punct_pos)


    ### KWIC LINES ALIAS
    def concordance_lines(self, before=5, after=5, group_by='lower'):
        return KWIC(self.filename, self.results_indices, before=before, after=after, group_by=group_by, search_string=self.search_string, punct_pos=self.punct_pos)

    ### COLLOCATES HANDLER
    def collocates(self, before=5, after=5, group_by='lemma_pos', mi_threshold=3, sample_size_threshold=2):
        ### ERROR HANDLING
        # If 0 results, return immediately.
        if len(self.results_indices) == 0:
            return None
        if group_by not in ['lemma', 'lower', 'pos', 'lower_pos', 'lemma_pos']:
            raise Exception(f"{{group_by}} value is invalid. It must be lemma, lower, pos, lower_pos, or lemma_pos.")

        collocates = Collocates(self.filename, self.results_indices, before, after, self.word_count, group_by, mi_threshold=mi_threshold, sample_size_threshold=sample_size_threshold, search_string=self.search_string)
        # Set the totals for each word that was found as a collocate. This cannot be done in collocates.py because it depends on search_results.py, which also depends on collocates.py
        collocates.set_total(self.calculate_collocate_totals(collocates.sample))
        # Once totals are available, statistics can be calculated.
        collocates.calculate_friends()
        return collocates

    def calculate_collocate_totals(self, samples):
        print('Getting totals for each collocating word.')
        totals = {}
        words = [word for word, value in samples.items()]
        totals = SearchResults(self.filename, words, self.word_count, punct_pos=self.punct_pos, verbose=False, text_filter=None, regex=False).results_totals
        return totals

    ### SENTENCES HANDLER
    def sentences(self, group_by='text'):
        return Sentences(self.filename, self.results_indices, group_by=group_by, search_string=self.search_string)
