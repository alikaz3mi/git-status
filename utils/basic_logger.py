import os
import sys
import logging


__all__ = ('simple_logger',)


def get_splitter_format():
    return '\n' + '-' * 100


class ColoredFormatter(logging.Formatter):
    green = '\u001b[32m'
    grey = '\u001b[36m'
    blue = '\x1b[38;5;39m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'
    splitter = get_splitter_format()

    def __init__(self, *args, **kwargs):
        super(ColoredFormatter, self).__init__(*args, **kwargs)
        self._level_color_format = {
            logging.NOTSET: self.reset + "{}" + self.reset,
            logging.DEBUG: self.grey + "{}" + self.reset,
            logging.INFO: self.blue + "{}" + self.reset,
            logging.WARNING: self.yellow + "{}" + self.reset,
            logging.ERROR: self.red + "{}" + self.reset,
            logging.CRITICAL: self.bold_red + "{}" + self.reset,
        }
        self._message_color_format = self.green + "{}" + self.reset

    def format(self, record: logging.LogRecord) -> str:
        # replace the level name with related level color
        record.levelname = self._level_color_format.get(record.levelno).format(record.levelname)
        record.msg = self._message_color_format.format(record.msg)
        return super(ColoredFormatter, self).format(record) + self.splitter


def simple_logger(name, stream_level=logging.DEBUG, file_level=logging.DEBUG, filename: str = None):
    if '--stream_level' in sys.argv:
        idx = sys.argv.index('--stream_level')
        try:
            stream_level = eval(sys.argv[idx+1])
        except Exception as e:
            print(e)
    if '--stream_level' in os.environ:
        idx = eval(os.environ['stream_level'])
    logger = logging.getLogger(name)
    file_format = '%(levelname)s-%(asctime)s-FILENAME:%(filename)s-MODULE:%(module)s-%(lineno)d-FUNC:%(funcName)s-THREAD:%(threadName)s :: %(message)s'
    console_format = '%(levelname)s-%(asctime)s-FILENAME:%(filename)s-MODULE:%(module)s-%(lineno)d-FUNC:%(funcName)s-THREAD:%(threadName)s :: %(message)s'
    file_formatter = logging.Formatter(
        file_format,
        datefmt='%Y-%m-%d %H:%M:%S')
    console_formatter = ColoredFormatter(
        console_format,
        datefmt='%Y-%m-%d %H:%M:%S')
    if filename is not None:
        file_handler = logging.FileHandler(filename=filename)
        file_handler.setLevel(file_level)
        file_handler.setFormatter(file_formatter)

        logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(stream_level)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG)

    logger.propagate = False
    return logger


if __name__ == '__main__':
    logger = simple_logger('test_logger')
    logger.debug('this is the test debug message to show you')
    logger.info('this is the test info message to show you')
    logger.warning('this is the test warning message to show you')
    logger.error('this is the test error message to show you')
    logger.critical('this is the test critical message to show you')
    print('')
