"""Case-local hex inputs; the simulation runner binds their hashes before use."""


def hex_input(evidence, directory, name, values, width):
    values = list(values)
    if not values:
        values = [0]
    if width < 1 or any(value < 0 or value >= 1 << width for value in values):
        raise ValueError(f"Invalid {width}-bit verification input: {name}")
    path = directory / (name + ".hex")
    with path.open("x", encoding="ascii") as output:
        output.writelines(f"{value:0{(width + 3) // 4}x}\n" for value in values)
    return f'$readmemh("{evidence.relative(path)}",{name});'
