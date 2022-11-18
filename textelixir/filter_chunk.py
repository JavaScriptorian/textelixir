def filter_chunk(chunk, text_filter, filter_regex):
    if text_filter == None:
        return chunk

    filter_index = 0
    for key, value in text_filter.items():
        # Change value:string to value:list
        if isinstance(value, str):
            value_list = [value]
        elif isinstance(value, list):
            value_list = value

        filter_wildcard = True if ('*' in value or '?' in value) and (filter_regex == False) else False
        
        for value in value_list:
            # If it's the first filter being applied.
            if filter_index == 0:
                # Look for everything excluding this one item.
                if value.startswith('!'):
                    value = value[1:]
                    # NEGATIVE REGEX HANDLER
                    if filter_regex:
                        new_chunk = chunk[~chunk[key].str.match(value)]
                    # NEGATIVE WILDCARD HANDLER
                    elif filter_wildcard:
                        value = value.replace('*', '.*').replace('?', '.')
                        new_chunk = chunk[~chunk[key].str.match(value)]
                    # NEGATIVE EXACT MATCH HANDLER
                    else:
                        new_chunk = chunk[chunk[key] != value]
                    
                # Look for everything including this item.
                else:
                    # POSITIVE REGEX HANDLER
                    if filter_regex:
                        new_chunk = chunk[chunk[key].str.match(value)]
                    # POSITIVE WILDCARD HANDLER
                    elif filter_wildcard:
                        value = value.replace('*', '.*').replace('?', '.')
                        new_chunk = chunk[chunk[key].str.match(value)]
                    # POSITIVE EXACT MATCH HANDLER
                    else:
                        new_chunk = chunk[chunk[key] == value]
            # If it's not the first filter being applied.
            else:
                if value.startswith('!'):
                    value = value[1:]
                    # NEGATIVE REGEX HANDLER
                    if filter_regex:
                        new_chunk = new_chunk[~new_chunk[key].str.match(value)]
                    # NEGATIVE WILDCARD HANDLER
                    elif filter_wildcard:
                        value = value.replace('*', '.*').replace('?', '.')
                        new_chunk = new_chunk[~new_chunk[key].str.match(value)]
                    # NEGATIVE EXACT MATCH HANDLER
                    else:
                        new_chunk = new_chunk[new_chunk[key] != value]
                else:
                    # POSITIVE REGEX HANDLER
                    if filter_regex:
                        new_chunk = new_chunk[new_chunk[key].str.match(value)]
                    elif filter_wildcard:
                        value = value.replace('*', '.*').replace('?', '.')
                        new_chunk = new_chunk[~new_chunk[key].str.match(value)]
                    # EXACT MATCH HANDLER
                    else:
                        new_chunk = new_chunk[new_chunk[key] == value]
            filter_index += 1
    return new_chunk