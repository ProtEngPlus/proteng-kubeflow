from pathlib import Path
import feather
from jax_unirep import get_reps, fit
from jax_unirep.utils import load_params
from Bio import SeqIO
import pandas as pd
import glob
import os
import numpy as np
import pkg_resources

from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.manifold import TSNE
from sklearn.model_selection import train_test_split, KFold
from sklearn.linear_model import RidgeCV, LinearRegression, HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.neighbors import KNeighborsRegressor

import warnings
warnings.filterwarnings('ignore')

from sklearn.preprocessing import normalize, StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Dict

# https://github.com/ElArkk/jax-unirep/blob/e3d756011fd539c803c669495b5c20357c47f661/jax_unirep/utils.py#L56
from joblib import dump

global PATH
PATH = '.'
# PATH = 'code/microservice'
# read FASTA file:
# input: file name
# output: names and sequences in the file as an array of dim-2 arrays [name, sequence].
def read_fasta(name):
    fasta_seqs = SeqIO.parse(open(gdrive_path + name + '.fasta.txt'),'fasta')
    data = []
    for fasta in fasta_seqs:
        data.append([fasta.id, str(fasta.seq).strip()])

    return data

# read sequence text file:
# input: file name
# output: names and sequences in the file as an array of dim-2 arrays [name, sequence].
def read_labeled_data(name):
    seqs = np.loadtxt(PATH  + "/src/data/" + name + '_seqs.txt', dtype='str')

    fitnesses = np.loadtxt(PATH + "/src/data/" + name + '_fitness.txt')
    data = []
    for seq, fitness in zip(seqs, fitnesses):
        data.append([str(seq).strip(), fitness])

    return data

# save represented dataframe of features as feather
def save_reps(df, path):
  feather.write_dataframe(df, path + '.feather')
  print(path + '.feather', 'saved!')


# read represented dataframe of features as feather
def read_reps(path):
  return feather.read_dataframe(path + '.feather')


aa_to_int = {
  'M':1,
  'R':2,
  'H':3,
  'K':4,
  'D':5,
  'E':6,
  'S':7,
  'T':8,
  'N':9,
  'Q':10,
  'C':11,
  'U':12,
  'G':13,
  'P':14,
  'A':15,
  'V':16,
  'I':17,
  'F':18,
  'Y':19,
  'W':20,
  'L':21,
  'O':22, #Pyrrolysine
  'X':23, # Unknown
  'Z':23, # Glutamic acid or GLutamine
  'B':23, # Asparagine or aspartic acid
  'J':23, # Leucine or isoleucine
  'start':24,
  'stop':25,
}


def get_int_to_aa():
  return {value:key for key, value in aa_to_int.items()}


def _one_hot(x, k, dtype=np.float32):
  # return np.array(x[:, None] == np.arange(k), dtype)
  return np.array(x[:, None] == np.arange(k))


def aa_seq_to_int(s):
  """Return the int sequence as a list for a given string of amino acids."""
  # Make sure only valid aa's are passed
  if not set(s).issubset(set(aa_to_int.keys())):
    raise ValueError(
      f"Unsupported character(s) in sequence found:"
      f" {set(s).difference(set(aa_to_int.keys()))}"
    )

  return [aa_to_int[a] for a in s]


def aa_seq_to_onehot(seq):
  return 1*np.equal(np.array(aa_seq_to_int(seq))[:,None], np.arange(21)).flatten()


def multi_onehot(seqs):
  return np.stack([aa_seq_to_onehot(s) for s in seqs.tolist()])


def distance_matrix(N):
	distance_matrix = np.zeros((N,N))
	for i in range(N):
		for j in range(N):
			# distance_matrix[i,j]=1- ((abs(i-j)/N)**2)
			distance_matrix[i,j]= 1-(abs(i-j)/N)

	return distance_matrix


def confusion_matrix_loss(Y_test,Y_preds_test):

  N = len(Y_test)
  Y_rank_matrix = np.zeros((N,N))
  Y_preds_rank_matrix = np.zeros((N,N))
  for i in range(N):
    for j in range(N):

      if Y_test[i] > Y_test[j]:
        Y_rank_matrix[i,j] = 1
      elif Y_test[i] <= Y_test[j]:
        Y_rank_matrix[i,j] = 0
      if Y_preds_test[i] > Y_preds_test[j]:
        Y_preds_rank_matrix[i,j] = 1
      elif Y_preds_test[i] <= Y_preds_test[j]:
        Y_preds_rank_matrix[i,j] = 0
  confusion_matrix = ~(Y_preds_rank_matrix == Y_rank_matrix)
  # dist_mat = distance_matrix(N)
  # confusion_matrix = confusion_matrix*dist_mat
  loss = np.sum(confusion_matrix)/confusion_matrix.size

  return loss

def get_weights_dir(folderpath: Optional[str] = None):
    """
    Fetch the paper weights per default, or from a specified folderpath
    """
    if folderpath:
        return Path(folderpath)
    else:
        return Path(
            pkg_resources.resource_filename(
                "jax_unirep", "weights/1900_weights/uniref50"
            )
        )
    
def load_params_1900(folderpath: Optional[str] = None) -> Dict:
    """Load pre-trained mLSTM1900 weights from the UniRep paper."""
    # weights_1900_dir = get_weights_dir(folderpath=folderpath)
    weights_1900_dir = get_weights_dir()


    params = dict()
    params["gh"] = np.load(weights_1900_dir / "rnn_mlstm_mlstm_gh_0.npy")
    params["gmh"] = np.load(weights_1900_dir / "rnn_mlstm_mlstm_gmh_0.npy")
    params["gmx"] = np.load(weights_1900_dir / "rnn_mlstm_mlstm_gmx_0.npy")
    params["gx"] = np.load(weights_1900_dir / "rnn_mlstm_mlstm_gx_0.npy")

    params["wh"] = np.load(weights_1900_dir / "rnn_mlstm_mlstm_wh_0.npy")
    params["wmh"] = np.load(weights_1900_dir / "rnn_mlstm_mlstm_wmh_0.npy")
    params["wmx"] = np.load(weights_1900_dir / "rnn_mlstm_mlstm_wmx_0.npy")
    params["wx"] = np.load(weights_1900_dir / "rnn_mlstm_mlstm_wx_0.npy")

    params["b"] = np.load(weights_1900_dir / "rnn_mlstm_mlstm_b_0.npy")

    return params


def load_data():
   return pd.DataFrame(read_labeled_data('example'), columns = ['sequence', 'fitness'])
def load_seqs(seqs_df, PARAMS = [None]):
    N_seqs = len(seqs_df)
    N_BATCHES = min(max(6, N_seqs // 500), N_seqs)
    BATCH_LEN = int(np.ceil(N_seqs / N_BATCHES))

    for param in PARAMS:
        # append path to param unless unirep (no param)
        if param == 'one_hot':
            print('getting reps for one hot')
            # name = 'one_hot'
            continue
            # onehot = multi_onehot(seqs_df.sequence)
            # feat_cols = ['feat' + str(j) for j in range(1, onehot.shape[1] + 1)]
            # this_df = pd.DataFrame(onehot, columns=feat_cols)
            # this_df.insert(0, "sequence", seqs_df.sequence)
            # this_df.insert(1, "fitness", seqs_df.fitness)

            # save_reps(this_df, gdrive_path + 'one_hot')

            # continue

        elif param is None:
            name = 'unirep'

        else:
            name = param
            # param = load_params(PATH + '/src/data/')
            param = load_params_1900(PATH + '/src/data/')
            print(param)

        print('getting reps for', name)

        # get 1st sequence
        reps, _, _ = get_reps(seqs_df.sequence[0], params=param)
        feat_cols = ['feat' + str(j) for j in range(1, reps.shape[1] + 1)]
        this_df = pd.DataFrame(reps, columns=feat_cols)
        this_df.insert(0, "sequence", seqs_df.sequence[0])
        this_df.insert(1, "fitness", seqs_df.fitness[0])
        for i in range(N_BATCHES):
            this_unirep, _, _ = get_reps(
                seqs_df.sequence[(1 + i * BATCH_LEN):min(1 + (i + 1) * BATCH_LEN, N_seqs)],
                params=param)
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

def do_ridge_regression(this_df, TRAIN_BATCH_SIZES=[24, 64, 96], N_BATCH=20, N_RAND_BATCHES=20, WT_FIT=0.63481905, ALPHA=0.01):
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

def do_top_model(PARAMS = ['model_weights.pkl']):
   data = load_data()
   print('load data ok')
  #  print(PARAMS)
   seqs = load_seqs(data,PARAMS=PARAMS)
   print('load seqs ok')
   top_model = do_ridge_regression(seqs)
   print('ridge regress ok')
   print(top_model)
   dump(top_model, 'ridgecv_model.joblib')
   return top_model
