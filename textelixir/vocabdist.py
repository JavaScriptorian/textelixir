from lib2to3.pytree import convert
import pandas
import plotly.express as px

class VocabDist:
    def __init__(self, filename, group_by=0, results_indices=None, punct_pos=None, search_string=''):
        self.filename = filename
        self.group_by = group_by
        self.results_indices = results_indices
        self.search_length = len(self.results_indices[0])
        self.punct_pos = punct_pos
        self.search_string =search_string
        self.data = self.calculate_distribution()
        self.data = self.add_totals(self.data)
        self.data = self.add_expected(self.data)
        self.data = self.add_normalized_freq(self.data)

    def calculate_distribution(self):
        self.elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=10000)
        data = {}
        convert_to_str_list = []
        for block_num, chunk in enumerate(self.elixir):
            
            # Figure out which column header should be used for the distribution of the vocabulary.
            if block_num == 0:
                # Save this to object because it'll be needed later anyway.
                self.column_headers = self.determine_column_header(chunk)
                # If the data type is not an object, then it needs to be converted into a str type object.
                for ch in self.column_headers:
                    if chunk.dtypes[ch].name != 'object':
                        # Add it to the convert to str list so it knows to convert that column every time.
                        convert_to_str_list.append(ch)
                        
            for column in convert_to_str_list:
                chunk[column] = chunk[column].apply(str)
            curr_indices = self.filter_indices_by_block(self.results_indices, block_num)
            for curr_index in curr_indices:
                word_num = int(curr_index[0].split(':')[1])
                citation = '/'.join([chunk.iloc[word_num][c]for c in self.column_headers])
                if citation not in data:
                    data[citation] = {
                        'freq': 0,
                        'total': 0,
                        'expected': 0,
                        'normFreq': 0
                        }
                ibrk = 0

                data[citation]['freq'] += 1
        return data

    
    def add_totals(self, data):
        self.elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=10000)
        for block_num, chunk in enumerate(self.elixir):
            # Eliminate punctuation from the ch
            filtered_chunk = chunk[~chunk['pos'].isin(self.punct_pos)]
            value_counts = filtered_chunk[self.column_headers].value_counts()
            for key, value in value_counts.to_dict().items():
                name = [str(i) for i in key]
                citation = '/'.join(name)
                if citation not in data:
                    data[citation] = {
                        'freq': 0,
                        'total': 0,
                        'expected': 0,
                        'normFreq': 0
                    }
                data[citation]['total'] += value
        
        
        if self.search_length == 1:
            return data
        
        # Subtract n words from each total if the search length is longer than 1.
        for k, v in data.items():
            data[k]['total'] -= self.search_length-1
        return data
        ibrk = 0

    def add_expected(self, data):
        corpus_total = sum([v['total']for k, v in data.items()])
        for k, v in data.items():
            percentage = v['total'] / corpus_total
            data[k]['percent'] = round(percentage * 100, 2)
            data[k]['expected'] = round(percentage * len(self.results_indices),1)
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

    def filter_indices_by_block(self, results_indices, block_num):
        filtered_indices = []
        for index in results_indices:
            curr_block_num, word_num = index[-1].split(':')
            if int(curr_block_num) == block_num:
                filtered_indices.append(index)
        return filtered_indices

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

        df = pandas.DataFrame(zipped_data, columns =[x_name, y_name])
        fig = px.bar(df, x=x_name, y=y_name, title=chart_title)
        fig.write_image(filename)

    def export_as_txt(self, filename):
        with open(filename, 'w', encoding='utf-8') as file_out:
            print(f'citation\tfreq\tnormFreq\texpected\ttotal\tpercent', file=file_out)
            for k, v in self.data.items():
                print(f'{k}\t{v["freq"]}\t{v["normFreq"]}\t{v["expected"]}\t{v["total"]}\t{v["percent"]}', file=file_out)
