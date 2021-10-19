from torch._C import Value


class KWIC:
    def __init__(self, kwic_lines):
        self.kwic_lines = kwic_lines


    def summary(self, **kwargs):
        for key, value in kwargs.items():
            if key == 'line_count':
                line_count = value
            elif key == 'sort_by':
                sort_by = value


        # SORT THE KWIC LINES FIRST
        sorted_kwic_lines = self.sort_kwic_lines()
        
        # Get Top X KWIC lines unless line_count == 'all'
        if isinstance(line_count, str) and line_count.lower() == 'all':
            summary = sorted_kwic_lines
        else:
            summary = sorted_kwic_lines[0:line_count]

        try:
            max_before = max([len(i['before']) for i in summary if 'before' in i])
        except ValueError:
            max_before = 1
        try:
            max_after = max([len(i['after']) for i in summary if 'after' in i])
        except ValueError:
            max_after = 1

        try:
            max_hit = max([len(i['hit']) for i in summary if 'hit' in i])
        except ValueError:
            print('KWIC ERROR: No search results')
            return 'KWIC ERROR: No search results'
        
        for i in summary:
            if 'before' not in i:
                i['before'] = ' '
            elif 'after' not in i:
                i['after'] = ' '

            print(f'{i["before"]:>{max_before}}{i["hit"]:^{max_hit+2}}{i["after"]:<{max_after}}') # noqa: E501


    def sort_kwic_lines(self, sort_by='alphabetical'):
        if sort_by == 'alphabetical':
            return sorted(self.kwic_lines, key=lambda k: k['hit']) 
        return self.kwic_lines

    def export_kwic_to_tsv(self, output_filename=None):
        # Give it a generic filename if none is provided.
        if output_filename == None:
            output_filename = f'kwic.tsv'

        with open(output_filename, 'w', encoding='utf-8') as file_out:
            for i in self.kwic_lines:
                print(i, file=file_out)


    def export_kwic_to_txt(self, **kwargs):
        for key, value in kwargs.items():
            if key == 'output_filename':
                output_filename = value
            else:
                output_filename = 'kwic.txt'
            
            if key == 'sort_by':
                sort_by = value
            else:
                sort_by = 'chronological'

        # Sort the KWIC lines
        sorted_kwic_lines = self.sort_kwic_lines(sort_by=sort_by)


        with open(output_filename, 'w', encoding='utf-8') as file_out:
            for i in self.kwic_lines:
                print(i, file=file_out)


    def export_kwic_to_html(self, output_filename=None):
        # Give it a generic filename if none is provided.
        if output_filename == None:
            output_filename = f'kwic.html'

        with open(output_filename, 'w', encoding='utf-8') as file_out:
            for i in self.kwic_lines:
                print(i, file=file_out)