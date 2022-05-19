def export_as_txt(filename, state, payload):
    with open(filename, 'w', encoding='utf-8') as file_out:
        for s in state:
            print('\t'.join([s[i] for i in payload]), file=file_out)
    return True