# requests问题处理-latin-1 codec xxx

参考文章

1. [UnicodeEncodeError: 'latin-1' codec can't encode characters](https://github.com/kennethreitz/requests/issues/1822)

```
请求失败 https://pic.haku77.com/upload/vod/2018-10-26/154054919811.jpg, referer http://97daimeng.com/index.php?m=vod-list-id-3-area-台湾
```

这个错误是在发送http请求时携带了中文, 一般是请求体, 但是在我们的情况中是因为referer字符串中携带的中文, 所以在发送请求前要先`.encode('utf-8')`