def get_full_citation(df):
    columns = list(df.columns)
    columns.remove('word')
    columns.remove('word_index')
    citation = []
    for column in columns:
        citation.append(str(df.iloc[0][column]))
    return '/'.join(citation)