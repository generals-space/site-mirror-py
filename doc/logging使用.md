# logging使用

参考文章

1. [python logging模块](http://www.cnblogs.com/dahu-daqing/p/7040764.html)

最初logging困扰我最大的问题是, 生成的logger对象是否为单例对象, 如何保证不同源文件中的logger的输出互不干扰.

实验后发现其实logging似乎并不在意是不是单例的问题, ta只是简单的print而已(按照指定的格式).

```
.
├── sublib
│   └── sub.py
└── main.py
```

`main.py`文件

```py
import logging

from sublib.sub import sub_show 
logging_config = {
    'level': logging.DEBUG,
    'format': '%(asctime)s %(levelname)-7s %(name)s - %(filename)s:%(lineno)d %(message)s',
}

logging.basicConfig(**logging_config)
logger = logging.getLogger(__name__)
## logger.setLevel(logging.DEBUG)

def show():
    logger.info("Start print log")
    logger.debug("Do something")
    logger.warning("Something maybe fail.")
    logger.error("Something error.")
    logger.info("Finish")

show()
sub_show()
```

`sublib/sub.py`文件

```py
import logging

logger = logging.getLogger(__name__)
## logger.setLevel(logging.DEBUG)

def sub_show():
    logger.info("Start print log")
    logger.debug("Do something")
    logger.warning("Something maybe fail.")
    logger.error("Something error.")
    logger.info("Finish")
```

------

输出

```
$ python .\main.py
2019-04-17 02:03:27,353 INFO    __main__ - main.py:14 Start print log
2019-04-17 02:03:27,353 DEBUG   __main__ - main.py:15 Do something
2019-04-17 02:03:27,354 WARNING __main__ - main.py:16 Something maybe fail.
2019-04-17 02:03:27,354 ERROR   __main__ - main.py:17 Something error.
2019-04-17 02:03:27,354 INFO    __main__ - main.py:18 Finish
2019-04-17 02:03:27,355 INFO    sublib.sub - sub.py:7 Start print log
2019-04-17 02:03:27,355 DEBUG   sublib.sub - sub.py:8 Do something
2019-04-17 02:03:27,355 WARNING sublib.sub - sub.py:9 Something maybe fail.
2019-04-17 02:03:27,356 ERROR   sublib.sub - sub.py:10 Something error.
2019-04-17 02:03:27,356 INFO    sublib.sub - sub.py:11 Finish
```
