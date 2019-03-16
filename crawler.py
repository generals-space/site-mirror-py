import os
import re
import requests
import time
import sqlite3
from urllib.parse import urlparse, urljoin
from queue import Queue

from pyquery import PyQuery

from settings import outsite_asset, doc_pool_max, res_pool_max, main_url, max_depth, max_retry_times, empty_link_pattern
from page_parser import get_page_charset, parse_linking_pages, parse_linking_assets, parse_css_file
from utils import request_get_async, save_file_async, trans_to_local_link
import settings
from worker_pool import WorkerPool
from db import init_db, query_url_record, add_url_record, query_page_tasks, query_asset_tasks, save_page_task, save_asset_task

class Crawler:
    def __init__(self):
        self.page_queue = Queue()
        self.asset_queue = Queue()
        ## 初始化数据文件, 创建表
        self.db_conn = init_db(settings.site_db)
        self.load_queue()
        self.enqueue_page(main_url, '', 1)

        self.page_worker = WorkerPool(self.page_queue, self.get_html_page, doc_pool_max)
        self.asset_worker = WorkerPool(self.asset_queue, self.get_static_asset, res_pool_max)

    def start(self):
        self.page_worker.start()

    def get_html_page(self, request_url, refer, depth, failed_times):
        '''
        抓取目标页面
        '''
        if 0 < max_depth and max_depth < depth: 
            print('目标url: %s 已超过最大深度' % request_url)
            return
        if failed_times > max_retry_times:
            print('目标url: %s 失败次数过多' % request_url)
            return
        code, resp = request_get_async(request_url, refer)
        if not code:
            print('请求页面失败, 重新入队列 %s' % request_url)
            self.page_queue.put((request_url, refer, depth, failed_times + 1))
            return
        charset = get_page_charset(resp.content)
        resp.encoding = charset
        pq_selector = PyQuery(resp.text)

        ## 超过最大深度的页面不再抓取, 在入队列前就先判断.
        ## 但超过静态文件无所谓深度, 所以还是要抓取的.
        if 0 < max_depth and max_depth < depth + 1:
            print('当前页面: %s 已达到最大深度, 不再抓取新页面')
        else:
            parse_linking_pages(pq_selector, request_url, depth+1, callback = self.enqueue_page)

        parse_linking_assets(pq_selector, request_url, depth+1, callback = self.enqueue_asset)

        ## 抓取此页面上的静态文件
        self.asset_worker.start()
        byte_content = pq_selector.outer_html().encode('utf-8')
        file_path, file_name, _ = trans_to_local_link(request_url)
        code, data = save_file_async(file_path, file_name, byte_content)

    def get_static_asset(self, request_url, refer, depth, failed_times):
        '''
        请求静态文件, css/js/img等并存储.
        '''
        ## 如果该链接已经超过了最大尝试次数, 则放弃
        if failed_times > max_retry_times: return

        code, resp = request_get_async(request_url, refer)
        if not code:
            ## print('请求静态资源失败, 重新入队列 %s' % request_url)
            ## 出现异常, 则失败次数加1
            self.asset_queue.put((request_url, refer, depth, failed_times + 1))
            return
        content = resp.content
        if 'content-type' in resp.headers and 'text/css' in resp.headers['content-type']:
            content = parse_css_file(resp.text, request_url, depth, callback = self.enqueue_asset)
        file_path, file_name, _ = trans_to_local_link(request_url)
        code, data = save_file_async(file_path, file_name, content)

    def enqueue_asset(self, url, refer, depth):
        '''
        如果该url已经添加入url_records记录, 就不再重新入队列.
        已进入队列的url, 必定已经存在记录, 但不一定能成功下载.
        '''
        if not query_url_record(self.db_conn, url):
            self.asset_queue.put((url, refer, depth, 0))
            add_url_record(self.db_conn, url, refer, depth)

    def enqueue_page(self, url, refer, depth):
        if not query_url_record(self.db_conn, url):
            self.page_queue.put((url, refer, depth, 0))
            add_url_record(self.db_conn, url, refer, depth)

    def load_queue(self):
        print('初始化任务队列')
        page_tasks = query_page_tasks(self.db_conn)
        for task in page_tasks:
            item = (task[0], task[1], int(task[2]), int(task[3]))
            self.page_queue.put(item)
        asset_tasks = query_asset_tasks(self.db_conn)
        for task in asset_tasks:
            item = (task[0], task[1], int(task[2]), int(task[3]))
            self.asset_queue.put(item)
        print('初始化任务队列完成')

    def save_queue(self):
        '''
        将队列中的任务元素存储到数据库中, 下次启动时加载, 继续执行.
        '''
        print('保存任务队列')
        page_tasks = []
        while True:
            if not self.page_queue.empty():
                item = self.page_queue.get()
                page_tasks.append(tuple(item))
            else:
                break
        if len(page_tasks) > 0:
            save_page_task(self.db_conn, page_tasks)

        asset_tasks = []
        while True:
            if not self.asset_queue.empty():
                item = self.asset_queue.get()
                asset_tasks.append(tuple(item))
            else:
                break
        if len(asset_tasks) > 0:
            save_asset_task(self.db_conn, asset_tasks)
        print('保存任务队列完成')

    def stop(self):
        '''
        任务停止前存储队列以便之后继续
        '''
        print('用户取消, 正在终止...')
        self.page_worker.stop()
        self.asset_worker.stop()
        self.save_queue()
        self.db_conn.close()
