#!/usr/bin/python
# -*- coding: UTF-8 -*-
from common import logging
from robot import detector, PluginEngine
import signal

logger = logging.getLogger(__name__)

class XiaoZhiAI(object):
    def __init__(self):
        self.detector = None
        self._interrupted = False

    def _signal_handler(self, signal, frame):
        self._interrupted = True

    def _interrupt_callback(self):
        return self._interrupted

    def run(self):
        pluginEngine = PluginEngine()
        # capture SIGINT signal, e.g., Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)
        try:
            # 初始化离线唤醒
            detector.initDetector(self, pluginEngine)
        except Exception as e:
            logger.error(f"初始化离线唤醒功能失败: {e}", stack_info=True)
            pass

if __name__ == "__main__":
    xiaozhiAI = XiaoZhiAI()
    xiaozhiAI.run()