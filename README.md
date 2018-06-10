## 基于文字密度的新闻正文提取模块

### 兼容性：

###该模块兼容python2.x和python3.x,可以作为工具包直接引用

### 准备工作：

###1.下载项目源码：https://github.com/StrongBoy998/CrawlArticle.git
###2.解压源码，切入源码目录：cd getContent
###3.安装项目需要依赖的库：pip install -r requireMents.txt

### 使用方法：

###1.直接使用
###1）用编辑器打开articleExtractor.py，修改为要抓取的url,如下图所示：
![](https://i.imgur.com/Pt5fOVP.png)
###2）在终端运行python articleExtractor.py，回车，效果如下：
![](https://i.imgur.com/x9Q5gMQ.png)
###2.作为其他项目的一个子模块传入源码，直接返回标题，发布时间，文章内容
###1）克隆项目代码解压放入自己的项目中，然后在该模块的同级目录创建自己的测试脚本，加入以下代码如下图：
    `#!/usr/bin/env python
    `# coding=utf-8

    `import requests
    `from getContent.articleExtractor import *

    `url = 'http://www.takefoto.cn/viewnews-1486870.html'
    `htmlCode = requests.get(url).text
    `msg = getResult(url, htmlCode)
    `print(msg['newsTitle'])
    `print('='*100)
    `print(msg['publicTime'])
    `print('='*100)
    `print(msg['article'])
    `print('='*100)`
![](https://i.imgur.com/60Pr0YX.png)
###2）在终端运行python demo.py，回车，效果如下：
![](https://i.imgur.com/JzVK67n.png)

### python3.x使用方法同上，附运行结果截图一张：
![](https://i.imgur.com/wb35Fgu.png)

