# -*- coding: utf-8 -*-
# author:jeffrycheng
# project:network_build_automation
# date:2020-03-11

def _init():  # 初始化
    global _global_dict
    _global_dict = {}


def set_value(key, value):
    _global_dict[key] = value


def get_value(key, defValue=None):
    try:
        return _global_dict[key]
    except KeyError:
        return defValue