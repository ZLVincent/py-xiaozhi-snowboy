# -*- coding: utf-8-*-
# 重启系统插件
import time
import subprocess
from common import logging, utils, constants
from robot import AbstractPlugin

logger = logging.getLogger(__name__)

class Plugin(AbstractPlugin):

    SLUG = 'reboot'

    def handle(self, text):
        logger.info('将要重新启动系统~')
        utils.play_audio_file(constants.DETECT_OFF)
        try:
            time.sleep(3)
            subprocess.Popen("sudo /sbin/reboot -f", shell=True)
        except Exception as e:
            logger.error(e)
            utils.play_audio_file(constants.DETECT_Ding)

    def isValid(self, text):
        return any(word in text for word in [u"重启", u"重新启动"])
