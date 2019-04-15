import logging

# 要爬取的网站url, 需要以http(s)开头
main_url = 'https://m.xieeda.com/'

# 设置代理
# 代理格式:
# {
#     "http": "127.0.0.1:1080",
#     "https": "127.0.0.1:1080",
# }
proxies = {}

# HTTP请求的header
headers = {
    'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
}

# 输出站点文件的路径，最后要加 '/'
site_path = './sites/'

site_db = 'site.db'
# 每次请求的最大超时时间
request_timeout = 30

# 爬取页面的协程数
doc_pool_max = 20

# 爬取资源文件的协程数
res_pool_max = 20

# 每次请求随机延迟的时间，单位s，[最大值,最小值]
wait_time = [1, 3]

# 爬取页面的深度, 从1开始计, 爬到第N层为止.
# 1表示只抓取单页, 0表示无限制
max_depth = 1
# 请求出错最大重试次数（超时也算出错）
max_retry_times = 5

logging_config = {
    'level': logging.DEBUG,
    'format': '%(asctime)s %(levelname)s - %(name)s - %(filename)s - %(message)s',
}
############################################################
## 抓取规则

## 是否爬取该站以外的静态资源(不是页面)
outsite_asset = True
no_js = True
no_css = False
no_images = False
no_fonts = False
## 黑名单, 列表类型. 规则格式为正则, 默认为空.
black_list = []
