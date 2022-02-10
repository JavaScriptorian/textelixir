import math

# Calculates the BIC value for the ngrams.
def calculate_keywords(ngrams1, ngrams2):
    total = 0
    c1 = 0
    c2 = 0
    combined_ngrams = {}
    for k, v in ngrams1:
        total += v
        c1 += v
        combined_ngrams[k] = {1: v, 2: 0}
    for k, v in ngrams2:
        total += v
        c2 += v
        if k in combined_ngrams:
            combined_ngrams[k][2] = v

    keywords = {}
    for k, v in ngrams1:
        o11 = combined_ngrams[k][1]
        o12 = combined_ngrams[k][2]
        if o12 == 0:
            continue
        r1 = o11 + o12
        prob = r1 / total
        e11 = c1 * prob
        e12 = r1 - e11
        rel1 = round(o11 / c1 * 1000000,1)
        rel2 = round(o12 / c2 * 1000000,1)
        ll = 2 * (o11*math.log(o11/e11) + o12 * math.log(o12/e12))
        bic = round(ll - math.log(total), 2)
        if bic < 0:
            continue
        keywords[k] = {'observed1': o11, 
                       'observed2': o12,
                       'rel1':  rel1,
                       'rel2': rel2,
                       'expected1': round(e11, 1),
                       'expected2': round(e12, 1),
                       'll': ll,
                       'bic': bic
                       }

    keywords = {k: v for k, v in sorted(keywords.items(), key=lambda item: item[1]['bic'], reverse=True)}
    return keywords
