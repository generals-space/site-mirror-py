import json

class CacheQueue(list):
    def __init__(self):
        super(CacheQueue, self).__init__()
        self.is_lock = False

    def empty(self):
        if self.is_lock or len(self) == 0:
            return True
        else:
            return False

    def lock(self):
        self.is_lock = True

    def unlock(self):
        self.is_lock = False

    def push(self, item):
        ## 新成员放在第一个位置
        self.insert(0, item)

    def pop(self):
        ## 取出列表中最后一个成员
        ## 注意: pop()前需要先调用empty()确认是否为空.
        return super(CacheQueue, self).pop()

    def __len__(self):
        if self.is_lock:
            return 0
        else:
            return super(CacheQueue, self).__len__()

    def size(self):
        return len(self)
