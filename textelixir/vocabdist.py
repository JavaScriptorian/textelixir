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

        for block_num, chunk in enumerate(self.elixir):
            # Figure out which column header should be used for the distribution of the vocabulary.
            if block_num == 0:
                # Save this to object because it'll be needed later anyway.
                self.column_headers = self.determine_column_header(chunk)
            curr_indices = self.filter_indices_by_block(self.results_indices, block_num)
            for curr_index in curr_indices:
                # Determine the usage from just the first word. 
                # TODO: Maybe this is a bad idea?
                word_num = int(curr_index[0].split(':')[1])
                citation = '/'.join([chunk.iloc[word_num][c]for c in self.column_headers])
                if citation not in data:
                    data[citation] = {
                        'freq': 0,
                        'total': 0,
                        'expected': 0,
                        'normFreq': 0
                        }

                data[citation]['freq'] += 1
        return data

    
    def add_totals(self, data):
        self.elixir = pandas.read_csv(self.filename, sep='\t', escapechar='\\', index_col=None, header=0, chunksize=10000)
        for block_num, chunk in enumerate(self.elixir):
            filtered_chunk = chunk[~chunk['pos'].isin(self.punct_pos)]
            value_counts = filtered_chunk[self.column_headers].value_counts()
            for idx,name in enumerate(value_counts.index.tolist()):
                citation = '/'.join(name)
                if citation not in data:
                    data[citation] = {
                        'freq': 0,
                        'total': 0,
                        'expected': 0,
                        'normFreq': 0
                    }
                
                data[citation]['total'] += int(value_counts[idx])
        
        
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
        chart_title = kwargs['chart_title'] if 'chart_title' in kwargs else f'Vocabulary Distribution for "{self.search_string}"'
        x = []
        y = []

        for k, v in self.data.items():
            x.append(k)
            y.append(v[output_metric])
        df = pandas.DataFrame(list(zip(x, y)), columns =[x_name, y_name])
        fig = px.bar(df, x=x_name, y=y_name, title=chart_title)
        fig.show()

        # df = pd.DataFrame(list(zip(x, y)),
        #     columns =[self.group_by, 'Normalized Frequency'])


    def save_chart(self, filename, output_metric='normFreq', **kwargs):
        x_name = kwargs['x'] if 'x' in kwargs else self.group_by
        y_name = kwargs['y'] if 'y' in kwargs else output_metric
        chart_title = kwargs['chart_title'] if 'chart_title' in kwargs else f'Vocabulary Distribution for "{self.search_string}"'
        x = []
        y = []

        for k, v in self.data.items():
            x.append(k)
            y.append(v[output_metric])
        df = pandas.DataFrame(list(zip(x, y)), columns =[x_name, y_name])
        fig = px.bar(df, x=x_name, y=y_name, title=chart_title)
        fig.write_image(filename)

    def export_as_txt(self, filename):
        with open(filename, 'w', encoding='utf-8') as file_out:
            print(f'citation\tfreq\tnormFreq\texpected\ttotal\tpercent', file=file_out)
            for k, v in self.data.items():
                print(f'{k}\t{v["freq"]}\t{v["normFreq"]}\t{v["expected"]}\t{v["total"]}\t{v["percent"]}', file=file_out)
