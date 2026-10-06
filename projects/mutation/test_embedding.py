import random
import sys

sys.path.append("../../")

import numpy as np
from jax_unirep import get_reps
from jax_unirep.utils import load_params
from src.service.directed_evo import _unirep_avg, get_embedding

WT = "MSIQFFRVALIPFFAAFCLPVFAHPETLVKVKDAEDQLGARVGYIELDLNSGKILESFRPEERFPMMSTFKVLLCGAVLSRVDAGQEQLGRRIHYSQNDLVEYSPVTEKHLTDGMTVRELCSAAITMSDNTAANLLLTTIGGPKELTAFLHNMGDHVTRLDRWEPELNEAIPNDERDTTMPAAMATTLRKLLTGELLTLASRQQLIDWMEADKVAGPLLRSALPAGWFIADKSGAGERGSRGIIAALGPDGKPSRIVVIYTTGSQATMDERNRQIAEIGASLIKHW"


def mutants(n, seed=0):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        seq = list(WT)
        seq[rng.randrange(len(seq))] = rng.choice("ACDEFGHIKLMNPQRSTVWYU")
        out.append("".join(seq))
    return out


def test_unirep_embedding_matches_get_reps():
    params = load_params(paper_weights=64)[1]
    for seq in mutants(5):
        expected, _, _ = get_reps([seq], params=params, mlstm_size=64)
        got = get_embedding(seq, "unirep", params)
        assert got.shape == expected.shape == (1, 64)
        np.testing.assert_allclose(got, expected, rtol=1e-6, atol=1e-6)


def test_unirep_embedding_compiles_once():
    params = load_params(paper_weights=64)[1]
    for seq in mutants(20, seed=1):
        get_embedding(seq, "unirep", params)
    assert _unirep_avg._cache_size() == 1


if __name__ == "__main__":
    test_unirep_embedding_matches_get_reps()
    test_unirep_embedding_compiles_once()
    print("ok")
