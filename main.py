import gevent.monkey
gevent.monkey.patch_all(thread=False)

import logging

from crawler import Crawler
from crawler.config import default_config

if __name__ == '__main__':
    config = {
        'main_url': 'https://www.lewenxiaoshuo.com/',
        'headers': {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'
        },
        'max_depth': 1,
        'logging_config': {
            'level': logging.DEBUG,
            ## %(name)s表示模块路径(其实是__name__的值)
            'format': '%(asctime)s %(levelname)-7s %(name)s - %(filename)s:%(lineno)d %(message)s',
        }
    }
    config = dict(default_config, **config)

    logging.basicConfig(**config['logging_config'])
    ## logger.setLevel(logging.DEBUG)
    try:
        c = Crawler(config)
        c.start()
    except KeyboardInterrupt:
        c.stop()
