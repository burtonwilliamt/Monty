import http.client
import json
import re
import urllib.parse
from dataclasses import dataclass

import discord

linked_terms_pattern = re.compile(r"\[([^]]*)\]")


@dataclass
class UrbanDefinition:
    """Class to store the response of an urban dictionary query."""

    word: str
    definition: str
    example: str
    permalink: str


async def fetch_urban_dictionary_definition(term: str) -> UrbanDefinition | None:
    # Do the network request.
    conn = http.client.HTTPSConnection("api.urbandictionary.com")
    encoded_term = urllib.parse.quote(term, safe="")
    conn.request("GET", f"/v0/define?term={encoded_term}")
    res = conn.getresponse()
    data_bytes = res.read()
    if len(data_bytes) == 0:
        return None
    first_result = json.loads(data_bytes.decode("utf-8"))["list"][0]
    return UrbanDefinition(
        word=first_result["word"],
        definition=first_result["definition"],
        example=first_result["example"],
        permalink=first_result["permalink"],
    )


async def send_urban_dictionary_definition(
    interaction: discord.Interaction, term: str, previous_terms: tuple[str] = tuple()
):
    """Respond to the interaction with an urban diction definition."""

    definition = await fetch_urban_dictionary_definition(term)
    if definition is None:
        await interaction.response.send_message("Failed to get a definition")
        return

    # Build a UI
    terms_to_get_here = tuple(list(previous_terms) + [definition.word])
    e = discord.Embed()

    def clean(text: str):
        return "\n".join(
            [
                l
                for l in text.replace(r"\r\n", "\n")
                .replace("[", "__")
                .replace("]", "__")
                .splitlines()
                if len(l.strip()) > 0
            ]
        )

    description = [f'# {" > ".join(terms_to_get_here)}']
    description.extend([f"### {l}" for l in clean(definition.definition).splitlines()])
    description.append("\n")
    description.extend([f"*{l}*" for l in clean(definition.example).splitlines()])
    description.append(f"[website]({definition.permalink})")
    e.description = "\n".join(description)
    other_terms = linked_terms_pattern.findall(
        definition.definition
    ) + linked_terms_pattern.findall(definition.example)
    view = discord.ui.View()
    processed_terms = set()
    for other_term in other_terms:
        other_term = other_term.lower()
        if other_term in processed_terms:
            continue
        view.add_item(
            UbanDictionaryButton(term=other_term, previous_terms=terms_to_get_here)
        )
        processed_terms.add(other_term)

    await interaction.response.send_message(embed=e, view=view)


class UbanDictionaryButton(discord.ui.Button):
    def __init__(self, term: str, previous_terms: tuple[str]):
        super().__init__(label=term)
        self.term = term
        self.previous_terms = previous_terms

    async def callback(self, interaction: discord.Interaction) -> None:
        await send_urban_dictionary_definition(
            interaction, self.term, self.previous_terms
        )
