import logging
from typing import Dict, Optional

LOG_LEVELS = {
    'NOTSET': logging.NOTSET,
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARN': logging.WARN,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'FATAL': logging.FATAL,
    'CRITICAL': logging.CRITICAL,
}

def set_log_level(level: int = LOG_LEVELS['INFO'], specify: Optional[Dict[str, int]] = None):
    """ Задает уровень логирования для приложения и сторонних библиотек

    У всех сторонних библиотек по умолчанию стоит уровень логирования `WARNING`, но у некоторых
    библиотек он сбрасывается если мы устанавливаем свой уровень логирования у корневого логера.

    Это приводит к появлению мусорных логов от сторонних библиотек если мы хотим установить
    для нашего приложения уровень логирования `INFO` или `DEBUG`

    Для того чтобы задать уровень логирования нашего приложения, мы сначала принудительно устанавливаем
    уровень `WARNING` у сторонних логеров найденных библиотекой `logging`, а затем уже устанавливаем
    свой заданный уровень логирования.

    Дополнительно можно указать уровни логирования для конкретного логера в виде словаря:
    `{'logger_name': LOG_LEVELS['lvl'], ...}`
    """
    specify_default = {
        'multipart': LOG_LEVELS['WARNING'],
        'multipart.multipart': LOG_LEVELS['WARNING'],
        'uvicorn.error': LOG_LEVELS['INFO']
    }
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    for logger in loggers:
        logger.setLevel(logging.WARNING)

    specify = specify_default if specify is None else specify_default | specify

    for logger_name, logger_level in specify.items():
        logging.getLogger(logger_name).setLevel(logger_level)

    logging.getLogger().setLevel(level)
