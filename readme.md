# 这是什么
一个python写的爬虫。输入一个网页的地址，它能帮你爬取这个网页以及它所涉及的资源文件(css,js,image)，还可以爬取这个页面所涉及的其他页面，甚至可以帮你把整站都爬下来。

当然，更准确地说，它是一个镜像工具。它能帮你把你想要离线浏览的网站镜像下来，你可以方便地在本地不联网地观看

# 如何安装
1. 命令行进入项目
2. pip install -r requirements.txt
3. 如果是windows，gevent安装不成功，<del>建议上 [http://www.lfd.uci.edu/~gohlke/pythonlibs/]() 直接下载编译好的安装</del>
4. 上面那个链接要翻墙，我下载好了放到InstallLib目录下了，自己根据32位64位系统选择安装

# 如何使用
1. 设置setting.py
2. 运行main.py
3. 爬取完毕后，运行browse.py，打开浏览器浏览
