"""Generate logical deduction questions calibrated for ~30-70% accuracy on 9B models.

Difficulty levers:
- Longer inference chains (4-6 hops)
- Negation and contradiction
- Distractor facts that are irrelevant
- Mixed quantifiers (all, some, none)
- Requires tracking multiple entity states
"""

import json
import random

ENTITIES = [
    "the cat", "the dog", "the bird", "the fish", "the rabbit",
    "the tiger", "the bear", "the lion", "the wolf", "the eagle",
    "the fox", "the deer", "the mouse", "the owl", "the snake",
]

PROPERTIES = [
    "red", "blue", "green", "big", "small", "fast", "slow",
    "cold", "hot", "young", "old", "quiet", "loud", "kind", "brave",
    "strong", "weak", "smart", "gentle", "fierce",
]


def _pick_unique(lst, n, rng):
    return rng.sample(lst, min(n, len(lst)))


def long_chain_with_distractors(seed: int, chain_len: int = 5) -> dict:
    """Long chain with distractor rules that don't connect."""
    rng = random.Random(seed)
    entity = rng.choice(ENTITIES)
    props = _pick_unique(PROPERTIES, chain_len + 3, rng)
    chain_props = props[:chain_len + 1]
    distractor_props = props[chain_len + 1:]

    facts = [f"{entity} is {chain_props[0]}."]
    rules = []
    for i in range(chain_len):
        rules.append(f"If something is {chain_props[i]}, then it is {chain_props[i+1]}.")

    # Add distractor rules
    other_entity = rng.choice([e for e in ENTITIES if e != entity])
    facts.append(f"{other_entity} is {distractor_props[0]}.")
    if len(distractor_props) > 1:
        rules.append(f"If something is {distractor_props[0]}, then it is {distractor_props[1]}.")

    # Shuffle rules to make order non-obvious
    rng.shuffle(rules)

    ask_valid = rng.random() < 0.5
    if ask_valid:
        # Ask about end of chain (true)
        target = chain_props[-1]
        answer = "true"
    else:
        # Ask about a distractor property (false for this entity)
        target = distractor_props[-1] if len(distractor_props) > 1 else distractor_props[0]
        answer = "false"

    premises = "\n".join(facts + rules)
    question = (
        f"Given the following facts and rules:\n{premises}\n\n"
        f"True or false: \"{entity} is {target}\"?"
    )
    return {
        "question": question,
        "answer": answer,
        "answer_type": "exact",
        "domain": "logic",
        "steps": chain_len,
        "template": f"long_chain_{chain_len}",
        "seed": seed,
    }


def negation_chain(seed: int) -> dict:
    """Chain with negations: A→B, B→¬C, ¬C→D. Is entity C? Is entity D?"""
    rng = random.Random(seed)
    entity = rng.choice(ENTITIES)
    props = _pick_unique(PROPERTIES, 6, rng)

    facts = [f"{entity} is {props[0]}."]
    rules = [
        f"If something is {props[0]}, then it is {props[1]}.",
        f"If something is {props[1]}, then it is not {props[2]}.",
        f"If something is not {props[2]}, then it is {props[3]}.",
        f"If something is {props[3]}, then it is not {props[4]}.",
    ]

    # Add a distractor
    other = rng.choice([e for e in ENTITIES if e != entity])
    facts.append(f"{other} is {props[2]}.")
    rules.append(f"If something is {props[2]}, then it is {props[5]}.")
    rng.shuffle(rules)

    choice = rng.randint(0, 3)
    targets = [
        (props[1], "true"),    # direct
        (props[2], "false"),   # negated
        (props[3], "true"),    # through negation
        (props[4], "false"),   # double negation chain end
    ]
    target_prop, answer = targets[choice]

    premises = "\n".join(facts + rules)
    question = (
        f"Given the following facts and rules:\n{premises}\n\n"
        f"True or false: \"{entity} is {target_prop}\"?"
    )
    return {
        "question": question,
        "answer": answer,
        "answer_type": "exact",
        "domain": "logic",
        "steps": choice + 2,
        "template": "negation_chain",
        "seed": seed,
    }


def multi_entity_tracking(seed: int) -> dict:
    """Track properties of 3-4 entities through shared rules."""
    rng = random.Random(seed)
    entities = _pick_unique(ENTITIES, 4, rng)
    props = _pick_unique(PROPERTIES, 8, rng)

    facts = [
        f"{entities[0]} is {props[0]}.",
        f"{entities[1]} is {props[1]}.",
        f"{entities[2]} is {props[2]}.",
        f"{entities[3]} is {props[0]}.",  # shares property with entity 0
    ]

    rules = [
        f"If something is {props[0]}, then it is {props[3]}.",
        f"If something is {props[1]}, then it is {props[4]}.",
        f"If something is {props[3]} and {props[2]}, then it is {props[5]}.",
        f"If something is {props[4]}, then it is not {props[3]}.",
    ]
    rng.shuffle(rules)

    # entity 0: props[0] → props[3] (but not props[5] because not props[2])
    # entity 1: props[1] → props[4] → not props[3]
    # entity 2: props[2] only (no chain)
    # entity 3: props[0] → props[3] (same as entity 0)

    queries = [
        (entities[0], props[3], "true"),     # direct rule
        (entities[1], props[3], "false"),     # negated via props[4]
        (entities[2], props[5], "false"),     # needs both props[3] and props[2]
        (entities[3], props[3], "true"),      # shares with entity 0
        (entities[0], props[5], "false"),     # has props[3] but not props[2]
    ]

    target_entity, target_prop, answer = rng.choice(queries)

    premises = "\n".join(facts + rules)
    question = (
        f"Given the following facts and rules:\n{premises}\n\n"
        f"True or false: \"{target_entity} is {target_prop}\"?"
    )
    return {
        "question": question,
        "answer": answer,
        "answer_type": "exact",
        "domain": "logic",
        "steps": 3,
        "template": "multi_entity_tracking",
        "seed": seed,
    }


def ordering_hard(seed: int) -> dict:
    """5-element ordering with indirect comparisons and a reversal."""
    rng = random.Random(seed)
    names = rng.sample(
        ["Alice", "Bob", "Carlos", "Diana", "Emma", "Frank", "Grace", "Hao"],
        5,
    )
    comp_type = rng.choice([
        ("taller", "tallest", "shortest"),
        ("older", "oldest", "youngest"),
        ("faster", "fastest", "slowest"),
    ])
    comp, sup, inv_sup = comp_type

    # Present facts in scrambled order, including indirect ones
    pairs = list(zip(names[:-1], names[1:]))
    rng.shuffle(pairs)

    facts = []
    for a, b in pairs:
        # Randomly use direct or inverse phrasing
        if rng.random() < 0.3:
            facts.append(f"{b} is not as {comp.replace('er', '')} as {a}.")
        else:
            facts.append(f"{a} is {comp} than {b}.")

    ask_pos = rng.randint(0, 4)
    answer = names[ask_pos]

    if ask_pos == 0:
        q_text = f"Who is the {sup}?"
    elif ask_pos == 4:
        q_text = f"Who is the {inv_sup}?"
    else:
        q_text = f"Who is the {rng.choice([2, 3])}{['nd', 'rd'][rng.choice([0,1])]} {sup}?"
        # Simplify: just ask for a specific position
        pos = ask_pos + 1
        ordinal = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th"}[pos]
        q_text = f"If they are ranked from {sup} to {inv_sup}, who is {ordinal}?"

    premises = " ".join(facts)
    question = f"{premises} {q_text}"

    return {
        "question": question,
        "answer": answer,
        "answer_type": "exact",
        "domain": "logic",
        "steps": 4,
        "template": "ordering_hard",
        "seed": seed,
    }


def knights_and_knaves(seed: int) -> dict:
    """Classic puzzle: knights always tell truth, knaves always lie."""
    rng = random.Random(seed)
    names = rng.sample(["Alice", "Bob", "Carlos", "Diana"], 3)

    # Assign types
    types = [rng.choice(["knight", "knave"]) for _ in range(3)]

    # Generate statements based on types
    # Person 0 says something about person 1
    if types[0] == "knight":
        # Truthful statement
        if types[1] == "knight":
            stmt0 = f"{names[0]} says: \"{names[1]} is a knight.\""
        else:
            stmt0 = f"{names[0]} says: \"{names[1]} is a knave.\""
    else:
        # Lying statement
        if types[1] == "knight":
            stmt0 = f"{names[0]} says: \"{names[1]} is a knave.\""
        else:
            stmt0 = f"{names[0]} says: \"{names[1]} is a knight.\""

    # Person 1 says something about person 2
    if types[1] == "knight":
        if types[2] == "knight":
            stmt1 = f"{names[1]} says: \"{names[2]} is a knight.\""
        else:
            stmt1 = f"{names[1]} says: \"{names[2]} is a knave.\""
    else:
        if types[2] == "knight":
            stmt1 = f"{names[1]} says: \"{names[2]} is a knave.\""
        else:
            stmt1 = f"{names[1]} says: \"{names[2]} is a knight.\""

    # Person 2 says something about themselves or person 0
    if types[2] == "knight":
        stmt2 = f"{names[2]} says: \"I am a knight.\""
    else:
        stmt2 = f"{names[2]} says: \"I am a knight.\""  # knaves also claim to be knights

    # This last statement is always "I am a knight" regardless, so add another
    if types[2] == "knight":
        if types[0] == "knight":
            stmt2 = f"{names[2]} says: \"{names[0]} and I are the same type.\""
        else:
            stmt2 = f"{names[2]} says: \"{names[0]} and I are different types.\""
    else:
        if types[0] == "knight":
            stmt2 = f"{names[2]} says: \"{names[0]} and I are the same type.\""  # lie
        else:
            stmt2 = f"{names[2]} says: \"{names[0]} and I are different types.\""  # lie

    ask_idx = rng.randint(0, 2)
    answer = types[ask_idx]

    question = (
        f"On an island, every person is either a knight (always tells the truth) "
        f"or a knave (always lies).\n\n"
        f"{stmt0}\n{stmt1}\n{stmt2}\n\n"
        f"What is {names[ask_idx]}: a knight or a knave?"
    )
    return {
        "question": question,
        "answer": answer,
        "answer_type": "exact",
        "domain": "logic",
        "steps": 4,
        "template": "knights_and_knaves",
        "seed": seed,
    }


LOGIC_GENERATORS = [
    lambda s: long_chain_with_distractors(s, chain_len=4),
    lambda s: long_chain_with_distractors(s, chain_len=5),
    negation_chain,
    multi_entity_tracking,
    ordering_hard,
    knights_and_knaves,
]


def generate_logic_questions(count: int, start_seed: int = 2000) -> list[dict]:
    questions = []
    per_template = max(1, count // len(LOGIC_GENERATORS))
    seed = start_seed
    for gen in LOGIC_GENERATORS:
        for _ in range(per_template):
            q = gen(seed)
            q["id"] = f"logic_{q['template']}_{seed}"
            questions.append(q)
            seed += 1
    while len(questions) < count:
        gen = LOGIC_GENERATORS[seed % len(LOGIC_GENERATORS)]
        q = gen(seed)
        q["id"] = f"logic_{q['template']}_{seed}"
        questions.append(q)
        seed += 1
    return questions[:count]


if __name__ == "__main__":
    qs = generate_logic_questions(10)
    for q in qs:
        print(json.dumps(q))
