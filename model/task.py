
def query_tasks(db_conn, table_name):
    sql_str = 'select url, refer, depth, failed_times from {:s}'
    sql_str = sql_str.format(table_name)
    cursor = db_conn.cursor()
    cursor.execute(sql_str)
    rows = cursor.fetchall()
    cursor.close()
    return rows

def query_page_tasks(db_conn):
    return query_tasks(db_conn, 'page_tasks')

def query_asset_tasks(db_conn):
    return query_tasks(db_conn, 'asset_tasks')

def update_record_status(db_conn, url, status):
    '''
    @param: url 目标记录url
    @param: status 目标记录状态, 字符串. 可选值为: init, success, failed
    '''
    sql_str = 'update url_records set status = ? where url = ?'
    cursor = db_conn.cursor()
    ## 单个元素的写法, 注意如果是元组形式, 必须为逗号结尾.
    cursor.execute(sql_str, (status, url,))
    db_conn.commit()
    cursor.close()

def save_task(db_conn, table_name, value_list):
    sql_str = 'delete from {:s}'.format(table_name)
    cursor = db_conn.cursor()
    cursor.execute(sql_str)

    sql_str = 'insert into {:s} (url, refer, depth, failed_times) values(?, ?, ?, ?)'
    sql_str = sql_str.format(table_name)
    cursor.executemany(sql_str, value_list)
    
    db_conn.commit()
    cursor.close()

def save_page_task(db_conn, value_list):
    save_task(db_conn, 'page_tasks', value_list)

def save_asset_task(db_conn, value_list):
    save_task(db_conn, 'asset_tasks', value_list)
