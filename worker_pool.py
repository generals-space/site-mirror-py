'''
gevent类型的协程工作池, 以while循环不断执行指定的worker方法
'''
from gevent import sleep
from gevent.pool import Pool

from utils import logger

class WorkerPool:
    def __init__(self, queue, func = None, pool_max=100, worker_type = 'page'):
        self.queue = queue
        self.worker = func
        self.exit_signal = False
        self.pool_max = pool_max
        ## Pool类基于gevent.pool.Group类
        self.pool = Pool(pool_max)
        self.worker_type = worker_type

    def start(self, page_url = ''):
        if self.worker_type == 'asset' and page_url != '':
            logger.debug('asset worker pool start for page: %s' % page_url)

        while True:
            if self.exit_signal: break
            if not self.queue.empty():
                item = self.queue.pop()
                logger.debug('从队列中取出成员: %s, 调用worker' % str(item))
                self.pool.spawn(self.worker, *item)
            elif self.pool.free_count() != self.pool.size:
                ## 如果队列已空, 但是协程池还未全部空闲, 说明仍有任务在执行, 等待.
                free = self.pool.free_count()
                total = self.pool.size
                working = total - free
                logger.debug('pool worker usage: %d/%d, page url: %s' % (working, total, page_url))
                sleep(1)
            elif self.exit_signal:
                ## 如果队列为空, 且各协程都已空闲, 或是触发了stop()方法, 则停止while循环
                break
            else: 
                break
        if self.worker_type == 'asset' and page_url != '':
            logger.debug('asset worker pool stop for page: %s' % page_url)

    def stop(self):
        self.exit_signal = True
        # 只让进队列, 不让出队列, 就是只把当前正在处理的页面中的链接入队列, 不再弹出任务
        ## 把协程池中的任务取出重新入队列并持久化到本地文件, 避免丢失.
        for item in self.pool:
            self.queue.push(item.args)
