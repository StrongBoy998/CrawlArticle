#!/usr/bin/env python
# coding=utf-8

import re
import sys
import pycurl
import random
import chardet
import requests
ver = sys.version[0]
from tools import uaList
if ver == '2':
    reload(sys)
    sys.setdefaultencoding('utf8') 
    from cStringIO import StringIO
else:
    import io
    from io import BytesIO as StringIO
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8')
'''
    get website's source code and return html
'''
ua = random.choice(uaList)
stopUrls = ['javascript', '.css', '.js', '.rar', '.csv', '.xls', '.exe', '.apk', '.doc', '.jpg', '.png', '.flv', '.mp4', '.EXE']
uaChrome = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
encodeList = ['gbk', 'GBK', 'gb2312', 'GB2312', 'big5', 'BIG5', 'utf8', 'UTF8', 'utf-8', 'UTF-8', 'ISO-8859-1', 'Unicode', 'gb18030', 'GB18030']
def pycGet(url):
    try:
        b = StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL,url)
        c.setopt(pycurl.FOLLOWLOCATION, True)
        c.setopt(pycurl.TIMEOUT, 5) 
        c.setopt(pycurl.ENCODING, 'gzip')
        c.setopt(pycurl.USERAGENT, ua)
        c.setopt(pycurl.NOSIGNAL, True)
        c.setopt(pycurl.WRITEFUNCTION, b.write)
        c.setopt(pycurl.MAXREDIRS, 5)
        c.setopt(c.WRITEFUNCTION, b.write)
        c.perform()
        if ver == 2:
            html = b.getvalue()
        else:
            try:
                html = b.getvalue().decode("utf-8", 'ignore')
            except:
                try:
                    codeDetect = chardet.detect(b.getvalue())['encoding']
                    html = result.decode(codeDetect, 'ignore')
                except:
                    html = reqGet(url)
        b.close()
    except:
        html = ''
    return html

def reqGet(url):
    try:
        html = requests.get(url, headers={"User-Agent":ua}).text
    except Exception as e:
        try:
            html = requests.get(url, headers={"User-Agent":uaChrome}).content
        except:
            html = ''
    return html

def get_html(url):
    flag = url[-11:]
    judStr = [x for x in stopUrls if x in flag]
    if len(judStr) == 0:
        if 'https' in url:
            html = reqGet(url)
            try:
                html = reqGet(url)
            except:
                try:
                    html = reqGet(url)
                except:
                    try:
                        html = pycGet(url)
                    except:
                        html = ''
        else:
            try:
                html = pycGet(url)
            except:
                try:
                    html = pycGet(url)
                except:
                    try:
                        html = reqGet(url)
                    except:
                        html = ''
    else:
        pass
    return html