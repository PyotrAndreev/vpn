from dataclass import dataclass


def user_choose(many: set) -> int:
    for i, country in enumerate(countries, 1):
        print(f"{i}. {country}")
    choice = int(input("Select country number: ")) - 1
    return countries[choice]

# create the map of flags and numbers

({})


@dataclass
class CountryOption:




