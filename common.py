#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import PurePath

from happy_python import HappyLog

CONFIG_DIR = PurePath(__file__).parent / 'configs'
LOG_CONFIG_FILENAME = str(CONFIG_DIR / 'log.ini')

hlog = HappyLog.get_instance(LOG_CONFIG_FILENAME)
