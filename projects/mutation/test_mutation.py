import sys

sys.path.append("../../")
from dotenv import load_dotenv
from src.model.model import RequestMutationBody
from src.service.thread import runMutationThread

load_dotenv()

# Sample RequestMutationBody for testing
request_body = RequestMutationBody(
    job_id="6811d38896587d7e563c4e75",
    input="MSIQFFRVALIPFFAAFCLPVFAHPETLVKVKDAEDQLGARVGYIELDLNSGKILESFRPEERFPMMSTFKVLLCGAVLSRVDAGQEQLGRRIHYSQNDLVEYSPVTEKHLTDGMTVRELCSAAITMSDNTAANLLLTTIGGPKELTAFLHNMGDHVTRLDRWEPELNEAIPNDERDTTMPAAMATTLRKLLTGELLTLASRQQLIDWMEADKVAGPLLRSALPAGWFIADKSGAGERGSRGIIAALGPDGKPSRIVVIYTTGSQATMDERNRQIAEIGASLIKHW",
    mutation_id="68173803b67ca8dce817556c",
    config={
        "temperature": 0.01,
        "num_iterations": 25,
        "num_trajectories": 5,
        "mutate_pos_range": 8,
    },
    artifact={
        "ESM": {"bucket_name": "unirep", "path": "6811d38896587d7e563c4e75.pkl"},
        "blast": {"bucket_name": "similar_protein", "path": "6811d38896587d7e563c4e75"},
        "ridgecv": {"bucket_name": "ridgecv", "path": "6811d38896587d7e563c4e75.pkl"},
    },
    meta=["blast", "ESM", "ridgecv", "mutation"],
)

# Call the function from thread.py
runMutationThread(request_body)
