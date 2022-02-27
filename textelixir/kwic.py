import pandas

class KWIC:
    def __init__(self, filename, results_indices, before, after, group_by='lower', search_string='', punct_pos=''):
        self.filename = filename
        self.results_indices = results_indices
        self.results_count = len(results_indices)
        if self.results_count == 0:
            return None
        self.before = before
        self.after = after
        self.group_by = group_by
        self.search_string = search_string
        self.punct_pos = punct_pos
        if self.results_count > 0:
            self.kwic_index_ranges = self.calculate_kwic_line_indices()
            self.calculate_kwic_lines()

    def calculate_kwic_line_indices(self):
        self.elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=10000)

        unfinished_kwic = []
        last_chunk = None

        kwic_index_ranges = []


        for block_num, chunk in enumerate(self.elixir):
            # Handle unfinished KWIC lines.
            if block_num > 0 and len(unfinished_kwic) > 0:
                while len(unfinished_kwic) > 0:
                    unfinished = unfinished_kwic[0]
                    if len(unfinished['after']) == 0:
                        collocates_after = self.get_kwic_ocr_after(chunk, block_num, f'{block_num}:-1', unfinished['after'])
                    else:
                        collocates_after = self.get_kwic_ocr_after(chunk, block_num, unfinished['after'][-1], unfinished['after'])
                    kwic_index_ranges.append((unfinished['before_range'], unfinished['search_words'], collocates_after[-1]))
                    unfinished_kwic.pop(0)

            curr_indices = self.filter_indices_by_block(self.results_indices, block_num)
            for curr_index in curr_indices:
                word1 = curr_index[0]
                word2 = curr_index[-1]


                curr_index1 = int(word1.split(':')[-1])
                curr_index2 = int(word2.split(':')[-1])

                block_num1 = int(word1.split(':')[0])
                block_num2 = int(word2.split(':')[0])

                # TODO: Verify that block numbers are appropriately being logged.
                if block_num1 != block_num or block_num2 != block_num:
                    ibrk = 0

                kwic_before = self.get_kwic_ocr_before(last_chunk, chunk, block_num, curr_index1)
                kwic_before_range = kwic_before[-1]


                kwic_after = self.get_kwic_ocr_after(chunk, block_num, curr_index2)
                if len(kwic_after) == self.after:
                    kwic_after_range = kwic_after[-1]
                else:
                    kwic_after_range = None

                if kwic_after_range != None:
                    kwic_index_ranges.append((kwic_before_range, curr_index, kwic_after_range))
                else:
                    unfinished_kwic.append({
                        'before_range': kwic_before_range,
                        'search_words': curr_index,
                        'after': kwic_after
                    })
            last_chunk = chunk

        # Check for any unfinished KWIC lines left untouched at the end of the corpus.
        while len(unfinished_kwic) > 0:
            unf = unfinished_kwic[0]
            if len(unf['after']) == 0:
                kwic_index_ranges.append((unf['before_range'], unf['search_words'], unf['search_words'][-1]))
            else:
                kwic_index_ranges.append((unf['before_range'], unf['search_words'], unf['after'][-1]))
            unfinished_kwic.pop(0)


        return kwic_index_ranges

    def calculate_kwic_lines(self):
        self.kwic_lines = []
        last_chunk = None

        self.full_kwic_index_ranges = self.get_full_index_ranges()
        self.elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=10000)
        for block_num, chunk in enumerate(self.elixir):
            curr_indices = self.filter_indices_by_block(self.full_kwic_index_ranges, block_num)
            
            
            for curr_index in curr_indices:
                dataframe_words_list = []
                for word in curr_index:
                    if '229:5438' in word:
                        ibrk = 0
                    word_block, word_idx = word.split(':')
                    # An exclamation point is added to the word_block if it's a search query word. The is_search_query_word flag helps with formatting later.
                    if word_block.startswith('!'):
                        is_search_query_word = True
                        word_block = word_block[1:]
                    else:
                        is_search_query_word = False
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
            
                kwic_line = ''
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
                        kwic_line += f'\t{word}'
                    elif is_search_query_word == True and i['search_query_word'] == False:
                        is_search_query_word = False
                        kwic_line += f'\t{word}'
                    else:
                        kwic_line += f'{prefix}{word}'
                self.kwic_lines.append(kwic_line.strip())

            last_chunk = chunk

    def get_full_index_ranges(self):
        full_kwic_index_ranges = []

        # Get the range for every word in KWIC lines needed...
        for curr_index in self.kwic_index_ranges:
            min_index = curr_index[0]
            max_index = curr_index[-1]

            min_block, min_idx = min_index.split(':')
            min_block = int(min_block)
            min_idx = int(min_idx)

            max_block, max_idx = max_index.split(':')
            max_block = int(max_block)
            max_idx = int(max_idx)
            
            # Check for any block crossing.
            kwic_ocr_indices = []
            if min_block != max_block:
                for i in range(min_idx, 10000):
                    if f'{min_block}:{i}' in curr_index[1]:
                        kwic_ocr_indices.append(f'!{min_block}:{i}')
                    else:
                        kwic_ocr_indices.append(f'{min_block}:{i}')
                for i in range(0, max_idx):
                    if f'{max_block}:{i}' in curr_index[1]:
                        kwic_ocr_indices.append(f'!{max_block}:{i}')
                    else:
                        kwic_ocr_indices.append(f'{max_block}:{i}')
            else:
                for i in range(min_idx, max_idx+1):
                    # Check to see if the word is part of the search query. Add an ! next to it if so.
                    if f'{min_block}:{i}' in curr_index[1]:
                        kwic_ocr_indices.append(f'!{min_block}:{i}')
                    else:
                        kwic_ocr_indices.append(f'{min_block}:{i}')
            kwic_ocr_indices = tuple(kwic_ocr_indices)
            full_kwic_index_ranges.append(kwic_ocr_indices)
        return full_kwic_index_ranges
    
    def filter_indices_by_block(self, results_indices, block_num):
        filtered_indices = []
        for index in results_indices:
            curr_block_num, word_num = index[-1].split(':')
            if int(curr_block_num) == block_num:
                filtered_indices.append(index)
        return filtered_indices

    # Filters the results_indices list to get only the word citations with the same block number.
    def filter_indices_by_block(self, results_indices, block_num):
        filtered_indices = []
        for index in results_indices:
            curr_block_num, word_num = index[-1].split(':')
            if curr_block_num.startswith('!'):
                curr_block_num = curr_block_num[1:]
            if int(curr_block_num) == block_num:
                filtered_indices.append(index)
        return filtered_indices

    def get_kwic_ocr_before(self, last_chunk, chunk, block_num, curr_index, kwic_list=None):
        # Check to see if kwic_list is None
        if kwic_list is None:
            kwic_list = []
        if len(kwic_list) == self.before:
            return kwic_list
        
        # Get the number of the previous word.
        find_index = curr_index-1
        
        if find_index < 0:
            find_index = 10000+curr_index-1
            # If last_chunk is None, then we are at the beginning of block 0.
            if last_chunk is None:
                return kwic_list
            # Otherwise, we can check the last chunk to get the next word.
            previous_word = last_chunk.iloc[find_index]
            used_block_num = block_num-1
        else:
            used_block_num = block_num
            previous_word = chunk.iloc[find_index]


        # If the pos is PUNCT, let's ignore it and continue to the next word.
        if previous_word['pos'] == 'PUNCT':
            kwic_list = self.get_kwic_ocr_before(last_chunk, chunk, block_num, curr_index-1, kwic_list)
        else:
            kwic_list.append(f'{used_block_num}:{find_index}')
        if len(kwic_list) != self.before:
            kwic_list = self.get_kwic_ocr_before(last_chunk, chunk, block_num, curr_index-1, kwic_list)

        return kwic_list


    def get_kwic_ocr_after(self, chunk, block_num, curr_index, kwic_list=None):
        if kwic_list is None:
            kwic_list = []
        if len(kwic_list) == self.after:
            return kwic_list

        # Get the number of the next word
        if isinstance(curr_index, str):
            find_index = 0
            curr_index = -1
        else:
            find_index = curr_index+1

        if find_index > 9999:
            # If the find_index is greater than the chunk size, we will need to add it to the unfinished category.
            return kwic_list
        else:
            try:
                next_word = chunk.iloc[find_index]
            except IndexError:
                return kwic_list

        # If the pos is PUNCT, let's ignore it and continue to the next word.
        if next_word['pos'] == 'PUNCT':
            kwic_list = self.get_kwic_ocr_after(chunk, block_num, curr_index+1, kwic_list)
        else:
            kwic_list.append(f'{block_num}:{find_index}')
        
        if len(kwic_list) != self.after:
            kwic_list = self.get_kwic_ocr_after(chunk, block_num, curr_index+1, kwic_list)

        return kwic_list

    def export_as_html(self, output_filename, group_by='text', ignore_punctuation=False):
        if self.results_count == 0:
            print('Cannot export KWIC lines when there are no results.')
            return
        text = f'<html><head><title>{self.search_string} KWIC Lines</title><link href="https://cdn.jsdelivr.net/npm/halfmoon@1.1.1/css/halfmoon-variables.min.css" rel="stylesheet" /><style>.table td, .table th {{padding: 0;}} .punct {{ color: #9c9c9c;}}</style></head><body><div class="container"><h1>KWIC Lines for "{self.search_string}"</h1><p>Click headers to sort</p>'
        table = '<table class="table" id="table">\n'
        
        self.elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=10000)
        for block_num, chunk in enumerate(self.elixir):
            # Gets the word indices that are directly available in this current block_num
            curr_indices = self.filter_indices_by_block(self.full_kwic_index_ranges, block_num)
            for kwic_line in curr_indices:

                tcells = []
                # Split the index into block numbers and index
                for word in kwic_line:
                    word_block, word_idx = word.split(':')
                    if word_block.startswith('!'):
                        is_search_query_word = True
                        word_block = word_block[1:]
                    else:
                        is_search_query_word = False
                    curr_block_num = int(word_block)
                    curr_block_index = int(word_idx)
                    # If the curr_block_num is not the same as the block_num, then get data from last chunk
                    if curr_block_num != block_num:
                        word = last_chunk.iloc[curr_block_index]
                    else:
                        word = chunk.iloc[curr_block_index]
                    
                    
                    if word['pos'] in self.punct_pos:
                        if len(tcells) == 0:
                            tcells.append(f'<span class="punct">{word[group_by]}</span>')
                        else:
                            tcells[-1] += f'<span class="punct">{word[group_by]}</span>'
                    else:
                        prefix = str(word['prefix'])
                        # TODO: Make this more apparent in the tagger!!!
                        if prefix == 'nan':
                            prefix = ''
                        if is_search_query_word:
                            tcells.append(
                                f'!<strong><span class="pre">{prefix}</span><span class="w" data-pos="{word["pos"]}" data-lemma="{word["lemma"]}" data-text="{word["text"]}">{word[group_by]}</span></strong>'
                            )
                        else:
                            tcells.append(
                                f'<span class="pre">{prefix}</span><span class="w" data-pos="{word["pos"]}" data-lemma="{word["lemma"]}" data-text="{word["text"]}">{word[group_by]}</span>'
                            )
                  
                # Get index of the first and last items that start with a !                
                search_word_tcell_indices = [tcells.index(i) for i in tcells if i.startswith('!')]
                # Good freaking luck trying to parse out what this means.
                # Basically the first and 3rd elements are just getting all the words before and after the search words.
                # The second one then combines all words that are within the range of the search string, removes the ! from the beginning of it, and adds <strong> tag around it.
                tcells_left = '<td class="text-right">'+ ''.join([*tcells[:search_word_tcell_indices[0]]]) + '</td>'
                tcells_right = '<td>' + ''.join([*tcells[search_word_tcell_indices[-1]+1:]]) + '</td>'
                
                tcells = [
                            *tcells_left,
                            '<td class="text-center">' + ''.join([i[1:] for i in tcells[search_word_tcell_indices[0]:search_word_tcell_indices[-1]+1]]) + '</td>',
                            *tcells_right   
                        ]

                tcells = ''.join(tcells)
                trow = f'<tr>{tcells}</tr>\n'
                table += trow
            last_chunk = chunk
        table += '</table>\n'
        with open(output_filename, 'w', encoding='utf-8') as file_out:
            print(text, file=file_out)
            print(table, file=file_out)
            print('</div>\n</body>\n</html>\n', file=file_out)