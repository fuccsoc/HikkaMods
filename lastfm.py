__version__ = (1, 1, 1)

# powered by hikari's love to fuccsoc.

# meta developer: @fuccsoc_will_be_free
# scope: hikka_only
# scope: hikka_min 1.2.10
# requires: pylast

import functools
from importlib.resources import as_file
import logging
import traceback
import contextlib
from types import FunctionType

import pylast
from requests import get as rget
from telethon.tl.types import Message

from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)
logging.getLogger("pylast").setLevel(logging.ERROR)


@loader.tds
class LastFMMod(loader.Module):
    """LastFM Module"""

    strings = {
        "name": "LastFM",
        "need_auth": "<b>Call</b><code>.lfauth</code><b> before using this action.</b>",
        "already_authed": "You are already logged in. Fuck off.",
        "error": "Fuck this. Fuck you. Fuck everyone. Suck the {}",
        "auth_process": "Authofuckingrizing...",
        "url_button": "Go fuck yourself here",
        "confirm_button": "After hard bdsm sex with hikari, press here",
        "success_auth": "Authofuckingrized successfully. Woo-Hoo!!",
        "user_not_found": "Fucking user fucking not fucking found fuck.",
        "user_have_no_scrobbles": "This fucking user is fucking as fuck so there's fucking nothing to fucking display. Suck it.",
        "now_playing": '<emoji document_id=5212941939053175244>🎧</emoji> Now playing: <a href="{}"><b><i>{} - {}</i></b></a>',
        "user_now_playing": '<emoji document_id=5212941939053175244>🎧</emoji> <a href="https://last.fm/user/{0}">{0}</a> is now playing: <a href="{1}"><b><i>{2} - {3}</i></b></a>',
        "file_not_found": (
            '<emoji document_id=5212941939053175244>🎧</emoji> Now playing: <a href="{}"><b><i>{} - {}</i></b></a>\n\n'
            "<code>We didn't found an mp3 file. Check if you started dialog with </code>@LossLessRobot <code>and try again.</code>"
        ),
        "user_file_not_found": (
            '<emoji document_id=5212941939053175244>🎧</emoji> <a href="https://last.fm/user/{0}">{0}</a> is now playing: <a href="{1}"><b><i>{2} - {3}</i></b></a>\n\n'
            "<code>We didn't found an mp3 file. Check if you started dialog with </code>@LossLessRobot <code>and try again.</code>"
        ),
        "unauth_success": "Unauthofuckingrizing successfully. Fuck off, bitch.",
        "processing": "<code>Processing your request...</code>",
    }

    def __init__(self):
        pass

    async def client_ready(self, client, db):
        self.musicdl = await self.import_lib(
            "https://libs.hikariatama.ru/musicdl.py",
            suspend_on_error=True,
        )
        try:
            self.pl = pylast.LastFMNetwork(
                api_key="a36b285105b787164c0fa2a053713564",
                api_secret="17595264a10181404441bc52302eea32",
                session_key=self.get("session_key"),
                username=self.get("username"),
            )
        except Exception:
            self.set("session_key", None)
            self.set("username", None)
            self.pl = None

    def tokenized(func) -> FunctionType:
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            if not args[0].get("session_key", False) or not args[0].pl:
                await utils.answer(args[1], args[0].strings("need_auth"))
                return
            return await func(*args, **kwargs)

        wrapped.__doc__ = func.__doc__
        wrapped.__module__ = func.__module__

        return wrapped

    def error_handler(func) -> FunctionType:
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception:
                logger.exception(traceback.format_exc())
                with contextlib.suppress(Exception):
                    await utils.answer(
                        args[1],
                        args[0].strings("err").format(traceback.format_exc()),
                    )

        wrapped.__doc__ = func.__doc__
        wrapped.__module__ = func.__module__

        return wrapped

    @error_handler
    async def lfauthcmd(self, message: Message):
        """Auth lastfm account"""
        if self.get("session_key", False):
            await utils.answer(message, self.strings("already_authed"))
            return
        else:
            sg = pylast.SessionKeyGenerator(
                pylast.LastFMNetwork(
                    api_key="a36b285105b787164c0fa2a053713564",
                    api_secret="17595264a10181404441bc52302eea32",
                )
            )
            url = sg.get_web_auth_url()
            token = sg.web_auth_tokens[url]
            self.set("url", url)
            self.set("token", token)

            await self.inline.form(
                text=self.strings("auth_process"),
                message=message,
                reply_markup=[
                    [
                        {
                            "text": self.strings("url_button"),
                            "url": url,
                        }
                    ],
                    [
                        {
                            "text": self.strings("confirm_button"),
                            "callback": self._finalize_auth,
                        }
                    ],
                ],
                force_me=True,
            )

    @error_handler
    async def _finalize_auth(self, call: InlineCall):
        sg = pylast.SessionKeyGenerator(
            pylast.LastFMNetwork(
                api_key="a36b285105b787164c0fa2a053713564",
                api_secret="17595264a10181404441bc52302eea32",
            )
        )
        try:
            session_key, username = sg.get_web_auth_session_key_username(
                self.get("url", "null"),
                self.get("token", "null"),
            )
            self.set("session_key", session_key)
            self.set("username", username)
            self.set("url", None)
            self.set("token", None)
            self.pl = pylast.LastFMNetwork(
                api_key="a36b285105b787164c0fa2a053713564",
                api_secret="17595264a10181404441bc52302eea32",
                session_key=self.get("session_key"),
                username=self.get("username"),
            )
        except Exception as e:
            await call.edit(text=self.strings("error").format(str(e)))
            return
        await call.edit(text=self.strings("success_auth"))

    @error_handler
    @tokenized
    async def lfnowcmd(self, message: Message):
        """Show current playback"""
        await utils.answer(message, self.strings("processing"))
        args = utils.get_args(message)
        username = self.get("username")
        user_is_self = True
        if len(args) > 0:
            username = args[0]
            user_is_self = False
            user = self.pl.get_user(username)
            try:
                track = user.get_now_playing()
            except:
                await utils.answer(message, self.strings("user_not_found"))
                return
        else:
            user = self.pl.get_user(username)
            track = user.get_now_playing()
        if track is None:
            track = self.pl.get_user(username).get_recent_tracks(1)[0].track
        if track is None:
            await utils.answer(message, self.strings("user_has_no_scrobbles"))
            return
        try:
            link = "https://song.link/i/" + str(
                rget(
                    f"https://itunes.apple.com/search?term={track}&country=RU&entity=song&limit=1"
                ).json()["results"][0]["trackId"]
            )
        except:
            link = "#"
        track_fl = await self.musicdl.dl(
            f"{track.artist.name} - {track.title}", only_document=True
        )
        if track_fl is not None:
            await self._client.send_file(
                message.peer_id,
                track_fl,
                caption=self.strings("now_playing").format(
                    link, track.artist.name, track.title
                )
                if user_is_self
                else self.strings("user_now_playing").format(
                    username, link, track.artist.name, track.title
                ),
                reply_to=getattr(message, "reply_to_msg_id", None),
            )
            await message.delete()
            return
        await utils.answer(
            message,
            self.strings("file_not_found").format(link, track.artist.name, track.title)
            if user_is_self
            else self.strings("user_file_not_found").format(
                username, link, track.artist.name, track.title
            ),
        )

    @error_handler
    @tokenized
    async def lfunauthcmd(self, message: Message):
        "Unauthorize"
        self.set("session_key", None)
        self.set("username", None)
        self.set("url", None)
        self.set("token", None)
        self.pl = None
        await utils.answer(message, self.strings("unauth_success"))
