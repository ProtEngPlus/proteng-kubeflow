from src.model.model import ArtifactPath, RequestFitTopBody
from src.service.run_top_model import doFitTop

# Prepare mock artifact paths
artifact_paths = {
    "ESM": ArtifactPath(bucket_name="unirep", path="680b87fd2e1ebf461a875858.pkl"),
    "blast": ArtifactPath(
        bucket_name="similar_protein", path="680b87fd2e1ebf461a875858"
    ),
}

# Prepare mock request
mock_request = RequestFitTopBody(
    job_id="680b87fd2e1ebf461a875858",
    input="MSIQFFRVALIPFFAAFCLPVFAHPETLVKVKDAEDQLGARVGYIELDLNSGKILESFRPEERFPMMSTFKVLLCGAVLSRVDAGQEQLGRRIHYSQNDLVEYSPVTEKHLTDGMTVRELCSAAITMSDNTAANLLLTTIGGPKELTAFLHNMGDHVTRLDRWEPELNEAIPNDERDTTMPAAMATTLRKLLTGELLTLASRQQLIDWMEADKVAGPLLRSALPAGWFIADKSGAGERGSRGIIAALGPDGKPSRIVVIYTTGSQATMDERNRQIAEIGASLIKHW",
    config={"train_batch_sizes": [24, 64, 96], "n_batch": 20, "alpha": 0.1},
    artifact=artifact_paths,
    lab_result={
        "total": 24,
        "sequences": [
            "ASIQHFHW",
            "CSIQHFHW",
            "DSIQHFHW",
            "ESIQHFHW",
            "FSIQHFHW",
            "GSIQHFHW",
            "HSIQHFHW",
            "ISIQHFHW",
            "JSIQHFHW",
            "KSIQHFHW",
            "LSIQHFHW",
            "MSIQHFHW",
            "NSIQHFHW",
            "OSIQHFHW",
            "PSIQHFHW",
            "QSIQHFHW",
            "RSIQHFHW",
            "SSIQHFHW",
            "TSIQHFHW",
            "USIQHFHW",
            "VSIQHFHW",
            "WSIQHFHW",
            "XSIQHFHW",
            "YSIQHFHW",
        ],
        "scores": [
            0.002914,
            0.00302,
            0.002219,
            0.004379,
            0.002914,
            0.00302,
            0.002219,
            0.004379,
            0.002914,
            0.00302,
            0.002219,
            0.004379,
            0.002914,
            0.00302,
            0.002219,
            0.004379,
            0.002914,
            0.00302,
            0.002219,
            0.004379,
            0.002914,
            0.00302,
            0.002219,
            0.004379,
        ],
    },
    meta=["blast", "ESM", "ridgecv", "mutation"],
)

# Patch external functions for dry run

# db.uploadToBucket = lambda bucket, name, data: f"Mock uploaded {name} to {bucket}"
# mq.publishCompletedJobStatusToMQ = lambda *args, **kwargs: print("✅ Published success message to MQ")
# mq.publishFailedJobStatusToMQ = lambda *args, **kwargs: print("❌ Published failure message to MQ")

# Run the function with mock

from dotenv import load_dotenv

load_dotenv()

# Verify environment variable loading

doFitTop(mock_request)
