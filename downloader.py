import requests
from bs4 import BeautifulSoup
import re
import queue
from string import ascii_letters
from string import digits
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

han = ascii_letters + digits
table = {c + 65248: c for c in map(ord, han)}


def extract(url):
    """urlからbeuatifulsoupでタイトルと本文を抽出。全角英数字は半角英数字へ、空白文字と改行コードの除去。

    :param url:
    :return: url、タイトル、本文を返す
    """
    soup = url[1]
    title = None
    main_text = None
    if "mainichi" in url[0]:
        title = soup.find_all("h1")[0].get_text()
        main_text = ''.join([t.text for t in soup.select("#main > div.article > div.main-text > p")])
    elif "asahi" in url[0]:
        title = soup.find_all("h1")[1].text
        main_text = ''.join([t.text for t in soup.select("#MainInner > div.ArticleBody > div.ArticleText > p")])
    elif "yomiuri" in url[0]:
        pass

    # titleを抽出した後、全角英数字を半角英数字に直し、空白文字と改行コードの除去
    title = ''.join([t.translate(table) for t in title])
    title = re.sub(r'\r|\n|\s|\t','', title)
    # main_textを抽出した後、全角英数字を半角英数字に直し、空白文字と改行コードの除去
    main_text = ''.join([t.translate(table) for t in main_text])
    main_text = re.sub(r'\r|\n|\s|\t','', main_text)
    return url, title, main_text


def parse(url):
    """urlのhtmlをダウンロードしてbeautifulsoupオブジェクトを返す（javascriptによって後から追加されていく要素に対応するためselenium使用してパーサーにかける）

    :param url:
    :return: soup: beutifulsoupのパースされたオブジェクトを返す
    """
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--disable-setuid-sandbox")
    chrome_driver_binary = "/mnt/c/Program Files (x86)/Google/Chrome/Application/chromedriver.exe"

    driver = webdriver.Chrome(chrome_driver_binary, chrome_options=options)

    driver.get(url)
    html = driver.page_source.encode('utf-8')
    soup = BeautifulSoup(html, "html.parser")
    driver.quit()
    return soup


def get_urls(url, dist, k, n, url_list):
    """urlを再帰的にurl_listへ格納していく

    :param url: スクレイピングするURL
    :param dist: distは最初のURLからどちらかの方向（前or次の記事）を探索していくか
    :param k: 何回再帰するか
    :param n: 何回目の再帰かカウント用
    :param url_list: 返り値として渡すため使われるリスト
    :return: クロールして得たURLのリストを返す
    """
    try:
        soup = parse(url)

        if n > 0:
            url_list[n] = [url, soup]
        else:
            url_list.append([url, soup])

        if "mainichi" in url:
            # クロールする方向へ進めるURLをゲットする
            if dist == 0:
                next_url = "https:" + soup.find(class_="col2 prev").find('a')['href']
            elif dist == 1:
                next_url = "https:" + soup.find(class_="col2 next").find('a')['href']
        elif "asahi" in url:
            if dist == 0:
                next_url = "https://www.asahi.com" + soup.find(id='PrevLink').find('a')['href']
            elif dist == 1:
                next_url = "https://www.asahi.com" + soup.find(id='NextLink').find('a')['href']
        elif "yomiuri" in url:
            print("pass")
            pass

        # 得たURLをリストに入れる
        url_list.append(next_url)
        print("dist:{}, url「{}」".format(dist, next_url))

        # 再帰処理を何回行うか
        if n >= k:
            return url_list[:-1]

        n += 1
        return get_urls(next_url, dist, k, n, url_list)
    except:
        return url_list[:-1]


def download(url, k, dist_prev=False):
    """クローリングとテキストの抽出を行う

    :param url: 最初の起点となるURLを入れる
    :return: url, タイトル, 本文のタプルを返す
    """
    # urlダウンロード
    print("urlダウンロード開始")
    if dist_prev is True:
        url_list = get_urls(url, 0, k, 0, list())
    else:
        list1 = get_urls(url, 0, k, 0, list())
        list2 = get_urls(url, 1, k, 0, list())
        url_list = list1 + list2[1:]
    #with concurrent.futures.ProcessPoolExecutor() as executor:
    #    futures = [executor.submit(get_urls, url, dist, k, 0, url_list) for dist in [0, 1]]
    #    results = [future.result() for future in futures]
    #    url_list = results[0] + results[1]
    #    for future in concurrent.futures.as_completed(futures):
    #        print("finished {}".format(future))
    print("ダウンロード終了")

    # htmlからtitle,main_textの抽出
    print("抽出開始")
    results = []
    for url in url_list:
        results.append(extract(url))
    #with concurrent.futures.ProcessPoolExecutor() as executor:
    #    futures = [executor.submit(get_contents, url) for url in url_list]
    #    results = [future.result() for future in futures]
    #    for future in concurrent.futures.as_completed(futures):
    #        print("finished {}".format(future))
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