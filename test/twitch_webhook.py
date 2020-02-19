import json

from flask import Flask, request
import requests


app = Flask(__name__)

@app.route("/webhook", methods=["POST", "GET"])
def index():
    try:
        if request.method == "POST":
            print(request.json)
            return ""

        else:
            return request.args.get("hub.challenge")

    except Exception as ex:
        return str(ex)

def main():
    with open("../settings.json", "r", encoding="utf-8") as fp:
        setting = json.load(fp)

    headers = {
        "Content-Type": "application/json",
        "Client-ID": setting["twitch_client_id"]
    }

    resp = requests.get(
        "https://api.twitch.tv/helix/users?login=domahoki",
        headers=headers
    )
    print(resp.json())
    user_id = resp.json()["data"][0]["id"]

    sub_body = {
        "hub.callback": setting["webhook_host"],
        "hub.mode": "subscribe",
        "hub.topic": "https://api.twitch.tv/helix/users?id={}".format(user_id),
        "hub.lease_seconds": 60,
    }

    resp = requests.post(
        "https://api.twitch.tv/helix/webhooks/hub",
        json.dumps(sub_body),
        headers=headers
    )
    if resp.status_code == 202:
        print("Successfully Subscribed!")

    else:
        print("Error Response: {}".format(resp.status_code))

if __name__ == "__main__":
    main()

    app.run(debug=True, host="0.0.0.0", port=8080)
