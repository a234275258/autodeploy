#!/bin/usr/env python
#coding: utf-8
import logging
import logging.config
logging.config.fileConfig("e:/python/git-autodeploy/logger.conf")
logger = logging.getLogger("prodution")

logger.debug('This is debug message')
logger.info('This is info message')
logger.warning('This is warning message')