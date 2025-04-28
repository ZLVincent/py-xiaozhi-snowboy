#!/usr/bin/python
# -*- coding: UTF-8 -*-
import yaml
import logging
import os
from common import constants

logger = logging.getLogger(__name__)

_config = {}
has_init = False

def reload():
    """
    重新加载配置
    """
    logger.info("配置文件发生变更，重新加载配置文件")
    init()

def init():
    global _config
    configFile = constants.getConfigPath()
    # Read config
    logger.debug("Trying to read config file: '%s'", configFile)
    try:
        with open(configFile, "r") as f:
            _config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"配置文件 {configFile} 读取失败: {e}", stack_info=True)
        raise

def get_path(items, default=None, warn=False):
    global _config
    curConfig = _config
    if isinstance(items, str) and items[0] == "/":
        items = items.split("/")[1:]
    for key in items:
        if key in curConfig:
            curConfig = curConfig[key]
        else:
            if warn:
                logger.warning(
                    "/%s not specified in profile, defaulting to " "'%s'",
                    "/".join(items),
                    default,
                )
            else:
                logger.debug(
                    "/%s not specified in profile, defaulting to " "'%s'",
                    "/".join(items),
                    default,
                )
            return default
    return curConfig

def has_path(items):
    global _config
    curConfig = _config
    if isinstance(items, str) and items[0] == "/":
        items = items.split("/")[1:]
    else:
        items = [items]
    for key in items:
        if key in curConfig:
            curConfig = curConfig[key]
        else:
            return False
    return True

def has(item):
    """
    判断配置里是否包含某个配置项

    :param item: 配置项名
    :returns: True: 包含; False: 不包含
    """
    return has_path(item)

def get(item="", default=None, warn=False):
    """
    获取某个配置的值

    :param item: 配置项名。如果是多级配置，则以 "/a/b" 的形式提供
    :param default: 默认值（可选）
    :param warn: 不存在该配置时，是否告警
    :returns: 这个配置的值。如果没有该配置，则提供一个默认值
    """
    global has_init
    if not has_init:
        init()
    if not item:
        return _config
    if item[0] == "/":
        return get_path(item, default, warn)
    try:
        return _config[item]
    except KeyError:
        if warn:
            logger.warning(
                "%s not specified in profile, defaulting to '%s'", item, default
            )
        else:
            logger.debug(
                "%s not specified in profile, defaulting to '%s'", item, default
            )
        return default

def getConfig():
    """
    返回全部配置数据

    :returns: 全部配置数据（字典类型）
    """
    return _config

def getText():
    if os.path.exists(constants.getConfigPath()):
        with open(constants.getConfigPath(), "r") as f:
            return f.read()
    return ""

def dump(configStr):
    with open(constants.getConfigPath(), "w") as f:
        f.write(configStr)
