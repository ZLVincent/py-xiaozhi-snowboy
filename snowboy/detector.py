from common import constants, logging, utils, config
from . import snowboydecoder
import xiaozhi

logger = logging.getLogger(__name__)

detector = None

def initDetector(XiaoZhiAI):
    """
    初始化离线唤醒热词监听器，支持 snowboy 和 porcupine 两大引擎
    """
    global detector
    logger.info("使用 snowboy 进行离线唤醒")
    detector and detector.terminate()
    models = constants.getHotwordModel(config.get("hotword", "wukong.pmdl"))
    detector = snowboydecoder.HotwordDetector(
        models, sensitivity=config.get("sensitivity", 0.5)
    )
    # main loop
    try:
        detector.start(
            detected_callback=_detected_callback,
            audio_recorder_callback=_audio_recorder_callback,
            interrupt_check=XiaoZhiAI._interrupt_callback,
            silent_count_threshold=config.get("silent_threshold", 15),
            recording_timeout=config.get("recording_timeout", 5) * 4,
            sleep_time=0.03
        )
        detector.terminate()
    except Exception as e:
        logger.critical(f"离线唤醒机制初始化失败：{e}", stack_info=True)

def _detected_callback():
    if not utils.is_proper_time():
        logger.warning("勿扰模式开启中")
        return
    utils.setRecordable(False)
    xiaozhi.run()
    utils.setRecordable(True)

def _audio_recorder_callback(audio_stream=None):
    if len(audio_stream) < (960 * 2):
        return
    logger.info("结束录音")
    utils.setRecordable(False)
    xiaozhi.send_audio(audio_stream)