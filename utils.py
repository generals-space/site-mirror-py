import os
import re
import hashlib
import logging
from urllib.parse import urlparse, unquote

import requests

from settings import main_url, headers, proxies, output_path, logging_config

logging.basicConfig(**logging_config)
logger = logging.getLogger(__name__)
## logger.setLevel(logging.DEBUG)

main_site = ''
def get_main_site():
    global main_site
    if main_site == '':
        main_site = urlparse(main_url).netloc
    return main_site

def request_get_async(url, refer):
    '''
    协程形式发起get请求
    return: requests.get()的结果
    '''
    try:
        _headers = headers.copy()
        _headers['Referer'] = refer.encode('utf-8')
        resp = requests.get(url=url, verify=True, headers=_headers, proxies=proxies)
        return (1, resp)
    except requests.exceptions.ConnectionError as err:
        logger.error('连接异常 %s : %s' % (url, err))
        return (0, err)
    except Exception as err:
        logger.error('请求失败 %s: %s' % (url, err))
        return (0, err)

def save_file_async(file_path, file_name, byte_content):
    '''
    写入文件, 事先创建目标目录
    '''
    path = output_path + file_path
    if not path.endswith('/'): path = path + '/'
    if not os.path.exists(path): os.makedirs(path)

    try:
        file = open(path + file_name, "wb")
        file.write(byte_content)
        file.close()
        return (1, None)
    except IOError as err:
        logger.error('Save Error: %s, path: %s, name: %s' % (err, path, file_name))
        return (0, err)

special_chars = {
    '\\': 'xg',
    ':': 'mh',
    '*': 'xh',
    '?': 'wh',
    '<': 'xy',
    '>': 'dy',
    '|': 'sx',
    ' ': 'kg'
}

def trans_to_local_link(url, is_page = True):
    '''
    @param
        url: 待处理的url, 有时url为动态链接, 包含&, ?等特殊字符, 这种情况下需要对其进行编码.
        is_page: 是否为页面, 包含.php, .asp等动态页面, 区别于常规静态文件. 我们需要根据这个参数判断是否需要对其加上.html后缀.
    @return
        local_path: 本地文件存储路径, 用于写入本地html文档中的link/script/img/a等标签的链接属性
    '''
    ## 对于域名为host的url, 资源存放目录为output根目录, 而不是域名文件夹. 默认不设置主host
    main_site = get_main_site()

    urlObj = urlparse(url)
    origin_host = urlObj.netloc
    origin_path = urlObj.path
    origin_query = urlObj.query

    local_path = origin_path
    # url除去最后的/
    if local_path.endswith('/'): local_path += 'index.html'

    if origin_query != '': 
        query_str = origin_query
        for k, v in special_chars.items():
            if k in query_str: query_str = query_str.replace(k, v)
        local_path = local_path + special_chars['?'] + query_str

    if is_page and not local_path.endswith('.html') and not local_path.endswith('.htm'):
        local_path += '.html'

    ## 如果该url就是这个站点域名下的，那么无需新建域名目录存放
    ## 如果是其他站点的(需要事先开启允许下载其他站点的配置), 
    ## 则要将资源存放在以站点域名为名的目录下, 路径中仍然需要保留域名部分.
    ## 有时host中可能包含冒号, 需要转义.
    if origin_host != main_site: 
        local_path = origin_host.replace(':', special_chars[':']) + local_path

    ## url中可能包含中文, 需要解码.
    local_path = unquote(local_path)

    if origin_host != main_site: local_path = '/' + local_path
    return local_path

def trans_to_local_path(url, is_page = True):
    '''
    @return
        file_path: 目标文件的存储目录, 相对路径(不以/开头), 为""时, 表示当前目录
        file_name: 目标文件名称
    '''
    local_link = trans_to_local_link(url, is_page)
    ## 如果是站外资源, local_link可能为/www.xxx.com/static/x.jpg, 
    ## 但我们需要的存储目录是相对路径, 所以需要事先将
    if local_link.startswith('/'): local_link = local_link[1:]
    file_dir = os.path.dirname(local_link)
    file_name = os.path.basename(local_link)

    return file_dir, file_name
