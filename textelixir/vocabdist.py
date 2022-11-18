
import pandas
import plotly.express as px
import re
import itertools

class VocabDist:
    def __init__(self, filename, group_by=0, results=None, punct_pos=None, search_string='', **kwargs):
        self.filename = filename
        self.basename = re.sub(r'^(.+)/[^/]+$', r'\1', self.filename)
        self.group_by = group_by
        self.match = kwargs['match']
        self.replace = kwargs['replace']
        self.results = results
        self.search_length = len(self.results[search_string[0]])
        self.punct_pos = punct_pos
        self.punct_word_ids = self.get_metadata('word', pos=[self.punct_pos])
        self.search_string = search_string
        # Create empty tables dictionary
        self.tables = {}
        self.data = self.calculate_distribution()
        self.data = self.add_totals(self.data)
        self.data = self.add_expected(self.data)
        self.data = self.add_normalized_freq(self.data)

    def calculate_distribution(self):
        elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=1000000, keep_default_na=False, na_values=[])
        data = {}
        for block_num, chunk in enumerate(elixir):
            
            # Figure out which column header should be used for the distribution of the vocabulary.
            if block_num == 0:
                # Save this to object because it'll be needed later anyway.
                self.column_headers = self.determine_column_header(chunk)
                for column_header in self.column_headers:
                    self.tables[column_header] = self.get_header_table(column_header)
                        
            curr_indices = self.filter_indices_by_block(self.results, block_num)
            for curr_index in curr_indices:
                w = chunk.loc[curr_index[0]]
                if self.match and self.replace:
                    citation = '/'.join(re.sub(self.match, self.replace, str(self.tables[column_header][w[column_header]])) for column_header in self.column_headers)
                else:
                    citation = '/'.join([str(self.tables[column_value][w[column_value]]) for idx, column_value in enumerate(self.column_headers)])
                if citation not in data:
                    data[citation] = {
                        'freq': 0,
                        'total': 0,
                        'expected': 0,
                        'normFreq': 0
                        }
                data[citation]['freq'] += 1
        return data

    def get_metadata(self, table_name, **kwargs):
        key = list(kwargs.keys())[0]
        value = list(kwargs.values())[0]
        metadata = pandas.read_csv(f'{self.basename}/{table_name}.tsv', sep='\t', escapechar='\\', index_col=None, header=0, keep_default_na=False, na_values=[])
        if isinstance(value, list):
            filtered_metadata = metadata[metadata[key].isin(value[0])]
        else:
            filtered_metadata = metadata[metadata[key] == value]
        return filtered_metadata['index'].to_list()

    def get_header_table(self, table_name):
        metadata = pandas.read_csv(f'{self.basename}/{table_name}.tsv', sep='\t', escapechar='\\', index_col=None, header=0, keep_default_na=False, na_values=[])
        metadata['value'] = metadata['value'].astype(str)
        return dict(zip(metadata['index'], metadata['value']))
    
    def add_totals(self, data):
        elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=1000000, keep_default_na=False, na_values=[])
        for block_num, chunk in enumerate(elixir):
            # Eliminate punctuation from the ch
            filtered_chunk = chunk[~chunk['word'].isin(self.punct_word_ids)]
            value_counts = filtered_chunk[self.column_headers].value_counts()
            for key, value in value_counts.to_dict().items():
                # TODO: This structure currently only works if there's one column specified...
                if self.match and self.replace:
                    name = [re.sub(self.match, self.replace, self.tables[self.column_headers[0]][key[0]])]
                else:
                    name = [str(self.tables[self.column_headers[idx]][column_value]) for idx, column_value in enumerate(key)]
                citation = '/'.join(name)
                if citation not in data:
                    data[citation] = {
                        'freq': 0,
                        'total': 0,
                        'expected': 0,
                        'normFreq': 0
                    }
                data[citation]['total'] += value
        
        # TODO: Remove one from total if the word is more than 1 word.
        return data

    def add_expected(self, data):
        corpus_total = sum([v['total']for k, v in data.items()])
        for k, v in data.items():
            percentage = v['total'] / corpus_total
            data[k]['percent'] = round(percentage * 100, 2)
            data[k]['expected'] = round(percentage * len(self.results),1)
            ibrk = 0
        return data

    def add_normalized_freq(self, data):
        for k, v in data.items():
            data[k]['normFreq'] = round(data[k]['freq'] / data[k]['total'] * 1000000, 2)
            ibrk = 0
        return data

    def determine_column_header(self, chunk):
        headers = list(chunk.columns.values)
        if isinstance(self.group_by, int):
            return [headers[self.group_by]]
        elif isinstance(self.group_by, str):
            if '/' in self.group_by:
                return  self.group_by.split('/')
            return [self.group_by]
        else:
            assert Exception('Please provide a string for your group_by argument.')

    def filter_indices_by_block(self, results, block_num):
        filtered_indices = []
        for search_word, result_list in results.items():
            filtered_indices.extend([indices for indices in result_list if (indices[0] >= block_num*1000000 and indices[0] < (block_num*1000000) + 1000000)])
        filtered_indices.sort()
        return list(k for k,_ in itertools.groupby(filtered_indices))

    def show_chart(self, output_metric='normFreq', **kwargs):
        x_name = kwargs['x'] if 'x' in kwargs else self.group_by
        y_name = kwargs['y'] if 'y' in kwargs else output_metric
        hide_zeros = kwargs['hide_zeros'] if 'hide_zeros' in kwargs else False
        chart_title = kwargs['chart_title'] if 'chart_title' in kwargs else f'Vocabulary Distribution for "{self.search_string}"'
        sort_x = kwargs['sort_x'] if 'sort_x' in kwargs else None
        sort_y = kwargs['sort_y'] if 'sort_y' in kwargs else None
        limit = kwargs['limit'] if 'limit' in kwargs else 0
        x = []
        y = []

        for k, v in self.data.items():
            # Hide any values that have 0 in their frequency.
            if hide_zeros == True and v['freq'] == 0:
                continue
            x.append(k)
            y.append(v[output_metric])

        zipped_data = list(zip(x, y))
        # Check for any sorting to be done.
        if sort_x == 'ascending':
            zipped_data.sort(key = lambda x: x[0]) 
        elif sort_x == 'descending':
            zipped_data.sort(key = lambda x: x[0], reverse=True)
            ibrk = 0
        
        if sort_y == 'ascending':
            zipped_data.sort(key = lambda x: x[1])
        elif sort_y == 'descending':
            zipped_data.sort(key = lambda x: x[1], reverse=True)

        # Limit the list if the "limit" argument is more than 0
        if limit > 0:
            zipped_data = zipped_data[0:limit]

        df = pandas.DataFrame(zipped_data, columns =[x_name, y_name])
        fig = px.bar(df, x=x_name, y=y_name, title=chart_title)
        fig.show()


    def save_chart(self, filename, output_metric='normFreq', **kwargs):
        x_name = kwargs['x'] if 'x' in kwargs else self.group_by
        y_name = kwargs['y'] if 'y' in kwargs else output_metric
        hide_zeros = kwargs['hide_zeros'] if 'hide_zeros' in kwargs else False
        chart_title = kwargs['chart_title'] if 'chart_title' in kwargs else f'Vocabulary Distribution for "{self.search_string}"'

        sort_x = kwargs['sort_x'] if 'sort_x' in kwargs else None
        sort_y = kwargs['sort_y'] if 'sort_y' in kwargs else None
        limit = kwargs['limit'] if 'limit' in kwargs else 0
        x = []
        y = []

        for k, v in self.data.items():
            # Hide any values that have 0 in their frequency.
            if hide_zeros == True and v['freq'] == 0:
                continue
            x.append(k)
            y.append(v[output_metric])

        zipped_data = list(zip(x, y))
        # Check for any sorting to be done.
        if sort_x == 'ascending':
            zipped_data.sort(key = lambda x: x[0]) 
        elif sort_x == 'descending':
            zipped_data.sort(key = lambda x: x[0], reverse=True)
            ibrk = 0
        
        if sort_y == 'ascending':
            zipped_data.sort(key = lambda x: x[1])
        elif sort_y == 'descending':
            zipped_data.sort(key = lambda x: x[1], reverse=True)

        # Limit the list if the "limit" argument is more than 0
        if limit > 0:
            zipped_data = zipped_data[0:limit]

        df = pandas.DataFrame(zipped_data, columns=[x_name, y_name])
        fig = px.bar(df, x=x_name, y=y_name, title=chart_title, text_auto=True)
        fig.write_image(filename, scale=8)

    def export_as_txt(self, filename):
        with open(filename, 'w', encoding='utf-8') as file_out:
            print(f'citation\tfreq\tnormFreq\texpected\ttotal\tpercent', file=file_out)
            for k, v in self.data.items():
                print(f'{k}\t{v["freq"]}\t{v["normFreq"]}\t{v["expected"]}\t{v["total"]}\t{v["percent"]}', file=file_out)
