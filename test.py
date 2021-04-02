import json
import collections

lasts = ['a','o','e','i','u','v'] + ['ai','ei','ui','ao','ou','iu','ie','ve'] + ['an','en','in','un','vn'] + ['ang','eng','ing','ong']
lasts += ['ia','ian','iang','iao','iong'] + ['ua','uai','uan','uang','uo','van']

initials = ['b','p','m','f','d','t','n','l','g','k','h','j','q','x','zh','ch','sh','r','z','c','s','y','w']

def filter_with_initial(initial, o):
    
    words = {}
    tones = ['','1','2','3','4']
    for l in lasts:
        for t in tones:
            pinyin = initial + l + t
            pinyinh = initial + 'h' + l + t

            if pinyin in o:
                words[pinyin] = o[pinyin]
            if pinyinh in o:
                words[pinyinh] = o[pinyinh]
    return words

def filter_with_last(last, o):
    
    words = {}
    tones = ['','1','2','3','4']
    for i in initials:
        for t in tones:
            pinyin = i + last + t
            pinying = i + last + 'g' + t

            if pinyin in o:
                words[pinyin] = o[pinyin]
            if pinying in o:
                words[pinying] = o[pinying]

    return words

def process_initial(o):
    
    z = filter_with_initial('z', o)
    s = filter_with_initial('s', o)
    c = filter_with_initial('c', o)

    for i, j in (z|s|c).items():
        print(i,j)

def process_last(o):
    
    ing = filter_with_last('in', o)

    for i, j in ing.items():
        print(i, j)

filename = "8105.json"

with open(filename) as f:
    o = json.load(f)

#process_initial(o)
process_last(o)
