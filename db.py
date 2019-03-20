import sqlite3

def init_db(db_file):
    '''
    初始化数据库.
    '''
    db_conn = sqlite3.connect(db_file)
    cursor = db_conn.cursor()
    ####################################################################################
    ## url_records: 已抓取页面记录
    sql_str = '''
    create table if not exists url_records(
        id integer primary key autoincrement, 
        url varchar(512) unique, -- '已抓取过的url(可以是页面, 可以是静态资源), 唯一, 作为索引键'
        refer varchar(512),
        depth int, 
        success int default 0
    )
    '''
    cursor.execute(sql_str)
    sql_str = '''
    create index if not exists url_records_index on url_records (url)
    '''
    cursor.execute(sql_str)
    ####################################################################################
    ## url_records: 页面抓取任务队列备份
    sql_str = '''
    create table if not exists page_tasks(
        id integer primary key autoincrement, 
        url varchar(512) unique, -- '已抓取过的url(可以是页面, 可以是静态资源), 唯一, 作为索引键'
        refer varchar(512), 
        depth int, 
        failed_times int
    )
    '''
    cursor.execute(sql_str)

    ####################################################################################
    ## url_records: 静态资源抓取任务队列备份
    sql_str = '''
    create table if not exists asset_tasks(
        id integer primary key autoincrement, 
        url varchar(512) unique, -- '已抓取过的url(可以是页面, 可以是静态资源), 唯一, 作为索引键'
        refer varchar(512), 
        depth int,
        failed_times int
    )
    '''
    cursor.execute(sql_str)
    ####################################################################################
    cursor.close()

    return db_conn

def query_url_record(db_conn, url):
    sql_str = 'select id from url_records where url = ?'
    cursor = db_conn.cursor()
    cursor.execute(sql_str, (url, ))
    row = cursor.fetchone()
    cursor.close()
    return row

def add_url_record(db_conn, url, refer, depth):
    '''
    return: 返回新插入行的id
    '''
    sql_str = 'insert into url_records(url, refer, depth) values(?, ?, ?)'
    cursor = db_conn.cursor()
    cursor.execute(sql_str, (url, refer, depth, ))
    ## 获取新插入数据id的方法
    last_id = cursor.lastrowid
    ## 默认关闭自动提交
    db_conn.commit()
    cursor.close()
    return last_id

def query_tasks(db_conn, table_name):
    sql_str = 'select url, refer, depth, failed_times from %s' % table_name
    cursor = db_conn.cursor()
    cursor.execute(sql_str)
    rows = cursor.fetchall()
    cursor.close()
    return rows

def query_page_tasks(db_conn):
    return query_tasks(db_conn, 'page_tasks')

def query_asset_tasks(db_conn):
    return query_tasks(db_conn, 'asset_tasks')

def update_record_to_success(db_conn, url):
    sql_str = 'update url_records set success = 1 where url = ?'
    cursor = db_conn.cursor()
    ## 单个元素的写法, 注意如果是元组形式, 必须为逗号结尾.
    cursor.execute(sql_str, (url,))
    db_conn.commit()
    cursor.close()

def save_task(db_conn, table_name, value_list):
    sql_str = 'delete from %s' % table_name
    cursor = db_conn.cursor()
    cursor.execute(sql_str)
    sql_str = 'insert into %s(url, refer, depth, failed_times) values(?, ?, ?, ?)' % table_name
    cursor.executemany(sql_str, value_list)
    db_conn.commit()
    cursor.close()

def save_page_task(db_conn, value_list):
    save_task(db_conn, 'page_tasks', value_list)

def save_asset_task(db_conn, value_list):
    save_task(db_conn, 'asset_tasks', value_list)
