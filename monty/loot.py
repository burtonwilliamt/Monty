import asyncio
import enum
import dataclasses
import random

import discord

from monty import money_db


class Rarity(enum.Enum):
    COMMON = 1
    RARE = 2
    VERY_RARE = 3


@dataclasses.dataclass
class LootItem:
    uid: int
    name: str
    desc: str
    value: float
    rarity: int


class LootBoxType(enum.Enum):
    BELLY_BUTTON = 1
    TRASH_BAG = 2


LOOT_BOXES = {
    LootBoxType.TRASH_BAG: [
        LootItem(
            uid=1,
            name="Infected razor",
            desc="You cut yourself, go to the hospital. Like, immediately.",
            value=-1000.0,
            rarity=Rarity.VERY_RARE,
        ),
        LootItem(
            uid=2,
            name="Dog poop",
            desc="This bag has a hole in it. Gross, now you have to replace your gloves.",
            value=-1.0,
            rarity=Rarity.RARE,
        ),
        LootItem(
            uid=3,
            name="Aluminum can",
            desc="I think this has a deposit on it?",
            value=0.05,
            rarity=Rarity.COMMON,
        ),
        LootItem(
            uid=4,
            name="Used boot",
            desc="Useless without the other one.",
            value=1.0,
            rarity=Rarity.COMMON,
        ),
        LootItem(
            uid=5,
            name="Wood",
            desc="You can burn it, or build something.",
            value=5.0,
            rarity=Rarity.COMMON,
        ),
        LootItem(
            uid=6,
            name="Wood with a nail in it",
            desc="In case there's an apocolypse.",
            value=10.0,
            rarity=Rarity.RARE,
        ),
        LootItem(
            uid=7,
            name="Broken xbox",
            desc="You could probably fix this up.",
            value=10.0,
            rarity=Rarity.RARE,
        ),
        LootItem(
            uid=8,
            name="Social security number",
            desc="Whooo! Let's go open some credit cards, boys!",
            value=1322.06,
            rarity=Rarity.VERY_RARE,
        ),
    ],
}

RARITY_WEIGHTS = {
    Rarity.COMMON: 80,
    Rarity.RARE: 15,
    Rarity.VERY_RARE: 5,
}


class OpenButton(discord.ui.Button):

    def __init__(self, generator: "ItemGenerator", cost: float):
        super().__init__(label=f"Open (Cost: {cost})")
        self.gen = generator

    async def callback(self, interaction: discord.Interaction):
        await self.gen.perform_open(interaction)


class ItemGenerator:

    def __init__(
        self, user: discord.User, money: money_db.MoneyDatabase, items: list[LootItem]
    ):
        self.user = user
        self.money = money
        self.items_found_so_far = set()
        self.items_by_rarity = {}
        for i in items:
            self.items_by_rarity.setdefault(i.rarity, []).append(i)

    def _choose_rarity_class(self) -> Rarity:
        rarity_classes_in_this_generator = list(self.items_by_rarity.keys())
        rarity_weights = [RARITY_WEIGHTS[r] for r in rarity_classes_in_this_generator]
        return random.choices(rarity_classes_in_this_generator, rarity_weights)[0]

    def pull(self) -> LootItem:
        if not self.items_by_rarity:
            raise ValueError("Attempting to generate from empty items list.")
        item_bucket = self.items_by_rarity[self._choose_rarity_class()]
        selected = random.choice(item_bucket)
        self.items_found_so_far.add(selected.uid)
        return selected

    def items_and_odds(self) -> list[tuple[LootItem, float]]:
        total_weights = sum([RARITY_WEIGHTS[r] for r in self.items_by_rarity])
        res = []
        for rarity, bucket in self.items_by_rarity.items():
            chance_of_this_rarity = RARITY_WEIGHTS[rarity] / total_weights
            chance_of_each_item = chance_of_this_rarity / len(bucket)
            res.extend([(i, chance_of_each_item) for i in bucket])
        return res

    def format_line_for_item(self, item: LootItem) -> str:
        if item.uid in self.items_found_so_far:
            return f"[{item.value}] {item.name}"
        else:
            return "?????"

    def make_embed(self, message: str = "") -> discord.Embed:
        e = discord.Embed()
        e.title = "Trash Bag"
        # e.set_image(url='https://cdn.discordapp.com/attachments/1155380240386883635/1155380872846004275/garbage.png')
        e.description = (
            "```\n"
            + "-" * 58
            + "\n"
            + "\n".join(
                f"{odds*100:05.2f}% {self.format_line_for_item(i)}"
                for i, odds in self.items_and_odds()
            )
            + "```"
        )
        e.description += f"\n```\n{message}\n```"
        e.set_footer(text=f"Balance: {self.money.stale_balance(self.user)}")
        return e

    async def perform_open(self, interaction: discord.Interaction):
        new_item = self.pull()
        await interaction.message.edit(embed=self.make_embed(f"Opening...\n..."))
        await asyncio.sleep(2)
        await interaction.message.edit(
            embed=self.make_embed(f"Opening...\nPutting gloves on...")
        )
        await asyncio.sleep(2)
        await interaction.message.edit(
            embed=self.make_embed(f"Opening...\nReaching in...")
        )
        await asyncio.sleep(2)
        await interaction.response.edit_message(
            embed=self.make_embed(
                f"{new_item.name} [{new_item.value}]\n{new_item.desc}"
            )
        )

    async def create_widget(self, interaction: discord.Interaction):
        view = discord.ui.View()
        view.add_item(OpenButton(self, 1.0))
        await interaction.response.send_message(embed=self.make_embed(), view=view)


async def create_lootbox_opener(
    interaction: discord.Interaction,
    money: money_db.MoneyDatabase,
    box_type: LootBoxType,
):
    gen = ItemGenerator(interaction.user, money, LOOT_BOXES[box_type])
    await gen.create_widget(interaction)
