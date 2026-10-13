import random
from dataclasses import dataclass

STANDARD_AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"

AMINO_ACID_SETS = {
    "20 standard": STANDARD_AMINO_ACIDS,
    "20 standard + U": STANDARD_AMINO_ACIDS + "U",  # U = selenocysteine
}


@dataclass
class Scope:  # what one trajectory may mutate
    positions: list  # 0-based
    low: int
    high: int
    region_of: dict | None = None  # set when mutants must cover at least 2 regions


def getAminoAcids(name):
    if name not in AMINO_ACID_SETS:
        raise ValueError(
            f"Unknown amino_acid_set {name!r}, expected one of {list(AMINO_ACID_SETS)}"
        )
    return AMINO_ACID_SETS[name]


def resolveRegions(regions, seq_len):
    # regions are 1-based and inclusive, empty means the whole sequence
    if not regions:
        return [range(seq_len)]

    spans = []
    for start, end in regions:
        if not 1 <= start <= end <= seq_len:
            raise ValueError(
                f"Invalid region [{start}, {end}] for a sequence of length {seq_len}"
            )
        spans.append((start - 1, end))
    spans.sort()

    merged = [list(spans[0])]
    for lo, hi in spans[1:]:
        if lo < merged[-1][1]:  # overlaps the previous region, so join them
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return [range(lo, hi) for lo, hi in merged]


def planTrajectoryScopes(
    regions, seq_len, num_trajectories, num_mutations_low, num_mutations_high
):
    # with 2+ regions: one trajectory per region, then one that combines regions
    if num_trajectories < 1:
        raise ValueError("num_trajectories must be at least 1")
    if num_mutations_low < 1 or num_mutations_high < num_mutations_low:
        raise ValueError(
            f"Invalid number of mutations {num_mutations_low}-{num_mutations_high}"
        )

    merged = resolveRegions(regions, seq_len)
    everywhere = [pos for region in merged for pos in region]
    if num_mutations_high > len(everywhere):
        raise ValueError(
            f"Cannot mutate up to {num_mutations_high} positions "
            f"when the regions only cover {len(everywhere)}"
        )

    if len(merged) < 2:
        return [
            Scope(everywhere, num_mutations_low, num_mutations_high)
            for _ in range(num_trajectories)
        ]

    if num_trajectories <= len(merged):
        raise ValueError(
            f"{num_trajectories} trajectories is too few for {len(merged)} regions, "
            f"at least {len(merged) + 1} are needed "
            "(one locked in each region and one combining them)"
        )

    scopes = []
    for region in merged:
        if len(region) < num_mutations_low:
            raise ValueError(
                f"Region [{region.start + 1}, {region.stop}] has {len(region)} "
                f"positions, fewer than the minimum of {num_mutations_low} mutations"
            )
        scopes.append(
            Scope(list(region), num_mutations_low, min(num_mutations_high, len(region)))
        )

    combining = Scope(everywhere, num_mutations_low, num_mutations_high)
    if num_mutations_high >= 2:  # one mutation can not reach two regions
        region_of = {pos: i for i, region in enumerate(merged) for pos in region}
        combining = Scope(
            everywhere, max(num_mutations_low, 2), num_mutations_high, region_of
        )
    scopes.append(combining)

    scopes += [
        Scope(everywhere, num_mutations_low, num_mutations_high)
        for _ in range(num_trajectories - len(scopes))
    ]
    return scopes


def applyMutations(s_wt, mutated):
    seq = list(s_wt)
    for pos, aa in mutated.items():
        seq[pos] = aa
    return "".join(seq)


def pickAminoAcid(amino_acids, *excluded):
    return random.choice([aa for aa in amino_acids if aa not in excluded])


def randomMutant(s_wt, scope, amino_acids):
    count = random.randint(scope.low, scope.high)
    if scope.region_of is None:
        chosen = random.sample(scope.positions, count)
    else:
        # one position in each of two regions, the rest anywhere
        by_region = {}
        for pos in scope.positions:
            by_region.setdefault(scope.region_of[pos], []).append(pos)
        first, second = random.sample(list(by_region), 2)
        chosen = [random.choice(by_region[first]), random.choice(by_region[second])]
        rest = [pos for pos in scope.positions if pos not in chosen]
        chosen += random.sample(rest, count - 2)
    return {pos: pickAminoAcid(amino_acids, s_wt[pos]) for pos in chosen}


def proposeMutant(s_wt, mutated, scope, amino_acids):
    # one random step that stays within the scope's limits
    region_of = scope.region_of
    free = [pos for pos in scope.positions if pos not in mutated]

    removable = list(mutated)
    shift_targets = {pos: free for pos in mutated}
    if region_of is not None:
        for pos in mutated:
            covered = {region_of[other] for other in mutated if other != pos}
            if len(covered) < 2:
                removable.remove(pos)
                # keep at least 2 regions covered
                shift_targets[pos] = [
                    p for p in free if covered and region_of[p] not in covered
                ]
    shiftable = [pos for pos, targets in shift_targets.items() if targets]

    moves = ["change"]
    if shiftable:
        moves.append("shift")
    if free and len(mutated) < scope.high:
        moves.append("add")
    if removable and len(mutated) > scope.low:
        moves.append("remove")

    move = random.choice(moves)
    proposal = dict(mutated)
    if move == "add":
        pos = random.choice(free)
        proposal[pos] = pickAminoAcid(amino_acids, s_wt[pos])
    elif move == "remove":
        del proposal[random.choice(removable)]
    elif move == "change":
        pos = random.choice(list(proposal))
        proposal[pos] = pickAminoAcid(amino_acids, s_wt[pos], proposal[pos])
    else:
        old = random.choice(shiftable)
        del proposal[old]
        pos = random.choice(shift_targets[old])
        proposal[pos] = pickAminoAcid(amino_acids, s_wt[pos])
    return proposal
