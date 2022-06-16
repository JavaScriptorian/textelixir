import csv
import pandas
from pkg_resources import resource_filename
import xlsxwriter


from .exports import export_as_txt
from .stats import calculate_keywords
from .citations import get_citation

JSDIR = resource_filename('textelixir', 'js')
CSSDIR = resource_filename('textelixir', 'css')

class NGrams:
    def __init__(self, filename, size, **kwargs):
        # Parse args and kwargs
        self.filename = filename
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
        self.elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=10000, keep_default_na=False)
        # word_tracking will contain each words. Once it hits correct size or end of sentence, then reset the words.
        word_tracking = []
        current_citation = ''
        # Iterate through each chunk of the elix file.
        for block_num, chunk in enumerate(self.elixir):
            chunk = self.filter_chunk(chunk)
            print(f'\rN-Gram Progress: {round((block_num+1)/self.chunk_num*100, 2)}%   ', end='')
            # Iterate through each word in the chunk.
            for w in chunk.to_dict('records'):
                # Check to see if the word is punctuation.
                if w['pos'] in self.punct_pos:
                    continue
                # Get the citation (location) of the word.
                # citation = get_citation(w)
                # If the citation is not the same as the current_citation, then we've hit a new sentence.
                # Words should not be in an ngram from different sentences.


                # if citation != current_citation:
                    # word_tracking = []
                    # current_citation = citation

                    
                # Append the next word to word_tracking
                word_tracking.append(w[self.group_by])
                
                if len(word_tracking) == self.size:
                    full_ngram = self.sep.join(word_tracking)
                    if full_ngram not in ngram_dict:
                        ngram_dict[full_ngram] = 0
                    ngram_dict[full_ngram] += 1
                    # Pop the first word in word_tracking in preparation for the next word.
                    word_tracking.pop(0)
        
        print(f'\rSorting N-Grams by Frequency...          ', end='')
        sorted_ngram_dict = sorted(ngram_dict.items(), key=lambda t: (-t[1], t[0]))
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
    def export_as_txt(self, output_filename):
        return export_as_txt(output_filename, [{'ngram': s[0], 'freq': s[1]} for s in self.ngrams], payload=['ngram', 'freq'])

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

