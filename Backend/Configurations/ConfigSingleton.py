import json

################ THIS IS THE ONLY VAR IN PROJECT THAT MAY BE CHANGE ##########
PRJ_DIR_PATH = "C:\\TelegramBot\\Backend\\"
##############################################################################


PRJ_CONFIG_FILE_PATH = PRJ_DIR_PATH + "Configurations\PrjConfiguration.json"
PRJ_KEYS_FILE_PATH = PRJ_DIR_PATH + "Configurations\PrivateKeys.json"
SPORT_CONFIGURATION_FILE_PATH = PRJ_DIR_PATH + "Configurations\SportsConfiguration.json"


class ConfigSingleton:
    _instance = None

    def _init_config(self):
        file = open(PRJ_CONFIG_FILE_PATH, 'r')
        self._prjConfiguration = json.load(file)

        file = open(PRJ_KEYS_FILE_PATH, 'r')
        self._private_keys = json.load(file)

        file = open(SPORT_CONFIGURATION_FILE_PATH, 'r')
        self._sport_config = json.load(file)

        # Here you can open new configuration files

    @staticmethod
    def get_instance():
        if ConfigSingleton._instance is None:
            ConfigSingleton._instance = ConfigSingleton()
            ConfigSingleton._instance._init_config()
        return ConfigSingleton._instance

    def get_prjConfig(self):
        return self._prjConfiguration

    def get_private_keys(self):
        return self._private_keys

    def get_sport_config(self):
        return self._sport_config
