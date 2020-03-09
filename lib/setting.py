import os
import json
from threading import Lock

class Setting(object):
    _unique_instance = None
    _lock = Lock()
    __setting = {}

    def __new__(cls):
        raise NotImplementedError('Cannot initialize via Constructor')

    def __getitem__(self, key):
        return self.__setting.get(key, None)

    @classmethod
    def __internal_new__(cls):
        return super().__new__(cls)

    @classmethod
    def get_instance(cls):
        if not cls._unique_instance:
            with cls._lock:
                if not cls._unique_instance:
                    cls._unique_instance = cls.__internal_new__()
        return cls._unique_instance

    def load_setting(self, path) -> None:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as fp:
                self.__setting = json.load(fp)

        else:
            self.__setting["webhook_host"] = os.environ["WEBHOOK_HOST"]
            self.__setting["discord_token"] = os.environ["DISCORD_TOKEN"]
            self.__setting["twitch_client_id"] = os.environ["TWITCH_CLIENT_ID"]

    def get_headers(self) -> None:
        return {
            "Content-Type": "application/json",
            "Client-ID": self.__setting["twitch_client_id"]
        }
