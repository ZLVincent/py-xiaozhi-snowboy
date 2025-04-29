from common import logging
from abc import ABCMeta, abstractmethod

logger = logging.getLogger(__name__)

class AbstractPlugin(metaclass=ABCMeta):
    """技能插件基类"""

    SLUG = "AbstractPlugin"

    def __init__(self, con):
        self.priority = 0
        self.con = con
        self.nlu = self.con.nlu

    def play(self, src, delete=False, onCompleted=None, volume=1):
        """
        播放音频

        :param play: 要播放的音频地址
        :param delete: 播放完成是否要删除，默认不删除
        :param onCompleted: 播放完后的回调
        :param volume: 音量
        """
        self.con.play(src, delete, onCompleted, volume)

    def say(self, text, cache=False, onCompleted=None, wait=False):
        """
        使用TTS说一句话

        :param text: 要说话的内容
        :param cache: 是否要缓存该音频，默认不缓存
        :param onCompleted: 播放完后的回调
        :param wait: 已废弃
        """
        self.con.say(text, cache=cache, plugin=self.SLUG, onCompleted=onCompleted)

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
