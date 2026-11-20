from schedule1mixertypes import *
from schedule1mixerutils import *
from json import JSONDecoder


def main():
    json_decoder: JSONDecoder = JSONDecoder()

    ranks: list[Rank]
    effects: list[Effect]
    base_drugs: list[BaseDrug]
    ingredients: list[Ingredient]
    try:
        ranks, choices, effects, base_drugs, ingredients = load_dataset()
    except Exception as e:
        print_exception(e)
        exit(1)

    while True:
        try:
            match choose_one(
                "Choose an option:",
                ["Exit", "Reload dataset", "Test mixes"],
            ):
                case 0:
                    raise KeyboardInterrupt()
                case 1:
                    ranks, choices, effects, base_drugs, ingredients = load_dataset()
                case 2:
                    base_drug: BaseDrug | None = choose_base_drug(base_drugs)
                    if base_drug == None:
                        continue
                    while True:
                        try:
                            print("How many ingredients does the mix have?")
                            ingredient_count: int = int(input("Your choice: "))
                            if ingredient_count < 0:
                                print("Not an option")
                                continue
                            break
                        except Exception as e:
                            print_exception(e)
                    mix: Mix = Mix(
                        base_drug,
                        [choose_ingredient(ingredients) for x in range(ingredient_count)],
                        {choice: choose_option(choice.options) for choice in base_drug.choices},
                    )
                    print(f"""Mix: {mix}
Rank: {mix.rank_tier}
Effects: {", ".join([str(effect) for effect in mix.effects])}
Sell price: ${mix.sell_price}
Batch yield: {mix.batch_yield}
Batch price: ${mix.batch_price}
Batch sell price: ${mix.sell_price * mix.batch_yield}
Addictiveness: {mix.addictiveness * 100}%
""")

        except KeyboardInterrupt as e:
            exit()
        except Exception as e:
            print_exception(e)


if __name__ == "__main__":
    main()
