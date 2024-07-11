# -*- coding: utf-8 -*-
import logging

class LoggerConfig:
    @staticmethod
    def get_logger(name):
        logger = logging.getLogger(name)
        if not logger.hasHandlers():
            logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]'))
            logger.addHandler(handler)
        return logger

# logger.debug('This is a debug message')
# logger.info('This is an info message')
# logger.warning('This is a warning message')
# logger.error('This is an error message')
# logger.critical('This is a critical message')
