import threading

class GlobalContext:
    """
    全局内存数据管理器，替代 extract.yaml 以支持高并发安全读写
    在协程或线程模式下，内存操作是极快且安全的
    """
    _vars = {}
    _lock = threading.Lock()  # 加入线程锁，为未来可能的多线程做防御性编程

    @classmethod
    def set_vars(cls, data: dict):
        """批量写入变量"""
        if isinstance(data, dict):
            with cls._lock:
                cls._vars.update(data)

    @classmethod
    def get_var(cls, key, second_key=None):
        """获取变量"""
        with cls._lock:
            val = cls._vars.get(key)
            if val and second_key:
                return val.get(second_key)
            return val

    @classmethod
    def clear(cls):
        """清空上下文"""
        with cls._lock:
            cls._vars.clear()