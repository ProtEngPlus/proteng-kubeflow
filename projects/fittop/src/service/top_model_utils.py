import numpy as np
import pandas as pd
from jax_unirep import get_reps
from pkg.common.db import downloadFromBucket
from sklearn.model_selection import KFold
from sklearn.linear_model import RidgeCV
import pickle as pkl

def formatData(amount, sequences, scores):
  if( amount != len(sequences) or amount != len(scores) ):
    raise ValueError("Amount of sequences and scores must be equal to amount")
  
  # Creating a Pandas DataFrame
  df = pd.DataFrame({'sequence': sequences, 'fitness': scores})

  # Stripping whitespace from the 'sequence' column
  df['sequence'] = df['sequence'].str.strip()
  
  return df

def loadSeqs(seqs_df,bucket_name,model_path):
    N_seqs = len(seqs_df)
    N_BATCHES = min(max(6, N_seqs // 500), N_seqs)
    BATCH_LEN = int(np.ceil(N_seqs / N_BATCHES))

    param = pkl.loads(downloadFromBucket(bucket_name, model_path))[1]

    # get 1st sequence
    reps, _, _ = get_reps(seqs_df.sequence[0], params=param, mlstm_size=64)
    feat_cols = ['feat' + str(j) for j in range(1, reps.shape[1] + 1)]
    this_df = pd.DataFrame(reps, columns=feat_cols)
    this_df.insert(0, "sequence", seqs_df.sequence[0])
    this_df.insert(1, "fitness", seqs_df.fitness[0])
    for i in range(N_BATCHES):
        this_unirep, _, _ = get_reps(
            seqs_df.sequence[(1 + i * BATCH_LEN):min(1 + (i + 1) * BATCH_LEN, N_seqs)],
            params=param,mlstm_size=64)
        this_unirep_df = pd.DataFrame(this_unirep, columns=feat_cols)
        this_unirep_df.insert(0, "sequence",
                                seqs_df.sequence[(1 + i * BATCH_LEN):min(1 + (i + 1) * BATCH_LEN, N_seqs)].reset_index(
                                    drop=True))
        this_unirep_df.insert(1, "fitness",
                                seqs_df.fitness[
                                (1 + i * BATCH_LEN):min(1 + (i + 1) * BATCH_LEN, N_seqs)].reset_index(drop=True))
        this_df = pd.concat([this_df.reset_index(drop=True), this_unirep_df.reset_index(drop=True)]).reset_index(
            drop=True)
    return this_df

def doRidgeRegression(this_df, train_batch_sizes, n_batch, alpha):
    for train_batch_size in train_batch_sizes:
        df = this_df
        for i in range(n_batch):
            np.random.seed(42 * (i + 2))
            rndperm = np.random.permutation(df.shape[0])

            X = df.loc[rndperm[0:train_batch_size], df.columns[2:]]
            Y = df.loc[rndperm[0:train_batch_size], "fitness"]

            kfold = KFold(n_splits=10, shuffle=True)

            model = RidgeCV(alphas=[alpha], cv=kfold)

            model.fit(X, Y)
    return model