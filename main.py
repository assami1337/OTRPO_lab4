import json
import requests
import os

TOKEN = os.getenv("TOKEN")
USER_ID = "404727166"

def get_followers():
    response = requests.get("https://api.vk.com/method/users.getFollowers",
                            {"access_token": TOKEN,
                                     "v": "5.199",
                                     "user_id": USER_ID,
                                     "fields": "123"})

    data = response.json()
    for i in data["response"]["items"]:
        keys_to_delete = [key for key in i if key not in ["id","first_name","last_name"]]
        for key in keys_to_delete:
            del i[key]

    del data["response"]["friends_count"]

    return data


def get_subscriptions(only_pages=False):
    response = requests.get("https://api.vk.com/method/users.getSubscriptions",
                            {"access_token": TOKEN,
                                    "v": "5.199",
                                    "user_id": USER_ID,
                                    "extended": 1,
                                    "count": 200})

    data = response.json()

    items = data.get("response", {}).get("items", [])

    if only_pages:
        items[:] = [item for item in items if item.get("type") == "page"]

    for item in items:
        if item.get("type") == "page":
            keys_to_keep = {"id", "name"}
        elif item.get("type") == "profile":
            keys_to_keep = {"id", "last_name", "first_name"}
        else:
            keys_to_keep = set()

        for key in list(item.keys()):
            if key not in keys_to_keep:
                del item[key]

    data["response"]["count"] = len(items)

    data["response"]["items"] = items

    return data


if __name__ == "__main__":
    followers_data = get_followers()
    subscriptions_data = get_subscriptions()
    subscriptions_pages_data = get_subscriptions(only_pages=True)

    result = {
        "followers": followers_data,
        "subscriptions": subscriptions_data,
        "subscriptions_pages": subscriptions_pages_data
    }

    with open(f"user_id{USER_ID}.json", "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

    print(f"Данные сохранены в user_id{USER_ID}.json")