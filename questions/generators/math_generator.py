"""Generate math reasoning questions calibrated for ~30-70% accuracy on 9B models.

Key difficulty levers:
- Multi-step (3-5 operations)
- Larger numbers requiring careful tracking
- Mixed operations (add/subtract/multiply/divide)
- Distractor information
- Percentage/ratio chains that require sequential computation
"""

import json
import random

NAMES = [
    "Alice", "Bob", "Carlos", "Diana", "Emma", "Frank", "Grace", "Hao",
    "Iris", "Jamal", "Kim", "Leo", "Maya", "Nora", "Oscar", "Priya",
    "Quinn", "Raj", "Sofia", "Tom", "Uma", "Victor", "Wendy", "Xavier",
    "Yuki", "Zara",
]

ITEMS = [
    "apples", "books", "cookies", "pencils", "marbles", "stickers",
    "flowers", "stamps", "coins", "cards", "toys", "shells",
]


def _pick(lst, rng, exclude=None):
    choices = [x for x in lst if x != exclude] if exclude else lst
    return rng.choice(choices)


def chained_operations(seed: int) -> dict:
    """4-step chain: start, then series of add/subtract/multiply operations."""
    rng = random.Random(seed)
    name = _pick(NAMES, rng)
    item = _pick(ITEMS, rng)
    start = rng.randint(12, 50)
    ops = []
    val = start

    for _ in range(4):
        op = rng.choice(["add", "subtract", "multiply", "give_fraction"])
        if op == "add":
            n = rng.randint(5, 25)
            val += n
            ops.append(f"finds {n} more {item}")
        elif op == "subtract":
            n = rng.randint(1, min(15, val - 1))
            val -= n
            ops.append(f"gives away {n} {item}")
        elif op == "multiply":
            n = rng.choice([2, 3])
            val *= n
            ops.append(f"trades each {item[:-1] if item.endswith('s') else item} for {n} new ones")
        elif op == "give_fraction":
            frac = rng.choice([2, 3, 4])
            given = val // frac
            val -= given
            ops.append(f"gives {name}'s friend one-{['half', 'third', 'quarter'][frac-2]} of the {item}")

    steps = [f"{name} starts with {start} {item}."]
    for o in ops:
        steps.append(f"Then {name} {o}.")
    steps.append(f"How many {item} does {name} have now?")

    return {
        "question": " ".join(steps),
        "answer": str(val),
        "answer_type": "numeric",
        "domain": "math",
        "steps": 4,
        "template": "chained_operations",
        "seed": seed,
    }


def multi_person_split(seed: int) -> dict:
    """3 people contribute different amounts, split costs, compute who owes whom."""
    rng = random.Random(seed)
    names = rng.sample(NAMES, 3)
    amounts = [rng.randint(15, 80) for _ in range(3)]
    total = sum(amounts)
    fair_share = total / 3

    # Ask how much the person who paid most is owed
    max_idx = amounts.index(max(amounts))
    owed = amounts[max_idx] - fair_share

    question = (
        f"{names[0]}, {names[1]}, and {names[2]} go out to eat. "
        f"{names[0]} pays ${amounts[0]}, {names[1]} pays ${amounts[1]}, "
        f"and {names[2]} pays ${amounts[2]}. "
        f"They agree to split the total bill equally. "
        f"How much is {names[max_idx]} owed by the other two combined? "
        f"Give your answer as a number rounded to two decimal places."
    )

    answer = f"{owed:.2f}"
    if owed == int(owed):
        answer = str(int(owed))

    return {
        "question": question,
        "answer": answer,
        "answer_type": "numeric",
        "domain": "math",
        "steps": 3,
        "template": "multi_person_split",
        "seed": seed,
    }


def compound_percentage(seed: int) -> dict:
    """Sequential percentage changes: increase by X%, decrease by Y%, tax of Z%."""
    rng = random.Random(seed)
    price = rng.choice([40, 60, 75, 80, 100, 120, 150, 200, 250])
    changes = []
    val = float(price)

    n_changes = rng.randint(3, 4)
    for _ in range(n_changes):
        pct = rng.choice([5, 8, 10, 12, 15, 20, 25, 30])
        direction = rng.choice(["increase", "decrease"])
        if direction == "increase":
            val *= (1 + pct / 100)
            changes.append(f"increased by {pct}%")
        else:
            val *= (1 - pct / 100)
            changes.append(f"decreased by {pct}%")

    answer = round(val, 2)
    answer_str = f"{answer:.2f}"
    if answer == int(answer):
        answer_str = str(int(answer))

    steps_text = f"A product starts at ${price}. Its price is "
    steps_text += ", then ".join(changes) + ". "
    steps_text += "What is the final price? Round to the nearest cent."

    return {
        "question": steps_text,
        "answer": answer_str,
        "answer_type": "numeric",
        "domain": "math",
        "steps": n_changes + 1,
        "template": "compound_percentage",
        "seed": seed,
    }


def system_of_equations_hard(seed: int) -> dict:
    """Harder system: 2 unknowns with larger coefficients, asks for expression."""
    rng = random.Random(seed)
    x = rng.randint(2, 12)
    y = rng.randint(2, 12)
    a, b = rng.randint(2, 7), rng.randint(2, 7)
    d, e = rng.randint(2, 7), rng.randint(2, 7)
    while a * e == b * d:
        e = rng.randint(2, 7)

    c1 = a * x + b * y
    c2 = d * x + e * y

    # Ask for x + y or x * y instead of just x
    expr = rng.choice(["sum", "product", "difference"])
    if expr == "sum":
        answer = x + y
        ask = "x + y"
    elif expr == "product":
        answer = x * y
        ask = "x × y"
    else:
        answer = abs(x - y)
        ask = "|x - y|"

    question = (
        f"Given the system of equations:\n"
        f"  {a}x + {b}y = {c1}\n"
        f"  {d}x + {e}y = {c2}\n"
        f"What is the value of {ask}?"
    )
    return {
        "question": question,
        "answer": str(answer),
        "answer_type": "numeric",
        "domain": "math",
        "steps": 4,
        "template": "system_of_equations_hard",
        "seed": seed,
    }


def work_rate_problem(seed: int) -> dict:
    """A can do a job in X hours, B in Y hours. Working together, then A leaves. How long total?"""
    rng = random.Random(seed)
    names = rng.sample(NAMES, 2)
    rate_a = rng.randint(4, 12)  # hours for A alone
    rate_b = rng.randint(4, 12)  # hours for B alone
    together_time = rng.randint(1, min(rate_a, rate_b) - 1)

    # Work done together
    done_together = together_time * (1/rate_a + 1/rate_b)
    remaining = 1 - done_together

    if remaining <= 0:
        # Job is done, ask how much work is left (0) or adjust
        answer = 0
        question = (
            f"{names[0]} can paint a house in {rate_a} hours. "
            f"{names[1]} can paint the same house in {rate_b} hours. "
            f"They work together for {together_time} hours. "
            f"What fraction of the house is still unpainted? Express as a simplified fraction or 0."
        )
        answer_str = "0"
    else:
        # B finishes alone
        b_alone_time = remaining * rate_b
        total = together_time + b_alone_time
        answer = round(total, 2)
        answer_str = f"{answer:.2f}" if answer != int(answer) else str(int(answer))

        question = (
            f"{names[0]} can paint a house in {rate_a} hours. "
            f"{names[1]} can paint the same house in {rate_b} hours. "
            f"They work together for {together_time} hours, then {names[0]} leaves. "
            f"How many total hours does it take to finish the entire house? "
            f"Round to two decimal places."
        )

    return {
        "question": question,
        "answer": answer_str,
        "answer_type": "numeric",
        "domain": "math",
        "steps": 4,
        "template": "work_rate_problem",
        "seed": seed,
    }


def profit_loss_chain(seed: int) -> dict:
    """Buy at X, sell at Y% profit, buy back at Z% less, sell again. Net profit?"""
    rng = random.Random(seed)
    name = _pick(NAMES, rng)
    buy1 = rng.choice([100, 150, 200, 250, 300, 400, 500])
    profit_pct = rng.choice([10, 15, 20, 25, 30])
    sell1 = buy1 * (1 + profit_pct / 100)
    discount_pct = rng.choice([5, 10, 15, 20])
    buy2 = sell1 * (1 - discount_pct / 100)
    profit2_pct = rng.choice([10, 15, 20, 25])
    sell2 = buy2 * (1 + profit2_pct / 100)

    net = sell1 - buy1 + sell2 - buy2
    answer = round(net, 2)
    answer_str = f"{answer:.2f}" if answer != int(answer) else str(int(answer))

    question = (
        f"{name} buys an item for ${buy1}. "
        f"{name} sells it at a {profit_pct}% profit. "
        f"Then {name} buys it back at {discount_pct}% less than the selling price. "
        f"Finally, {name} sells it again at a {profit2_pct}% profit. "
        f"What is {name}'s total net profit from both transactions?"
    )
    return {
        "question": question,
        "answer": answer_str,
        "answer_type": "numeric",
        "domain": "math",
        "steps": 5,
        "template": "profit_loss_chain",
        "seed": seed,
    }


def mixture_problem(seed: int) -> dict:
    """Mix two solutions of different concentrations. What's the final concentration?"""
    rng = random.Random(seed)
    vol1 = rng.randint(100, 500)
    conc1 = rng.randint(10, 40)
    vol2 = rng.randint(100, 500)
    conc2 = rng.randint(50, 90)

    total_solute = vol1 * conc1 / 100 + vol2 * conc2 / 100
    total_vol = vol1 + vol2
    final_conc = total_solute / total_vol * 100
    answer = round(final_conc, 1)
    answer_str = f"{answer}" if answer != int(answer) else str(int(answer))

    question = (
        f"You mix {vol1} ml of a {conc1}% salt solution with "
        f"{vol2} ml of a {conc2}% salt solution. "
        f"What is the concentration of the resulting mixture? "
        f"Express as a percentage rounded to one decimal place."
    )
    return {
        "question": question,
        "answer": answer_str,
        "answer_type": "numeric",
        "domain": "math",
        "steps": 3,
        "template": "mixture_problem",
        "seed": seed,
    }


MATH_GENERATORS = [
    chained_operations,
    multi_person_split,
    compound_percentage,
    system_of_equations_hard,
    work_rate_problem,
    profit_loss_chain,
    mixture_problem,
]


def generate_math_questions(count: int, start_seed: int = 1000) -> list[dict]:
    questions = []
    per_template = max(1, count // len(MATH_GENERATORS))
    seed = start_seed
    for gen in MATH_GENERATORS:
        for _ in range(per_template):
            q = gen(seed)
            q["id"] = f"math_{q['template']}_{seed}"
            questions.append(q)
            seed += 1
    while len(questions) < count:
        gen = MATH_GENERATORS[seed % len(MATH_GENERATORS)]
        q = gen(seed)
        q["id"] = f"math_{q['template']}_{seed}"
        questions.append(q)
        seed += 1
    return questions[:count]


if __name__ == "__main__":
    qs = generate_math_questions(10)
    for q in qs:
        print(json.dumps(q))
