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
        refer varchar(512),
        depth int, 
        url_type varchar(50),        -- page, asset 2种类型
        status varchar(50) default 'init' -- init, success, failed 3种类型
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
        url varchar(512) unique, -- 已抓取过的url(可以是页面, 可以是静态资源), 唯一, 作为索引键
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
        url varchar(512) unique, -- 已抓取过的url(可以是页面, 可以是静态资源), 唯一, 作为索引键
        refer varchar(512), 
        depth int,
        failed_times int
    )
    '''
    cursor.execute(sql_str)
    ####################################################################################
    cursor.close()

    return db_conn
