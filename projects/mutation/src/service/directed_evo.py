import numpy as np
import pandas as pd
import random
from jax_unirep import get_reps
from src.logger import mutationLogger as logger
from src.service.utils import getIntToAa

def mutateSequence(seq,m,prev_mut_loc): # produce a mutant sequence (integer representation), given an initial sequence and the number of mutations to introduce ("m")
    for i in range(m): #iterate through number of mutations to add
        rand_loc = random.randint(prev_mut_loc-8,prev_mut_loc+8) # find random position to mutate
        while (rand_loc <=0) or (rand_loc >= len(seq)):
            rand_loc = random.randint(prev_mut_loc-8,prev_mut_loc+8)

        rand_aa = random.randint(1,21) # find random amino acid to mutate to
        seq = list(seq)
        seq[rand_loc] = getIntToAa()[rand_aa] # update sequence to have new amino acid at randomely chosen position
        seq = ''.join(seq)

    return seq,rand_loc # output the randomely mutated sequence

def directedEvolution(s_wt,num_iterations,T,Model, params): # input = (wild-type sequence, number of mutation iterations, "temperature")		
    s_traj = [] # initialize an array to keep records of the protein sequences for this trajectory
    y_traj = [] # initialize an array to keep records of the fitness scores for this trajectory

    mut_loc_seed = random.randint(0,len(s_wt)) # randomely choose the location of the first mutation in the trajectory
    s,new_mut_loc = mutateSequence(s_wt, (np.random.poisson(2) + 1),mut_loc_seed) # initial mutant sequence for this trajectory, with m = Poisson(2)+1 mutations

    x,_,_ = get_reps([s],params=params,mlstm_size=64)# eUniRep representation of the initial mutant sequence for this trajectory
    feat_cols = ['feat' + str(j) for j in range(1, x.shape[1] + 1)]
    x = pd.DataFrame(x, columns=feat_cols)

    y = Model.predict(x) # predicted fitness score for the initial mutant sequence for this trajectory

    # iterate through the trial mutation steps for the directed evolution trajectory
    for i in range(num_iterations):
        mu = np.random.uniform(1,2.5) # "mu" parameter for poisson function: used to control how many mutations to introduce
        m = np.random.poisson(mu-1) + 1 # how many random mutations to apply to current sequence

        s_new,new_mut_loc = mutateSequence(s, m, new_mut_loc) # new trial sequence, produced from "m" random mutations

        x_new,_,_ = get_reps([s_new],params=params,mlstm_size=64)
        feat_cols = ['feat' + str(j) for j in range(1, x_new.shape[1] + 1)]
        x_new = pd.DataFrame(x_new, columns=feat_cols)

        y_new = Model.predict(x_new) # new fitness value for trial sequence

        p = min(1,np.exp((y_new-y)/T)) # probability function for trial sequence
        rand_var = random.random()

        if rand_var < p: # metropolis-Hastings update selection criterion
            logger.debug(str(new_mut_loc+1)+" "+s[new_mut_loc]+"->"+s_new[new_mut_loc])
            s, y = s_new, y_new # if criteria is met, update sequence and corresponding fitness

        s_traj.append(s) # update the sequence trajectory records for this iteration of mutagenesis
        y_traj.append(y) # update the fitness trajectory records for this iteration of mutagenesis

    return s_traj, y_traj # output = (sequence record for trajectory, fitness score recorf for trajectory)

def runDirectedEvoTrajectories(s_wt, Model, T, num_iterations, num_trajectories, params):
    s_records = [] # initialize list of sequence records
    y_records = [] # initialize list of fitness score records

    for i in range(num_trajectories): #iterate through however many mutation trajectories we want to sample
        s_traj, y_traj = directedEvolution(s_wt,num_iterations,T,Model,params) # call the directed evolution function, outputting the trajectory sequence and fitness score records

        s_records.append(s_traj) # update the sequence trajectory records for this full mutagenesis trajectory
        y_records.append(y_traj) # update the fitness trajectory records for this full mutagenesis trajectory
        
        logger.debug("finished trajectory #",i)

    s_records = np.array(s_records)
    y_records = np.array(y_records)

    return s_records, y_records