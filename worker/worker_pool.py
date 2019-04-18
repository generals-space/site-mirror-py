'''
gevent类型的协程工作池, 以while循环不断执行指定的worker方法
'''
import logging

from gevent import sleep
from gevent.pool import Pool

logger = logging.getLogger(__name__)

class WorkerPool:
    def __init__(self, queue, func = None, pool_size = 100, worker_type = 'page'):
        self.queue = queue
        self.worker = func
        self.exit_signal = False
        self.pool_size = pool_size
        ## Pool类基于gevent.pool.Group类
        self.pool = Pool(pool_size)
        self.worker_type = worker_type

    def start(self, page_task = None):
        if self.worker_type == 'asset':
            msg = '静态资源工作池启动, 所属页面: {:s}'
            logger.debug(msg.format(page_task['refer']))

        while True:
            if self.exit_signal: break
            if not self.queue.empty():
                task = self.queue.pop()
                msg = '从队列中取出成员, 调用worker. task: {task:s}'
                logger.debug(msg.format(task = str(task)))
                self.pool.spawn(self.worker, task)
            elif self.pool.free_count() != self.pool.size:
                ## 如果队列已空, 但是协程池还未全部空闲, 说明仍有任务在执行, 等待.
                free = self.pool.free_count()
                total = self.pool.size
                working = total - free
                if self.worker_type == 'asset':
                    msg = '工作池使用率: {working:d}/{total:d}, page_task: {page_task:s}'
                    logger.debug(msg.format(working = working, total = total, page_task = str(page_task)))
                sleep(1)
            elif self.exit_signal:
                ## 如果队列为空, 且各协程都已空闲, 或是触发了stop()方法, 则停止while循环
                break
            else: 
                break
        if self.worker_type == 'asset':
            msg = '静态资源工作池结束, 所属页面: {:s}'
            logger.debug(msg.format(page_task['refer']))

    def stop(self):
        self.exit_signal = True
        # 只让进队列, 不让出队列, 就是只把当前正在处理的页面中的链接入队列, 不再弹出任务
        ## 把协程池中的任务取出重新入队列并持久化到本地文件, 避免丢失.
        for item in self.pool:
            self.queue.push(item.args)
