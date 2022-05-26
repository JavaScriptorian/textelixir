# lc = last chunk (the block from pandas dataframe prior to the current chunk)
# ch = current chunk (the current block from the pandas dataframe)
# bn = block number (the number associated to the current chunk)
# idx = current index (the current index number associated to the word within the current block)
# dst = distance (the length of word list required to exit out of the function)
# wl = word list (the list which is returned with dictionaries containing the block ID info and pandas word dataframe)

def get_previous_word(lc, ch, bn, idx, dst, wl=None):
    # Set word list to be empty list if it's None
    wl = wl if wl != None else []
    # If the length of the wl meets the criteria, then we can exit out of the recursion.
    if len(wl) == dst:
        return wl
    # Get the number of the previous word.
    find_index = idx-1
    # If the find index is less than 0, then it must search in the lc.
    if find_index < 0:
        find_index = 10000+idx-1
        # If lc is None, then we are at the beginning of block 0.
        if lc is None:
            return wl
        # Otherwise, we can check the last chunk to get the next word.
        previous_word = lc.iloc[find_index]
        used_bn = bn-1
    else:
        previous_word = ch.iloc[find_index]
        used_bn = bn


    # If the pos is PUNCT, let's ignore it and continue to the next word.
    if previous_word['pos'] == 'PUNCT':
        wl = get_previous_word(lc, ch, bn, idx-1, dst, wl)
    else:
        wl.append({f'{used_bn}:{find_index}': previous_word})
    if len(wl) != dst:
        wl = get_previous_word(lc, ch, bn, idx-1, dst, wl)

    return wl


def get_next_word(ch, bn, idx, dst, wl=None):
    # Set word list to be empty list if it's None
    wl = wl if wl != None else []
    if len(wl) == dst:
        return wl
    # Get the number of the next word
    if isinstance(idx, str):
        find_index = 0
        idx = -1
    else:
        find_index = idx+1

    if find_index > 9999:
        # If the find_index is greater than the chunk size, we will need to add it to the unfinished category.
        return wl
    else:
        try:
            next_word = ch.iloc[find_index]
        except IndexError:
            return wl

    # If the pos is PUNCT, let's ignore it and continue to the next word.
    if next_word['pos'] == 'PUNCT':
        wl = get_next_word(ch, bn, idx+1, dst, wl)
    else:
        wl.append({f'{bn}:{find_index}': next_word})
    
    if len(wl) != dst:
        wl = get_next_word(ch, bn, idx+1, dst, wl)

    return wl