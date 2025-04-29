#!/usr/bin/python
# -*- coding: UTF-8 -*-
import importlib
import pkgutil
from common import logging, config, constants
from . import AbstractPlugin

logger = logging.getLogger(__name__)

class PluginEngine(object):
    def __init__(self):
        """
        负责处理技能的匹配和响应

        参数：
        conversation -- 管理对话
        """
        self._plugins_query = []
        self.init_plugins()

    def init_plugins(self):
        """
        动态加载技能插件
        """
        locations = [constants.PLUGIN_PATH]
        logger.info(f"检查插件目录：{locations}")
        
        nameSet = set()
        
        for finder, name, ispkg in pkgutil.iter_modules(locations):
            try:
                # 构造模块的完整路径
                # 假设 plugins 是个包，比如 plugins.xxx
                full_name = f"plugins.{name}"
        
                # 关键：使用 importlib 代替旧的 finder.load_module
                mod = importlib.import_module(full_name)
            except Exception:
                logger.warning(f"插件 {name} 加载出错，跳过", exc_info=True)
                continue
        
            if not hasattr(mod, "Plugin"):
                logger.debug(f"模块 {name} 非插件，跳过")
                continue
        
            plugin = mod.Plugin()
        
            if plugin.SLUG == "AbstractPlugin":
                plugin.SLUG = name
        
            if plugin.SLUG in nameSet:
                logger.warning(f"插件 {name} SLUG({plugin.SLUG}) 重复，跳过")
                continue
            nameSet.add(plugin.SLUG)
        
            if config.has(plugin.SLUG) and "enable" in config.get(plugin.SLUG):
                if not config.get(plugin.SLUG)["enable"]:
                    logger.info(f"插件 {name} 已被禁用")
                    continue
        
            if issubclass(mod.Plugin, AbstractPlugin):
                logger.info(f"插件 {name} 加载成功 ")
                self._plugins_query.append(plugin)
        
        def sort_priority(m):
            return getattr(m, "PRIORITY", 0)
        
        self._plugins_query.sort(key=sort_priority, reverse=True)

    def isValid(self, plugin, text):
        return plugin.isValid(text)

    def query(self, text):
        """
        query 模块

        Arguments:
        text -- 原文本
        """

        for plugin in self._plugins_query:
            if not plugin.isValid(text):
                continue

            logger.info(f"'{text}' 命中技能 {plugin.SLUG}")

            continueHandle = False
            try:
                continueHandle = plugin.handle(text)
            except Exception as e:
                logger.critical(f"Failed to execute plugin: {e}", stack_info=True)
            else:
                logger.debug(
                    "Handling of phrase '%s' by " + "plugin '%s' completed",
                    text,
                    plugin.SLUG,
                )
            finally:
                if not continueHandle:
                    return True

        logger.debug(f"No plugin was able to handle phrase {text} ")
        return False