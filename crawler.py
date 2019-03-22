import os
import re
import requests
import time
import sqlite3
import copy
from urllib.parse import urlparse, urljoin

from pyquery import PyQuery

from settings import outsite_asset, doc_pool_max, res_pool_max, main_url, max_depth, max_retry_times, empty_link_pattern, site_db
from page_parser import get_page_charset, parse_linking_pages, parse_linking_assets, parse_css_file
from utils import logger, request_get_async, save_file_async, trans_to_local_link, trans_to_local_path
from worker_pool import WorkerPool
from db import init_db, query_url_record, add_url_record, query_page_tasks, query_asset_tasks, save_page_task, save_asset_task, update_record_to_success
from cache_queue import CacheQueue

class Crawler:
    def __init__(self):
        self.page_queue = CacheQueue()
        self.asset_queue = CacheQueue()
        self.page_counter = 0
        self.asset_counter = 0

        ## 初始化数据文件, 创建表
        self.db_conn = init_db(site_db)
        self.load_queue()
        self.enqueue_page(main_url, '', 1)

        self.page_worker_pool = WorkerPool(self.page_queue, self.get_html_page, doc_pool_max, worker_type = 'page')
        self.asset_worker_pool = WorkerPool(self.asset_queue, self.get_static_asset, res_pool_max, worker_type = 'asset')

    def start(self):
        self.page_worker_pool.start()
        logger.info('page worker pool complete')

    def get_html_page(self, request_url, refer, depth, failed_times):
        '''
        抓取目标页面
        '''
        msg = 'get_static_asset: request_url %s, refer %s, depth %d, failed_times %d' % (request_url, refer, depth, failed_times)
        logger.debug(msg)
        if 0 < max_depth and max_depth < depth: 
            logger.warning('目标url: %s 已超过最大深度' % request_url)
            return
        if failed_times > max_retry_times:
            logger.warning('目标url: %s 失败次数过多, 不再重试' % request_url)
            return
        code, resp = request_get_async(request_url, refer)
        if not code:
            logger.error('请求页面失败 %s, referer %s, 重新入队列 %s' % (request_url, refer, resp))
            ## 出现异常, 则失败次数加1
            ## 不需要调用enqueue(), 直接入队列.
            self.page_queue.push((request_url, refer, depth, failed_times + 1))
            return

        try:
            charset = get_page_charset(resp.content)
            resp.encoding = charset
            pq_selector = PyQuery(resp.text)

            ## 超过最大深度的页面不再抓取, 在入队列前就先判断.
            ## 但超过静态文件无所谓深度, 所以还是要抓取的.
            if 0 < max_depth and max_depth < depth + 1:
                logger.warning('当前页面: %s 已达到最大深度, 不再抓取新页面' % (request_url, ))
            else:
                parse_linking_pages(pq_selector, request_url, depth+1, callback = self.enqueue_page)

            parse_linking_assets(pq_selector, request_url, depth+1, callback = self.enqueue_asset)

            ## 抓取此页面上的静态文件
            self.asset_worker_pool.start(page_url=request_url)
            byte_content = pq_selector.outer_html().encode('utf-8')
            file_path, file_name = trans_to_local_path(request_url, True)
            code, data = save_file_async(file_path, file_name, byte_content)
            if code: self.set_record_to_success(request_url)
        except Exception as err:
            logger.error('parse page failed for %s refer %s: %s' % (request_url, refer, err))

    def get_static_asset(self, request_url, refer, depth, failed_times):
        '''
        请求静态文件, css/js/img等并存储.
        '''
        msg = 'get_static_asset: request_url %s, refer %s, depth %d, failed_times %d' % (request_url, refer, depth, failed_times)
        logger.debug(msg)
        ## 如果该链接已经超过了最大尝试次数, 则放弃
        if failed_times > max_retry_times: return

        code, resp = request_get_async(request_url, refer)
        if not code:
            logger.error('请求静态资源失败 %s, 重新入队列' % (request_url,))
            ## 出现异常, 则失败次数加1
            self.asset_queue.push((request_url, refer, depth, failed_times + 1))
            return
    
        try:
            content = resp.content
            if 'content-type' in resp.headers and 'text/css' in resp.headers['content-type']:
                content = parse_css_file(resp.text, request_url, depth, callback = self.enqueue_asset)
            file_path, file_name = trans_to_local_path(request_url, False)
            code, data = save_file_async(file_path, file_name, content)
            if code: self.set_record_to_success(request_url)
        except Exception as err:
            logger.error('parse static asset failed for %s in page %s: %s' % (request_url, refer, err))

    def enqueue_asset(self, url, refer, depth):
        '''
        如果该url已经添加入url_records记录, 就不再重新入队列.
        已进入队列的url, 必定已经存在记录, 但不一定能成功下载.
        每50个url入队列都将队列内容备份到数据库, 以免丢失.
        '''
        if query_url_record(self.db_conn, url): return

        self.asset_queue.push((url, refer, depth, 0))
        add_url_record(self.db_conn, url, refer, depth, 'asset')
        self.asset_counter += 1
        if self.asset_counter >= 50: 
            self.asset_counter = 0
            self.save_queue()

    def enqueue_page(self, url, refer, depth):
        if query_url_record(self.db_conn, url): return
        self.page_queue.push((url, refer, depth, 0))
        add_url_record(self.db_conn, url, refer, depth, 'page')
        self.page_counter += 1
        if self.page_counter >= 50: 
            self.page_counter = 0
            self.save_queue()

    def load_queue(self):
        logger.debug('初始化任务队列')
        page_tasks = query_page_tasks(self.db_conn)
        for task in page_tasks:
            item = (task[0], task[1], int(task[2]), int(task[3]))
            self.page_queue.push(item)
        asset_tasks = query_asset_tasks(self.db_conn)
        for task in asset_tasks:
            item = (task[0], task[1], int(task[2]), int(task[3]))
            self.asset_queue.push(item)
        logger.debug('初始化任务队列完成')

    def save_queue(self):
        '''
        将队列中的任务元素存储到数据库中, 下次启动时加载, 继续执行.
        '''
        logger.debug('保存任务队列')
        page_tasks = []
        asset_tasks = []
        _tmp_page_queue = copy.copy(self.page_queue)
        _tmp_asset_queue = copy.copy(self.asset_queue)

        ## 将队列中的成员写入数据库作为备份
        while True:
            if _tmp_page_queue.empty(): break
            item = _tmp_page_queue.pop()
            page_tasks.append(tuple(item))

        while True:
            if _tmp_asset_queue.empty(): break
            item = _tmp_asset_queue.pop()
            asset_tasks.append(tuple(item))

        if len(page_tasks) > 0:
            save_page_task(self.db_conn, page_tasks)
        if len(asset_tasks) > 0:
            save_asset_task(self.db_conn, asset_tasks)
        logger.debug('保存任务队列完成')

    def set_record_to_success(self, url):
        update_record_to_success(self.db_conn, url)

    def stop(self):
        '''
        任务停止前存储队列以便之后继续
        '''
        logger.info('用户取消, 正在终止...')
        self.page_worker_pool.stop()
        self.asset_worker_pool.stop()
        self.save_queue()
        self.db_conn.close()
