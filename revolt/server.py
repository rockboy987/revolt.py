from __future__ import annotations

from typing import TYPE_CHECKING, Optional, cast, Union

from .channel import Channel
from .permissions import ServerPermissions
from .role import Role
from .asset import Asset
from .category import Category

if TYPE_CHECKING:
    from .member import Member
    from .state import State
    from .channel import TextChannel
    from .types import (Server as ServerPayload, File as FilePayload, Permission as PermissionPayload, SystemMessagesConfig, Category as CategoryPayload)


__all__ = ("Server", "SystemMessages")

class SystemMessages:
    def __init__(self, data: SystemMessagesConfig, state: State):
        self.state = state
        self.user_joined_id = data.get("user_joined")
        self.user_left_id = data.get("user_left")
        self.user_kicked_id = data.get("user_kicked")
        self.user_banned_id = data.get("user_banned")

    @property
    def user_joined(self) -> Optional[TextChannel]:
        if not self.user_joined_id:
            return

        channel = self.state.get_channel(self.user_joined_id)
        assert isinstance(channel, TextChannel)
        return channel

    @property
    def user_left(self) -> Optional[TextChannel]:
        if not self.user_left_id:
            return

        channel = self.state.get_channel(self.user_left_id)
        assert isinstance(channel, TextChannel)
        return channel

    @property
    def user_kicked(self) -> Optional[TextChannel]:
        if not self.user_kicked_id:
            return

        channel = self.state.get_channel(self.user_kicked_id)
        assert isinstance(channel, TextChannel)
        return channel

    @property
    def user_banned(self) -> Optional[TextChannel]:
        if not self.user_banned_id:
            return

        channel = self.state.get_channel(self.user_banned_id)
        assert isinstance(channel, TextChannel)
        return channel

class Server:
    """Represents a server

    Attributes
    -----------
    id: :class:`str`
        The id of the server
    name: :class:`str`
        The name of the server
    owner_id: :class:`str`
        The owner's id of the server
    description: Optional[:class:`str`]
        The servers description
    nsfw: :class:`bool`
        Whether the server is nsfw or not
    system_messages: :class:`SystemMessages`
        The system message config for the server
    categories: list[:class:`Category`]
        The categories in the server
    icon: Optional[:class:`Asset`]
        The servers icon
    banner: Optional[:class:`Asset`]
        The servers banner
    """
    __slots__ = ("state", "id", "name", "owner_id", "default_permissions", "_members", "_roles", "_channels", "description", "icon", "banner", "nsfw", "system_messages", "categories")

    def __init__(self, data: ServerPayload, state: State):
        self.state = state
        self.id = data["_id"]
        self.name = data["name"]
        self.owner_id = data["owner"]
        self.default_permissions = ServerPermissions(*data["default_permissions"])
        self.description = data.get("description") or None
        self.nsfw = data.get("nsfw", False)
        self.system_messages = SystemMessages(data.get("system_messages", {}), state)
        self.categories = [Category(data, state) for data in data.get("categories", [])]

        if icon := data.get("icon"):
            self.icon = Asset(icon, state)
        else:
            self.icon = None

        if banner := data.get("banner"):
            self.banner = Asset(banner, state)
        else:
            self.banner  = None

        self._members: dict[str, Member] = {}
        self._roles: dict[str, Role] = {role_id: Role(role, role_id, state, self) for role_id, role in data.get("roles", {}).items()}

        channels = cast(list[Channel], list(filter(bool, [state.get_channel(channel_id) for channel_id in data["channels"]])))
        self._channels: dict[str, Channel] = {channel.id: channel for channel in channels}

    def _update(self, *, owner: Optional[str] = None, name: Optional[str] = None, description: Optional[str] = None, icon: Optional[FilePayload] = None, banner: Optional[FilePayload] = None, default_permissions: Optional[PermissionPayload] = None, nsfw: Optional[bool] = None, system_messages: Optional[SystemMessagesConfig] = None, categories: Optional[list[CategoryPayload]] = None):
        if owner:
            self.owner_id = owner
        if name:
            self.name = name
        if description is not None:
            self.description = description or None
        if icon:
            self.icon = Asset(icon, self.state)
        if banner:
            self.banner = Asset(banner, self.state)
        if default_permissions:
            self.default_permissions = ServerPermissions(*default_permissions)
        if nsfw is not None:
            self.nsfw = nsfw
        if system_messages is not None:
            self.system_messages = SystemMessages(system_messages, self.state)
        if categories is not None:
            self.categories = [Category(data, self.state) for data in categories]

    @property
    def roles(self) -> list[Role]:
        """list[:class:`Role`] Gets all roles in the server in decending order"""
        return list(self._roles.values())
    
    @property
    def members(self) -> list[Member]:
        """list[:class:`Member`] Gets all members in the server"""
        return list(self._members.values())

    @property
    def channels(self) -> list[Channel]:
        """list[:class:`Member`] Gets all channels in the server"""
        return list(self._channels.values())

    def get_role(self, role_id: str) -> Role:
        """Gets a role from the cache
        
        Parameters
        -----------
        id: :class:`str`
            The id of the role
        
        Returns
        --------
        :class:`Role`
            The role
        """
        return self._roles[role_id]

    def get_member(self, member_id: str) -> Member:
        """Gets a member from the cache
        
        Parameters
        -----------
        id: :class:`str`
            The id of the member
        
        Returns
        --------
        :class:`Member`
            The member
        """
        return self._members[member_id]

    def get_channel(self, channel_id: str) -> Channel:
        """Gets a channel from the cache
        
        Parameters
        -----------
        id: :class:`str`
            The id of the channel
        
        Returns
        --------
        :class:`Channel`
            The channel
        """
        return self._channels[channel_id]

    @property
    def owner(self) -> Member:
        """:class:`Member` The owner of the server"""
        return self.get_member(self.owner_id)

    async def set_default_permissions(self, permissions: ServerPermissions) -> None:
        """Sets the default server permissions.
        Parameters
        -----------
        permissions: :class:`ServerPermissions`
            The new default server permissions
        """
        await self.state.http.set_default_permissions(self.id, *permissions.value)
