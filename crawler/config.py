import logging

default_config = {
    ## 起始页面, 要爬取的网站url, 需要以http(s)开头
    'main_url': '',
    ## proxies: request代理, 代理格式:
    ## {
    ##     "http": "127.0.0.1:1080",
    ##     "https": "127.0.0.1:1080",
    ## }
    'proxies': {},
    ## HTTP请求的header
    'headers': {},
    ## request请求超时时间
    'request_timeout': 30,

    ## 站点保存路径
    'site_path': './sites/',
    ## 抓取记录存储文件
    'site_db': 'site.db',
    ## 页面抓取协程池中协程的数量
    'page_pool_size': 20,
    ## 静态资源抓取协程池中协程的数量
    'asset_pool_size': 20,
    ## 页面任务队列容量(超过容量插入数据会阻塞)
    'page_queue_size': 10000,
    ## 静态资源任务队列容量(超过容量插入数据会阻塞)
    'asset_queue_size': 10000,
    ## 爬取页面的深度, 从1开始计, 爬到第N层为止.
    ## 1表示只抓取单页, 0表示无限制
    'max_depth': 0,
    ## 请求出错最大重试次数
    'max_retry_times': 5,

    ## 是否爬取该站以外的静态资源(不是页面)
    'outsite_asset': True,
    'no_js': True,
    'no_css': False,
    'no_images': False,
    'no_fonts': False,
    'no_audio': False,
    'no_video': False,
    ## 黑名单, 列表类型. 规则格式为正则, 默认为空.
    'black_list': [
        # '/login/*'
        # '/admin/*'
        # '/comments/*'
    ],

    'logging_config': {
        'level': logging.INFO,
        'format': '%(asctime)s %(levelname)s - %(name)s - %(filename)s - %(message)s',
    }
}