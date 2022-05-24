import re

def export_as_txt(filename, state, payload):
    if 'collocates' in payload:
        payload.pop(0)

        has_pos = True if '_' in state[0]['word'] else False
        if has_pos:
            payload.insert(1, 'pos')

        with open(filename, 'w', encoding='utf-8') as file_out:
            for s in state:
                if has_pos:
                    word, pos = s['word'].split('_')
                    pos = re.sub(r'/', r'', pos)
                    s['word'] = word
                    s['pos'] = pos
                print('\t'.join([str(s[i]) for i in payload]), file=file_out)
    else:
        with open(filename, 'w', encoding='utf-8') as file_out:
            print('\t'.join(payload), file=file_out)
            for s in state:
                # print('\t'.join([s[i] for i in payload]), file=file_out)
                print('\t'.join([str(s[i]) for i in payload]), file=file_out)
    return True