```py
def save_task(db_conn, table_name, value_list):
    sql_str = 'delete from {:s}'.format(table_name)
    cursor = db_conn.cursor()
    cursor.execute(sql_str)

    sql_str = 'insert into {:s} (url, refer, depth, failed_times) values(?, ?, ?, ?)'
    sql_str = sql_str.format(table_name)
    cursor.executemany(sql_str, value_list)
    
    db_conn.commit()
    cursor.close()
```