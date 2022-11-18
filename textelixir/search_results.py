import pandas
import re
from operator import itemgetter
from .kwic import KWIC
from .collocates import Collocates
from .sentences import Sentences
from .vocabdist import VocabDist
from .regex_validator import regex_delimiter
from .get_metadata import *
from .get_full_citation import *        # get_full_citation(df)

class SearchResults:
    def __init__(self, filename, search_string, word_count, **kwargs):
        self.filename = filename
        self.basename = re.sub(r'^(.+)/[^/]+$', r'\1', self.filename)
        self.search_string = self.parse_search_string(search_string)
        # Parse kwargs
        self.punct_pos = kwargs['punct_pos']
        self.punct_word_ids = get_metadata(self.basename, 'word', pos=[self.punct_pos])
        # Word tables
        self.word_dict = self.get_word_data()
        self.verbose = kwargs['verbose']
        self.text_filter = kwargs['text_filter']
        # Check for regex within text_filter
        if self.text_filter and 'is_regex' in self.text_filter:
            self.filter_regex = self.text_filter['is_regex']
            del self.text_filter['is_regex']
        else:
            self.filter_regex = False
        self.regex = kwargs['regex']
        self.group_by = kwargs['group_by']
        # Total words in corpus
        self.word_count = word_count    
        # Create index of corpus
        self.index = self.get_index()
        # If the search_string is just one string, then get the results_indices for that word.
        self.results = self.get_results()
        # Create search query - frequency dictionary
        self.search_frequency = self.get_search_frequency()
        # Fix indices of results
        self.results = self.fix_result_indices()
        # Memory Management
        del self.word_dict
        del self.index
        del self.punct_word_ids
        del self.word_count


    def __str__(self):
        output_string = ''
        if len(self.search_frequency) > 20:
            top20 = {k: self.search_frequency[k] for k in list(self.search_frequency.keys())[:20]}
            output_string += f'Displaying the top 20 of {len(self.search_frequency)} results.\n'
            output_string += 'text\tfreq\n'
            for k, v in top20.items():
                output_string += f'{k}\t{v}\n'
            output_string += '...\t...'
        else:
            output_string += 'text\tfreq\n'
            for k, v in self.search_frequency.items():
                output_string += f'{k}\t{v}\n'
        return output_string

    def __repr__(self):
        return str(self)


    def get_search_frequency(self):
        search_frequency = {}
        reverse_index = self.get_reverse_index()
        for search_word, result_list in self.results.items():
            search_frequency[search_word] = {}
            for i in result_list:
                # TODO: Make it join by other things besides lower...
                if self.group_by == 'lemma_pos':
                    ngram = ' '.join([self.word_dict['lemma'][reverse_index[x]] + '_' + self.word_dict['pos'][reverse_index[x]] for x in i])
                elif self.group_by == 'lower_pos':
                    ngram = ' '.join([self.word_dict['lower'][reverse_index[x]] + '_' + self.word_dict['pos'][reverse_index[x]] for x in i])
                else:
                    ngram = ' '.join([self.word_dict[self.group_by][reverse_index[x]] for x in i])
                if ngram not in search_frequency[search_word]:
                    search_frequency[search_word][ngram] = 0
                search_frequency[search_word][ngram] += 1
            search_frequency[search_word] = {k: v for k, v in sorted(search_frequency[search_word].items(), key=itemgetter(1), reverse=True)}
        
        return search_frequency


    def check_string_for_wildcards(self, value):
        return True if ('*' in value or '?' in value) and self.regex == False else False


    def parse_search_string(self, search_string):
        if isinstance(search_string, str):
            return [search_string]
        elif isinstance(search_string, list):
            return search_string
        else:
            raise Exception(f'You\'ve provided a {type(search_string)} for your search string. Only strings and lists are compatible.')


    # SECTION New Content for Search Method
    def get_results(self):
        results = {}
        # Actual Search
        # Turn search_string into a list of search queries
        for string in self.search_string:
            print(string)
            search_results_ids = []
            search_words, distance_settings, search_length = self.parse_search_query(string)
            
            indices = {}
            for hit_index, search_word in enumerate(search_words):
                word_type, search_word = self.get_word_type(search_word)
                indices[hit_index] = self.get_search_result_ids(search_word, word_type, hit_index)
            indices = self.combine_indices(indices)
            if search_length == 1:
                results[string] = [[k] for k, v in indices.items()]
            else:
                results[string] = self.pair_matches(indices, distance_settings, search_length)
        return results


    def combine_indices(self, indices):
        new_indices = {}
        for hit_index, index_dict in indices.items():
            for k, v in index_dict.items():
                if k not in new_indices:
                    new_indices[k] = v
                else:
                    new_indices[k].extend(v)
        return new_indices
            

    def parse_search_query(self, search_string):
        # Split search_string by space.
        search_words = search_string.split(' ')
        # Identify any distance markers
        distance_marker_count = 0
        distance_settings = {}
        for idx, search_word in enumerate(search_words):
            # Identify distance markers
            if search_word.startswith('~') and search_word.endswith('~'):
                # The first word in search query really shouldn't start be a distance marker.
                if idx == 0 or idx == len(search_words)-1:
                    raise Exception('The first or last word in your search query should not be a distance marker.')
                else:
                    distance_settings[idx-distance_marker_count] = int(re.search(r'~(\d+)~', search_word).group(1))
                    distance_marker_count += 1
        # Remove distance markers from search_words list
        search_words = [sw for sw in search_words if not re.search(r'^~\d+~', sw)]
        search_length = len(search_words)
        # Add default distance settings to any words that didn't have a distance marker.
        for i in range(1, len(search_words)):
            if i not in distance_settings:
                distance_settings[i] = 1

        return (search_words, distance_settings, search_length)

   
    def get_index(self):
        index = []
        elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=1000000, keep_default_na=False, na_values=[])
        for block_num, chunk in enumerate(elixir):
            # Filter out punctuation
            chunk = chunk[~chunk['word'].isin(self.punct_word_ids)]
            # Add optional filters to the chunk
            chunk = self.filter_chunk(chunk)
            
            index.extend(list(chunk.index.values))
        return {i: idx for idx, i in enumerate(index)}     


    def get_reverse_index(self):
        reverse_index = []
        elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=1000000, keep_default_na=False, na_values=[])
        for block_num, chunk in enumerate(elixir):
            # Filter out punctuation
            chunk = chunk[~chunk['word'].isin(self.punct_word_ids)]
            # Add optional filters to the chunk
            chunk = self.filter_chunk(chunk)
            
            reverse_index.extend(list(chunk['word']))
        return {idx: i for idx, i in enumerate(reverse_index)}   


    def pair_matches(self, indices, distance_settings, search_length):
        final_results = []
        looking_for_hit_num = 0
        word_tracking = []
        
        for k, v in {k: v for k,v in sorted(indices.items())}.items():
            if looking_for_hit_num in v:
                if looking_for_hit_num == 0:
                    word_tracking.append(k)
                    looking_for_hit_num += 1
                else:
                    if k-word_tracking[-1] > distance_settings[looking_for_hit_num]:
                        word_tracking = []
                        looking_for_hit_num = 0
                        if looking_for_hit_num in v:
                            word_tracking.append(k)
                            looking_for_hit_num += 1
                    else:
                        word_tracking.append(k)
                        looking_for_hit_num += 1

                if looking_for_hit_num == search_length:
                    final_results.append(word_tracking)
                    word_tracking = []
                    looking_for_hit_num = 0
            else:
                word_tracking = []
                looking_for_hit_num = 0
                if 0 in v:
                    word_tracking.append(k)
                    looking_for_hit_num += 1

        return final_results
    # !SECTION


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
        
        search_word = re.sub(r'^/(.+?)/$', r'\1', search_word)

        return (search_type_list, search_word)



    # SECTION Get search result IDs
    def get_search_result_ids(self, search_word, word_type, hit_index):
        indices = {}
        # Get word IDs that match the search query.
        word_ids = self.get_word_ids(search_word, word_type)
        # Initialize a list or dictionary depending on the type of search.
        elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=1000000, keep_default_na=False, na_values=[])
        
        for block_num, chunk in enumerate(elixir):
            # Filter out punctuation
            chunk = chunk[~chunk['word'].isin(self.punct_word_ids)]
            # Add optional filters to the chunk
            chunk = self.filter_chunk(chunk)
            # Normal Search Handler
            found_words = chunk[chunk['word'].isin(word_ids)]
            for word in found_words.to_dict('index'):
                corpus_index = self.index[word]
                if corpus_index not in indices:
                    indices[corpus_index] = [hit_index]
                else:
                    indices[corpus_index].append(hit_index)
        return indices
        # TODO Collocates Handler
    # !SECTION

    def fix_result_indices(self):
        reverse_index = {v: k for k, v in self.index.items()}
        fixed_indices = {}
        for search_word, result_list in self.results.items():
            fixed_indices[search_word] = []
            for i in result_list:
                fixed_indices[search_word].append([reverse_index[w] for w in i])
        return fixed_indices


    # SECTION Match metadata numbers
    def match_metadata_numbers(self, basename, table, search_query, is_regex):
        # Check to see if the table is negative or not.
        if table.startswith('!'):
            is_negative = True
            table = table[1:]
        else:
            is_negative = False

        metadata = pandas.read_csv(f'{basename}/{table}.tsv', sep='\t', escapechar='\\', index_col=None, header=0, keep_default_na=False, na_values=[])
        metadata['value'] = metadata['value'].astype(str)
        if isinstance(search_query, list):
            search_query = [str(s) for s in search_query]
            if is_negative:
                filtered_metadata = metadata[~metadata.value.isin(search_query)]
            else:
                filtered_metadata = metadata[metadata.value.isin(search_query)]
        elif isinstance(search_query, str):
            if is_negative:
                filtered_metadata = metadata[metadata.value != search_query]
            else:
                filtered_metadata = metadata[metadata.value == search_query]
        return filtered_metadata['index'].to_list()
    # !SECTION


    # SECTION Get word IDs
    def get_word_ids(self, search_word, word_type):
        metadata = pandas.read_csv(f'{self.basename}/word.tsv', sep='\t', escapechar='\\', index_col=None, header=0, keep_default_na=False, na_values=[])
        wildcard = self.check_string_for_wildcards(search_word)

        if len(word_type) == 2:
            # TODO: Handle this differently if pos is the second word type
            search_words = [w for w in re.split(r'(?<!\\)_', search_word)]
            # POSITIVE REGEX HANDLER
            if self.regex:
                filtered_metadata = metadata[(metadata[word_type[0]].str.match(regex_delimiter(search_words[0]), na=False)) & (metadata[word_type[1]].str.match(regex_delimiter(search_words[1]), na=False))]
            # POSITIVE WILDCARD HANDLER
            elif wildcard:
                search_words[0] = search_words[0].replace('*', '.*').replace('?', '.')
                search_words[1] = search_words[1].replace('*', '.*').replace('?', '.')
                filtered_metadata = metadata[(metadata[word_type[0]].str.match(regex_delimiter(search_words[0]), na=False)) & (metadata[word_type[1]].str.match(regex_delimiter(search_words[1]), na=False))]
            # POSITIVE EXACT MATCH HANDLER
            else:
                filtered_metadata = metadata[(metadata[word_type[0]] == search_words[0]) & (metadata[word_type[1]] == search_words[1])]
        else:

            # POSITIVE REGEX HANDLER
            if self.regex:
                filtered_metadata = metadata[metadata[word_type[0]].str.match(regex_delimiter(search_word), na=False)]
            # POSITIVE WILDCARD HANDLER
            elif wildcard:
                search_word = search_word.replace('*', '.*').replace('?', '.')
                filtered_metadata = metadata[metadata[word_type[0]].str.match(regex_delimiter(search_word), na=False)]
            # POSITIVE EXACT MATCH HANDLER
            else:
                filtered_metadata = metadata[metadata[word_type[0]] == search_word]
        return filtered_metadata['index'].to_list()
    # !SECTION

    # Filters the results_indices list to get only the word citations with the same block number.
    def filter_indices_by_block(self, results_indices, block_num):
        filtered_indices = []
        for _, indices in results_indices.items():
            for index in indices:
                curr_block_num, word_num = index[-1].split(':')
                if int(curr_block_num) == block_num:
                    filtered_indices.append(index)
        return filtered_indices

    # SECTION Filter Chunk
    # TODO Fix chunk filtering
    def filter_chunk(self, chunk):
        if self.text_filter == None:
            return chunk
        if not isinstance(self.text_filter, dict):
            raise Exception(f'The text_filter argument accepts dictionaries, not {type(self.text_filter)}.')

        
        # Check for invalid key input
        valid_columns = list(chunk.columns)[0:-3]
        for key, _ in self.text_filter.items():
            if key.startswith('!') and key[1:] in valid_columns:
                continue
            elif key.startswith('!') and key[1:] not in valid_columns:
                raise Exception(f'The key "{key[1:]}" in your text_filter is not valid. Please use one of the following keys: {str(valid_columns)}')
            elif key not in valid_columns:
                raise Exception(f'The key "{key}" in your text_filter is not valid. Please use one of the following keys: {str(valid_columns)}')
        filter_index = 0
        for key, value in self.text_filter.items():
            # Get all metadata numbers that match the filter.
            if isinstance(value, str) or isinstance(value, list):
                metadata_numbers = self.match_metadata_numbers(self.basename, key, value, self.regex)
                # ADD NEW FUNCTION HERE
            else:
                raise Exception(f'The text_filter dictionary accepts values with a string or list, not {type(value)}.')

            if key.startswith('!'):
                key = key[1:]
            # Filter the original chunk now that we have the filter.
            if filter_index == 0:
                new_chunk = chunk[chunk[key].isin(metadata_numbers)]
            else:
                new_chunk = new_chunk[new_chunk[key].isin(metadata_numbers)]
            filter_index += 1
        return new_chunk
    # !SECTION

    def get_word_data(self):
        word_metadata = pandas.read_csv(f'{self.basename}/word.tsv', sep='\t', escapechar='\\', index_col=None, header=0, keep_default_na=False, na_values=[])
        word_metadata.drop('prefix', inplace=True, axis=1)
        word_metadata[['text', 'lower', 'pos', 'lemma']] = word_metadata[['text', 'lower', 'pos', 'lemma']].astype(str) 
        return word_metadata.set_index('index').to_dict()


    # SECTION: Vocabulary Distribution
    def vocab_distribution(self, **kwargs):
        group_by = kwargs['group_by'] if 'group_by' in kwargs else 0
        match = kwargs['match'] if 'match' in kwargs else None
        replace = kwargs['replace'] if 'replace' in kwargs else None
        return VocabDist(self.filename, group_by, self.results, self.punct_pos, self.search_string, match=match, replace=replace)
    # !SECTION


    # SECTION: KWIC Lines
    def kwic_lines(self, before=5, after=5, group_by='lower'):
        return KWIC(self.filename, self.results, before=before, after=after, group_by=group_by, search_string=self.search_string, punct_pos=self.punct_pos)
    # !SECTION


    ### SECTION: Concordance Lines
    # Another alis for KWIC 
    def concordance_lines(self, before=5, after=5, group_by='lower'):
        return KWIC(self.filename, self.results_indices, before=before, after=after, group_by=group_by, search_string=self.search_string, punct_pos=self.punct_pos)
    # !SECTION

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
