"""Generate deliberately hard questions that target ~30-70% accuracy on 9B models.

These are designed around known failure modes of small LLMs:
- Carrying errors in multi-digit arithmetic
- Tracking sign changes through operations
- Resisting intuitive-but-wrong answers (CRT-style)
- Multi-hop reasoning with distractors
- Counting/tracking with frequent state changes
"""

import json
import random


def multi_digit_carry(seed: int) -> dict:
    """Multi-digit multiplication requiring careful carrying."""
    rng = random.Random(seed)
    a = rng.randint(13, 49)
    b = rng.randint(13, 49)
    answer = a * b

    question = f"What is {a} × {b}? Give only the number."
    return {
        "id": f"hard_multiply_{seed}",
        "question": question,
        "answer": str(answer),
        "answer_type": "numeric",
        "domain": "math",
        "steps": 3,
        "template": "multi_digit_carry",
        "seed": seed,
    }


def negative_tracking(seed: int) -> dict:
    """Operations with negative numbers requiring sign tracking."""
    rng = random.Random(seed)
    start = rng.randint(-20, 20)
    ops = []
    val = start
    for _ in range(4):
        op = rng.choice(["add", "subtract", "multiply"])
        n = rng.randint(2, 12)
        if op == "add":
            val += n
            ops.append(f"add {n}")
        elif op == "subtract":
            val -= n
            ops.append(f"subtract {n}")
        else:
            val *= rng.choice([-1, 2, -2])
            if val == start * -1:
                ops.append("multiply by -1")
            elif val == start * 2:
                ops.append("multiply by 2")
            else:
                ops.append(f"multiply by {rng.choice([-1, 2, -2])}")
                # Recalculate
                val = start
                for o in ops:
                    if o.startswith("add"):
                        val += int(o.split()[-1])
                    elif o.startswith("subtract"):
                        val -= int(o.split()[-1])
                    elif o.startswith("multiply"):
                        val *= int(o.split()[-1])

    steps = [f"Start with {start}."]
    for o in ops:
        steps.append(f"Then {o}.")
    steps.append("What is the final result?")

    return {
        "id": f"hard_negative_{seed}",
        "question": " ".join(steps),
        "answer": str(val),
        "answer_type": "numeric",
        "domain": "math",
        "steps": 4,
        "template": "negative_tracking",
        "seed": seed,
    }


def bat_ball_variant(seed: int) -> dict:
    """Cognitive reflection test variants — intuitive answer is wrong."""
    rng = random.Random(seed)
    templates = [
        {
            "q": "A notebook and a pen cost ${total} in total. The notebook costs ${diff} more than the pen. How much does the pen cost?",
            "params": lambda r: {"total": r.choice([1.10, 2.20, 3.30, 5.50]), "diff": None},
            "answer": lambda p: (p["total"] - p["diff"]) / 2,
            "setup": lambda r, p: p.update({"diff": p["total"] - 2 * r.choice([0.05, 0.10, 0.15, 0.20])}),
        },
        {
            "q": "If it takes {n} machines {n} minutes to make {n} widgets, how many minutes would it take {m} machines to make {m} widgets?",
            "params": lambda r: {"n": r.choice([5, 7, 8, 10]), "m": r.choice([50, 100, 200])},
            "answer": lambda p: p["n"],  # Same time regardless of scale
        },
        {
            "q": "In a lake, there is a patch of lily pads. Every day, the patch doubles in size. If it takes {days} days for the patch to cover the entire lake, how many days would it take for the patch to cover half of the lake?",
            "params": lambda r: {"days": r.choice([30, 48, 60, 100])},
            "answer": lambda p: p["days"] - 1,
        },
    ]

    t = rng.choice(templates)
    params = t["params"](rng)
    if "setup" in t:
        t["setup"](rng, params)
    answer = t["answer"](params)

    question = t["q"].format(**params)
    answer_str = f"{answer:.2f}" if isinstance(answer, float) and answer != int(answer) else str(int(answer))

    return {
        "id": f"hard_crt_{seed}",
        "question": question,
        "answer": answer_str,
        "answer_type": "numeric",
        "domain": "math",
        "steps": 2,
        "template": "bat_ball_variant",
        "seed": seed,
    }


def modular_arithmetic(seed: int) -> dict:
    """What is the remainder when X is divided by Y?"""
    rng = random.Random(seed)
    # Make it non-trivial
    base = rng.randint(2, 9)
    exp = rng.randint(3, 8)
    mod = rng.choice([3, 5, 7, 11, 13])
    val = pow(base, exp, mod)

    question = f"What is the remainder when {base}^{exp} (that is, {base} raised to the power {exp}) is divided by {mod}?"
    return {
        "id": f"hard_modular_{seed}",
        "question": question,
        "answer": str(val),
        "answer_type": "numeric",
        "domain": "math",
        "steps": 3,
        "template": "modular_arithmetic",
        "seed": seed,
    }


def boolean_satisfiability(seed: int) -> dict:
    """Given variable assignments, evaluate a boolean expression."""
    rng = random.Random(seed)
    vars = {"P": rng.choice([True, False]),
            "Q": rng.choice([True, False]),
            "R": rng.choice([True, False])}

    expressions = [
        ("(P AND Q) OR (NOT R)", lambda v: (v["P"] and v["Q"]) or (not v["R"])),
        ("(P OR Q) AND (NOT P OR R)", lambda v: (v["P"] or v["Q"]) and (not v["P"] or v["R"])),
        ("NOT (P AND Q) OR (Q AND R)", lambda v: (not (v["P"] and v["Q"])) or (v["Q"] and v["R"])),
        ("(P AND NOT Q) OR (Q AND NOT R) OR (R AND NOT P)",
         lambda v: (v["P"] and not v["Q"]) or (v["Q"] and not v["R"]) or (v["R"] and not v["P"])),
        ("NOT (P OR Q) AND R", lambda v: (not (v["P"] or v["Q"])) and v["R"]),
    ]

    expr_text, expr_fn = rng.choice(expressions)
    result = expr_fn(vars)

    assignments = ", ".join(f"{k} = {str(v).upper()}" for k, v in vars.items())
    question = f"Given {assignments}, evaluate the following expression:\n{expr_text}\n\nIs the result TRUE or FALSE?"
    return {
        "id": f"hard_boolean_{seed}",
        "question": question,
        "answer": "true" if result else "false",
        "answer_type": "exact",
        "domain": "logic",
        "steps": 3,
        "template": "boolean_satisfiability",
        "seed": seed,
    }


def counting_constraint(seed: int) -> dict:
    """Count objects satisfying multiple constraints."""
    rng = random.Random(seed)
    n = rng.randint(20, 50)
    div1 = rng.choice([2, 3, 4, 5])
    div2 = rng.choice([d for d in [3, 4, 5, 6, 7] if d != div1])

    # Count numbers from 1 to n divisible by div1 OR div2 (inclusion-exclusion)
    from math import gcd
    lcm = div1 * div2 // gcd(div1, div2)
    count = n // div1 + n // div2 - n // lcm

    question = (
        f"How many integers from 1 to {n} (inclusive) are divisible by {div1} or {div2} (or both)?"
    )
    return {
        "id": f"hard_counting_{seed}",
        "question": question,
        "answer": str(count),
        "answer_type": "numeric",
        "domain": "math",
        "steps": 3,
        "template": "counting_constraint",
        "seed": seed,
    }


def long_object_tracking(seed: int) -> dict:
    """Track object through 7-10 swaps."""
    rng = random.Random(seed)
    n_cups = rng.choice([4, 5])
    n_swaps = rng.randint(7, 10)

    labels = [f"Box {i+1}" for i in range(n_cups)]
    ball_pos = rng.randint(0, n_cups - 1)

    instructions = [f"A ball is placed in {labels[ball_pos]}."]
    for _ in range(n_swaps):
        i, j = rng.sample(range(n_cups), 2)
        instructions.append(f"Swap {labels[i]} and {labels[j]}.")
        if ball_pos == i:
            ball_pos = j
        elif ball_pos == j:
            ball_pos = i

    question = "\n".join(instructions) + f"\n\nWhich box is the ball in now?"
    return {
        "id": f"hard_tracking_{seed}",
        "question": question,
        "answer": labels[ball_pos],
        "answer_type": "exact",
        "domain": "spatial",
        "steps": n_swaps,
        "template": "long_object_tracking",
        "seed": seed,
    }


def grid_navigation_hard(seed: int) -> dict:
    """8-step navigation with diagonal moves and backtracking."""
    rng = random.Random(seed)
    directions = {
        "north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0),
        "northeast": (1, 1), "southwest": (-1, -1),
    }
    n_steps = rng.randint(7, 10)
    dir_names = list(directions.keys())
    x, y = 0, 0
    steps = []
    for _ in range(n_steps):
        d = rng.choice(dir_names)
        amt = rng.randint(1, 4)
        dx, dy = directions[d]
        x += dx * amt
        y += dy * amt
        steps.append(f"Go {d} {amt} step{'s' if amt > 1 else ''}.")

    # Ask for Manhattan distance from origin
    dist = abs(x) + abs(y)
    question = (
        f"Starting at (0,0), follow these directions:\n"
        + "\n".join(steps)
        + f"\n\nWhat is your Manhattan distance from the origin? "
        f"(Manhattan distance = |x| + |y|)"
    )
    return {
        "id": f"hard_grid_{seed}",
        "question": question,
        "answer": str(dist),
        "answer_type": "numeric",
        "domain": "spatial",
        "steps": n_steps,
        "template": "grid_navigation_hard",
        "seed": seed,
    }


HARD_GENERATORS = [
    multi_digit_carry,
    negative_tracking,
    bat_ball_variant,
    modular_arithmetic,
    boolean_satisfiability,
    counting_constraint,
    long_object_tracking,
    grid_navigation_hard,
]


def generate_hard_questions(count: int, start_seed: int = 5000) -> list[dict]:
    questions = []
    per_template = max(1, count // len(HARD_GENERATORS))
    seed = start_seed
    for gen in HARD_GENERATORS:
        for _ in range(per_template):
            q = gen(seed)
            questions.append(q)
            seed += 1
    while len(questions) < count:
        gen = HARD_GENERATORS[seed % len(HARD_GENERATORS)]
        q = gen(seed)
        questions.append(q)
        seed += 1
    return questions[:count]


if __name__ == "__main__":
    qs = generate_hard_questions(10)
    for q in qs:
        print(json.dumps(q))
