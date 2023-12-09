from Bio import SeqIO
import numpy as np
import feather
import pandas as pd
from jax_unirep import get_reps, fit
from jax_unirep.utils import load_params
from common.db import downloadFromBucket,uploadToBucket
from sklearn.model_selection import train_test_split, KFold
from sklearn.linear_model import RidgeCV, LinearRegression, HuberRegressor
import pickle as pkl

global PATH
PATH = '.'
# PATH = 'code/microservice'
# read FASTA file:
# input: file name
# output: names and sequences in the file as an array of dim-2 arrays [name, sequence].
def readFasta(name):
    fasta_seqs = SeqIO.parse(open(gdrive_path + name + '.fasta.txt'),'fasta')
    data = []
    for fasta in fasta_seqs:
        data.append([fasta.id, str(fasta.seq).strip()])

    return data

# read sequence text file:
# input: file name
# output: names and sequences in the file as an array of dim-2 arrays [name, sequence].
def readLabeledData(name):
    seqs = np.loadtxt(PATH  + "/src/data/" + name + '_seqs.txt', dtype='str')

    fitnesses = np.loadtxt(PATH + "/src/data/" + name + '_fitness.txt')
    data = []
    for seq, fitness in zip(seqs, fitnesses):
        data.append([str(seq).strip(), fitness])

    return data

# save represented dataframe of features as feather
def saveReps(df, path):
  feather.write_dataframe(df, path + '.feather')
  print(path + '.feather', 'saved!')


# read represented dataframe of features as feather
def readReps(path):
  return feather.read_dataframe(path + '.feather')


AATOINT = {
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


def getIntToAa():
  return {value:key for key, value in AATOINT.items()}


def oneHot(x, k, dtype=np.float32):
  # return np.array(x[:, None] == np.arange(k), dtype)
  return np.array(x[:, None] == np.arange(k))


def aaSeqToInt(s):
  """Return the int sequence as a list for a given string of amino acids."""
  # Make sure only valid aa's are passed
  if not set(s).issubset(set(AATOINT.keys())):
    raise ValueError(
      f"Unsupported character(s) in sequence found:"
      f" {set(s).difference(set(AATOINT.keys()))}"
    )

  return [AATOINT[a] for a in s]


def aaSeqToOnehot(seq):
  return 1*np.equal(np.array(aaSeqToInt(seq))[:,None], np.arange(21)).flatten()


def multiOnehot(seqs):
  return np.stack([aaSeqToOnehot(s) for s in seqs.tolist()])


def distanceMatrix(N):
	distance_matrix = np.zeros((N,N))
	for i in range(N):
		for j in range(N):
			# distance_matrix[i,j]=1- ((abs(i-j)/N)**2)
			distance_matrix[i,j]= 1-(abs(i-j)/N)

	return distance_matrix


def confusionMatrixLoss(Y_test,Y_preds_test):

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

def loadData():
   return pd.DataFrame(readLabeledData('example'), columns = ['sequence', 'fitness'])
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

def doRidgeRegression(this_df, train_batch_sizes, n_batch, n_rand_batches, wt_fit, alpha):
    batch_level = []
    for train_batch_size in train_batch_sizes:
        holdout_batch_size = train_batch_size * 10

        params_level = []
        df = this_df

        scores_level = []
        for i in range(n_batch):
            np.random.seed(42 * (i + 2))
            rndperm = np.random.permutation(df.shape[0])

            X = df.loc[rndperm[0:train_batch_size], df.columns[2:]]
            Y = df.loc[rndperm[0:train_batch_size], "fitness"]

            X_holdout = df.loc[rndperm[train_batch_size:train_batch_size + holdout_batch_size], df.columns[2:]]
            Y_holdout = df.loc[rndperm[train_batch_size:train_batch_size + holdout_batch_size], "fitness"]

            kfold = KFold(n_splits=10, shuffle=True)

            model = RidgeCV(alphas=[alpha], cv=kfold)

            model.fit(X, Y)

            Y_preds = model.predict(X_holdout)

            usorted = np.array(Y_holdout)[np.argsort(Y_preds)][::-1][:int(holdout_batch_size / 10)]

            usorted_count = np.sum([1 if i > wt_fit else 0 for i in usorted])

            avg_rand_count = 0
            for k in range(n_rand_batches):
                np.random.seed(42 * (i + 2) + (1 + k))
                rand_Y = np.random.permutation(np.array(Y_holdout))[:int(holdout_batch_size / 10)]
                avg_rand_count += np.sum([1 if i > wt_fit else 0 for i in rand_Y])
            avg_rand_count /= n_rand_batches

            scores_level.append(usorted_count / avg_rand_count)

        params_level.append(scores_level)
        batch_level.append(params_level)

    return model