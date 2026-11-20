from schedule1mixertypes import *
from annotationlib import get_annotations
from collections.abc import Collection, Mapping
from json.decoder import JSONDecoder
from typing import Annotated, Any, ClassVar, Final, Literal, get_origin, get_args, Any, Union, NotRequired


def print_exception(e: BaseException):
    if e.__cause__ != None:
        print_exception(e.__cause__)
        print("\x1b[31mCaused: " + repr(e) + "\x1b[0m")  # Print it red
    elif e.__context__ != None and not e.__suppress_context__:
        print_exception(e.__context__)
        print("\x1b[31mCaused during handling: " + repr(e) + "\x1b[0m")  # Print it red
    else:
        print("\x1b[31mError: " + repr(e) + "\x1b[0m")  # Print it red


def print_warning(e: BaseException):
    if e.__cause__ != None:
        print_exception(e.__cause__)
        print("\x1b[33mCaused: " + repr(e) + "\x1b[0m")  # Print it yellow
    elif e.__context__ != None and not e.__suppress_context__:
        print_exception(e.__context__)
        print("\x1b[33mCaused during handling: " + repr(e) + "\x1b[0m")  # Print it yellow
    else:
        print("\x1b[33mWarning: " + repr(e) + "\x1b[0m")  # Print it yellow


def validate_type(element: Any, element_type: type = object):
    def raise_to_bool(element: Any, element_type: type) -> bool:
        try:
            validate_type(element, element_type)
        except Exception:
            return False
        return True

    def get_unwrapped_type(wrapped: type) -> type:
        type_origin = get_origin(wrapped)
        type_args = get_args(wrapped)
        if type_origin in [ClassVar, Final, Annotated, NotRequired]:
            return type_args[0]
        else:
            return wrapped

    unwrapped_type: type = get_unwrapped_type(element_type)
    unwrapped_type_origin: type | None = get_origin(unwrapped_type)
    unwrapped_type_stripped: type = unwrapped_type if unwrapped_type_origin is None else unwrapped_type_origin
    unwrapped_type_stripped_isinstance: type = (
        dict if hasattr(unwrapped_type_stripped, "__required_keys__") else unwrapped_type_stripped
    )
    unwrapped_type_annotations: dict[str, Any] = get_annotations(unwrapped_type_stripped)
    unwrapped_type_args: tuple[Any] = get_args(unwrapped_type)

    if unwrapped_type_stripped is Union:
        assert any(
            raise_to_bool(element, t) for t in get_args(unwrapped_type)
        ), f"Expected type {element_type}, got {type(element)}"
    elif unwrapped_type_stripped is Literal:
        assert any(element == x for x in get_args(unwrapped_type)), f"Expected type {element_type}, got {type(element)}"
    else:
        assert isinstance(element, unwrapped_type_stripped_isinstance), f"Expected type {element_type}, got {type(element)}"

        if issubclass(unwrapped_type_stripped, Mapping):
            if len(unwrapped_type_args) >= 2:  # Check Mapping[Keytype, Valuetype]
                for key, value in element.items():
                    try:
                        validate_type(key, unwrapped_type_args[0])
                    except Exception as e:
                        raise TypeError(f"Error while validating key type of key {key} value {repr(value)}") from e
                    try:
                        validate_type(value, unwrapped_type_args[1])
                    except Exception as e:
                        raise TypeError(f"Error while validating value type of key {key} value {repr(value)}") from e

            if hasattr(unwrapped_type_stripped, "__required_keys__"):  # Check TypedDicts
                for key, keytype in unwrapped_type_annotations.items():
                    if key in getattr(unwrapped_type_stripped, "__required_keys__", frozenset({})) or key in element:
                        assert key in element, f"Key {key} is required in {unwrapped_type_stripped}"
                        try:
                            validate_type(element[key], keytype)
                        except Exception as e:
                            raise TypeError(f"Error while validating key {key} value {repr(element[key])}") from e

        if issubclass(unwrapped_type_stripped, Collection) and len(unwrapped_type_args) >= 1:  # Check Collection[ValueType]
            for value in element:
                try:
                    validate_type(value, unwrapped_type_args[0])
                except Exception as e:
                    raise TypeError(f"Error while validating {value}") from e


def choose_one(question: str, options: list[str], *, start: int = 1) -> int:
    while True:
        try:
            print(question)
            for i, option in enumerate(options):
                print(f"    [{i + start}]: {option}")

            choice: int = int(input("Your choice: "))
            if (choice - start) >= len(options):
                raise ValueError("Not an option")
            return choice - start
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            print_exception(e)


def choose_rank(ranks: list[Rank]) -> Rank:
    return ranks[choose_one("Choose a rank:", [rank.display_name for rank in ranks])]


def choose_option(options: list[Option]) -> Option:
    return options[choose_one("Choose an option:", [option.display_name for option in options])]


def choose_base_drug(base_drugs: list[BaseDrug]) -> BaseDrug:
    return base_drugs[choose_one("Choose a base drug:", [base_drug.display_name for base_drug in base_drugs])]


def choose_ingredient(ingredients: list[Ingredient]) -> Ingredient:
    return ingredients[choose_one("Choose an ingredient:", [ingredient.display_name for ingredient in ingredients])]


def choose_effect(effects: list[Effect]) -> Effect:
    return effects[choose_one("Choose an effect:", [effect.display_name for effect in effects])]


def load_dataset() -> tuple[list[Rank], list[Choice], list[Effect], list[BaseDrug], list[Ingredient]]:
    def json_basic_checks(
        elements: list[JSONRank] | list[JSONChoice] | list[JSONEffect] | list[JSONBaseDrug] | list[JSONIngredient],
        elementtype: type,
        elementtypestr: str,
    ):
        found_ids: list[str] = []
        for element in elements:
            try:
                validate_type(element, elementtype)
            except Exception as e:
                try:
                    raise ValueError(f"Error while validating {elementtypestr} {element["id"]}") from e
                except KeyError:
                    raise ValueError(f"Error while validating {elementtypestr} <unknown id>") from e
            assert element["id"] not in found_ids, f"Found duplicate {elementtypestr}: {element["id"]}"
            found_ids.append(element["id"])

    json_decoder: JSONDecoder = JSONDecoder()
    try:
        json_ranks: list[JSONRank] = json_decoder.decode(open("ranks.json").read())
        json_choices: list[JSONChoice] = json_decoder.decode(open("choices.json").read())
        json_effects: list[JSONEffect] = json_decoder.decode(open("effects.json").read())
        json_base_drugs: list[JSONBaseDrug] = json_decoder.decode(open("baseDrugs.json").read())
        json_ingredients: list[JSONIngredient] = json_decoder.decode(open("ingredients.json").read())
    except OSError as e:
        raise RuntimeError("Couldn't load dataset") from e

    ranks: list[Rank] = []
    choices: list[Choice] = []
    effects: list[Effect] = []
    base_drugs: list[BaseDrug] = []
    ingredients: list[Ingredient] = []

    try:
        json_basic_checks(json_ranks, JSONRank, "rank")
        json_basic_checks(json_choices, JSONChoice, "choice")
        json_basic_checks(json_effects, JSONEffect, "effect")
        json_basic_checks(json_base_drugs, JSONBaseDrug, "base drug")
        json_basic_checks(json_ingredients, JSONIngredient, "ingredient")

        for json_rank in json_ranks:
            if json_rank["tierXp"] < 1:
                raise ValueError(f"Rank {json_rank["id"]} has less than 1 xp per tier")

        ranks = [Rank.from_json(json_rank) for json_rank in json_ranks]
        choices = [Choice.from_json(json_choice, ranks) for json_choice in json_choices]
        effects = [Effect.from_json(json_effect) for json_effect in json_effects]
        base_drugs = [BaseDrug.from_json(json_base_drug, choices, ranks, effects) for json_base_drug in json_base_drugs]
        ingredients = [Ingredient.from_json(json_ingredient, ranks, effects) for json_ingredient in json_ingredients]

    except Exception as e:
        raise ValueError("Errors found in dataset") from e
    return ranks, choices, effects, base_drugs, ingredients
