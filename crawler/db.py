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
        url varchar(512) unique, -- 已抓取过的url(可以是页面, 可以是静态资源), 唯一, 作为索引键
        url_type varchar(50),        -- page, asset 2种类型
        refer varchar(512),
        depth int default 0, 
        failed_times int default 0, 
        status varchar(50) default 'init' -- init, pending, success, failed 4种类型
    )
    '''
    cursor.execute(sql_str)
    sql_str = '''
    create index if not exists url_records_index on url_records (url)
    '''
    cursor.execute(sql_str)
    cursor.close()
    return db_conn

def query_url_record(db_conn, url):
    sql_str = 'select id from url_records where url = ?'
    cursor = db_conn.cursor()
    cursor.execute(sql_str, (url, ))
    row = cursor.fetchone()
    cursor.close()
    return row

def add_or_update_url_record(db_conn, task):
    '''
    @return: 新插入行(或更新行)的id
    '''
    row_id = 0
    row = query_url_record(db_conn, task['url'])
    if row:
        sql_str = "update url_records set failed_times = ?, status = 'pending' where url = ?"
        cursor = db_conn.cursor()
        cursor.execute(sql_str, (task['failed_times'], task['url'], ))
        row_id = row[0]
    else:
        sql_str = 'insert into url_records(url, refer, depth, url_type) values(?, ?, ?, ?)'
        cursor = db_conn.cursor()
        cursor.execute(sql_str, (task['url'], task['refer'], task['depth'], task['url_type'], ))
        ## 获取新插入数据id的方法
        row_id = cursor.lastrowid
    ## 默认关闭自动提交
    db_conn.commit()
    cursor.close()
    return row_id

def update_record_status(db_conn, url, status):
    '''
    @param: url 目标记录url
    @param: status 目标记录状态, 字符串. 可选值为: init, pending, success, failed
    '''
    sql_str = 'update url_records set status = ? where url = ?'
    cursor = db_conn.cursor()
    ## 单个元素的写法, 注意如果是元组形式, 必须为逗号结尾.
    cursor.execute(sql_str, (status, url,))
    db_conn.commit()
    cursor.close()

def query_unfinished_tasks(db_conn, url_type):
    sql_str = "select url, url_type, refer, depth, failed_times from url_records where url_type = '{url_type:s}' and status in ('init', 'pending')"
    sql_str = sql_str.format(url_type = url_type)
    cursor = db_conn.cursor()
    cursor.execute(sql_str)
    rows = cursor.fetchall()
    cursor.close()
    tasks = []
    for row in rows:
        task = {
            'url': row[0],
            'url_type': row[1],
            'refer': row[2],
            ## 从数据库查出的数据都是字符串类型.
            'depth': int(row[3]), 
            'failed_times': int(row[4]),
        }
        tasks.append(task)
    return tasks

def query_unfinished_page_tasks(db_conn):
    return query_unfinished_tasks(db_conn, 'page')

def query_unfinished_asset_tasks(db_conn):
    return query_unfinished_tasks(db_conn, 'asset')
