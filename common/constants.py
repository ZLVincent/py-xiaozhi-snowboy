#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os

# main directory
APP_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
)

TEMP_PATH = os.path.join(APP_PATH, "temp")
CONFIG_PATH = APP_PATH
CUSTOM_CONFIG_NAME = "config.yml"
DATA_PATH = os.path.join(APP_PATH, "static")
DETECT_HI = os.path.join(APP_PATH, "static/beep_hi.wav")
DETECT_LO = os.path.join(APP_PATH, "static/beep_lo.wav")
DETECT_Ding = os.path.join(APP_PATH, "static/ding.wav")
DETECT_Dong = os.path.join(APP_PATH, "static/dong.wav")
DETECT_OFF = os.path.join(APP_PATH, "static/off.wav")
DETECT_ON = os.path.join(APP_PATH, "static/on.wav")

PLUGIN_PATH = os.path.join(APP_PATH, "plugins")

def getConfigPath():
    """
    获取配置文件的路径

    returns: 配置文件的存储路径
    """
    return os.path.join(CONFIG_PATH, CUSTOM_CONFIG_NAME)

def getData(*fname):
    """
    获取资源目录下指定文件的路径

    :param *fname: 指定文件名。如果传多个，则自动拼接
    :returns: 配置文件的存储路径
    """
    return os.path.join(DATA_PATH, *fname)

def getConfigData(*fname):
    """
    获取配置目录下的指定文件的路径

    :param *fname: 指定文件名。如果传多个，则自动拼接
    :returns: 配置目录下的某个文件的存储路径
    """
    return os.path.join(CONFIG_PATH, *fname)

def getHotwordModel(fname):
    if os.path.exists(getData(fname)):
        return getData(fname)
    else:
        return getConfigData(fname)