import os
import re
import logging
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

empty_link_pattern = r'about:blank|javascript:(void\(0\))?'

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

image_pattern = '\.((jpg)|(png)|(bmp)|(jpeg)|(gif)|(webp))$'
font_pattern = '\.((ttf)|(woff)|(woff2)|(otf)|(eot))$'

def request_get_async(task, config):
    '''
    协程形式发起get请求
    return: requests.get()的结果
    '''
    try:
        _headers = config['headers'].copy()
        _headers['Referer'] = task['refer'].encode('utf-8')
        request_options = {
            'url': task['url'],
            'verify': True,
            'headers': _headers,
            'proxies': config['proxies'],
        }
        resp = requests.get(**request_options)
        return (1, resp)
    except requests.exceptions.ConnectionError as err:
        msg = '连接异常: task: {task:s}, err: {err:s}'
        logger.error(msg.format(task = str(task), err = err))
        return (0, err)
    except Exception as err:
        msg = '请求失败: task: {task:s}, err: {err:s}'
        logger.error(msg.format(task = str(task), err = err))
        return (0, err)

def save_file_async(site_path, file_path, file_name, byte_content):
    '''
    写入文件, 事先创建目标目录
    '''
    path = site_path + file_path
    if not path.endswith('/'): path = path + '/'
    if not os.path.exists(path): os.makedirs(path)

    try:
        file = open(path + file_name, "wb")
        file.write(byte_content)
        file.close()
        return (1, None)
    except IOError as err:
        msg = '保存文件失败: path: {path:s}, file: {file:s}, err: {err:s}'
        logger.error(msg.format(path = path, file = file_name, err = err))
        return (0, err)

def url_filter(url, url_type, config):
    '''
    @function 这个函数对url比对所有设置的规则, 判断目标url是否可以抓取.
    @param: url_type url类型: page/asset
    @return: True: 可以抓取, False: 不可以抓取
    '''
    main_site = urlparse(config['main_url']).netloc
    ## 站外的页面绝对不会抓取, 倒是站外的资源可以下载下来
    if url_type == 'page' and urlparse(url).netloc != main_site:
        logger.info('不抓取站外页面: %s' % url)
        return False

    urlObj = urlparse(url)
    host = urlObj.netloc
    if url_type == 'asset' and host != main_site and not config['outsite_asset']:
        logger.info('不抓取站外资源: %s' % url)
        return False

    path = urlObj.path
    if url_type == 'asset' and path.endswith('.js') and config['no_js']:
        logger.info('不抓取js资源: %s' % url)
        return False

    if url_type == 'asset' and path.endswith('.css') and config['no_css']:
        logger.info('不抓取css资源: %s' % url)
        return False

    if url_type == 'asset' and re.search(image_pattern, url) and config['no_images']:
        logger.info('不抓取图片资源: %s' % url)
        return False

    if url_type == 'asset' and re.search(font_pattern, url) and config['no_fonts']:
        logger.info('不抓取字体资源: %s' % url)
        return False

    ## 不抓取黑名单中的url
    for pattern in config['black_list']:
        if re.search(pattern, url):
            logger.info('不抓取黑名单中的url: %s' % url)
            return False

    return True
