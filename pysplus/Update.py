import json
from typing import TYPE_CHECKING,Optional
from .async_sync import async_to_sync
if TYPE_CHECKING:
    from .Client import Client

class Update:
    def __init__(self, data, client: 'Client', chat_id: str):
        self._data_ = data
        self.client = client
        self.chat_id = chat_id

    @property
    def message_id(self) -> str:
        return self._data_["message_id"]

    @property
    def day(self) -> str:
        return self._data_["day"]

    @property
    def date(self) -> Optional[str]:
        return self._data_["date"]

    @property
    def time(self) -> str:
        return self._data_["time"]
    
    @property
    def is_me(self) -> bool:
        return self._data_["is_me"]
    
    @property
    def text(self) -> str:
        return self._data_["text"]
    
    @property
    def summary(self) -> str:
        return self._data_["summary"]
    
    @property
    def classes(self) -> list:
        return self._data_["classes"]

    @async_to_sync
    async def reply(self,text:str,reply:bool = True):
        return await self.client.send_text(self.chat_id,text,self.message_id if reply else None)

    @async_to_sync
    async def delete(self):
        return await self.client.delete_message(self.message_id,self.chat_id)

    @async_to_sync
    async def pin(self):
        return await self.client.pin_message(self.message_id,self.chat_id)

    def __str__(self) -> str:
        return json.dumps(self._data_, indent=4, ensure_ascii=False)