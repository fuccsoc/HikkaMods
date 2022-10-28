__version__ = (1, 0, 1)

# powered by hikari's love to fuccsoc.

# meta developer: @fuccsoc_will_be_free

import asyncio
import logging
from telethon import TelegramClient

from telethon.tl import types, functions

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class AdminListMod(loader.Module):
    """Admin list module - show adminned and owned chats."""

    strings = {
        "name": "AdminList",
        "result": "<b>Adminned chats ({adminned_chats_count}):</b>\n{adminned_chats_list}\n\n<b>Owned chats ({owned_chats_count}):</b>\n{owned_chats_list}\n\n<b>Owned chats with username ({owned_usernamed_chats_count}):</b>\n{owned_usernamed_chats_list}\n\n<b>Total: {total_count}</b>",
    }

    def __init__(self):
        pass

    async def admlistcmd(self, message: types.Message):
        """Show adminned and owned chats chats."""
        self.client: TelegramClient
        result = await self.client(functions.messages.GetAllChatsRequest(except_ids=[]))

        chats = result.chats

        adminned_chats = []
        owned_chats = []
        owned_usernamed_chats = []

        for chat in chats:
            chat: types.Chat
            if getattr(chat, "migrated_to", False):
                continue
            if chat.creator and getattr(chat, "username", False):
                owned_usernamed_chats.append(chat)
            elif chat.creator:
                owned_chats.append(chat)
            elif getattr(chat, "admin_rights", False):
                adminned_chats.append(chat)

        await utils.answer(
            message,
            self.strings("result").format(
                adminned_chats_count=len(adminned_chats),
                adminned_chats_list="\n".join(
                    [
                        '{i}. <a href="{link}">{title}</a>'.format(
                            i=index,
                            link="https://t.me/c/{}/1".format(chat.id),
                            title=chat.title,
                        )
                        for index, chat in enumerate(adminned_chats, 1)
                    ]
                ),
                owned_chats_count=len(owned_chats),
                owned_chats_list="\n".join(
                    [
                        '{i}. <a href="{link}">{title}</a>'.format(
                            i=index,
                            link="https://t.me/c/{}/1".format(chat.id),
                            title=chat.title,
                        )
                        for index, chat in enumerate(owned_chats, 1)
                    ]
                ),
                owned_usernamed_chats_count=len(owned_usernamed_chats),
                owned_usernamed_chats_list="\n".join(
                    [
                        "{i}. [@{username}] {title}".format(
                            i=index,
                            username=chat.username,
                            title=chat.title,
                        )
                        for index, chat in enumerate(owned_usernamed_chats, 1)
                    ]
                ),
                total_count=len(owned_chats)
                + len(owned_usernamed_chats)
                + len(adminned_chats),
            ),
        )
