import os
from urllib.parse import urlparse, unquote

from utils import special_chars

def trans_to_local_link_for_page(urlObj):
    origin_path = urlObj.path
    origin_query = urlObj.query

    local_link = origin_path
    if local_link == "": local_link = 'index.html'
    if local_link.endswith('/'): local_link += 'index.html'
    if origin_query != '': 
        query_str = origin_query
        for k, v in special_chars.items():
            if k in query_str: query_str = query_str.replace(k, v)
        local_link = local_link + special_chars['?'] + query_str
    if not local_link.endswith('.html') and not local_link.endswith('.htm'):
        local_link += '.html'
    return local_link

def trans_to_local_link_for_asset(urlObj):
    origin_path = urlObj.path
    origin_query = urlObj.query

    local_link = origin_path
    if local_link == "": local_link = 'index'
    if local_link.endswith('/'): local_link += 'index'
    if origin_query != '': 
        query_str = origin_query
        for k, v in special_chars.items():
            if k in query_str: query_str = query_str.replace(k, v)
        local_link = local_link + special_chars['?'] + query_str
    return local_link

def trans_to_local_link(url, url_type, main_site):
    '''
    @param
        url: 待处理的url, 有时url为动态链接, 包含&, ?等特殊字符, 这种情况下需要对其进行编码.
        is_page: 是否为页面, 包含.php, .asp等动态页面, 区别于常规静态文件. 我们需要根据这个参数判断是否需要对其加上.html后缀.
    @return
        local_link: 本地文件存储路径, 用于写入本地html文档中的link/script/img/a等标签的链接属性
    '''
    ## 对于域名为host的url, 资源存放目录为output根目录, 而不是域名文件夹. 默认不设置主host

    urlObj = urlparse(url)
    origin_host = urlObj.netloc
    local_link = ''
    if url_type == 'page':
        local_link = trans_to_local_link_for_page(urlObj)
    else:
        local_link = trans_to_local_link_for_asset(urlObj)

    ## 如果该url就是当前站点域名下的，那么无需新建域名目录存放.
    ## 如果是其他站点的(需要事先开启允许下载其他站点的配置), 
    ## 则要将资源存放在以站点域名为名的目录下, 路径中仍然需要保留域名部分.
    ## 有时host中可能包含冒号, 需要转义.
    if origin_host != main_site: 
        local_link = '/' + origin_host.replace(':', special_chars[':']) + local_link

    ## url中可能包含中文, 需要解码.
    local_link = unquote(local_link)
    return local_link

def trans_to_local_path(url, url_type, main_site):
    '''
    @return
        file_path: 目标文件的存储目录, 相对路径(不以/开头), 为""时, 表示当前目录
        file_name: 目标文件名称
    '''
    local_link = trans_to_local_link(url, url_type, main_site)
    ## 如果是站外资源, local_link可能为/www.xxx.com/static/x.jpg, 
    ## 但我们需要的存储目录是相对路径, 所以需要事先将链接起始的/移除
    if local_link.startswith('/'): local_link = local_link[1:]
    file_dir = os.path.dirname(local_link)
    file_name = os.path.basename(local_link)

    return file_dir, file_name
