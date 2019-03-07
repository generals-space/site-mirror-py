# coding=utf-8
import gevent.monkey
gevent.monkey.patch_all(thread=False)

from crawler import Crawler

if __name__ == '__main__':
    try:
        c = Crawler()
        c.start()
    except KeyboardInterrupt:
        c.stop()
