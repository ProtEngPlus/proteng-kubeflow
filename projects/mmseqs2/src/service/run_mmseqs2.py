import datetime
import json
import re
import subprocess

import numpy as np
import pandas as pd
from bson import ObjectId
from src.logger import mmseqs2Logger as logger
from src.model.model import MMseqs2Params

from pkg.common.db import uploadToBucket
from pkg.common.publisher import *


def runMMseqs2Thread(mmseqs2Params: MMseqs2Params, jobId, queryResultId, randomState):
    try:
        logger.info(f"job id {jobId}: Running MMseqs2")

        seq_length = mmseqs2Params.seq_length

        current_dir = os.getcwd()
        QUERY_FILE = "query.fasta"
        DB_FILE = "uniprot_sprot.fasta"
        RESULT_FILE = "result.m8"
        TMP_DIR = "tmp"

        # Create query file
        with open(os.path.join(current_dir, QUERY_FILE), "w") as f:
            f.write(f">input_protein\n{mmseqs2Params.sequence}\n")

        # Ensure tmp dir exists
        tmp_dir_path = os.path.join(current_dir, TMP_DIR)
        if not os.path.exists(tmp_dir_path):
            os.makedirs(tmp_dir_path)

        # Clean result if already exists
        result_file_path = os.path.join(current_dir, RESULT_FILE)
        if os.path.exists(result_file_path):
            os.remove(result_file_path)

        cmd = [
            "mmseqs",
            "easy-search",
            f"{current_dir}/{QUERY_FILE}",
            f"{current_dir}/{DB_FILE}",
            f"{current_dir}/{RESULT_FILE}",
            f"{current_dir}/{TMP_DIR}",
            "--format-output",
            "tseq,raw,bits,qstart,qend,evalue,target,pident,tlen,alnlen,theader",
            "--max-seqs",
            str(mmseqs2Params.max_seqs),
            "-e",
            str(mmseqs2Params.e),
            "--min-seq-id",
            str(mmseqs2Params.min_seq_id / 100),
            "--min-aln-len",
            str(mmseqs2Params.min_aln_len),
            "--cov-mode",
            str(mmseqs2Params.cov_mode),
            "-c",
            str(mmseqs2Params.c / 100),
        ]
        raw_result = subprocess.run(
            cmd, capture_output=True, text=True, check=False, timeout=600
        )

        if raw_result.returncode != 0 or not os.path.exists(RESULT_FILE):
            logger.error(f"job id {jobId}: error run mmseqs2: No result from mmseqs2")
            message = JobStatusEventMessage(
                service_name="mmseqs2-microservice",
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                data=JobUpdateData(
                    job_id=jobId,
                    stage_id=0,
                    status="FAILED",
                    artifact=Artifact(bucket_name="similar_protein", path=jobId),
                    error="No result from mmseqs2",
                ),
            )
            publishJobStatusEvent(message)
            logger.info(f"Job {jobId} failed")
            return

        with open(RESULT_FILE, "r") as f:
            lines = [line.strip() for line in f if line.strip()]

        # Data preparation
        split_list = [s.split("\t") for s in lines]
        processed_list = []
        for row in split_list:
            last_element = row[-1]
            protein_name, organism_name = extract_info(last_element)

            row = row[:-1]
            row.append(protein_name)
            row.append(organism_name)

            processed_list.append(row)

        df = pd.DataFrame(
            processed_list,
            columns=[
                "sequences",
                "score",
                "max_score",
                "hsp_query_from",
                "hsp_query_to",
                "e_values",
                "accession",
                "percent_identity",
                "acc_len",
                "aln_len",
                "description",
                "organisms",
            ],
        )

        df["score"] = df["score"].astype(int)
        df["max_score"] = df["max_score"].astype("float64")
        df["hsp_query_from"] = df["hsp_query_from"].astype(int)
        df["hsp_query_to"] = df["hsp_query_to"].astype(int)
        df["e_values"] = df["e_values"].astype("float64")
        df["percent_identity"] = df["percent_identity"].astype("float64")
        df["acc_len"] = df["acc_len"].astype(int)
        df["aln_len"] = df["aln_len"].astype(int)
        df["length"] = df["sequences"].apply(len)
        df["Id"] = [str(ObjectId()) for _ in range(len(df))]
        df["is_selected"] = [True for _ in range(len(df))]

        query_length = len(mmseqs2Params.sequence)
        cov_mode = mmseqs2Params.cov_mode

        if cov_mode == 1 or cov_mode == 4:
            df["query_cover"] = (df["aln_len"] / df["length"]) * 100
        elif cov_mode == 2 or cov_mode == 3:
            df["query_cover"] = (df["aln_len"] / query_length) * 100
        else:
            df["query_cover"] = (
                df["aln_len"] / np.maximum(query_length, df["length"])
            ) * 100

        df.drop(columns=["aln_len"], inplace=True)

        filtered_df = df[df["length"] < seq_length].dropna(subset=["query_cover"])
        isEmpty = False
        # Check if filtered_df is empty and log or return an empty list if true
        if filtered_df.empty:
            logger.info("No rows match the filter conditions, returning empty list.")
            filtered_df = df.dropna(subset=["query_cover"])
            isEmpty = True

        query_result = filtered_df.to_dict(orient="records")

        query_resultJson = filtered_df.to_json(orient="split")
        results = {"query_results": query_resultJson, "randomState": randomState}
        resultsJson = json.dumps(results)

        logger.info(f"job id {jobId}: Uploading results to object storage")
        # Upload the JSON string directly to the object storage bucket
        upload_status = uploadToBucket("similar_protein", jobId, resultsJson)
        logger.info(f"job id {jobId}: Upload status: {upload_status}")

        if isEmpty:
            logger.error(f"job id {jobId}: error run mmseqs2: No sequence found")
            message = JobStatusEventMessage(
                service_name="mmseqs2-microservice",
                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                data=JobUpdateData(
                    job_id=jobId,
                    stage_id=0,
                    status="FAILED",
                    artifact=Artifact(bucket_name="similar_protein", path=jobId),
                    error="No sequence found",
                ),
            )
            publishJobStatusEvent(message)
            logger.info(f"Job {jobId} failed")
            return

        message = JobStatusEventMessage(
            service_name="mmseqs2-microservice",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            data=JobUpdateData(
                job_id=jobId,
                stage_id=0,
                status="COMPLETED",
                artifact=Artifact(bucket_name="similar_protein", path=jobId),
                query_result_id=queryResultId,
                query_result=query_result,
            ),
        )
        publishJobStatusEvent(message)
        logger.info(f"Job {jobId} completed successfully")
    except Exception as err:  # noqa: BLE001 -- reports failure via job-status queue
        logger.error(
            f"job id {jobId}: error run mmseqs2: Unexpected {err=}, {type(err)=}"
        )
        message = JobStatusEventMessage(
            service_name="mmseqs2-microservice",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            data=JobUpdateData(
                job_id=jobId,
                stage_id=0,
                status="FAILED",
                artifact=Artifact(bucket_name="similar_protein", path=jobId),
                error=str(err),
            ),
        )
        publishJobStatusEvent(message)


def extract_info(theader):
    theader = theader.lstrip(">")
    protein_match = re.search(r"^[^|]+\|[^|]+\|[^| ]+ (.+?) OS=", theader)
    protein_name = protein_match.group(1).strip() if protein_match else None
    organism_match = re.search(r"OS=(.*?)\s+OX=", theader)
    organism_name = organism_match.group(1).strip() if organism_match else None
    return protein_name, organism_name
