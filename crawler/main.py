import os
import re
import requests
import time
import sqlite3
import copy
import logging
from queue import Queue
from urllib.parse import urlparse, urljoin

from pyquery import PyQuery

from crawler.page_parser import get_page_charset, parse_linking_pages, parse_linking_assets, parse_css_file
from crawler.utils import empty_link_pattern, request_get_async, save_file_async
from crawler.transform import trans_to_local_path
from crawler.worker_pool import WorkerPool
from crawler.db import init_db, query_unfinished_page_tasks, query_unfinished_asset_tasks, add_or_update_url_record, update_record_status

logger = logging.getLogger(__name__)

class Crawler:
    def __init__(self, config):
        ## 队列满时put会使整个进程阻塞无法继续执行, 之后要改成异步形式
        ## self.page_queue = Queue(maxsize = config['page_queue_size'])
        ## self.asset_queue = Queue(maxsize = config['asset_queue_size'])
        self.page_queue = Queue()
        self.asset_queue = Queue()

        self.config = config

        self.main_site = urlparse(self.config['main_url']).netloc

        ## 初始化数据文件, 创建表.
        self.db_conn = init_db(self.config['site_db'])
        self.load_queue()
        main_task = {
            'url': self.config['main_url'],
            'url_type': 'page',
            'refer': '',
            'depth': 1,
            'failed_times': 0,
        }
        self.enqueue_page(main_task)

        page_worker_pool_args = {
            'func': self.get_html_page, 
            'pool_size': self.config['page_pool_size'],
            'worker_type': 'page',
        }
        self.page_worker_pool = WorkerPool(self.page_queue, **page_worker_pool_args)
        asset_worker_pool_args = {
            'func': self.get_static_asset, 
            'pool_size': self.config['asset_pool_size'],
            'worker_type': 'asset',
        }
        self.asset_worker_pool = WorkerPool(self.asset_queue, **asset_worker_pool_args)

    def start(self):
        logger.info('页面工作池启动')
        self.page_worker_pool.start()

    def get_html_page(self, task):
        '''
        抓取目标页面
        '''
        msg = 'get_html_page(): task: {task:s}'
        logger.debug(msg.format(task = str(task)))
        ## 更新记录状态
        update_record_status(self.db_conn, task['url'], 'pending')

        if 0 < self.config['max_depth'] < task['depth']: 
            msg = '已超过最大深度: task: {task:s}'
            logger.warning(msg.format(task = str(task)))
            return
        if task['failed_times'] > self.config['max_retry_times']:
            msg = '失败次数过多, 不再重试: task: {task:s}'
            logger.warning(msg.format(task = str(task)))
            update_record_status(self.db_conn, task['url'], 'failed')
            return

        code, resp = request_get_async(task, self.config)
        if not code:
            msg = '请求页面失败, 重新入队列: task: {task:s}, err: {err:s}'
            logger.error(msg.format(task = str(task), err = resp))
            ## 出现异常, 则失败次数加1
            ## 不需要调用enqueue(), 直接入队列.
            task['failed_times'] += 1
            self.enqueue_page(task)
            return
        elif resp.status_code == 404:
            ## 抓取失败一般是5xx或403, 405等, 出现404基本上就没有重试的意义了, 可以直接放弃
            update_record_status(self.db_conn, task['url'], 'failed')
            return
        msg = '请求页面成功, 准备解析并保存: task: {task:s}'
        logger.debug(msg.format(task = str(task)))

        try:
            charset = get_page_charset(resp.content)
            resp.encoding = charset
            pq_selector = PyQuery(resp.text)
            ## 超过最大深度的页面不再抓取, 在入队列前就先判断.
            ## 但静态资源无所谓深度, 所以还是要抓取的.
            if 0 < self.config['max_depth'] < task['depth'] + 1:
                msg = '当前页面已达到最大深度, 不再抓取新页面: task {task:s}'
                logger.warning(msg.format(task = str(task)))
            else:
                parse_linking_pages(pq_selector, task, self.config, callback = self.enqueue_page)
            parse_linking_assets(pq_selector, task, self.config, callback = self.enqueue_asset)
            logger.debug('修改页面元素链接完成')
            ## 抓取此页面上的静态资源
            self.asset_worker_pool.start(task)
            byte_content = pq_selector.outer_html().encode('utf-8')
            file_path, file_name = trans_to_local_path(task['url'], 'page', self.main_site)
            code, data = save_file_async(self.config['site_path'], file_path, file_name, byte_content)
            if code: update_record_status(self.db_conn, task['url'], 'success')
        except Exception as err:
            msg = '保存页面文件失败: task: {task:s}, err: {err:s}'
            logger.error(msg.format(task = str(task), err = err))

    def get_static_asset(self, task):
        '''
        请求静态资源, css/js/img等并存储.
        '''
        msg = 'get_static_asset(): task: {task:s}'
        logger.debug(msg.format(task = str(task)))
        ## 更新记录状态
        update_record_status(self.db_conn, task['url'], 'pending')
        ## 如果该链接已经超过了最大尝试次数, 则放弃
        if task['failed_times'] > self.config['max_retry_times']: 
            msg = '失败次数过多, 不再重试: task: {task:s}'
            logger.warning(msg.format(task = str(task)))
            update_record_status(self.db_conn, task['url'], 'failed')
            return

        code, resp = request_get_async(task, self.config)
        if not code:
            msg = '请求静态资源失败, 重新入队列: task: {task:s}, err: {err:s}'
            logger.error(msg.format(task = str(task), err = resp))
            ## 出现异常, 则失败次数加1
            task['failed_times'] += 1
            self.enqueue_asset(task)
            return
        elif resp.status_code == 404:
            ## 抓取失败一般是5xx或403, 405等, 出现404基本上就没有重试的意义了, 可以直接放弃
            update_record_status(self.db_conn, task['url'], 'failed')
            return

        try:
            content = resp.content
            if 'content-type' in resp.headers and 'text/css' in resp.headers['content-type']:
                content = parse_css_file(resp.text, task, self.config, callback = self.enqueue_asset)
            file_path, file_name = trans_to_local_path(task['url'], 'asset', self.main_site)
            code, data = save_file_async(self.config['site_path'], file_path, file_name, content)
            if code: update_record_status(self.db_conn, task['url'], 'success')
        except Exception as err:
            msg = '保存静态资源失败: task: {task:s}, err: {err:s}'
            logger.error(msg.format(task = str(task), err = err))

    def enqueue_asset(self, task):
        '''
        如果该url已经添加入url_records记录, 就不再重新入队列.
        已进入队列的url, 必定已经存在记录, 但不一定能成功下载.
        每50个url入队列都将队列内容备份到数据库, 以免丢失.
        '''
        self.asset_queue.put(task)
        add_or_update_url_record(self.db_conn, task)

    def enqueue_page(self, task):
        self.page_queue.put(task)
        add_or_update_url_record(self.db_conn, task)

    def load_queue(self):
        logger.debug('初始化任务队列')
        page_tasks = query_unfinished_page_tasks(self.db_conn)
        for task in page_tasks:
            self.page_queue.put(task)
        asset_tasks = query_unfinished_asset_tasks(self.db_conn)
        for task in asset_tasks:
            self.asset_queue.put(task)
        logger.debug('初始化任务队列完成')

    def stop(self):
        '''
        任务停止前存储队列以便之后继续
        '''
        logger.info('用户取消, 正在终止...')
        self.page_worker_pool.stop()
        self.asset_worker_pool.stop()
        self.db_conn.close()
