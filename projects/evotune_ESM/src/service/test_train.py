# sys.path.append("../../../..")
import logging
import os
import sys

# Correct the path to the src directory in the current project
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
sys.path.insert(0, src_dir)

from service.train import trainESM

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    # Sample training and validation sets (short dummy sequences for testing)
    trainSet = ["MKTAYIAKQRQISFVKSHFSRQDILD"]  # Example protein sequence
    outDomainValSet = ["GHPDYKVDVFGCGRVNKEVHF"]  # Another example sequence

    # Dummy config dictionary (not used but passed to match function signature)
    config = {
        "n_epochs_config": 1,  # Example: Set number of epochs for the test
        "learning_rate_config": 1e-5,  # Example: Set learning rate for the test
        "weight_decay": 0.01,  # Example: Set weight decay for the test
    }

    logger.info("Starting ESM training test...")

    # Run trainESM
    df = trainESM(trainSet, outDomainValSet, config)
    esm_np = df.to_numpy()
    print(esm_np)

    # Log output DataFrame
    logger.info(f"Generated DataFrame:\n{df}")

    # Save DataFrame to a CSV file for verification
    directory_path = "service/output/"
    os.makedirs(directory_path, exist_ok=True)
    df.to_feather(directory_path + "BIOTEC-eESM-avg.feather")
    logger.info("Saved DataFrame to BIOTEC-eESM-avg.feather")


if __name__ == "__main__":
    main()
