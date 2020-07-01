import glob
import re
from sklearn.feature_extraction.text import TfidfVectorizer
import csv

file_list = glob.glob('./data/*.txt')
print(len(file_list))
docs = list()
for file in file_list:
    with open(file, mode='r') as f:
        l = f.readlines()
        docs.append(l[4].replace(re.findall(':\d+', l[4])[0], ''))

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(docs)
print('feature_names:', vectorizer.get_feature_names())
words = vectorizer.get_feature_names()
words.insert(0,'doc_id')
doc_tfidf_list = list()
with open('./tfidf.csv', 'w',  encoding='utf8') as f:
    writer = csv.writer(f)
    writer.writerow(words)

for doc_id, vec in zip(range(len(docs)), X.toarray()):
    print(doc_id)
    tfidf_list = list()
    tfidf_list.append(doc_id)
    for w_id, tfidf in sorted(enumerate(vec), key=lambda x: x[1], reverse=True):
        lemma = words[w_id]
        tfidf_list.append(tfidf)
    with open('./tfidf.csv', 'a') as f:
        writer = csv.writer(f)
        writer.writerow(tfidf_list)


