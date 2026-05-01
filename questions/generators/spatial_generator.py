"""Generate spatial/pattern reasoning questions for the thinking-token experiment.

Produces BBH-navigate-style grid navigation and object-tracking problems.
"""

import json
import random


DIRECTIONS = {
    "north": (0, 1),
    "south": (0, -1),
    "east": (1, 0),
    "west": (-1, 0),
}

OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}


def grid_navigation(seed: int) -> dict:
    """Follow a sequence of directions from the origin. Where do you end up?"""
    rng = random.Random(seed)
    n_steps = rng.randint(4, 7)
    dirs = list(DIRECTIONS.keys())
    steps = [rng.choice(dirs) for _ in range(n_steps)]
    amounts = [rng.randint(1, 5) for _ in range(n_steps)]

    x, y = 0, 0
    instructions = []
    for d, a in zip(steps, amounts):
        dx, dy = DIRECTIONS[d]
        x += dx * a
        y += dy * a
        instructions.append(f"Go {d} {a} steps.")

    # Ask for final position or specific coordinate
    ask_x = rng.random() < 0.5
    if ask_x:
        answer = str(x)
        ask_text = "What is your final east-west position? (East is positive, West is negative)"
    else:
        answer = str(y)
        ask_text = "What is your final north-south position? (North is positive, South is negative)"

    question = (
        f"Starting at position (0, 0), follow these directions:\n"
        + "\n".join(instructions)
        + f"\n\n{ask_text}"
    )
    return {
        "question": question,
        "answer": answer,
        "answer_type": "numeric",
        "domain": "spatial",
        "steps": n_steps,
        "template": "grid_navigation",
        "seed": seed,
    }


def return_to_origin(seed: int) -> dict:
    """After a sequence of moves, what single move returns you to the origin?"""
    rng = random.Random(seed)
    n_steps = rng.randint(3, 5)
    dirs = list(DIRECTIONS.keys())
    steps = [rng.choice(dirs) for _ in range(n_steps)]
    amounts = [rng.randint(1, 4) for _ in range(n_steps)]

    x, y = 0, 0
    instructions = []
    for d, a in zip(steps, amounts):
        dx, dy = DIRECTIONS[d]
        x += dx * a
        y += dy * a
        instructions.append(f"Go {d} {a} steps.")

    # Need to go (-x, -y) to return
    # Express as direction + distance
    parts = []
    if x > 0:
        parts.append(f"west {x} steps")
    elif x < 0:
        parts.append(f"east {abs(x)} steps")
    if y > 0:
        parts.append(f"south {y} steps")
    elif y < 0:
        parts.append(f"north {abs(y)} steps")

    answer = " and ".join(parts) if parts else "stay"

    # For easier extraction, just ask about one axis
    if abs(x) >= abs(y) and x != 0:
        if x > 0:
            answer = str(x)
            question_suffix = "How many steps west must you go to return to x=0?"
        else:
            answer = str(abs(x))
            question_suffix = "How many steps east must you go to return to x=0?"
    elif y != 0:
        if y > 0:
            answer = str(y)
            question_suffix = "How many steps south must you go to return to y=0?"
        else:
            answer = str(abs(y))
            question_suffix = "How many steps north must you go to return to y=0?"
    else:
        answer = "0"
        question_suffix = "How many steps in any direction must you go to return to the origin?"

    question = (
        f"Starting at position (0, 0), follow these directions:\n"
        + "\n".join(instructions)
        + f"\n\n{question_suffix}"
    )
    return {
        "question": question,
        "answer": answer,
        "answer_type": "numeric",
        "domain": "spatial",
        "steps": n_steps + 1,
        "template": "return_to_origin",
        "seed": seed,
    }


def object_tracking(seed: int) -> dict:
    """Track which cup/box an object is under after a series of swaps."""
    rng = random.Random(seed)
    n_cups = rng.choice([3, 4, 5])
    n_swaps = rng.randint(3, 6)

    labels = [f"Cup {chr(65+i)}" for i in range(n_cups)]
    ball_pos = rng.randint(0, n_cups - 1)

    instructions = [f"A ball is placed under {labels[ball_pos]}."]
    for _ in range(n_swaps):
        i, j = rng.sample(range(n_cups), 2)
        instructions.append(f"{labels[i]} and {labels[j]} are swapped.")
        if ball_pos == i:
            ball_pos = j
        elif ball_pos == j:
            ball_pos = i

    answer = labels[ball_pos]
    question = (
        "\n".join(instructions)
        + f"\n\nWhich cup is the ball under now?"
    )
    return {
        "question": question,
        "answer": answer,
        "answer_type": "exact",
        "domain": "spatial",
        "steps": n_swaps,
        "template": "object_tracking",
        "seed": seed,
    }


def rotation_tracking(seed: int) -> dict:
    """A person faces north, then turns. Which direction are they facing?"""
    rng = random.Random(seed)
    compass = ["north", "east", "south", "west"]
    n_turns = rng.randint(3, 6)
    facing = 0  # 0=north, 1=east, 2=south, 3=west

    instructions = ["You start facing north."]
    for _ in range(n_turns):
        turn = rng.choice(["left", "right"])
        amount = rng.choice([90, 180, 270])
        if turn == "right":
            facing = (facing + amount // 90) % 4
        else:
            facing = (facing - amount // 90) % 4
        instructions.append(f"Turn {turn} {amount} degrees.")

    answer = compass[facing]
    question = (
        "\n".join(instructions)
        + "\n\nWhich direction are you now facing?"
    )
    return {
        "question": question,
        "answer": answer,
        "answer_type": "exact",
        "domain": "spatial",
        "steps": n_turns,
        "template": "rotation_tracking",
        "seed": seed,
    }


SPATIAL_GENERATORS = [
    grid_navigation,
    return_to_origin,
    object_tracking,
    rotation_tracking,
]


def generate_spatial_questions(count: int, start_seed: int = 4000) -> list[dict]:
    """Generate `count` spatial/pattern questions."""
    questions = []
    per_template = max(1, count // len(SPATIAL_GENERATORS))
    seed = start_seed

    for gen in SPATIAL_GENERATORS:
        for _ in range(per_template):
            q = gen(seed)
            q["id"] = f"spatial_{q['template']}_{seed}"
            questions.append(q)
            seed += 1

    while len(questions) < count:
        gen = SPATIAL_GENERATORS[seed % len(SPATIAL_GENERATORS)]
        q = gen(seed)
        q["id"] = f"spatial_{q['template']}_{seed}"
        questions.append(q)
        seed += 1

    return questions[:count]


if __name__ == "__main__":
    qs = generate_spatial_questions(10)
    for q in qs:
        print(json.dumps(q))
