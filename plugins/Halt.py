# -*- coding: utf-8-*-
# 关闭系统插件
import time
import subprocess
from common import logging, utils, constants
from robot.AbstractPlugin import AbstractPlugin

logger = logging.getLogger(__name__)   

class Plugin(AbstractPlugin):

    SLUG = "halt"

    def handle(self, text):
        logger.info('将要关闭系统~')
        utils.play_audio_file(constants.DETECT_OFF)
        try:
            time.sleep(3)
            subprocess.Popen("sudo /sbin/shutdown -h now", shell=True)
        except Exception as e:
            logger.error(e)
            utils.play_audio_file(constants.DETECT_Ding)

    def isValid(self, text):
        return any(word in text for word in [u"关机", u"关闭系统"])
