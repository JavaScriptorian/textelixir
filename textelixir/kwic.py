import pandas
from pkg_resources import resource_filename
from .citations import get_citation
from .exports import export_as_txt
from .getwords import get_previous_word
from .getwords import get_next_word

JSDIR = resource_filename('textelixir', 'js')
CSSDIR = resource_filename('textelixir', 'css')
IMGDIR = resource_filename('textelixir', 'img')

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
                    raise Exception('Jesse, this is broken! You dimwit....')
                    # unfinished = unfinished_kwic[0]
                    # if len(unfinished['after']) == 0:
                    #     collocates_after = self.get_kwic_ocr_after(chunk, block_num, f'{block_num}:-1', unfinished['after'])
                    # else:
                    #     collocates_after = self.get_kwic_ocr_after(chunk, block_num, unfinished['after'][-1], unfinished['after'])
                    # kwic_index_ranges.append((unfinished['before_range'], unfinished['search_words'], collocates_after[-1]))
                    # unfinished_kwic.pop(0)

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

                kwic_before = get_previous_word(last_chunk, chunk, block_num, curr_index1, self.before)
                kwic_before_range = next(iter(kwic_before[-1].keys()))

                kwic_after = get_next_word(chunk, block_num, curr_index2, self.after)
                if len(kwic_after) == self.after:
                    kwic_after_range = next(iter(kwic_after[-1].keys()))
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
                kwic_index_ranges.append((unf['before_range'], unf['search_words'], next(iter(unf['after'][-1]))))

                
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
                # Here we are going to identify the first search word so that we can use it to show the citation of the KWIC line.
                first_search_word = False 
                
                for word in curr_index:
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

                    if is_search_query_word == True and first_search_word == False:
                        first_search_word = True
                        cit = get_citation(dataframe_words_list[-1]['word'])

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
                self.kwic_lines.append({'citation': cit, 'line':kwic_line.strip()})
                ibrk = 0

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



    def export_as_txt(self, output_filename):
        return export_as_txt(output_filename, self.kwic_lines, payload=['citation', 'line'])

    def export_as_html(self, output_filename, group_by='text', ignore_punctuation=False):
        if self.results_count == 0:
            print('Cannot export KWIC lines when there are no results.')
            return

        text = f'<html>\n<head>\n<title>{self.search_string} KWIC Lines</title>\n<meta charset="utf-8" />\n<link rel="stylesheet" href="https://unpkg.com/tippy.js@6/themes/light.css" />\n<link href="https://cdn.jsdelivr.net/npm/halfmoon@1.1.1/css/halfmoon-variables.min.css" rel="stylesheet" />\n<link rel="stylesheet" href="{CSSDIR}/kwic.css">\n</head>\n<body>\n<div class="container">\n<h1 class="text-center">KWIC Lines for "{self.search_string}"</h1>\n<input class="btn copyAll align-left" id="copyButton" type="button" value="Copy All"><input type="button" id="showAll" value="Table Options" class="btn align-right">'
        dots = '<td class="text-right">'
        b = 0
        a = 0
        while b < self.before:
            dots += f'<span class="dot" data-order="l{b}"></span>'
            b += 1
        dots +=f'</td><td class="text-center"><span class="dot" data-order="c"></span></td><td>'
        while a < self.after:
            dots += f'<span class="dot" data-order="r{a}"></span>'
            a += 1
        
        table = f'<table class="table" id="table">\n<thead><tr><td class="text-right">Before</td><td class="text-center">Hit</td><td>After</td></tr>\n<tr>{dots}</td></tr>\n</thead>\n<tbody>'
            

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
                tcells_right = '<td>' + ''.join([*tcells[search_word_tcell_indices[-1]+1:]]) + f'<img src="{IMGDIR}/copy-solid.svg" class="btn-sm hide copyBtn align-right" onclick="copyRow()"></td>'
                tcells_center = '<td class="text-center">' 
                # tcells_copy = '<td></td>'
                for i in tcells[search_word_tcell_indices[0]:search_word_tcell_indices[-1]+1]:
                    if i.startswith('!'):
                        tcells_center += i[1:]
                    else:
                        tcells_center += i
                tcells = [
                            *tcells_left,
                            tcells_center,
                            *tcells_right   
                        ]

                tcells = ''.join(tcells)
                trow = f'<tr>{tcells}</tr>\n'
                table += trow
            last_chunk = chunk
        table += '</tbody></table>\n'
        with open(output_filename, 'w', encoding='utf-8') as file_out:
            print(text, file=file_out)
            print(table, file=file_out)
            # TODO: Think about fixing this issue later... But it might be ok. :)
            print(f'</div>\n<script src="{JSDIR}/kwic.js"></script>\n<!-- Tippy Development -->\n<script src="https://unpkg.com/@popperjs/core@2/dist/umd/popper.min.js"></script>\n<script src="https://unpkg.com/tippy.js@6/dist/tippy-bundle.umd.js"></script>\n\n<!-- Tippy Production -->\n<script src="https://unpkg.com/@popperjs/core@2"></script>\n<script src="https://unpkg.com/tippy.js@6"></script>\n\n\n<script>\nconst hideTippy = (instance) => {{\n setTimeout (() => {{\n let buttons = document.querySelectorAll("div.tippy-content input");\n buttons.forEach(element => {{\n element.addEventListener("click", function () {{\n instance.hide();\n }})\n }});\n }}, 200)\n}}\ntippy(".dot", {{\ncontent: `\n<div>\n<div id="sort">\n<h2 class="text-center">sort</h2>\n<input class="btn btn-alpha" id="A-Z" type="button" value="A-Z">\n<input class="btn btn-alpha" id="Z-A" type="button" value="Z-A">\n</div>\n<div id="show">\n<h2 class="text-center">show</h2>\n<div class="center btn-group-toggle" id="buttons" data-toggle="buttons">\n<input class="btn btn-showtype" id="lemma" type="button" value="lemma">\n<input class="btn btn-showtype" id="word" type="button" value="word">\n<input class="btn btn-showtype" id="pos" type="button" value="POS">\n</div>\n</div>\n</div>`,\nplacement: "bottom",\nallowHTML: true,\ninteractive: true,\ntheme: "light",\nanimation: "fade",\n trigger: "click", onShow(instance){{\nhideTippy(instance)}},}})\n tippy("#showAll", {{content: `<div><div id="show"><h2 class="text-center">show</h2><div class="center btn-group-toggle" id="buttons" data-toggle="buttons"><input class="btn btn-showtype" id="lemma" type="button" value="lemma"><input class="btn btn-showtype" id="word" type="button" value="word"><input class="btn btn-showtype" id="pos" type="button" value="POS"></div></div></div>`,placement: "bottom",allowHTML: true,interactive: true,theme: "light",animation: "fade",trigger: "click", onShow(instance){{\nhideTippy(instance)}}}})</script></body>\n</html>\n', file=file_out)