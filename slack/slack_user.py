from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import weechat

from slack.shared import shared
from slack.task import create_task
from slack.util import with_color

if TYPE_CHECKING:
    from slack_api.slack_bots_info import SlackBotInfo
    from slack_api.slack_users_info import SlackUserInfo

    from slack.slack_workspace import SlackApi, SlackWorkspace


def nick_color(nick: str) -> str:
    return weechat.info_get("nick_color_name", nick)


def format_bot_nick(nick: str, colorize: bool = False) -> str:
    nick = nick.replace(" ", "")

    if colorize:
        nick = with_color(nick_color(nick), nick)

    return nick + shared.config.look.bot_user_suffix.value


class SlackUser:
    def __init__(
        self,
        workspace: SlackWorkspace,
        id: str,
        info: Optional[SlackUserInfo] = None,
    ):
        self.workspace = workspace
        self.id = id
        if info:
            self._info = info
            self._set_info_task = None
        else:
            self._set_info_task = create_task(self._set_info())

    @property
    def _api(self) -> SlackApi:
        return self.workspace.api

    async def _set_info(self):
        info_response = await self._api.fetch_user_info(self.id)
        self._info = info_response["user"]

    async def ensure_initialized(self):
        if self._set_info_task:
            await self._set_info_task

    def nick(self, colorize: bool = False) -> str:
        nick = self._name_without_spaces()

        if colorize:
            nick = with_color(self._nick_color(), nick)

        if self._info["profile"]["team"] != self.workspace.id:
            nick += shared.config.look.external_user_suffix.value

        return nick

    def _name_from_profile(self) -> str:
        display_name = self._info["profile"].get("display_name")
        if display_name and not self.workspace.config.use_real_names.value:
            return display_name

        return (
            self._info["profile"].get("display_name")
            or self._info.get("real_name")
            or self._info["name"]
        )

    def _name_without_spaces(self) -> str:
        return self._name_from_profile().replace(" ", "")

    def _nick_color(self) -> str:
        if self.id == self.workspace.my_user.id:
            return weechat.config_string(
                weechat.config_get("weechat.color.chat_nick_self")
            )

        return nick_color(self._name_without_spaces())


class SlackBot:
    def __init__(
        self,
        workspace: SlackWorkspace,
        id: str,
        info: Optional[SlackBotInfo] = None,
    ):
        self.workspace = workspace
        self.id = id
        if info:
            self._info = info
            self._set_info_task = None
        else:
            self._set_info_task = create_task(self._set_info())

    @property
    def _api(self) -> SlackApi:
        return self.workspace.api

    async def _set_info(self):
        info_response = await self._api.fetch_bot_info(self.id)
        self._info = info_response["bot"]

    async def ensure_initialized(self):
        if self._set_info_task:
            await self._set_info_task

    def nick(self, colorize: bool = False) -> str:
        return format_bot_nick(self._info["name"], colorize)
