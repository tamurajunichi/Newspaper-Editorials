import requests
from bs4 import BeautifulSoup
import re
import queue
from string import ascii_letters
from string import digits
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_path = "/home/tj/.local/lib/python3.8/site-packages/chromedriver_binary"

han = ascii_letters + digits
table = {c + 65248: c for c in map(ord, han)}


def get_contents(url):
    """urlからbeuatifulsoupでタイトルと本文を抽出。全角英数字は半角英数字へ、空白文字と改行コードの除去。

    :param url:
    :param news_company:
    :return: url、タイトル、本文を返す
    """
    soup = parse(url)
    if "mainichi" in url:
        title = soup.find_all("h1")[0].get_text()
        main_text = ''.join([t.text for t in soup.select("#main > div.article > div.main-text > p")])
    elif "asahi" in url:
        title = soup.select("#MainInner > div.ArticleTitle > div > h1").text
        main_text = ''.join([t.text for t in soup.select("#MainInner > div.ArticleBody > div.ArticleText > p")])
        print(main_text)
    elif "yomiuri" in url:
        pass
        print("この新聞社の社説は取扱できません")

    # titleを抽出した後、全角英数字を半角英数字に直し、空白文字と改行コードの除去
    title = ''.join([t.translate(table) for t in title])
    title = re.sub(r'\r|\n|\s','', title)
    # main_textを抽出した後、全角英数字を半角英数字に直し、空白文字と改行コードの除去
    main_text = ''.join([t.translate(table) for t in main_text])
    main_text = re.sub(r'\r|\n|\s','', main_text)
    return url, title, main_text


def parse(url):
    """urlのhtmlをダウンロードしてbeautifulsoupオブジェクトを返す

    :param url:
    :return: soup: beutifulsoupのパースされたオブジェクトを返す
    """
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    driver = webdriver.Chrome(chrome_options=options, executable_path=chrome_path+"/chromedriver")
    driver.get(url)
    html = driver.page_source.encode('utf-8')
    soup = BeautifulSoup(html, "html.parser")
    return soup


def get_urls(url, dist, k, n, url_list):
    """urlを再帰的にurl_listへ格納していく

    :param url:
    :param dist: distは最初のURLからどちらかの方向（前or次の記事）を探索していくかを表す
    :param n: 何回再帰処理を行うか。パワポでいうk/2に相当する
    :param url_list: 返り値として渡すため使われるリスト
    :param news_company:
    :return: クロールして得たURLのリストを返す
    """
    try:
        soup = parse(url)
        if "mainichi" in url:
            url_elems = soup.find_all(href=re.compile("//mainichi.jp/articles/"))

            # クロールする方向へ進めるURLをゲットする
            if dist == 0:
                next_url = "https:" + url_elems[1].attrs['href']
            elif dist == 1:
                next_url = "https:" + url_elems[2].attrs['href']
        elif "asahi" in url:

            # クロールする方向へ進めるURLをゲットする
            if dist == 0:
                next_url = soup.find(id='NextLink').find('a')['href']
            elif dist == 1:
                next_url = soup.find(id='PrevLink').find('a')['href']
        elif "yomiuri" in url:
            pass

        #　得たURLをリストに入れる
        url_list.append(next_url)
        print("dist:{}, url「{}」".format(dist, next_url))

        #再帰処理を何回行うか
        if n > k/2:
            # 不正なURLが出るので応急処置
            url_list[-1] = url_list[-1].replace("https:https", "https")
            return url_list
        n += 1
        return get_urls(next_url, dist, k, n, url_list)
    except:
        # 不正なURLが出るので応急処置
        url_list[-1] = url_list[-1].replace("https:https", "https")
        return url_list


def download(url, k):
    """クローリングとテキストの抽出をマルチプロセスで行う

    :param url: 最初の起点となるURLを入れる
    :return: url, タイトル, 本文のタプルを返す
    """
    # urlダウンロード
    url_list = []
    print("urlダウンロード開始")
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(get_urls, url, dist, k, 0, url_list) for dist in [0, 1]]
        results = [future.result() for future in futures]
        url_list = results[0] + results[1]
        for future in concurrent.futures.as_completed(futures):
            print("finished {}".format(future))
    print("ダウンロード終了")

    # htmlからtitle,main_textの抽出
    print("抽出開始")
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(get_contents, url) for url in url_list]
        results = [future.result() for future in futures]
        for future in concurrent.futures.as_completed(futures):
            print("finished {}".format(future))
    print("抽出終了")
    return results


# converterの方で別のファイル出力用関数を作成したため使わない
def out_files(result):
    path = "./"
    url = result[0]
    title = result[1]
    main_txt = result[2]
    # print(re.findall(r'\d{7,}',url))

    print("書き込み開始")
    file = path+title+".txt"
    print(file+"を書き込み")
    with open(file, 'w') as f:
        f.writelines([title, "\n", main_txt, "\n\n"])
    print("書き込み終了")


def main():
    url = "https://mainichi.jp/articles/20200624/ddm/005/070/085000c"
    results = download(url, k=60)
    print(results)
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(out_files, result) for result in results]
        for future in concurrent.futures.as_completed(futures):
            print("finished {}".format(future))


if __name__ == '__main__':
    main()
