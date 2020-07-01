import glob
import re
import numpy as np
import matplotlib.pyplot as plt
#from matplotlib import pyplot as plt
#plt.rcParams['font.family'] = 'IPAexGothic'
#import matplotlib as mpl
#print(mpl.get_configdir())


def count_word(newspaper_company):
    """記事ごとに単語数をカウントしてリストへ保存

    :param newspaper_company: 新聞社名の文字列
    :return:
    """
    file_list = glob.glob('./*' + newspaper_company + '*')
    word_numbers = list()
    word_numbers.append(newspaper_company)
    for file in file_list:
        with open(file, mode='r') as f:
            l = f.readlines()
        word_numbers.append(int(re.findall(r':\d+', l[4])[0].replace(':','')))
    return word_numbers


def each_visualize(x_list):
    """別々で単語数ヒストグラムを表示

    :param x_list: xのリストを渡す
    :return:
    """
    for i, x in enumerate(x_list[1:]):
        plt.subplot(len(x_list), 1, i+1)
        plt.hist(x[1:], label=x_list[0][i])
        plt.title("Histogram of " + x_list[0][i])
        plt.ylabel("Number of Articles")
        if len(x_list[1:]) == i:
            plt.xlabel("Number of Words")
    plt.show()


def same_visualize(x_list):
    """同じグラフにヒストグラムを表示する

    :param x_list:
    :return:
    """
    labels = x_list.pop(0)
    plt.hist(x_list, label=labels)
    plt.legend()
    plt.show()


def main():
    x1 = count_word("mainichi")
    x2 = count_word("asahi")
    labels = [x1.pop(0), x2.pop(0)]

    x_list = [labels, x1, x2]
    each_visualize(x_list)
    same_visualize(x_list)

    x1 = np.log10(x1)
    x2 = np.log10(x2)
    x_list = [labels, x1, x2]
    each_visualize(x_list)
    same_visualize(x_list)


if __name__ == '__main__':
    main()
