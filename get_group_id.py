from telethon.sync import TelegramClient
from telethon.tl.types import Channel, Chat

api_id = 21859092
api_hash = 'f12c3af27de519c05e7062b02ef73976'
with TelegramClient('session_name', api_id, api_hash) as client:
    for dialog in client.iter_dialogs():
        entity = dialog.entity
        if isinstance(entity, (Channel, Chat)):
            print(f"Group Name : {dialog.name}")
            print(f"Group ID   : {dialog.id}")
            print("-" * 50)
