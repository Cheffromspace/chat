import json


def output_json(data):
    json_output = json.dumps(data, indent=2)
    print(json_output)
