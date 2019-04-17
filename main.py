import gevent.monkey
gevent.monkey.patch_all(thread=False)

import logging

from crawler import Crawler
from config import default_config

if __name__ == '__main__':
    config = {
        'main_url': 'https://m.xieeda.com/',
        'headers': {
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
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
