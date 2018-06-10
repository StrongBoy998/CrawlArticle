#!/usr/bin/env python
# coding=utf-8

import os
import re
import sys
import copy
import tools
ver = sys.version[0]
from lxml import etree
from htmlFilter import *
from getHtml import get_html
from collections import Counter
from operator import itemgetter
if ver == '2':
    reload(sys)
    sys.setdefaultencoding('utf8') 
'''
    正文提取核心模块
'''
class NewsParser:

    def __init__(self):

        self.score = 6
        self.length = 5

    def _cal_score(self, text):
        """
            计算兴趣度
        """
        if "。" not in text:
            if "，" in text:
                return 0
            else:
                return -1
        else:
            score = text.count('，') + 1
            score += text.count(',') + 1
            score += text.count('；')
            score += text.count('。')
            return score

    def _line_div(self, html):
        """
            线性重构html代码
        """
        html = re.sub("</?div>|</?table>", "</div><div>", html, flags=re.I)
        html = html.replace('</div>', '', 1)
        index = html.rfind('<div>')
        html = html[:index] + html[index:].replace('<div>', '', 1)
        return html

    def _line_p(self, text):
        """
            p标签变成2层嵌套结构，第二层为线性
        """
        text_list = list()
        text = re.sub(r'</?p\s?.*?>', r'</p><p class="news_body">', text, flags=re.I | re.S)
        text = text.replace('</p>', '', 1)
        index = text.rfind('<p>')
        text = text[:index] + text[index:].replace('<p>', '', 1)
        text = '<p class="news_head">{0}</p>'.format(text)
        return text

    def _extract_paragraph(self, html):
        """
            通过计算兴趣度得分，抽取聚类段落集和吸收段落集
            param: html
            return: tuple
        """
        cluster_para = {}
        absorb_para = {}
        for index, div_str in enumerate(re.findall("<div>(.*?)</div>", html, flags=re.S | re.I)):
            if len(div_str.strip()) == 0:
                continue
            para_str = div_str.strip()
            score = self._cal_score(para_str)
            if score > self.score:
                cluster_para[index] = [para_str, score]
            else:
                absorb_para[index] = [para_str, score]
        return cluster_para, absorb_para

    def _extract_feature(self, para_dict):
        """
            抽取聚类段落集里的特征，获得得分最高的div下的p最多的属性值
            param: para_dict:
            return: index, feature
        """
        c = Counter()
        index, text = max(para_dict.items(), key=lambda asd: asd[1][1])
        feature_list = re.findall("(<p.*?>)", text[0], flags=re.I | re.S)
        for feature in feature_list:
            c[feature] += 1
        if c.most_common(1):
            feature, amount = c.most_common(1)[0]
        else:
            feature = ''
        feature = feature.replace('(', '\(').replace(')', '\)')
        return index, feature

    def _gen_skeleton(self, para_dict, index, feature):
        """ 
            聚类段落集聚类生成生成正文脉络集合
        """
        skeleton_dict = {}
        num_list = []
        if not feature:
            skeleton_dict[index] = para_dict[index]
            return skeleton_dict
        for num in para_dict.keys():
            num_list.append(num)
        num_list = sorted(num_list)
        od = num_list.index(index)
        f_list = num_list[0:od]
        l_list = num_list[od:len(num_list)]
        # 向后聚类
        while l_list:
            tmp = l_list.pop(0)
            length = abs(tmp - index)
            if length < self.length:
                if re.match(r".*?{0}".format(feature), para_dict[tmp][0], flags=re.S | re.I):
                    skeleton_dict[tmp] = para_dict[tmp]
            index = tmp
        # 向前聚类
        while f_list:
            tmp = f_list.pop()
            length = abs(index - tmp)
            if length < self.length:
                if re.match(r".*?{0}".format(feature), para_dict[tmp][0], flags=re.S):
                    skeleton_dict[tmp] = para_dict[tmp]
            index = tmp
        return skeleton_dict

    def _absorb_text(self, skeleton_dict, para_dict):
        """
            从伪噪声段落吸收噪声段落
        """
        content_dict = skeleton_dict
        sk_list = skeleton_dict.keys()
        pa_list = para_dict.keys()
        sk_list = sorted(sk_list)
        pa_list = sorted(pa_list)
        heads = []
        middle = []
        tail = []
        for each in pa_list:
            if each < sk_list[0]:
                heads.append(each)
            if each > sk_list[-1]:
                tail.append(each)
            if (each >= sk_list[0]) and (each <= sk_list[-1]):
                middle.append(each)
        while heads:
            tmp = heads.pop()
            index = sk_list[0]
            if abs(tmp - index) < self.length:
                if para_dict[tmp][1] * 2 > self.score:
                    content_dict[tmp] = para_dict[tmp]
            else:
                break
        while tail:
            tmp = tail.pop(0)
            index = sk_list[-1]
            if abs(tmp - index) < self.length:
                if para_dict[tmp][1] * 2 > self.score:
                    content_dict[tmp] = para_dict[tmp]
            else:
                break
        while middle:
            tmp = middle.pop()
            if para_dict[tmp][1] * 2 > self.score:
                content_dict[tmp] = para_dict[tmp]
        return content_dict

    def _substring(self, text):
        text = self._line_p(text)
        text = pretty_html(text)
        selector = etree.HTML(text)
        xpath_result = selector.xpath('//p')
        if len(xpath_result) == 1:
            sub_string = xpath_result[0].xpath('string(.)')
            sub_string = tools.drop_mutil_br(sub_string)
        else:
            text_list = []
            xpath_result = selector.xpath('//p[@class="news_body"]')
            for item in xpath_result:
                p_string = item.xpath('string(.)').strip()
                if not p_string:
                    continue
                p_string = tools.drop_null(p_string)
                text_list.append(p_string)
            if text_list:
                sub_string = '\n'.join(text_list)
            else:
                sub_string = ''
        return sub_string

    def _pretty_text(self, index_content_list):
        contents = list()
        for each in index_content_list:
            sub_text = self._substring(each[1][0])
            if not sub_text:
                continue
            else:
                contents.append(sub_text)
        text = "\n".join(contents)
        return text

    def extract_news(self, html):
        html = handle_html(html)
        html = self._line_div(html)
        index = 0
        cluster_para, absorb_para = self._extract_paragraph(html)
        if cluster_para:
            index, feature = self._extract_feature(cluster_para)
            skeleton_dict = self._gen_skeleton(cluster_para, index, feature)
            if skeleton_dict:
                if absorb_para:
                    content_dict = self._absorb_text(skeleton_dict, absorb_para)
                else:
                    content_dict = skeleton_dict
                index_content_list = sorted(content_dict.items(), key=itemgetter(0))
                top_div_list = list()
                top_text = ''
                index = index_content_list[0][0]
                for ind, each_div in enumerate(re.findall("<div>(.*?)</div>", html, flags=re.S)):
                    if ind >= index:
                        break
                    top_text += each_div
                    top_div_list.append((ind, each_div))
        else:
            return

        def extract_content():
            text = ''
            if index_content_list:
                text = self._pretty_text(index_content_list)
                text = text.strip()
            return text

        def extract_pubtime():
            pubtime = ''
            tmp_top_div_list = copy.deepcopy(top_div_list)
            while tmp_top_div_list:
                ind, item = tmp_top_div_list.pop()
                if not item.strip():
                    continue
                div_selector = etree.HTML(item)
                if div_selector is None:
                    continue
                div_text = div_selector.xpath('string(.)').strip()
                if not div_text:
                    continue
                pubtime = re.search(r'(\d{4}\s*[年\-:/]\s*)\d{1,2}\s*[月\-：/]\s*\d{1,2}\s*[\-_:日]?\s*\d{1,2}\s*:\s*\d{1,2}\s*(:\s*\d{1,2})?', div_text, flags=re.S|re.I)
                if pubtime:
                    pubtime = pubtime.group()
                    index = ind
                    break
            if not pubtime:
                tmp_top_div_list = copy.deepcopy(top_div_list)
                while tmp_top_div_list:
                    ind, item = tmp_top_div_list.pop()
                    if not item.strip():
                        continue
                    div_selector = etree.HTML(item)
                    if div_selector is None:
                        continue
                    div_text = div_selector.xpath('string(.)')
                    pubtime = re.search(r'(\d{4}\s*[年\-:/]\s*)\d{1,2}\s*[月\-：/]\s*\d{1,2}\s*[\-_:日/]?', div_text, flags=re.S)
                    if pubtime:
                        pubtime = pubtime.group()
                        index = ind
                        break
            if pubtime:
                pubtime = pubtime.strip()
                pubtime = pubtime.replace('年', '-').replace('月', '-').replace('日', ' ').replace('/', '-')
                pubtime = tools.drop_mutil_blank(pubtime)
                return pubtime, index
            else:
                return pubtime, 0

        def extract_title():
            title = ''
            selector = etree.HTML(top_text)
            tmps = selector.xpath('//body//h1|//body//h2|//body//h3|//body//h4')
            if not tmps:
                tmps = selector.xpath('//h1|//h2|//h3|//h4')
            tmp_title_list = list()
            title_list = list()
            for tmp in tmps:
                title_str = tmp.xpath('string(.)').strip()
                tmp_title_list.append((len(title_str), title_str))
                title_list = sorted(tmp_title_list, key=itemgetter(0))
            while title_list:
                title_str_tuple = title_list.pop()
                title_str = title_str_tuple[1]
                if tools.is_longsent(title_str):
                    title_str = tools.clear_pan(title_str)
                    title = tools.drop_null(title_str)
                    break
            if not title:
                top_div_list = list()
                for ind, each_div in enumerate(re.findall("<div>(.*?)</div>", html, flags=re.S)):
                    div_str = re.sub(r"<ul\s+[^>]*?>.*?</ul>", "", each_div, flags=re.I | re.S)
                    div_str = re.sub(r"<a\s+[^>]*?>.*?</a>", "", div_str, flags=re.I | re.S)
                    if ind > index - 1:
                        break
                    if div_str.strip():
                        top_div_list.append((ind, each_div))
                tmp_top_div_list = copy.deepcopy(top_div_list)
                while tmp_top_div_list:
                    ind, item = tmp_top_div_list.pop()
                    if abs(index - ind) > 5:
                        break
                    if not item.strip():
                        continue
                    div_selector = etree.HTML(item)
                    if div_selector is None:
                        continue
                    div_text = div_selector.xpath('string(.)').strip()
                    filter_toptext = re.sub(r'[^\u4E00-\u9FFF]', '', div_text, flags=re.S).strip()
                    if len(filter_toptext) >= 6:
                        title = div_text
                        if '\n' in div_text:
                            title = div_text.split('\n')[0]
                        break
            selector = etree.HTML(html)
            if not title:
                tmps = selector.xpath('//title/text()')
                if tmps:
                    title = tmps[0].strip()
                    title = tools.clear_title(title)
            return title

        news = {}
        news_content = extract_content()
        news_pubtime, index = extract_pubtime()
        news_title = extract_title()
        news['news_content'] = news_content
        news['news_pubtime'] = news_pubtime
        news['news_title'] = news_title
        return news

def clean_folder():
    try:
      fileNameList = [x for x in os.listdir(os.getcwd()) if x[-3:] == 'pyc']
      temp = [os.remove(x) for x in fileNameList]
      os.system('rm -rf __pycache__')
    except:
      pass

def online_parse(url, sourceCode=False):
    if sourceCode != False:
        html = sourceCode
    else:
        html = get_html(url)
    parser = NewsParser()
    article = parser.extract_news(html)
    clean_folder()
    return article

def offline_parse(html):
    parser = NewsParser()
    article = parser.extract_news(html)
    return article

def getResult(url, *args):  
    if args:
        res = online_parse(url, args[0])
    else:
        res = online_parse(url)
    # 获取文章正文
    article = res.get('news_content')
    # 获取文章发布时间
    publicTime = res.get('news_pubtime')
    # 获取文章标题
    newsTitle = res.get('news_title')
    return {'newsTitle':newsTitle, 'publicTime':publicTime, 'article':article}

if __name__ == '__main__':

    url = 'http://www.takefoto.cn/viewnews-1486870.html'
    # htmlCode = requests.get('http://www.takefoto.cn/viewnews-1486870.html').text
    # msg = getResult(url, htmlCode)
    msg = getResult(url)
    print(msg['newsTitle'])
    print('='*100)
    print(msg['publicTime'])
    print('='*100)
    print(msg['article'])
    print('='*100)