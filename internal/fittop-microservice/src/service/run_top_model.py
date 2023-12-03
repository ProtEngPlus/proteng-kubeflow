from jax_unirep import get_reps, fit
from jax_unirep.utils import load_params
import pandas as pd
import numpy as np
import pickle as pkl

from sklearn.model_selection import train_test_split, KFold
from sklearn.linear_model import RidgeCV, LinearRegression, HuberRegressor
import warnings

from src.service.db import downloadFromBucket,uploadToBucket
warnings.filterwarnings('ignore')

# https://github.com/ElArkk/jax-unirep/blob/e3d756011fd539c803c669495b5c20357c47f661/jax_unirep/utils.py#L56
from joblib import dump

from src.service.top_model_utils import PATH,read_fasta,read_labeled_data,save_reps,read_reps,aa_to_int,get_int_to_aa,_one_hot,aa_seq_to_int,aa_seq_to_onehot,multi_onehot,distance_matrix,confusion_matrix_loss
from src.model.model import RequestFitTopBody

def loadData():
   return pd.DataFrame(read_labeled_data('example'), columns = ['sequence', 'fitness'])
def loadSeqs(seqs_df,bucket_name,model_path):
    N_seqs = len(seqs_df)
    N_BATCHES = min(max(6, N_seqs // 500), N_seqs)
    BATCH_LEN = int(np.ceil(N_seqs / N_BATCHES))

    param= pkl.loads(downloadFromBucket(bucket_name, model_path))[1]

    # get 1st sequence
    reps, _, _ = get_reps(seqs_df.sequence[0], params=param,mlstm_size=64)
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

def doRidgeRegression(this_df, TRAIN_BATCH_SIZES, N_BATCH, N_RAND_BATCHES, WT_FIT, ALPHA):
    batch_level = []
    for TRAIN_BATCH_SIZE in TRAIN_BATCH_SIZES:
        HOLDOUT_BATCH_SIZE = TRAIN_BATCH_SIZE * 10

        params_level = []
        df = this_df

        scores_level = []
        for i in range(N_BATCH):
            np.random.seed(42 * (i + 2))
            rndperm = np.random.permutation(df.shape[0])

            X = df.loc[rndperm[0:TRAIN_BATCH_SIZE], df.columns[2:]]
            Y = df.loc[rndperm[0:TRAIN_BATCH_SIZE], "fitness"]

            X_holdout = df.loc[rndperm[TRAIN_BATCH_SIZE:TRAIN_BATCH_SIZE + HOLDOUT_BATCH_SIZE], df.columns[2:]]
            Y_holdout = df.loc[rndperm[TRAIN_BATCH_SIZE:TRAIN_BATCH_SIZE + HOLDOUT_BATCH_SIZE], "fitness"]

            kfold = KFold(n_splits=10, shuffle=True)

            model = RidgeCV(alphas=[ALPHA], cv=kfold)

            model.fit(X, Y)

            Y_preds = model.predict(X_holdout)

            usorted = np.array(Y_holdout)[np.argsort(Y_preds)][::-1][:int(HOLDOUT_BATCH_SIZE / 10)]

            usorted_count = np.sum([1 if i > WT_FIT else 0 for i in usorted])

            avg_rand_count = 0
            for k in range(N_RAND_BATCHES):
                np.random.seed(42 * (i + 2) + (1 + k))
                rand_Y = np.random.permutation(np.array(Y_holdout))[:int(HOLDOUT_BATCH_SIZE / 10)]
                avg_rand_count += np.sum([1 if i > WT_FIT else 0 for i in rand_Y])
            avg_rand_count /= N_RAND_BATCHES

            scores_level.append(usorted_count / avg_rand_count)

        params_level.append(scores_level)
        batch_level.append(params_level)

    return model

def doFitTop(requestBody: RequestFitTopBody):
    data = loadData()
    print('load data ok')
    #  print(PARAMS)
    seqs = loadSeqs(
        seqs_df=data,
        bucket_name=requestBody.artifact.unirep.bucket_name,
        model_path=requestBody.artifact.unirep.path)
    print('load seqs ok')
    top_model = doRidgeRegression(
        this_df=seqs,
        TRAIN_BATCH_SIZES=requestBody.config.TRAIN_BATCH_SIZES,
        N_BATCH=requestBody.config.N_BATCH,
        N_RAND_BATCHES=requestBody.config.N_RAND_BATCHES,
        WT_FIT=requestBody.config.WT_FIT,
        ALPHA=requestBody.config.ALPHA
    )
    print('ridge regress ok')
    print(top_model)
    model_data = pkl.dumps(top_model)
    bucket_name = "ridgecv"
    model_filename = requestBody.job_id + '.pkl'
    upload_result = uploadToBucket(bucket_name, model_filename, model_data)
    print(upload_result)
    # ------------------------------------------------------------
    # param= pkl.loads(downloadFromBucket("fittop", "test1.pkl"))
    # print(param)

    return top_model
