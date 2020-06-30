import MeCab
import downloader as dl
import concurrent.futures
import urllib
import re

tagger = MeCab.Tagger('/usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd')
rule = ['名詞', '動詞', '形容詞', '副詞']

def tokenize(sentence, stemming):
    """日本語の文を形態素の列に分割する関数

    :param sentence: str, 日本語の文
    :return tokenized_sentence: list of str, 形態素のリスト
    """
    tokenized_sentence = []
    if stemming is True:
        node = tagger.parseToNode(sentence)
        while node:
            word_surface = node.surface
            word_features = node.feature.split(',')

            if word_features[0] in rule:
                # 原形にする
                word = word_features[6]
                if word is not '*':
                    tokenized_sentence.append(word)
            node = node.next
    else:
        node = tagger.parse(sentence)
        node = node.split("\n")
        for i in range(len(node)):
            feature = node[i].split("\t")
            if feature[0] == "EOS":
                # 文が終わったら終了
                break
            # 分割された形態素を追加
            tokenized_sentence.append(feature[0])
    return tokenized_sentence


def out_tokenized_txt(data, tokenized_title, tokenized_main_txt):
    path = "./"
    url = data[0]
    title = data[1]
    main_txt = data[2]
    date = re.findall(r'\d{7,}',url)[0]

    file = path+title+"-" + date + "mainichi-" +".txt"
    with open(file, 'w') as f:
        f.writelines([title, "\n", main_txt, "\n\n", " ".join(tokenized_title), ":"+str(len(tokenized_title)),
                      "\n", " ".join(tokenized_main_txt), ":"+str(len(tokenized_main_txt))])


def convert(data, stopword=True, stemming=True):
    # トークン化する
    tokenized_title = tokenize(data[1], stemming)
    tokenized_main_txt = tokenize(data[2], stemming)

    # ストップワードを除去
    if stopword is True:
        try:
            with open('stop_word.txt', 'r', encoding='utf-8') as file:
                stopwords = [word.replace('\n', '') for word in file.readlines()]
        except Exception as e:
            print(e)
            url = 'http://svn.sourceforge.jp/svnroot/slothlib/CSharp/Version1/SlothLib/NLP/Filter/StopWord/word/Japanese.txt'
            urllib.request.urlretrieve(url, 'stop_word.txt')

        tokenized_title = [word for word in tokenized_title if word not in stopwords]
        tokenized_main_txt = [word for word in tokenized_main_txt if word not in stopwords]

    # ファイルへ出力する
    out_tokenized_txt(data, tokenized_title, tokenized_main_txt)


def main():
    url = "https://mainichi.jp/articles/20200624/ddm/005/070/085000c"
    url ="https://www.asahi.com/articles/DA3S14526484.html?iref=pc_rensai_article_long_16_prev"
    datas = dl.download(url, k=10)
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(convert, data) for data in datas]
        for future in concurrent.futures.as_completed(futures):
            print("finished {}".format(future))


if __name__ == '__main__':
    main()
