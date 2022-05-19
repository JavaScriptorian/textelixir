import pandas
from .exports import export_as_txt 

class Sentences:
    def __init__(self, filename, results_indices, group_by, search_string):
        self.filename = filename
        self.results_indices = results_indices
        self.group_by = group_by
        self.search_string = search_string
        if len(self.results_indices) > 0:
            self.sentence_index_ranges = self.calculate_sentence_indices()
            self.calculate_sentence_lines()
        else:
            # Leave it empty if there are no search results.
            self.sentences = []

    def calculate_sentence_indices(self):
        self.elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=10000)

        unfinished_sentences = []
        last_chunk = None

        sentence_index_ranges = []

        for block_num, chunk in enumerate(self.elixir):
            # Handle unfinished sentence lines.
            if block_num > 0 and len(unfinished_sentences) > 0:
                while len(unfinished_sentences) > 0:
                    unf = unfinished_sentences[0]
                    if len(unf['after']) == 0:
                        sentence_after = self.get_sentence_ocr_after(chunk, block_num, f'{block_num}:-1', unf['word_citation'], unf['after'])
                    else:
                        sentence_after = self.get_sentence_ocr_after(chunk, block_num, unf['after'][-1], unf['word_citation'], unf['after'])
                    # kwic_index_ranges.append((unfinished['before_range'], unfinished['search_words'], collocates_after[-1]))
                    sentence_index_ranges.append((unf['before_range'], unf['search_words'], unf['after'][-1]))
                    unfinished_sentences.pop(0)

            curr_indices = self.filter_indices_by_block(self.results_indices, block_num)
            for curr_index in curr_indices:
                word1 = curr_index[0]
                word2 = curr_index[-1]

                # Verify that word1 and word2 citations are the same. Skip if not in the same sentence.
                word1_citation = self.get_citation(chunk, last_chunk, block_num, word1)
                word2_citation = self.get_citation(chunk, last_chunk, block_num, word2)
                if word1_citation != word2_citation:
                    continue

                ibrk = 0

                curr_index1 = int(word1.split(':')[-1])
                curr_index2 = int(word2.split(':')[-1])

                block_num1 = int(word1.split(':')[0])
                block_num2 = int(word2.split(':')[0])

                # TODO: Verify that block numbers are appropriately being logged.
                if block_num1 != block_num or block_num2 != block_num:
                    ibrk = 0

                if block_num == 105 and curr_index1 == 6279:
                    ibrk = 0
                sentence_before = self.get_sentence_ocr_before(last_chunk, chunk, block_num, curr_index1, word1_citation)
                
                # If the word is the first word in the sentence, then sentence_before is empty.
                if len(sentence_before) == 0:
                    sentence_before_range = '^'
                else:
                    sentence_before_range = sentence_before[-1]




                sentence_after = self.get_sentence_ocr_after(chunk, block_num, curr_index2, word2_citation)
                # If the search word is the last word in sentence, then set the last word in sentence_after to the word index of the last word in the search query.
                if len(sentence_after) == 0:
                    sentence_after.append(curr_index[-1])
                # Check to see if sentence requires to go into the unfinished_sentences list.
                if '$BLOCKLENGTH%=' in sentence_after:
                    sentence_after.pop(-1)
                    unfinished_sentences.append({
                        'before_range': sentence_before_range,
                        'search_words': curr_index,
                        'after': sentence_after,
                        'word_citation': word1_citation
                    })
                else:
                    
                    sentence_after_range = sentence_after[-1]
                    sentence_index_ranges.append((sentence_before_range, curr_index, sentence_after_range))
            last_chunk = chunk

        # Check for any unfinished KWIC lines left untouched at the end of the corpus.
        while len(unfinished_sentences) > 0:
            unf = unfinished_sentences[0]
            sentence_index_ranges.append((unf['before_range'], unf['search_words'], unf['after'][-1]))
            unfinished_sentences.pop(0)
        return sentence_index_ranges


    def filter_indices_by_block(self, results_indices, block_num):
        filtered_indices = []
        for index in results_indices:
            curr_block_num, word_num = index[-1].split(':')
            # Remove the ! from the beginning of curr_block_num.
            if '!' in curr_block_num:
                curr_block_num = curr_block_num[1:]
            
            if int(curr_block_num) == block_num:
                filtered_indices.append(index)
        return filtered_indices

    def get_citation(self, chunk, last_chunk, block_num, word1):
        if word1.startswith('!'):
            word1 = word1[1:]
        word_block_num = int(word1.split(':')[0])
        word_index = int(word1.split(':')[1])


        headers = list(chunk.columns.values)
        index_of_word_index = headers.index('word_index')
        citation_headers = headers[0:index_of_word_index]
        if word_block_num < block_num:
            citation = [last_chunk.iloc[word_index][i] for i in citation_headers]
        elif word_block_num == block_num:
            citation = '/'.join([str(chunk.iloc[word_index][i]) for i in citation_headers])
        else:
            print('PROBLEM!')
            ibrk = 0
        return citation

    def get_sentence_ocr_before(self, last_chunk, chunk, block_num, curr_index, word_citation, sentence_list=None):
        # Check to see if kwic_list is None
        if sentence_list is None:
            sentence_list = []
        
        # Get the number of the previous word.
        find_index = curr_index-1
        
        if find_index < 0:
            find_index = 10000+curr_index-1
            # If last_chunk is None, then we are at the beginning of block 0.
            if last_chunk is None:
                return sentence_list
            # Otherwise, we can check the last chunk to get the next word.
            previous_word = last_chunk.iloc[find_index]
            used_block_num = block_num-1
        else:
            used_block_num = block_num
            previous_word = chunk.iloc[find_index]

        previous_word_citation = self.get_citation(chunk, last_chunk, block_num, f'{used_block_num}:{find_index}')

        if previous_word_citation == word_citation:
            sentence_list.append(f'{used_block_num}:{find_index}')
            sentence_list = self.get_sentence_ocr_before(last_chunk, chunk, block_num, curr_index-1, word_citation, sentence_list)
        else:
            return sentence_list

        return sentence_list

    def get_sentence_ocr_after(self, chunk, block_num, curr_index, word_citation, sentence_list=None):
        if sentence_list is None:
            sentence_list = []

        # Get the number of the next word
        if isinstance(curr_index, str):
            find_index = 0
            curr_index = -1
        else:
            find_index = curr_index+1

        if find_index > 9999:
            # If the find_index is greater than the chunk size, we will need to add it to the unfinished category.
            sentence_list.append('$BLOCKLENGTH%=')
            return sentence_list
        else:
            try:
                next_word = chunk.iloc[find_index]
            except IndexError:

                return sentence_list

        # If the pos is PUNCT, let's ignore it and continue to the next word.
        next_word_citation = self.get_citation(chunk, None, block_num, f'{block_num}:{find_index}')


        if next_word_citation == word_citation:
            sentence_list.append(f'{block_num}:{find_index}')
            sentence_list = self.get_sentence_ocr_after(chunk, block_num, curr_index+1, word_citation, sentence_list)
        else:
            return sentence_list

        return sentence_list


    def calculate_sentence_lines(self):
        self.sentences = []
        last_chunk = None

        full_sentence_index_ranges = self.get_full_index_ranges()
        
        self.elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=10000)
        for block_num, chunk in enumerate(self.elixir):
            curr_indices = self.filter_indices_by_block(full_sentence_index_ranges, block_num)
            
            for curr_index in curr_indices:
                dataframe_words_list = []
                for word in curr_index:
                    word_block, word_idx = word.split(':')
                    # An exclamation point is added to the word_block if it's a search query word. The is_search_query_word flag helps with formatting later.
                    if word_block.startswith('!'):
                        is_search_query_word = True
                        word_block = word_block[1:]
                    else:
                        is_search_query_word = False
                        False
                    word_block = int(word_block)
                    word_idx = int(word_idx)

                    if word_block == block_num:
                        dataframe_words_list.append({
                            'word': chunk.iloc[word_idx],
                            'search_query_word': is_search_query_word
                        })
                    else:
                        dataframe_words_list.append({
                            'word': last_chunk.iloc[word_idx],
                            'search_query_word': is_search_query_word
                        })
            
                sentence_line = ''
                # Set a boolean to know when to add a tab between words.
                is_search_query_word = False
                for i in dataframe_words_list:
                    prefix = str(i['word']['prefix'])
                    # TODO: Make this more apparent in the tagger!!!
                    if prefix == 'nan':
                        prefix = ''

                    # Handle different group_by options.
                    if self.group_by == 'lemma_pos':
                        word = f'{i["word"]["lemma"]}_{i["word"]["pos"]}'
                    elif self.group_by == 'lower_pos':
                        word = f'{i["word"]["lower"]}_{i["word"]["pos"]}'
                    else:
                        word = i['word'][self.group_by]

                    if is_search_query_word == False and i['search_query_word'] == True:
                        is_search_query_word = True
                        sentence_line += f'\t{word}'
                    elif is_search_query_word == True and i['search_query_word'] == False:
                        is_search_query_word = False
                        sentence_line += f'\t{word}'
                    else:
                        sentence_line += f'{prefix}{word}'
                self.sentences.append(
                    {   
                        'cit': self.get_citation(chunk, last_chunk, block_num, curr_index[-1]),
                        'sent': sentence_line.strip()
                    }
                )

            last_chunk = chunk

    
    def get_full_index_ranges(self):
        full_sentence_index_ranges = []

        # Get the range for every word in KWIC lines needed...
        for curr_index in self.sentence_index_ranges:

            min_index = curr_index[0]
            max_index = curr_index[-1]

            # Get min block and index. If first word of sentence is in search term, 
            if min_index == '^':
                min_block, min_idx = [int(i) for i in curr_index[1][0].split(':')]
            else:
                min_block, min_idx = [int(i) for i in min_index.split(':')]
            # Get max block and index.
            max_block, max_idx = [int(i) for i in max_index.split(':')]
            sentence_ocr_indices = []
            # Check for any block crossing.
            if min_block != max_block:
                if min_block != None:
                    for i in range(min_idx, 10000):
                        # If the word occurrence is this one, add ! to the beginning of it.
                        if f'{min_block}:{i}' in curr_index[1]:
                            sentence_ocr_indices.append(f'!{min_block}:{i}')
                        else:
                            sentence_ocr_indices.append(f'{min_block}:{i}')
                for i in range(0, max_idx):
                    if f'{max_block}:{i}' in curr_index[1]:
                        sentence_ocr_indices.append(f'!{max_block}:{i}')
                    else:
                        sentence_ocr_indices.append(f'{max_block}:{i}')
            else:
                for i in range(min_idx, max_idx+1):
                    # Check to see if the word is part of the search query. Add an ! next to it if so.
                    if f'{min_block}:{i}' in curr_index[1]:
                        sentence_ocr_indices.append(f'!{min_block}:{i}')
                    else:
                        sentence_ocr_indices.append(f'{min_block}:{i}')
            sentence_ocr_indices = tuple(sentence_ocr_indices)
            full_sentence_index_ranges.append(sentence_ocr_indices)
        return full_sentence_index_ranges

    def export_as_txt(self, filename):
        return export_as_txt(filename, state=self.sentences, payload=['cit', 'sent'])


    def export_as_html(self, filename, group_by='text', ignore_punctuation=False):
        assert Exception('Sorry, this is not ready yet!')