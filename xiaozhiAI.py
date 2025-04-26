#!/usr/bin/python
# -*- coding: UTF-8 -*-
from common import logging
from snowboy import detector
import signal

import xiaozhi
import time
import pyaudio

logger = logging.getLogger(__name__)

class XiaoZhiAI(object):
    def init(self):
        self.detector = None
        self._interrupted = False

    def startL(self):
        audio = pyaudio.PyAudio()
        try:
             print('开始录音')
		     # 打开麦克风流, 帧大小，应该与Opus帧大小匹配
             mic = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=960)
             time.sleep(3)
             data = mic.read(960)
             print(len(data))
             xiaozhi.send_audio(data)
        except Exception as e:
            print(f"send audio err: {e}")
        finally:
            print("send audio exit()")
			# 关闭流和PyAudio
            mic.stop_stream()
            mic.close()

    def _signal_handler(self, signal, frame):
        self._interrupted = True

    def _interrupt_callback(self):
        return self._interrupted

    def run(self):
        # capture SIGINT signal, e.g., Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)
        try:
            # 初始化离线唤醒
            detector.initDetector(self)

            # xiaozhi.run()
            # print("222")
            # time.sleep(2)
            # xiaozhi.StartListen()
            # self.startL()
        except Exception as e:
            logger.error(f"初始化离线唤醒功能失败: {e}", stack_info=True)
            pass

if __name__ == "__main__":
    xiaozhiAI = XiaoZhiAI()
    xiaozhiAI.run()