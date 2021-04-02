import requests, json
from pyquery import PyQuery as pq
from pinyin_converter import latnum
url = "https://en.wiktionary.org/wiki/Index:Mandarin_Pinyin/Table_of_General_Standard_Chinese_Characters"

sess = requests.Session()

r = sess.get(url)

d = pq(r.content)

db = {}
for g in d('#mw-content-text>div>ul>li'):
    o = pq(g)
    p = o.children('a').text()
    pp = latnum(p)
    
    cc = []
    for c in o.children('span a'):
        cc.append(c.text)
    
    db[pp] = cc
    pass
    pass

with open('8105.json', 'w') as f:
    json.dump(db, f, indent=4, ensure_ascii=False)
pass
pass
