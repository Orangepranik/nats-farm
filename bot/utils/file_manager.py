import json
import os


def load_from_json(path: str):
    if os.path.isfile(path):
        with open(path, encoding='utf-8') as file:
            return json.load(file)
    else:
        with open(path, 'x', encoding='utf-8') as file:
            example = {
                 "session_name": "name_example",
                 "user_agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36",
                 "proxy": "type://user:pass:ip:port"
            }
            json.dump([example], file, ensure_ascii=False, indent=2)
            return [example]
    