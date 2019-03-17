import logging

# 要爬取的网站url, 需要以http(s)开头
main_url = 'http://97daimeng.com/'

# 设置代理
proxies = {}
# 代理格式:
# {
#     "http": "127.0.0.1:1080",
#     "https": "127.0.0.1:1080",
# }

# HTTP请求的header
headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'
}

# 输出站点文件的路径，最后要加 '/'
output_path = './output/'

site_db = 'site.db'
# 每次请求的最大超时时间
request_timeout = 30

# 爬取页面的协程数
doc_pool_max = 20

# 爬取资源文件的协程数
res_pool_max = 20

# 每次请求随机延迟的时间，单位s，[最大值,最小值]
wait_time = [1, 3]

# 是否爬取该站以外的静态资源(不是页面)
outsite_asset = True

# 爬取页面的深度, 从1开始计, 爬到第N层为止.
# 1表示只抓取单页, 0表示无限制
max_depth = 2
# 请求出错最大重试次数（超时也算出错）
max_retry_times = 5

empty_link_pattern = r'about:blank|javascript:(void\(0\))?'

logging_config = {
    'level': logging.DEBUG,
    'format': '%(asctime)s %(levelname)s - %(name)s - %(filename)s - %(message)s',
}
