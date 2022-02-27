import csv
import json
from math import log2
import pandas
import re
from .scripts import copy_btn
from .scripts import sort_alpha
from .scripts import sort_num

class Collocates:
    def __init__(self, filename, results_indices, before, after, word_count, group_by, mi_threshold=3, sample_size_threshold=2, search_string=''):
        self.filename = filename
        self.results_indices = results_indices
        self.results_count = len(results_indices)
        self.before = before
        self.after = after
        self.word_count = word_count    # Total words in corpus
        self.group_by = group_by
        self.mi_threshold = mi_threshold
        self.sample_size_threshold = sample_size_threshold
        self.search_string = search_string

        if self.results_count > 0:
            # Adds the self.collocates_before and self.collocates_after to Collocates class.
            self.calculate_collocate_samples()
            # Looks up each word and returns
            self.collocates_before = self.collocate_lookup(self.collocates_before)
            self.collocates_after = self.collocate_lookup(self.collocates_after)
            self.sample = self.combine_collocates(self.collocates_before, self.collocates_after)

    def __str__(self):
        return str(dict(sorted(self.sample.items(), key=lambda k: k[1], reverse=True)))

    def __repr__(self):
        return str(dict(sorted(self.sample.items(), key=lambda k: k[1], reverse=True)))

    def calculate_collocate_samples(self):
        self.elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=10000)
        
        unfinished_collocations = []
        last_chunk = None
    
        # Initialize the collocates that will hold all the word IDs of collocating words.
        collocates_before_set = set()
        collocates_after_set = set()


        for block_num, chunk in enumerate(self.elixir):
            if block_num > 0 and len(unfinished_collocations) > 0:
                while len(unfinished_collocations) > 0:
                    # TODO: If triggered, collocates get messed up!!!
                    unfinished_collocation = unfinished_collocations[0]
                    curr_index = unfinished_collocation['curr_index']
                    collocates_after = self.get_collocates_after(chunk, block_num, unfinished_collocation['curr_index'], unfinished_collocation['collocates'])
                    for collocate in collocates_after:
                        collocates_after_set.add((collocate,))
                    unfinished_collocations.pop(0)
            

            curr_indices = self.filter_indices_by_block(self.results_indices, block_num)
            for curr_index in curr_indices:
                # Calculate the collocates BEFORE
                word1 = curr_index[0]
                word2 = curr_index[-1]

                curr_index1 = int(word1.split(':')[-1])
                curr_index2 = int(word2.split(':')[-1])

                block_num1 = int(word1.split(':')[0])
                block_num2 = int(word2.split(':')[0])
                
                if block_num1 != block_num or block_num2 != block_num:
                    ibrk = 0

                collocates_before = self.get_collocates_before(last_chunk, chunk, block_num, curr_index1)
                for collocate in collocates_before:
                    collocates_before_set.add((collocate,))
                
                # Calculate the collocates AFTER
                collocates_after = self.get_collocates_after(chunk, block_num, curr_index2)
                # Send collocates_after list to unfinished list if it's not the right length.
                if len(collocates_after) != self.after:
                    unfinished_collocations.append({
                        'collocates': collocates_after,
                        'curr_index': word2
                    })
                # Otherwise, add it to the collocates_after_count dictionary.
                else:
                    for collocate in collocates_after:
                        collocates_after_set.add((collocate,))
            last_chunk = chunk
        
        # Check to see if any collocations are left unfinished.
        while len(unfinished_collocations) > 0:
            unfinished_collocation = unfinished_collocations[0]
            collocates_after = self.get_collocates_after(chunk, block_num, unfinished_collocation['curr_index'], unfinished_collocation['collocates'])
            for collocate in collocates_after:
                collocates_after_set.add((collocate,))
            unfinished_collocations.pop(0)

        self.collocates_before = collocates_before_set
        self.collocates_after = collocates_after_set
        print(f'Found {len(collocates_before_set)+len(collocates_after_set)} collocates.')
        ibrk = 0

    def get_collocates_before(self, last_chunk, chunk, block_num, curr_index, collocate_list=None):
        # Check to see if collocate_list is None
        if collocate_list is None:
            collocate_list = []
        if len(collocate_list) == self.before:
            return collocate_list
        
        # Get the number of the previous word.
        find_index = curr_index-1
        
        if find_index < 0:
            find_index = 10000+curr_index-1
            # If last_chunk is None, then we are at the beginning of block 0.
            if last_chunk is None:
                return collocate_list
            # Otherwise, we can check the last chunk to get the next word.
            previous_word = last_chunk.iloc[find_index]
            used_block_num = block_num-1
        else:
            used_block_num = block_num
            previous_word = chunk.iloc[find_index]


        # If the pos is PUNCT, let's ignore it and continue to the next word.
        if previous_word['pos'] == 'PUNCT':
            collocate_list = self.get_collocates_before(last_chunk, chunk, block_num, curr_index-1, collocate_list)
        else:
            collocate_list.append(f'{used_block_num}:{find_index}')
        if len(collocate_list) != self.before:
            collocate_list = self.get_collocates_before(last_chunk, chunk, block_num, curr_index-1, collocate_list)

        return collocate_list
    
    def get_collocates_after(self, chunk, block_num, curr_index, collocate_list=None):
        if collocate_list is None:
            collocate_list = []
        if len(collocate_list) == self.after:
            return collocate_list

        # Get the number of the next word
        # Get the number of the next word
        if isinstance(curr_index, str):
            find_index = 0
            curr_index = -1
        else:
            find_index = curr_index+1

        if find_index > 9999:
            # If the find_index is greater than the chunk size, we will need to add it to the unfinished category.
            return collocate_list
        else:
            try:
                next_word = chunk.iloc[find_index]
            except IndexError:
                return collocate_list

        # If the pos is PUNCT, let's ignore it and continue to the next word.
        if next_word['pos'] == 'PUNCT':
            collocate_list = self.get_collocates_after(chunk, block_num, curr_index+1, collocate_list)
        else:
            collocate_list.append(f'{block_num}:{find_index}')
        
        if len(collocate_list) != self.after:
            collocate_list = self.get_collocates_after(chunk, block_num, curr_index+1, collocate_list)

        return collocate_list


    # Filters the results_indices list to get only the word citations with the same block number.
    def filter_indices_by_block(self, results_indices, block_num):
        filtered_indices = []
        for index in results_indices:
            curr_block_num, word_num = index[-1].split(':')
            if int(curr_block_num) == block_num:
                filtered_indices.append(index)
        return filtered_indices

    # Returns the word based on the group_by format.
    def collocate_lookup(self, collocate_id_set):
        # Determine format of word lookup by self.group_by
        search_type_list = self.group_by.split('_')

        collocate_dict = {}
        self.elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=10000)
        for block_num, chunk in enumerate(self.elixir):
            curr_indices = self.filter_indices_by_block(collocate_id_set, block_num)
            for index in curr_indices:
                # Get the word dataframe from the list.
                word_df = chunk.iloc[int(index[0].split(':')[-1])]
                # Format the word with an underscore between each search type.
                formatted_word = []
                for search_type in search_type_list:
                    w = word_df[search_type]
                    if search_type == 'pos':
                        formatted_word.append(f'/{w}/')
                    else:
                        formatted_word.append(w)
                formatted_word = '_'.join(formatted_word)
                
                if formatted_word not in collocate_dict:
                    collocate_dict[formatted_word] = 0
                collocate_dict[formatted_word] += 1
        
        return collocate_dict

    def combine_collocates(self, a, b):
        return {k: a.get(k, 0) + b.get(k, 0) for k in set(a) | set(b)}

    def set_total(self, total_dict):
        self.total = total_dict

    def calculate_friends(self):
        print('Calculating best collocating words (friends).')
        self.friends = []
        for word, sample in self.sample.items():
            o11 = sample
            C1 = self.total[word]
            R1 = self.results_count
            Total = self.word_count
            e11 = C1 * (R1/Total)
            MI = log2(o11/e11)
            # To get e11, you need C1, R1, and Total
            if MI >= self.mi_threshold and o11 >= self.sample_size_threshold:
                self.friends.append({
                    'word': word,
                    'sample': o11,
                    'total': C1,
                    'mi': round(MI, 2),
                    'expected': round(e11, 2)
                })
        self.friends = sorted(self.friends, key = lambda i: i['sample'], reverse=True)

    def export_as_txt(self, output_filename):
        with open(output_filename, 'w', encoding='utf-8') as file_out:

            for idx, friend in enumerate(self.friends):
                if '_' in friend['word']:
                    word, pos = friend['word'].split('_')
                    pos = re.sub(r'/', r'', pos)
                    headers = 'word\tpos\tsample\ttotal\texpected\tMI'

                    if idx == 0:
                        print(f'search term: {self.search_string}', file=file_out)
                        print(headers, file=file_out)
                    print(f'{friend["word"]}\t{pos}\t{friend["sample"]}\t{friend["total"]}\t{friend["expected"]}\t{friend["mi"]}', file=file_out)
                else:
                    word = friend['word']
                    headers = 'word\tsample\ttotal\texpected\tMI'

                    if idx == 0:
                        print(f'search term: {self.search_string}', file=file_out)                    
                        print(headers, file=file_out)
                    print(f'{friend["word"]}\t{friend["sample"]}\t{friend["total"]}\t{friend["expected"]}\t{friend["mi"]}', file=file_out)
                

    def export_as_csv(self, output_filename):
        with open(output_filename, 'w', encoding='utf-8', newline='') as file_out:
            writer = csv.writer(file_out) 
            for idx, friend in enumerate(self.friends):
                if '_' in friend['word']:
                    word, pos = friend['word'].split('_')
                    pos = re.sub(r'/', r'', pos)
                    data = [word, pos, friend['sample'], friend['total'], friend['expected'], friend['mi']] 
                    
                    if idx == 0:
                        writer.writerow(['search term', self.search_string])
                        writer.writerow(['word', 'pos', 'sample', 'total', 'expected', 'MI'])            
                    writer.writerow(data)
                else:
                    word = friend['word']
                    data = [word, friend['sample'], friend['total'], friend['expected'], friend['mi']]
                    
                    if idx == 0:
                       writer.writerow(['word', 'sample', 'total', 'expected', 'MI'])            
                    writer.writerow(data) 

    def export_as_tsv(self, output_filename):
        # collocates_list = []        
        with open(output_filename, 'w', encoding='utf-8', newline='') as file_out:            
            writer = csv.writer(file_out, delimiter='\t')
            for idx, friend in enumerate(self.friends):
                if '_' in friend['word']:
                    word, pos = friend['word'].split('_')
                    pos = re.sub(r'/', r'', pos)
                    data = [word, pos, friend['sample'], friend['total'], friend['expected'], friend['mi']] 
                    
                    if idx == 0:
                        writer.writerow(['word', 'pos', 'sample', 'total', 'expected', 'MI'])
                    writer.writerow(data)
                else:
                    word = friend['word']
                    data = [word, friend['sample'], friend['total'], friend['expected'], friend['mi']]
                    
                    if idx == 0:
                       writer.writerow(['search term', self.search_string])
                       writer.writerow(['word', 'sample', 'total', 'expected', 'MI'])            
                    writer.writerow(data)


    def export_as_json(self, output_filename):
        collocates_list = []
        with open(output_filename, 'w', encoding='utf-8') as file_out:                   
            for idx, friend in enumerate(self.friends):
                if '_' in friend['word']:
                    pos = friend['word'].split('_')[-1]
                    pos = re.sub(r'/', r'', pos)
                    data = {'word': friend['word'], 'pos': pos, 'sample': friend['sample'], 'total': friend['total'], 'expected': friend['expected'], 'mi': friend['mi']}
                else:
                    data = {'word': friend['word'], 'sample': friend['sample'], 'total': friend['total'], 'expected': friend['expected'], 'mi': friend['mi']}

                collocates_list.append(data)

            # TODO: Jesse, add search query to Collocates class.
            json_data = json.dumps({'search_string': self.search_string,
                                    'collocates': collocates_list}, ensure_ascii=False)
            print(json_data, file=file_out)

    def export_as_html(self, output_filename):
        with open(output_filename, 'w', encoding='utf-8') as file_out:

            text = f'<html><head><title>{self.search_string} Collocates</title><link href="https://cdn.jsdelivr.net/npm/halfmoon@1.1.1/css/halfmoon-variables.min.css" rel="stylesheet" /></head><body><div class="container"><h1>Collocates for "{self.search_string}"</h1><p>Click headers to sort</p><input id="copy_btn" type="button" value="Copy Table"></p>'
            table = '<table class="table" id="table">\n'          
            for idx, friend in enumerate(self.friends):
                if '_' in friend['word']:
                    word, pos = friend['word'].split('_')
                    pos = re.sub(r'/', r'', pos)
                    data = [word, pos, friend['sample'], friend['total'], friend['expected'], friend['mi']]
                    
                    if idx == 0:
                        table += " <tr>\n"
                        header = ['word', 'pos', 'sample', 'total', 'expected', 'MI']
                        i = 0
                        # add Alpha javascript for word and pos, but num javascript for all other columns
                        for column in header:
                            if i < 2:
                                table += f'  <th style="cursor:pointer;" onclick="sortAlpha({i})">{column}</th>\n'.format(column.strip())
                            else:
                                table +=f'  <th style="cursor:pointer;" onclick="sortNum({i})">{column}</th>\n'.format(column.strip())
                            i += 1
                        table += "  </tr>\n"
                    else:
                        table += "  <tr>\n"
                        for column in data:
                            table += f"  <td>{column}</td>\n"
                        table += "  </tr>\n"
                else:
                    data = [friend['word'], friend['sample'], friend['total'], friend['expected'], friend['mi']]
                    
                    if idx == 0:
                        table += " <tr>\n"
                        header = ['word', 'sample', 'total', 'expected', 'MI']
                        i = 0
                        # add Alpha javascript for word, num javascript for all other columns
                        for column in header:
                            if i == 0:
                                table += f'  <th style="cursor:pointer;" onclick="sortAlpha({i})">{column}</th>\n'.format(column.strip())
                            else:
                                table +=f'  <th style="cursor:pointer;" onclick="sortNum({i})">{column}</th>\n'.format(column.strip())
                            i += 1
                        table += "  </tr>\n"
                    else:
                        table += "  <tr>\n"
                        for column in data:
                            table += f"  <td>{column}</td>\n"
                        table += "  </tr>\n"

            # Print out table output.
            table += "</table></div>"
            print(text, file=file_out)
            print(table, file=file_out)
                                  
            # Print out scripts for sorting and copying. 
            print(f'<script>{sort_alpha}</script>', file=file_out)
            print(f'<script>{sort_num}</script>', file=file_out)
            print(f'<script>{copy_btn}</script>', file=file_out)

            # End output of HTML file.
            print('</body></html>', file=file_out)
                
                
        
            