import pickle as pkl

import numpy as np
import pandas as pd
from jax_unirep import get_reps
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import KFold

from pkg.common.db import downloadFromBucket


def formatData(amount, sequences, scores):
    if amount != len(sequences) or amount != len(scores):
        raise ValueError("Amount of sequences and scores must be equal to amount")

    # Creating a Pandas DataFrame
    df = pd.DataFrame({"sequence": sequences, "fitness": scores})

    # Stripping whitespace from the 'sequence' column
    df["sequence"] = df["sequence"].str.strip()

    return df


def loadSeqs(seqs_df, bucket_name, model_path):
    N_seqs = len(seqs_df)
    N_BATCHES = min(max(6, N_seqs // 500), N_seqs)
    BATCH_LEN = int(np.ceil(N_seqs / N_BATCHES))

    param = pkl.loads(downloadFromBucket(bucket_name, model_path))[1]

    # get 1st sequence

    reps, _, _ = get_reps(seqs_df.sequence[0], params=param, mlstm_size=64)

    feat_cols = ["feat" + str(j) for j in range(1, reps.shape[1] + 1)]
    this_df = pd.DataFrame(reps, columns=feat_cols)
    this_df.insert(0, "sequence", seqs_df.sequence[0])
    this_df.insert(1, "fitness", seqs_df.fitness[0])
    for i in range(N_BATCHES):
        # -----Proteng specific block start
        start_seq = 1 + i * BATCH_LEN
        end_seq = min(1 + (i + 1) * BATCH_LEN, N_seqs)
        batch_seqs = seqs_df.sequence[start_seq:end_seq]
        if len(batch_seqs) == 0:
            continue
        # -----Proteng specific block end
        this_unirep, _, _ = get_reps(
            seqs_df.sequence[
                (1 + i * BATCH_LEN) : min(1 + (i + 1) * BATCH_LEN, N_seqs)
            ],
            params=param,
            mlstm_size=64,
        )
        this_unirep_df = pd.DataFrame(this_unirep, columns=feat_cols)
        this_unirep_df.insert(
            0,
            "sequence",
            seqs_df.sequence[
                (1 + i * BATCH_LEN) : min(1 + (i + 1) * BATCH_LEN, N_seqs)
            ].reset_index(drop=True),
        )
        this_unirep_df.insert(
            1,
            "fitness",
            seqs_df.fitness[
                (1 + i * BATCH_LEN) : min(1 + (i + 1) * BATCH_LEN, N_seqs)
            ].reset_index(drop=True),
        )
        this_df = pd.concat(
            [this_df.reset_index(drop=True), this_unirep_df.reset_index(drop=True)]
        ).reset_index(drop=True)

    return this_df


def loadESMseqs(seqs_df, bucket_name, model_path):
    N_seqs = len(seqs_df)
    N_BATCHES = min(max(6, N_seqs // 500), N_seqs)
    BATCH_LEN = int(np.ceil(N_seqs / N_BATCHES))

    # Load ESM representations from bucket
    esm_np = pkl.loads(downloadFromBucket(bucket_name, model_path))

    # Prepare column names based on the number of features
    feat_cols = ["feat" + str(j) for j in range(1, esm_np.shape[1] + 1)]

    # Initialize DataFrame with the first sequence
    this_df = pd.DataFrame([esm_np[0]], columns=feat_cols)
    this_df.insert(0, "sequence", seqs_df.sequence[0])
    this_df.insert(1, "fitness", seqs_df.fitness[0])

    for i in range(N_BATCHES):
        # -----Proteng specific block start
        start_seq = 1 + i * BATCH_LEN
        end_seq = min(1 + (i + 1) * BATCH_LEN, N_seqs)
        batch_seqs = seqs_df.sequence[start_seq:end_seq]
        if len(batch_seqs) == 0:
            continue
        # -----Proteng specific block end
        batch_reps = esm_np[start_seq:end_seq]
        this_batch_df = pd.DataFrame(batch_reps, columns=feat_cols)
        this_batch_df.insert(0, "sequence", batch_seqs.reset_index(drop=True))
        this_batch_df.insert(
            1, "fitness", seqs_df.fitness[start_seq:end_seq].reset_index(drop=True)
        )

        this_df = pd.concat(
            [this_df.reset_index(drop=True), this_batch_df.reset_index(drop=True)]
        ).reset_index(drop=True)

    # Drop rows with any NaNs in feature columns or log them
    feature_cols = this_df.columns[2:]
    n_nan_rows = this_df[feature_cols].isna().any(axis=1).sum()
    if n_nan_rows > 0:
        this_df = this_df.dropna(subset=feature_cols).reset_index(drop=True)

    # Optional strict check
    assert (
        not this_df[feature_cols].isna().any().any()
    ), "Still found NaNs after dropping!"
    return this_df


def doRidgeRegression(this_df, train_batch_sizes, n_batch, alpha):
    for train_batch_size in train_batch_sizes:
        df = this_df
        for i in range(n_batch):
            np.random.seed(42 * (i + 2))
            rndperm = np.random.permutation(df.shape[0])

            X = df.loc[rndperm[0:train_batch_size], df.columns[2:]]
            Y = df.loc[rndperm[0:train_batch_size], "fitness"]

            kfold = KFold(n_splits=min(10, len(X)), shuffle=True)

            model = RidgeCV(alphas=[alpha], cv=kfold)

            model.fit(X, Y)
    return model
