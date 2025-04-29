from common import logging
from abc import ABCMeta, abstractmethod

logger = logging.getLogger(__name__)

class AbstractPlugin(metaclass=ABCMeta):
    """技能插件基类"""

    SLUG = "AbstractPlugin"

    def __init__(self):
        self.priority = 0

    @abstractmethod
    def isValid(self, text):
        """
        是否适合由该插件处理

        参数：
        text -- 用户的指令字符串

        返回：
        True: 适合由该插件处理
        False: 不适合由该插件处理
        """
        return False

    @abstractmethod
    def handle(self, text):
        """
        处理逻辑

        参数：
        text -- 用户的指令字符串
        """
        pass
