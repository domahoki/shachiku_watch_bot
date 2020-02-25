import json

class Setting(object):
    setting = None

    @staticmethod
    def load_setting(path):
        with open(path, "r", encoding="utf-8") as fp:
            Setting.setting = json.load(fp)

    @staticmethod
    def get_headers():
        return {
            "Content-Type": "application/json",
            "Client-ID": Setting.setting["twitch_client_id"]
        }
