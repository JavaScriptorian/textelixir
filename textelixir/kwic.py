import pandas
import re
from pkg_resources import resource_filename
from .exports import export_as_txt
from .filter_indices_by_block import *  # filter_indices_by_block(results, block_num)
from .get_metadata import *
from .get_word_data import *            # get_word_data(basename, word_types)

JSDIR = resource_filename('textelixir', 'js')
CSSDIR = resource_filename('textelixir', 'css')
IMGDIR = resource_filename('textelixir', 'img')

class KWIC:
    def __init__(self, filename, results, before, after, group_by='lower', search_string='', punct_pos=''):
        self.filename = filename
        self.basename = re.sub(r'^(.+)/[^/]+$', r'\1', self.filename)
        self.results = results
        self.before = before
        self.after = after
        self.group_by = group_by
        self.search_string = search_string
        self.punct_pos = punct_pos
        self.punct_word_ids = get_metadata(self.basename, 'word', pos=[self.punct_pos])
        
        self.kwic_lines = self.get_kwic_lines(self.results)

    def get_kwic_lines(self, results):
        kwic_dfs = self.get_kwic_dfs(results)
        return self.get_kwic_text(kwic_dfs)

    
    def get_kwic_dfs(self, results):
        elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=1000000, keep_default_na=False, na_values=[])
        kwic_dfs = []
        unfinished_segments = []
        for block_num, chunk in enumerate(elixir):
            curr_indices = filter_indices_by_block(results, block_num)


            for curr_index in curr_indices:
                w1_order = int(curr_index[0])
                w2_order = int(curr_index[-1])

                next_find = int(w1_order)
                before_indices = []
                
                while len(before_indices) < self.before:
                    next_find -= 1
                    # Check for less than zero boundary.
                    if next_find < 0:
                        break
                    # Get the next word in the chunk.
                    if (next_find >= block_num*1000000 and next_find < (block_num*1000000) + 1000000):
                        next_word = chunk.loc[next_find].word
                    else:
                        next_word = last_chunk[next_find].word

                    if next_word not in self.punct_word_ids:
                        before_indices.append(next_find)

                next_find = int(w2_order)
                after_indices = []
                while len(after_indices) < self.after:
                    next_find += 1
                    # Check for 1mil boundary.
                    if next_find >= (block_num*1000000) + 1000000:
                        unfinished_segments.append({'before': before_indices, 'hit': curr_indices, 'after': after_indices})
                        break
                    # Check for unfinished segments.
                    if len(unfinished_segments) > 0:
                        raise Exception('There are unfinished segments that have not been resolved')
                    
                    try:
                        next_word = chunk.loc[next_find].word
                    except KeyError: # If there is a KeyError here, it means you're at the end of the corpus.
                        break
                    if next_word not in self.punct_word_ids:
                        after_indices.append(next_find)

                kwic_min = before_indices[-1]
                kwic_max = after_indices[-1]

                kwic_df = chunk.loc[kwic_min:kwic_max]
                kwic_dfs.append({'df': kwic_df, 'hits': curr_index})   
            last_chunk = chunk
        return kwic_dfs

    
    def get_kwic_text(self, kwic_dfs):
        kwic_lines = []
        word_data = get_word_data(self.basename, ['prefix', 'lower', 'lemma', 'pos'])
        for kwic_df in kwic_dfs:
            hits = kwic_df['hits']
            df = kwic_df['df']
            row = list(zip(list(df.index), list(df.word)))

            kwic_line = ''
            for word in row:
                prefix = word_data['prefix'][word[1]]
                text = word_data[self.group_by][word[1]]

                if word[0] in hits:
                    if word[0] == hits[0]:
                        kwic_line += '\t'
                    kwic_line += f'{prefix}{text}'

                    if word[0] == hits[-1]:
                        kwic_line += '\t'
                else:
                    kwic_line += f'{prefix}{text}'
            kwic_line = re.sub(r'\t +?', r'\t', kwic_line).strip()
            kwic_lines.append(kwic_line)
        return kwic_lines

    def export_as_txt(self, output_filename):
        return export_as_txt(output_filename, self.kwic_lines, payload=['citation', 'line'])

    def export_as_html(self, output_filename, group_by='text'):
        word_data = get_word_data(self.basename, ['prefix', 'lower', 'lemma', 'pos'])

        for kwic_df in self.kwic_dfs:
            pass

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