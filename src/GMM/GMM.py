# -*- coding: utf-8 -*-
import numpy as np
import copy
from data_helper import load_samples_data, load_samples_test_data, load_mnist_data


def gaussian(data, mean, cov):
    """
    计算高维高斯函数概率密度.
    :param data: 样本数据
    :param mean: 均值
    :param cov: 协方差
    :return:
    """
    dim = np.shape(cov)[0]   # 计算维度
    covdet = np.linalg.det(cov)  # 计算|cov|
    covinv = np.linalg.inv(cov)  # 计算cov的逆
    if covdet == 0:              # 以防行列式为0
        covdet = np.linalg.det(cov+np.eye(dim)*0.01)
        covinv = np.linalg.inv(cov+np.eye(dim)*0.01)
    m = data - mean
    z = -0.5 * np.dot(np.dot(m, covinv), m)    # 计算exp()里的值
    return 1.0/(np.power(np.power(2*np.pi, dim)*abs(covdet), 0.5))*np.exp(z)  # 返回概率密度值1234567891011


def isdistance(means, criterion=0.03):
    """
    用于判断初始聚类簇中的means是否距离离得比较近
    :param means: 初始聚类簇means集合
    :param criterion:
    :return:
    """
    K = len(means)
    for i in range(K):
     for j in range(i+1, K):
         if criterion > np.linalg.norm(means[i]-means[j]):
             return False
     return True


def getInitialMeans(data, K, criterion):
    """
    获取最初的聚类中心.
    :param data: 数据集合
    :param K:
    :param criterion:
    :return:
    """
    dim = data.shape[1]  # 数据的维度
    means = [[] for k in range(K)]  # 存储均值
    minmax = []  # 存储每一维的最大最小值
    for i in range(dim):
        minmax.append(np.array([min(data[:, i]), max(data[:, i])]))
    minmax = np.array(minmax)

    # 随机产生means
    while True:
        for i in range(K):
            means[i] = []
            for j in range(dim):
                 means[i].append(np.random.random()*(minmax[i][1]-minmax[i][0])+minmax[i][0])
            means[i] = np.array(means[i])
        # judge
        if isdistance(means, criterion):
            break
    return means


def kmeans(data, K):
    """
    k-means cluster.
    估计大约几个样本属于一个GMM.
    :param data: 样本数据集
    :param K: K个类别
    :return:
    """
    N = data.shape[0]  # 样本数量
    dim = data.shape[1]  # 样本维度
    # 初始化聚类中心点
    means = getInitialMeans(data, K, 15)

    means_old = [np.zeros(dim) for k in range(K)]
    # 收敛条件
    while np.sum([np.linalg.norm(means_old[k] - means[k]) for k in range(K)]) > 0.01:
        means_old = copy.deepcopy(means)
        numlog = [0] * K  # 存储属于某类的个数
        sumlog = [np.zeros(dim) for k in range(K)]  # 存储属于某类的样本均值

        # E步
        for i in range(N):
            dislog = [np.linalg.norm(data[i]-means[k]) for k in range(K)]
            tok = dislog.index(np.min(dislog))
            numlog[tok] += 1         # 属于该类的样本数量加1
            sumlog[tok] += data[i]   # 存储属于该类的样本取值

        # M步
        for k in range(K):
            means[k] = 1.0 / (numlog[k] + 1.) * sumlog[k]
    return means


def GMM(data, K):
    """
    GMM Models.
    :param data: 数据集合
    :param K: K
    :return:
    """
    N = data.shape[0]
    dim = data.shape[1]
    means = kmeans(data, K)
    convs = [0] * K
    # 初始方差等于整体data的方差
    for i in range(K):
        convs[i] = np.cov(data.T)
    pis = [1.0/K] * K
    gammas = [np.zeros(K) for i in range(N)]
    loglikelyhood = 0
    oldloglikelyhood = 1

    while np.abs(loglikelyhood - oldloglikelyhood) > 0.0001:
        oldloglikelyhood = loglikelyhood

        # E步
        for i in range(N):
            res = [pis[k] * gaussian(data[i], means[k], convs[k]) for k in range(K)]
            sumres = np.sum(res)
            for k in range(K):           # gamma表示第n个样本属于第k个混合高斯的概率
                gammas[i][k] = res[k] / sumres

        # M步
        for k in range(K):
            Nk = np.sum([gammas[n][k] for n in range(N)])  # N[k] 表示N个样本中有多少属于第k个高斯

            pis[k] = 1.0 * Nk/N
            means[k] = (1.0/Nk) * np.sum([gammas[n][k] * data[n] for n in range(N)], axis=0)
            xdiffs = data - means[k]
            convs[k] = (1.0/Nk)*np.sum([gammas[n][k] * xdiffs[n].reshape(dim, 1) * xdiffs[n] for n in range(N)], axis=0)
        # 计算最大似然函数
        loglikelyhood = np.sum(
            [np.log(np.sum([pis[k] * gaussian(data[n], means[k], convs[k]) for k in range(K)])) for n in range(N)])

        print("current pi: ", pis, " means: ", means, " convs: ", convs, ' loglikelyhood: ', loglikelyhood)
    return pis, means, convs


def GMM_prob(data, pis, means, convs):
    """
    calc the GMM prob of the sample data.
    :param data:
    :param pis:
    :param means:
    :param convs:
    :return:
    """
    K = len(pis)
    probs = [pis[i]*gaussian(data, means[i], convs[i]) for i in range(K)]
    return np.sum(probs)


def experiment1():
    """
    1. 使用训练样本估计GMM参数(2个GMM)
    2. 构造区分两类的GMM分类器
    :return:
    """
    # train GMM1 and GMM2
    K = 2
    train_data1, train_data2 = load_samples_data()
    print("for Train1 data: ")
    pis1, means1, convs1 = GMM(train_data1, K)
    print("train1 data,  pi: ", pis1, " means: ", means1, " convs: ", convs1)

    print("*"*100)

    print("for Train2 data: ")
    pis2, means2, convs2 = GMM(train_data2, K)
    print("train2 data,  pi: ", pis2, " means: ", means2, " convs: ", convs2)

    # test the GMM classifier
    test_data1, test_data2 = load_samples_test_data()
    count_1 = 0
    for data in test_data1:
        if GMM_prob(data, pis1, means1, convs1) > GMM_prob(data, pis2, means2, convs2):
            count_1 += 1

    count_2 = 0
    for data in test_data2:
        if GMM_prob(data, pis2, means2, convs2) > GMM_prob(data, pis1, means1, convs1):
            count_2 += 1

    print("count1: ", count_1)
    print("count2: ", count_2)


def experiment2():
    """
    GMM分类mnist.
    ---------
    1. 对每一个类别训练一个GMM.
    2. 对于一个样本，判断这个样本属于哪个GMM的概率大就属于哪个类别.
    :return:
    """
    # 设置GMM中的K值
    K = 3
    # 将数据分为C类
    datas = {}
    train_datas, train_labels = load_mnist_data(filename='data/TrainSamples.csv',
                                                label_filename='data/TrainLabels.csv')
    for idx, j in enumerate(train_labels):
        if j not in datas.keys():
            datas[j] = []
        datas[j].append(train_datas[idx])

    # train C GMM
    print("train C GMM....")
    params = {}
    for c in datas.keys():
        pis, means, convs = GMM(np.array(datas[c], dtype='float64'), K)
        params[c] = (pis, means, convs)

    # test the test_data accuracy
    print("test the data acc.....")
    test_datas, test_labels = load_mnist_data(filename='data/TestSamples.csv',
                                              label_filename='data/TestLabels.csv')
    count = 0
    for idx, test_data in enumerate(test_datas):
        target = test_labels[idx]
        max_prob = 0.
        max_c = 0
        for c in params.keys():
            pis, means, convs = params[c]
            prob = GMM_prob(test_data, pis, means, convs)
            if prob > max_prob:
                max_prob = prob
                max_c = c
        if target == max_c:
            count += 1
    print("test accuracy is:{} / {} = {} ".format(count, len(test_datas), count / (len(test_datas) + 0.)))


if __name__ == "__main__":
    experiment2()








