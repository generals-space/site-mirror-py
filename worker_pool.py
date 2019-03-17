'''
gevent类型的协程工作池, 以while循环不断执行指定的worker方法
'''
from gevent import sleep
from gevent.pool import Pool

class WorkerPool:
    def __init__(self, queue, func = None, pool_max=100):
        self.queue = queue
        self.worker = func
        self.exit_signal = False
        self.pool_max = pool_max
        self.pool = Pool(pool_max)

    def start(self):
        while True:
            if self.exit_signal: break
            if not self.queue.empty():
                t = self.queue.pop()
                self.pool.spawn(self.worker, *t)
            elif self.pool.free_count() == self.pool.size or self.exit_signal:
                ## 如果各协程都已空闲, 或是触发了stop()方法, 则停止while循环
                break
            else:
                ## 如果队列已空, 但是协程池还未全部空闲, 说明仍有任务在执行. 等待
                sleep(0)

    def stop(self):
        self.exit_signal = True
        # 只让进队列, 不让出队列, 就是只把当前正在处理的页面中的链接入队列, 不再弹出任务
        ## 把协程池中的任务取出重新入队列并持久化到本地文件, 避免丢失.
        for item in self.pool:
            self.queue.push(item.args)
