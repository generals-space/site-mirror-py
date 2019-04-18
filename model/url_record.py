
def query_url_record(db_conn, url):
    sql_str = 'select id from url_records where url = ?'
    cursor = db_conn.cursor()
    cursor.execute(sql_str, (url, ))
    row = cursor.fetchone()
    cursor.close()
    return row

def add_url_record(db_conn, task):
    '''
    return: 返回新插入行的id
    '''
    sql_str = 'insert into url_records(url, refer, depth, url_type) values(?, ?, ?, ?)'
    cursor = db_conn.cursor()
    cursor.execute(sql_str, (task['url'], task['refer'], task['depth'], task['url_type'], ))
    ## 获取新插入数据id的方法
    last_id = cursor.lastrowid
    ## 默认关闭自动提交
    db_conn.commit()
    cursor.close()
    return last_id
