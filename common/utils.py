#!/usr/bin/python
# -*- coding: UTF-8 -*-
import time
import wave
import pyaudio
from common import config

do_not_bother = False
is_recordable = True
in_conversation = False

def setInConversation(value):
    global in_conversation
    in_conversation = value

def isInConversation():
    global in_conversation
    return in_conversation

def setRecordable(value):
    """设置是否可以开始录制语音"""
    global is_recordable
    is_recordable = value

def isRecordable():
    """是否可以开始录制语音"""
    global is_recordable
    return is_recordable

def is_proper_time():
    """是否合适时间"""
    global do_not_bother
    if do_not_bother == True:
        return False
    if not config.has("do_not_bother"):
        return True
    bother_profile = config.get("do_not_bother")
    if not bother_profile["enable"]:
        return True
    if "since" not in bother_profile or "till" not in bother_profile:
        return True
    since = bother_profile["since"]
    till = bother_profile["till"]
    current = time.localtime(time.time()).tm_hour
    if till > since:
        return current not in range(since, till)
    else:
        return not (current in range(since, 25) or current in range(-1, till))
    
def play_audio_file(fname):
    """play a wave file
    :param str fname: wave file name
    :return: None
    """
    ding_wav = wave.open(fname, "rb")
    ding_data = ding_wav.readframes(ding_wav.getnframes())
    audio = pyaudio.PyAudio()
    stream_out = audio.open(
        format=audio.get_format_from_width(ding_wav.getsampwidth()),
        channels=ding_wav.getnchannels(),
        rate=ding_wav.getframerate(),
        input=False,
        output=True,
    )
    stream_out.start_stream()
    stream_out.write(ding_data)
    time.sleep(0.2)
    stream_out.stop_stream()
    stream_out.close()
    audio.terminate()