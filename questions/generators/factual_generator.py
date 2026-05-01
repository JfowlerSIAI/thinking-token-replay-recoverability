"""Generate factual MCQ questions for the thinking-token experiment.

These are multi-step factual reasoning questions (not pure recall) that require
combining 2+ pieces of knowledge. Format: 4-option MCQ with one correct answer.
"""

import json
import random

# Each question template produces questions that require 2+ inferential steps
# and have unambiguous, verifiable answers.

QUESTIONS_BANK = [
    {
        "question": "Which planet in our solar system has the most moons?\nA) Jupiter\nB) Saturn\nC) Uranus\nD) Neptune",
        "answer": "B",
        "explanation": "Saturn has the most confirmed moons (over 140).",
    },
    {
        "question": "If you are standing at the South Pole and walk north for 1 km, then east for 1 km, then south for 1 km, approximately how far are you from where you started?\nA) 0 km\nB) 1 km\nC) Less than 1 km\nD) More than 1 km",
        "answer": "C",
        "explanation": "At the South Pole, walking north then east traces a curve, and walking south returns you close but not exactly to the pole.",
    },
    {
        "question": "A substance has a pH of 2. Which of the following best describes it?\nA) Strong base\nB) Weak base\nC) Neutral\nD) Strong acid",
        "answer": "D",
        "explanation": "pH 2 is strongly acidic (pH < 7 is acidic, lower = stronger).",
    },
    {
        "question": "If sound travels at approximately 343 m/s in air, and you see lightning and hear thunder 6 seconds later, approximately how far away was the lightning?\nA) About 0.5 km\nB) About 1 km\nC) About 2 km\nD) About 3 km",
        "answer": "C",
        "explanation": "343 m/s × 6 s = 2,058 m ≈ 2 km.",
    },
    {
        "question": "Water at sea level boils at 100°C. At higher altitudes, water boils at:\nA) A higher temperature\nB) A lower temperature\nC) The same temperature\nD) It depends on humidity",
        "answer": "B",
        "explanation": "Lower atmospheric pressure at altitude means water boils at a lower temperature.",
    },
    {
        "question": "A car traveling at 60 km/h needs to cover 150 km. Halfway through the journey, it increases speed to 90 km/h. What is the total journey time?\nA) 2 hours\nB) 2 hours 5 minutes\nC) 2 hours 15 minutes\nD) 2 hours 10 minutes",
        "answer": "D",
        "explanation": "First 75 km at 60 km/h = 1.25 hours. Second 75 km at 90 km/h = 0.833 hours. Total = 2.083 hours ≈ 2h 5min. Actually: 75/60 + 75/90 = 1.25 + 0.833 = 2.083h = 2h5min. Answer is D (2h10min) — let me recalculate: actually this is closest to 2h5min which is B.",
    },
    {
        "question": "What is the sum of the interior angles of a hexagon?\nA) 540°\nB) 720°\nC) 900°\nD) 1080°",
        "answer": "B",
        "explanation": "(6-2) × 180° = 720°.",
    },
    {
        "question": "If you mix equal volumes of a 0.1M HCl solution and a 0.1M NaOH solution, the resulting solution will be:\nA) Acidic\nB) Basic\nC) Neutral\nD) Cannot determine",
        "answer": "C",
        "explanation": "Equal moles of strong acid and strong base neutralize completely.",
    },
    {
        "question": "A train leaves Station A at 9:00 AM traveling at 80 km/h. Another train leaves Station B (200 km away) at 9:30 AM traveling toward Station A at 120 km/h. At what time do they meet?\nA) 10:00 AM\nB) 10:15 AM\nC) 10:30 AM\nD) 10:45 AM",
        "answer": "C",
        "explanation": "At 9:30, train A has covered 40 km, leaving 160 km. Combined speed: 200 km/h. Time: 160/200 = 0.8 hours = 48 min after 9:30 = 10:18. Closest is B. Actually let me be precise: at 9:30 gap=160km, closing at 200km/h, meet at 9:30 + 48min = 10:18. Hmm, needs recalculation.",
    },
    {
        "question": "Which of the following elements has the highest electronegativity?\nA) Sodium\nB) Chlorine\nC) Fluorine\nD) Oxygen",
        "answer": "C",
        "explanation": "Fluorine has the highest electronegativity of all elements (3.98).",
    },
    {
        "question": "If a die is rolled twice, what is the probability that the sum is 7?\nA) 1/6\nB) 1/12\nC) 5/36\nD) 1/36",
        "answer": "A",
        "explanation": "There are 6 favorable outcomes (1+6, 2+5, 3+4, 4+3, 5+2, 6+1) out of 36. 6/36 = 1/6.",
    },
    {
        "question": "A satellite orbits Earth at an altitude where gravity is 1/4 of surface gravity. Approximately how far from Earth's center is it?\nA) 1 Earth radius\nB) 2 Earth radii\nC) 4 Earth radii\nD) 16 Earth radii",
        "answer": "B",
        "explanation": "Gravity follows inverse square law. g/4 at distance r means r² = 4R², so r = 2R.",
    },
    {
        "question": "In a population of 1000 people, a disease has a prevalence of 1%. A test for the disease has 95% sensitivity and 90% specificity. If a random person tests positive, what is the approximate probability they actually have the disease?\nA) About 9%\nB) About 50%\nC) About 90%\nD) About 95%",
        "answer": "A",
        "explanation": "Bayes' theorem: P(disease|+) = (0.95 × 0.01) / (0.95 × 0.01 + 0.10 × 0.99) = 0.0095 / 0.1085 ≈ 8.8%.",
    },
    {
        "question": "Two identical resistors, each of 10 ohms, are connected in parallel. What is their combined resistance?\nA) 20 ohms\nB) 10 ohms\nC) 5 ohms\nD) 2.5 ohms",
        "answer": "C",
        "explanation": "Parallel: 1/R = 1/10 + 1/10 = 2/10, so R = 5 ohms.",
    },
    {
        "question": "A ball is thrown upward at 20 m/s. Ignoring air resistance, approximately how high does it go? (g = 10 m/s²)\nA) 10 m\nB) 20 m\nC) 30 m\nD) 40 m",
        "answer": "B",
        "explanation": "h = v²/(2g) = 400/20 = 20 m.",
    },
    {
        "question": "How many diagonals does an octagon have?\nA) 8\nB) 16\nC) 20\nD) 24",
        "answer": "C",
        "explanation": "n(n-3)/2 = 8(5)/2 = 20.",
    },
    {
        "question": "If a gene has 900 nucleotide bases, how many amino acids will the resulting protein have (approximately)?\nA) 100\nB) 300\nC) 450\nD) 900",
        "answer": "B",
        "explanation": "Each amino acid is coded by 3 bases (a codon). 900/3 = 300 amino acids.",
    },
    {
        "question": "What is the GCD (greatest common divisor) of 48 and 180?\nA) 6\nB) 12\nC) 18\nD) 24",
        "answer": "B",
        "explanation": "48 = 2⁴ × 3, 180 = 2² × 3² × 5. GCD = 2² × 3 = 12.",
    },
    {
        "question": "A rectangular tank is 2m long, 1.5m wide, and 1m deep. How many liters of water can it hold?\nA) 300\nB) 3000\nC) 30000\nD) 300000",
        "answer": "B",
        "explanation": "Volume = 2 × 1.5 × 1 = 3 m³ = 3000 liters.",
    },
    {
        "question": "In a group of 30 students, 18 play soccer and 15 play basketball. If every student plays at least one sport, how many play both?\nA) 3\nB) 5\nC) 12\nD) 15",
        "answer": "A",
        "explanation": "By inclusion-exclusion: |S ∪ B| = |S| + |B| - |S ∩ B|. 30 = 18 + 15 - x. x = 3.",
    },
    {
        "question": "If log₂(x) = 5, what is x?\nA) 10\nB) 25\nC) 32\nD) 64",
        "answer": "C",
        "explanation": "2⁵ = 32.",
    },
    {
        "question": "A 10 kg block is on a frictionless ramp inclined at 30°. What is the net force along the ramp? (g = 10 m/s²)\nA) 25 N\nB) 50 N\nC) 75 N\nD) 100 N",
        "answer": "B",
        "explanation": "F = mg sin(30°) = 10 × 10 × 0.5 = 50 N.",
    },
    {
        "question": "A compound has the empirical formula CH₂O and a molar mass of 180 g/mol. What is its molecular formula?\nA) CH₂O\nB) C₂H₄O₂\nC) C₃H₆O₃\nD) C₆H₁₂O₆",
        "answer": "D",
        "explanation": "Empirical mass = 12 + 2 + 16 = 30. 180/30 = 6. So C₆H₁₂O₆.",
    },
    {
        "question": "What is the next number in the sequence: 2, 6, 18, 54, ...?\nA) 108\nB) 162\nC) 216\nD) 72",
        "answer": "B",
        "explanation": "Geometric sequence with ratio 3. 54 × 3 = 162.",
    },
    {
        "question": "If the half-life of a radioactive substance is 5 years, what fraction of the original amount remains after 15 years?\nA) 1/2\nB) 1/4\nC) 1/8\nD) 1/16",
        "answer": "C",
        "explanation": "15 years = 3 half-lives. (1/2)³ = 1/8.",
    },
]


def _clean_bank():
    """Fix any questions with calculation errors and return cleaned bank."""
    cleaned = []
    # Remove the two questions with known calculation issues
    skip_explanations = [
        "First 75 km",  # car speed problem has wrong answer
        "At 9:30, train A",  # train problem has wrong answer
    ]
    for q in QUESTIONS_BANK:
        skip = False
        for s in skip_explanations:
            if s in q.get("explanation", ""):
                skip = True
                break
        if not skip:
            cleaned.append(q)
    return cleaned


def generate_factual_questions(count: int, start_seed: int = 3000) -> list[dict]:
    """Generate `count` factual MCQ questions from the bank."""
    bank = _clean_bank()
    rng = random.Random(start_seed)

    # Use all available questions, cycling if needed
    questions = []
    for i in range(count):
        src = bank[i % len(bank)]
        q = {
            "id": f"factual_mcq_{start_seed + i}",
            "question": src["question"],
            "answer": src["answer"],
            "answer_type": "mcq",
            "domain": "factual",
            "steps": 2,
            "template": "factual_mcq",
            "seed": start_seed + i,
        }
        questions.append(q)

    return questions[:count]


if __name__ == "__main__":
    qs = generate_factual_questions(10)
    for q in qs:
        print(json.dumps(q))
