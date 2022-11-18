import csv
import pandas
from pkg_resources import resource_filename
import re
import xlsxwriter
from operator import itemgetter


from .exports import export_as_txt
from .stats import calculate_keywords
from .citations import get_citation

JSDIR = resource_filename('textelixir', 'js')
CSSDIR = resource_filename('textelixir', 'css')

class NGrams:
    def __init__(self, filename, size, **kwargs):
        # Parse args and kwargs
        self.filename = filename
        self.basename = re.sub(r'^(.+)/[^/]+$', r'\1', self.filename)
        self.size = size
        self.group_by = kwargs['group_by']
        self.sep = kwargs['sep']
        self.text_filter = kwargs['text_filter']
        self.punct_pos = kwargs['punct_pos']
        self.chunk_num = kwargs['chunk_num']
        self.ngram_references = {}
        self.ngrams = self.calculate_ngrams()
        
    # This is the cool method for getting keywords
    def __truediv__(self, other):
        return calculate_keywords(self.ngrams, other.ngrams)

    def calculate_ngrams(self):
        ngram_dict = {}
        self.elixir = pandas.read_csv(self.filename, sep='\t', index_col=None, header=0, chunksize=1000000, keep_default_na=False, na_values=[])
        # ngram_running_list will contain each words. Once it hits correct size or end of sentence, then reset the words.
        ngram_running_list = []
        current_citation = ''

        # Get all word ID data. Key: 0, Value: "the"
        word_data = self.get_word_data()
        # Identify all word IDs that are punctuation related.
        punctuation_word_ids = self.get_metadata('word', pos=self.punct_pos)
        # Iterate through each chunk of the elix file.
        for block_num, chunk in enumerate(self.elixir):
            print(f'\rɴgram Progress: {round((block_num+1)/self.chunk_num*100, 2)}%   ', end='')
            # If there are any filters applied to the ngrams query, apply the filters here.
            chunk = self.filter_chunk(chunk)
            # Remove any punctuation from the chunk.
            chunk = chunk[~chunk['word'].isin(punctuation_word_ids)]
            # Add the word_text column to the chunk.
            # chunk['word_text'] = chunk['word'].map(word_data)
            # Iterate through each word to add to ngrams.
            for word in chunk['word'].to_list():
            # for index, word in chunk.set_index('word').to_dict()['word_text'].items():

                # if index in punctuation_word_ids:
                #     continue
                    
                ngram_running_list.append(word_data[word])
                
                if len(ngram_running_list) == self.size:
                    full_ngram = self.sep.join(ngram_running_list)
                    if full_ngram not in ngram_dict:
                        ngram_dict[full_ngram] = 0
                    ngram_dict[full_ngram] += 1
                    # Pop the first word in ngram_running_list in preparation for the next word.
                    ngram_running_list.pop(0)


        
        print(f'\rSorting N-Grams by Frequency...          ', end='')
        sorted_ngram_dict = {k: v for k,v in sorted(ngram_dict.items(), key=itemgetter(1), reverse=True)}
        print('\n')
        return sorted_ngram_dict


    # Filters the chunk based on optional filters.
    def filter_chunk(self, chunk):
        if self.text_filter == None:
            return chunk
        elif isinstance(self.text_filter, dict):
            filter_index = 0
            for key, value in self.text_filter.items():
                if filter_index == 0:
                    if value.startswith('!'):
                        new_chunk = chunk[chunk[key] != value[1:]]
                    else:
                        new_chunk = chunk[chunk[key] == value]
                else:
                    if value.startswith('!'):
                        new_chunk = new_chunk[new_chunk[key] != value[1:]]
                    else:
                        new_chunk = new_chunk[new_chunk[key] == value]
                filter_index += 1
            return new_chunk
        elif isinstance(self.text_filter, list):
            pass
            # TODO: This is where a user could input ['Book of Mormon/1 Nephi/1/1'] to specify exact citation filtering.
    

    def get_metadata(self, table_name, **kwargs):
        # pos
        key = list(kwargs.keys())[0]
        # [ 'SYM', 'PUNCT', 'SPACE' ]
        value = list(kwargs.values())[0]
        # word.tsv
        metadata = pandas.read_csv(f'{self.basename}/{table_name}.tsv', sep='\t', escapechar='\\', index_col=None, header=0, keep_default_na=False, na_values=[])
        if isinstance(value, list):
            filtered_metadata = metadata[metadata[key].isin(value)]
        else:
            filtered_metadata = metadata[metadata[key] == value]
        return filtered_metadata['index'].to_list()

    def get_word_data(self):
        word_metadata = pandas.read_csv(f'{self.basename}/word.tsv', sep='\t', escapechar='\\', index_col=None, header=0, keep_default_na=False, na_values=[])
        word_metadata[['text', 'lower', 'pos', 'lemma']] = word_metadata[['text', 'lower', 'pos', 'lemma']].astype(str) 
        return word_metadata.set_index('index').to_dict()[self.group_by]
    
    def export_as_txt(self, output_filename):
        return export_as_txt(output_filename, [{'ngram': k, 'freq': v} for k, v in self.ngrams.items()], payload=['ngram', 'freq'])

    def export_as_csv(self, output_filename):
        with open(output_filename, 'w', encoding='utf-8', newline='') as file_out:
            writer = csv.writer(file_out) 
            writer.writerow(['ngram', 'freq'])
            for s in self.ngrams:
                writer.writerow([s[0], s[1]])

    def export_as_xlsx(self, output_filename):
        book = xlsxwriter.Workbook(output_filename)
        sheet = book.add_worksheet()
        sheet.write(0, 0, 'ngram')
        sheet.write(0, 1, 'freq')
        row = 1
        for ngram, freq in self.ngrams:
            sheet.write(row, 0, ngram)
            sheet.write(row, 1, freq)
            row += 1
        book.close()

    def export_as_html(self, output_filename):
        with open(output_filename, 'w', encoding='utf-8') as file_out:
            text = f'<html><head><title>N-grams</title><link href="https://cdn.jsdelivr.net/npm/halfmoon@1.1.1/css/halfmoon-variables.min.css" rel="stylesheet" /><link rel="stylesheet" href="{CSSDIR}/ngrams.css"></head><body><div class="container"><h1>N-grams for {self.filename}</h1><h2>Length:{self.size} </h2><input id="copy_btn" type="button" value="Copy Table"></p>'
            table = '<table class="table" id="table">\n<thead><tr><td>n-gram</td><td>freq</td></tr></thead><tbody>'

            # append every row
            curr = 0
            # max number of rows
            max = 200

            while curr in range(0, max):
                table += f'<tr><td>{self.ngrams[curr][0]}</td><td>{self.ngrams[curr][1]}</td></tr>\n'
                curr += 1
            table += '</tbody></table></div>'
            # print table
            print(text, file=file_out)
            print(table, file=file_out)

            # attach js scripts
            print(f'<script src="{JSDIR}/ngrams.js"></script>', file=file_out)

            # End output of HTML file.
            print('</body></html>', file=file_out)





