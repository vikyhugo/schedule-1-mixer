from json.decoder import JSONDecoder
from typing import Any, TypedDict, Mapping, get_origin, get_args
from types import UnionType

Rank = TypedDict(
    "Rank",
    {
        "id": str,
        "displayName": str,
        "unbounded": bool,
        "tierXp": int,
    },
)

BaseDrug = TypedDict(
    "BaseDrug",
    {
        "id": str,
        "displayName": str,
        "rank": str,
        "rankTier": int,
        "basePrice": int,
        "effects": list[str],
    },
)

Ingredient = TypedDict(
    "Ingredient",
    {
        "id": str,
        "displayName": str,
        "price": int,
        "rank": str,
        "rankTier": int,
        "baseEffect": str,
        "transformations": dict[str, str],
    },
)

Effect = TypedDict(
    "Effect",
    {
        "id": str,
        "displayName": str,
        "displayColor": str,
        "multiplier": (float | int),
    },
)


def check_typed_dict(td: Mapping[Any, Any], tdtype: type):
    for key, ktype in tdtype.__annotations__.items():
        keytype = None
        if get_origin(ktype) is None or get_origin(ktype) is UnionType:
            keytype = ktype
        else:
            keytype = get_origin(ktype)
        if key in tdtype.__required_keys__ or key in td:
            assert key in td
            assert isinstance(td[key], keytype)
            if keytype is list and get_origin(ktype) != None:
                assert all(isinstance(x, get_args(ktype)) for x in td[key])
            if keytype is dict and get_origin(ktype) != None:
                assert all(
                    isinstance(key, get_args(ktype)[0]) and isinstance(val, get_args(ktype)[1])
                    for key, val in td[key].items()
                )


class Color:
    def __init__(self, r: int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b

    @classmethod
    def parse_color(cls, color: str):
        if color.startswith("#"):
            return cls(int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
        if color.startswith("rgb(") and color.endswith(")"):
            rgb = color[4:-1].split(",")
            r = int(rgb[0].strip())
            g = int(rgb[1].strip())
            b = int(rgb[2].strip())
            return cls(r, g, b)
        raise ValueError("Unsupported color format")


def check_dataset(ranks: list[Rank], base_drugs: list[BaseDrug], ingredients: list[Ingredient], effects: list[Effect]):
    try:
        print("Testing ranks")
        found_unbounded: bool = False
        found_rank_ids: list[str] = []
        for rank in ranks:
            print(f"    Testing rank {rank["id"]}")

            print("        Testing values")
            check_typed_dict(rank, Rank)

            print("        Testing duplicate")
            assert rank["id"] not in found_rank_ids
            found_rank_ids.append(rank["id"])

            print("        Testing duplicate unboundedness")
            assert not (rank["unbounded"] and found_unbounded)
            found_unbounded = found_unbounded or rank["unbounded"]

        print("Testing base drugs")
        found_base_drug_ids: list[str] = []
        for base_drug in base_drugs:
            print(f"    Testing base drug {base_drug["id"]}")

            print("        Testing values")
            check_typed_dict(base_drug, BaseDrug)

            print("        Testing duplicate")
            assert base_drug["id"] not in found_base_drug_ids
            found_base_drug_ids.append(base_drug["id"])

            print("        Testing required rank")
            assert [x for x in ranks if x["id"] == base_drug["rank"]]

            print("        Testing required rank tier")
            assert 1 <= base_drug["rankTier"] <= 5

            print("        Testing effects")
            assert all([[y for y in effects if y["id"] == x] for x in base_drug["effects"]])

        print("Testing ingredients")
        found_ingredient_ids: list[str] = []
        for ingredient in ingredients:
            print(f"    Testing ingredient {ingredient["id"]}")
            print("        Testing values")
            check_typed_dict(ingredient, Ingredient)

            print("        Testing duplicate")
            assert ingredient["id"] not in found_ingredient_ids
            found_ingredient_ids.append(ingredient["id"])

            print("        Testing required rank")
            assert [x for x in ranks if x["id"] == ingredient["rank"]]

            print("        Testing required rank tier")
            assert 1 <= ingredient["rankTier"] <= 5

            print("        Testing base effect")
            assert [x for x in effects if x["id"] == ingredient["baseEffect"]]

            print("        Testing transformations")
            found_from_effect_ids: list[str] = []
            for fromEffect, toEffect in ingredient["transformations"].items():
                print(f"            Testing transformation {fromEffect} -> {toEffect}")

                print("                Testing duplicate")
                assert fromEffect not in found_from_effect_ids
                found_from_effect_ids.append(fromEffect)

                print("                Testing from effect")
                assert [x for x in effects if x["id"] == fromEffect]

                print("                Testing to effect")
                assert [x for x in effects if x["id"] == toEffect]

        print("Testing effects")
        found_effect_ids: list[str] = []
        for effect in effects:
            print(f"    Testing effect {effect["id"]}")

            print("        Testing values")
            check_typed_dict(effect, Effect)

            print("        Testing duplicate")
            assert effect["id"] not in found_effect_ids
            found_effect_ids.append(effect["id"])
    except AssertionError:
        raise ValueError("Errors found in dataset")


def choose_option(question: str, options: list[str]) -> int:
    while True:
        try:
            print(f"{question}")
            for i, option in enumerate(options):
                print(f"    [{i}]: {option}")

            choice: int = int(input("Your choice: "))
            if choice >= len(options):
                raise ValueError("Not an option")
            return choice
        except Exception as e:
            print(e)


def choose_rank(ranks: list[Rank]) -> Rank:
    return ranks[choose_option("Choose a rank:", ["Back"] + [rank["displayName"] for rank in ranks]) - 1]


def choose_base_drug(base_drugs: list[BaseDrug]) -> BaseDrug:
    return base_drugs[
        choose_option("Choose a base drug:", ["Back"] + [base_drug["displayName"] for base_drug in base_drugs]) - 1
    ]


def choose_ingredient(ingredients: list[Ingredient]) -> Ingredient:
    return ingredients[
        choose_option("Choose an ingredient:", ["Back"] + [ingredient["displayName"] for ingredient in ingredients]) - 1
    ]


def choose_effect(effects: list[Effect]) -> Effect:
    return effects[choose_option("Choose an effect:", ["Back"] + [effect["displayName"] for effect in effects]) - 1]


def main():
    if __name__ != "__main__":
        return
    
    json_decoder: JSONDecoder = JSONDecoder()

    ranks: list[Rank] = json_decoder.decode(
        open("ranks.json").read(),
    )
    base_drugs: list[BaseDrug] = json_decoder.decode(
        open("baseDrugs.json").read(),
    )
    ingredients: list[Ingredient] = json_decoder.decode(
        open("ingredients.json").read(),
    )
    effects: list[Effect] = json_decoder.decode(
        open("effects.json").read(),
    )

    while True:
        try:
            match choose_option(
                "Choose an option:",
                [
                    "Exit",
                    "Reload dataset",
                    "Dump all ingredients",
                    "Dump all effects",
                    "Check dataset for errors",
                    "Test mixes",
                ],
            ):
                case 0:
                    break
                case 1:
                    ranks = json_decoder.decode(
                        open("ranks.json").read(),
                    )
                    base_drugs = json_decoder.decode(
                        open("baseDrugs.json").read(),
                    )
                    ingredients = json_decoder.decode(
                        open("ingredients.json").read(),
                    )
                    effects = json_decoder.decode(
                        open("effects.json").read(),
                    )
                case 2:
                    print(ingredients)
                case 3:
                    print(effects)
                case 4:
                    check_dataset(ranks, base_drugs, ingredients, effects)
                case 5:
                    ingredient: Ingredient = choose_ingredient(ingredients)
                    print(ingredient)
        except Exception as e:
            print("\x1b[31m" + repr(e) + "\x1b[0m")


main()
