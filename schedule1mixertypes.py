from typing import Self, TypedDict, NotRequired, Literal
from math import floor, ceil


class Color:
    def __init__(self, r: int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b

    def __str__(self) -> str:
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    def __repr__(self) -> str:
        return f"Color({self.r}, {self.g}, {self.b})"

    def __add__(self, other) -> Self:
        if not isinstance(self, type(other)):
            return NotImplemented
        return type(self)(self.r + other.r, self.g + other.g, self.b + other.b)

    @classmethod
    def parse_color(cls, color: str) -> Self:
        if color.startswith("#"):  # Format: #RRGGBB
            return cls(int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
        if color.startswith("rgb(") and color.endswith(")"):  # Format: rgb(r, g, b)
            rgb = list(map((lambda string: string.strip()), color[4:-1].split(",")))
            try:
                r = int(rgb[0])
                g = int(rgb[1])
                b = int(rgb[2])
            except IndexError as e:
                raise ValueError("Invalid color specification")
            return cls(r, g, b)
        raise ValueError("Unsupported color format")


class JSONRank(TypedDict):
    index: int
    id: str
    displayName: str
    bound: int
    tierXp: int


class JSONOption(TypedDict):
    id: str
    displayName: str
    batchYield: NotRequired[int]
    batchPrice: NotRequired[int]
    rank: NotRequired[str]
    rankTier: NotRequired[int]


class JSONChoice(TypedDict):
    id: str
    displayName: str
    options: list[JSONOption]


class JSONEffect(TypedDict):
    id: str
    displayName: str
    displayColor: str
    multiplier: float | int
    addictiveness: float | int


class JSONBaseDrug(TypedDict):
    id: str
    displayName: str
    batchPrice: int
    batchYield: int
    choices: list[str]
    rank: str
    rankTier: int
    basePrice: int
    baseAddictiveness: float | int
    mixAddictivenessBonus: float | int
    effects: list[str]


class JSONIngredient(TypedDict):
    id: str
    displayName: str
    price: int
    rank: str
    rankTier: int
    baseEffect: str
    transformations: dict[str, str]


def json_lookup_by_id[T: JSONRank | JSONEffect | JSONBaseDrug | JSONIngredient | JSONOption | JSONChoice](
    elements: list[T], id: str
) -> T:
    for element in elements:
        try:
            if element["id"] == id:
                return element
        except Exception as e:
            raise ValueError("Invalid element") from e
    raise ValueError("No element with specified id")


class Rank:
    def __init__(
        self,
        index: int,
        id: str,
        display_name: str,
        bound: int,
        tier_xp: int,
    ) -> None:
        self.index = index
        self.id = id
        self.display_name = display_name
        self.bound = bound
        self.tier_xp = tier_xp

    def __eq__(self, other: Self) -> bool:
        return self.index == other.index

    def __lt__(self, other: Self) -> bool:
        return self.index < other.index

    def __gt__(self, other: Self) -> bool:
        return self.index > other.index

    def __ne__(self, other: Self) -> bool:
        return not (self == other)

    def __le__(self, other: Self) -> bool:
        return self < other or self == other

    def __ge__(self, other: Self) -> bool:
        return self > other or self == other

    def __str__(self) -> str:
        return self.display_name

    @classmethod
    def from_json(cls, json: JSONRank) -> Self:
        try:
            return cls(
                json["index"],
                json["id"],
                json["displayName"],
                json["bound"],
                json["tierXp"],
            )
        except Exception as e:
            raise ValueError("Invalid JSONRank") from e


class Option:
    def __init__(self, id: str, display_name: str, batch_yield: int, batch_price: int, rank_tier: RankTier) -> None:
        self.id = id
        self.display_name = display_name
        self.batch_yield = batch_yield
        self.batch_price = batch_price
        self.rank_tier = rank_tier

    def __str__(self) -> str:
        return f"{self.display_name}"

    @classmethod
    def from_json(cls, json: JSONOption, ranks: list[Rank]) -> Self:
        try:
            return cls(
                json["id"],
                json["displayName"],
                json.get("batchYield", 0),
                json.get("batchPrice", 0),
                RankTier(
                    lookup_by_id(ranks, json.get("rank", ranks[0].id)),
                    json.get("rankTier", 1),
                ),
            )
        except Exception as e:
            raise ValueError("Invalid JSONOption") from e


class Choice:
    def __init__(self, id: str, display_name: str, options: list[Option]) -> None:
        self.id = id
        self.display_name = display_name
        self.options = options

    def __str__(self) -> str:
        return f"{self.display_name}"

    @classmethod
    def from_json(cls, json: JSONChoice, ranks: list[Rank]) -> Self:
        try:
            return cls(
                json["id"],
                json["displayName"],
                [Option.from_json(json_option, ranks) for json_option in json["options"]],
            )
        except Exception as e:
            raise ValueError("Invalid JSONChoice") from e


class RankTier:
    def __init__(
        self,
        rank: Rank,
        tier: int,
    ):
        if rank.bound != -1 and tier > rank.bound:
            raise ValueError(f"Tier {tier} out of bounds for rank {rank.id}")
        self.rank = rank
        self.tier = tier

    def __eq__(self, other: Self) -> bool:
        return self.rank == other.rank and self.tier == other.tier

    def __lt__(self, other: Self) -> bool:
        if self.rank < other.rank:
            return True
        elif self.rank > other.rank:
            return False
        else:
            return self.tier < other.tier

    def __gt__(self, other: Self) -> bool:
        if self.rank > other.rank:
            return True
        elif self.rank < other.rank:
            return False
        else:
            return self.tier > other.tier

    def __ne__(self, other: Self) -> bool:
        return not (self == other)

    def __le__(self, other: Self) -> bool:
        return self < other or self == other

    def __ge__(self, other: Self) -> bool:
        return self > other or self == other

    def __str__(self) -> str:
        if self.tier <= 5:
            return f"{self.rank.display_name} {["I", "II", "III", "IV", "V"][self.tier - 1]}"
        else:
            return f"{self.rank.display_name} {self.tier}"


class Effect:
    def __init__(
        self,
        id: str,
        display_name: str,
        display_color: Color,
        multiplier: float,
        addictiveness: float,
    ) -> None:
        self.id = id
        self.display_name = display_name
        self.display_color = display_color
        self.multiplier = multiplier
        self.addictiveness = addictiveness

    def __str__(self) -> str:
        return self.display_name

    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def from_json(cls, json: JSONEffect) -> Self:
        try:
            return cls(
                json["id"],
                json["displayName"],
                Color.parse_color(json["displayColor"]),
                float(json["multiplier"]),
                float(json["addictiveness"]),
            )
        except Exception as e:
            raise ValueError("Invalid JSONEffect") from e


class BaseDrug:
    def __init__(
        self,
        id: str,
        display_name: str,
        batch_price: int,
        batch_yield: int,
        choices: list[Choice],
        rank_tier: RankTier,
        base_price: int,
        base_addictiveness: float,
        mix_addictiveness_bonus: float,
        effects: list[Effect],
    ) -> None:
        self.id = id
        self.display_name = display_name
        self.batch_price = batch_price
        self.batch_yield = batch_yield
        self.choices = choices
        self.rank_tier = rank_tier
        self.base_price = base_price
        self.base_addictiveness = base_addictiveness
        self.mix_addictiveness_bonus = mix_addictiveness_bonus
        self.effects = effects

    def __str__(self) -> str:
        return self.display_name

    @classmethod
    def from_json(cls, json: JSONBaseDrug, choices: list[Choice], ranks: list[Rank], effects: list[Effect]) -> Self:
        try:
            return cls(
                json["id"],
                json["displayName"],
                json["batchPrice"],
                json["batchYield"],
                [lookup_by_id(choices, json_choice) for json_choice in json["choices"]],
                RankTier(
                    lookup_by_id(ranks, json["rank"]),
                    json["rankTier"],
                ),
                json["basePrice"],
                float(json["baseAddictiveness"]),
                float(json["mixAddictivenessBonus"]),
                [lookup_by_id(effects, json_effect) for json_effect in json["effects"]],
            )
        except Exception as e:
            raise ValueError("Invalid JSONBaseDrug") from e


class Ingredient:
    def __init__(
        self,
        id: str,
        display_name: str,
        price: int,
        rank_tier: RankTier,
        base_effect: Effect,
        transformations: dict[Effect, Effect],
    ) -> None:
        self.id = id
        self.display_name = display_name
        self.price = price
        self.rank_tier = rank_tier
        self.base_effect = base_effect
        self.transformations = transformations

    def __str__(self) -> str:
        return self.display_name

    @classmethod
    def from_json(cls, json: JSONIngredient, ranks: list[Rank], effects: list[Effect]) -> Self:
        try:
            return cls(
                json["id"],
                json["displayName"],
                json["price"],
                RankTier(
                    lookup_by_id(ranks, json["rank"]),
                    json["rankTier"],
                ),
                lookup_by_id(effects, json["baseEffect"]),
                {
                    lookup_by_id(effects, from_effect): lookup_by_id(effects, to_effect)
                    for from_effect, to_effect in json["transformations"].items()
                },
            )
        except Exception as e:
            raise ValueError("Invalid JSONIngredient") from e


def lookup_by_id[T: Option | Choice | Rank | Effect | BaseDrug | Ingredient](elements: list[T], id: str) -> T:
    for element in elements:
        try:
            if element.id == id:
                return element
        except Exception as e:
            raise ValueError("Invalid element") from e
    raise ValueError("No element with specified id")


class Mix:
    def __init__(self, base_drug: BaseDrug, ingredients: list[Ingredient], base_drug_choices: dict[Choice, Option]) -> None:
        for choice, option in base_drug_choices.items():
            if option not in choice.options:
                raise ValueError(f"Choice {choice} has no option {option}")
        self.base_drug = base_drug
        self.ingredients = ingredients
        self.base_drug_choices = base_drug_choices

    def __len__(self) -> int:
        return len(self.ingredients)

    def __str__(self) -> str:
        return " + ".join([str(self.base_drug)] + [str(ingredient) for ingredient in self.ingredients])

    @property
    def effects(self) -> list[Effect]:
        result: list[Effect] = self.base_drug.effects.copy()
        for ingredient in self.ingredients:
            for from_effect, to_effect in ingredient.transformations.items():
                if from_effect in result and to_effect not in result:
                    result.remove(from_effect)
                    result.append(to_effect)
            if ingredient.base_effect not in result and len(result) < 8:
                result.append(ingredient.base_effect)
        return result

    @property
    def sell_price(self) -> int:
        total_multiplier: float = 0
        for effect in self.effects:
            total_multiplier += effect.multiplier
        result = self.base_drug.base_price * (total_multiplier + 1)
        if result % 1 == 0.5:
            if total_multiplier < 1:
                return floor(result)
            else:
                return ceil(result)
        else:
            return round(result)

    @property
    def batch_yield(self) -> int:
        return self.base_drug.batch_yield + sum(
            [option.batch_yield for choice, option in self.base_drug_choices.items() if choice in self.base_drug.choices]
        )

    @property
    def batch_price(self) -> int:
        return self.base_drug.batch_price + sum(
            [option.batch_price for choice, option in self.base_drug_choices.items() if choice in self.base_drug.choices]
        )

    @property
    def batch_profit(self) -> int:
        return self.sell_price * self.batch_yield - self.batch_price

    @property
    def rank_tier(self) -> RankTier:
        return max(
            [ingredient.rank_tier for ingredient in self.ingredients]
            + [self.base_drug.rank_tier]
            + [option.rank_tier for choice, option in self.base_drug_choices.items() if choice in self.base_drug.choices]
        )

    @property
    def addictiveness(self) -> float | Literal[0, 1]:
        return max(
            0,
            min(
                1,
                sum(
                    [effect.addictiveness for effect in self.effects],
                    self.base_drug.mix_addictiveness_bonus if len(self.ingredients) > 0 else 0,
                )
                // 0.01
                * 0.01,
            ),
        )
