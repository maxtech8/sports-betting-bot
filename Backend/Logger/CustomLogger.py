import logging
from datetime import datetime
from Configurations import ConfigSingleton


class CustomLogger:
    _logger = None
    _instance = None

    @staticmethod
    def _init_logger():
        prj_config = ConfigSingleton.ConfigSingleton.get_instance().get_prjConfig()
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        current_date = datetime.now().strftime("%d-%m-%Y")
        current_time = datetime.now().strftime("%H-%M-%S")
        log_filename = f"Champions_{current_date}_-_{current_time}.log"
        file_handler = logging.FileHandler(f'{ConfigSingleton.PRJ_DIR_PATH + prj_config["Logger"]["Logs_Folder_Path"]}{log_filename}')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s, %(name)s, %(levelname)s] - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    @staticmethod
    def get_instance():
        if CustomLogger._instance is None:
            CustomLogger._instance = CustomLogger()
            CustomLogger._logger = CustomLogger._init_logger()
        return CustomLogger._instance

    def debug(self, msg):
        self._logger.debug(msg)

    def info(self, msg):
        self._logger.info(msg)

    def warning(self, msg):
        self._logger.warning(msg)

    def error(self, msg):
        self._logger.error(msg)

    def critical(self, msg):
        self._logger.critical(msg)


# Usage
if __name__ == "__main__":
    myLogger = CustomLogger.get_instance()
    myLogger.info("Yuval Gever")
    myLogger.critical("dodo")
