import random

import numpy as np
import pandas as pd
from jax_unirep import get_reps
from src.logger import mutationLogger as logger
from src.service.mutation_space import (
    applyMutations,
    planTrajectoryScopes,
    proposeMutant,
    randomMutant,
)


def get_embedding(seq, representation_type, repr_source):
    if representation_type == "unirep":
        reps, _, _ = get_reps([seq], params=repr_source, mlstm_size=64)
        return reps
    elif representation_type == "ESM":
        reps = repr_source.reshape(1, -1)
        return reps

    else:
        raise ValueError("Unsupported representation_type")


def predictScore(seq, Model, params, representation_type):
    x = get_embedding(
        seq, representation_type, params
    )  # eUniRep, eESM representation of the sequence
    feat_cols = ["feat" + str(j) for j in range(1, x.shape[1] + 1)]
    x = pd.DataFrame(x, columns=feat_cols)

    return float(np.asarray(Model.predict(x)).ravel()[0])  # predicted fitness score


def directedEvolution(
    s_wt,
    num_iterations,
    T,
    scope,
    amino_acids,
    Model,
    params,
    representation_type,
):  # input = (wild-type sequence, number of mutation iterations, "temperature")
    mutated = randomMutant(s_wt, scope, amino_acids)
    s = applyMutations(s_wt, mutated)  # initial mutant sequence for this trajectory
    y = predictScore(s, Model, params, representation_type)

    s_best, y_best = s, y  # best sequence this trajectory has been at

    # iterate through the trial mutation steps for the directed evolution trajectory
    for i in range(num_iterations):
        proposal = proposeMutant(s_wt, mutated, scope, amino_acids)
        s_new = applyMutations(s_wt, proposal)  # new trial sequence

        try:
            y_new = predictScore(s_new, Model, params, representation_type)
        except ValueError:
            logger.warning(f"Skipping sequence due to missing embedding: {s_new}")
            continue

        # probability function for trial sequence
        p = 1.0 if y_new >= y else np.exp((y_new - y) / T)

        if random.random() < p:  # metropolis-Hastings update selection criterion
            mutated, s, y = proposal, s_new, y_new
            if y > y_best:
                s_best, y_best = s, y

    return (
        s_best,
        y_best,
    )  # output = (best sequence of the trajectory, its fitness score)


def runDirectedEvoTrajectories(
    s_wt,
    Model,
    T,
    num_iterations,
    num_trajectories,
    regions,
    num_mutations_low,
    num_mutations_high,
    amino_acids,
    params,
    representation_type,
):
    # what each trajectory may mutate
    scopes = planTrajectoryScopes(
        regions, len(s_wt), num_trajectories, num_mutations_low, num_mutations_high
    )

    s_records = []  # initialize list of best sequences, one per trajectory
    y_records = []  # initialize list of their fitness scores

    for i, scope in enumerate(scopes):
        s_best, y_best = directedEvolution(
            s_wt,
            num_iterations,
            T,
            scope,
            amino_acids,
            Model,
            params,
            representation_type,
        )  # call the directed evolution function, outputting the best sequence and its score

        s_records.append(s_best)
        y_records.append(y_best)

        logger.debug(f"finished trajectory #{i}")

    return s_records, y_records
