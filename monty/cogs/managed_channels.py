from pydantic import BaseModel

# TODO: Switch the str identifiers to be int identifiers.

class ManagedChannel(BaseModel):
    name: str
    role: str

class GuildChannels:
    category: str
    channels: list[ManagedChannel]

class Guilds:
    guilds: dict[int, GuildChannels]