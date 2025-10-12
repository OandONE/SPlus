import json

class Update:
    def __init__(self,data):
        self._data_ = data
    def __str__(self) -> str:
        return json.dumps(self._data_,indent=4,ensure_ascii=False)
