# sqlite3-获取新插入行的id

参考文章

1. [How to retrieve inserted id after inserting row in SQLite using Python?](https://stackoverflow.com/questions/6242756/how-to-retrieve-inserted-id-after-inserting-row-in-sqlite-using-python)

标准sql语句支持`insert into xxx() values() returning 某一列`在插入新数据后返回其中的某一列, 在使用`psycopg2`时可以在`execute`后(commit之前)再使用`fetchone`得到这个值.

不过`returning`子句在sqlite里貌似是不合法的, 所以获取新插入数据的id值需要通过`cursor.lastrowid`值, 见参考文章1.
