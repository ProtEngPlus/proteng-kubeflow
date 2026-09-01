import datetime
import json
import re
import socket

import pandas as pd
from Bio.Blast import NCBIWWW
from bson import ObjectId
from src.logger import blastLogger as logger
from src.model.model import BlastParams

from pkg.common.db import uploadToBucket
from pkg.common.publisher import *

socket.setdefaulttimeout(180)


def runBlastThread(blastParams: BlastParams, jobId, queryResultId, randomState):
    try:
        logger.info(f"job id {jobId}: Running BLAST")

        hsp_cov = blastParams.hsp_cov
        seq_length = blastParams.seq_length
        del blastParams.hsp_cov

        # Run BLAST
        blastArgs = {
            k: v
            for k, v in blastParams.dict().items()
            if v is not None and k != "seq_length"
        }
        resultHandle = NCBIWWW.qblast(**blastArgs)
        result = resultHandle.read()

        # data preparation
        sequences = re.findall(r"<Hsp_hseq>(.*?)</Hsp_hseq>", result)
        scores = re.findall(r"<Hsp_score>(.*?)</Hsp_score>", result)
        max_scores = re.findall(r"<Hsp_bit-score>(.*?)</Hsp_bit-score>", result)
        hsp_query_from = re.findall(r"<Hsp_query-from>(.*?)</Hsp_query-from>", result)
        hsp_query_to = re.findall(r"<Hsp_query-to>(.*?)</Hsp_query-to>", result)
        e_values = re.findall(r"<Hsp_evalue>(.*?)</Hsp_evalue>", result)
        accession = re.findall(r"<Hit_accession>(.*?)</Hit_accession>", result)
        identity = re.findall(r"<Hsp_identity>(.*?)</Hsp_identity>", result)
        align_length = re.findall(r"<Hsp_align-len>(.*?)</Hsp_align-len>", result)
        acc_len = re.findall(r"<Hit_len>(.*?)</Hit_len>", result)
        hit_def = re.findall(r"<Hit_def>(.*?)</Hit_def>", result)

        # Extract protein name, description, and organisms from hit_def
        descriptions = []
        organisms = []

        for hit in hit_def:
            organism_matches = re.findall(r"\[([^\]]+)\]", hit)
            organism = organism_matches[0] if organism_matches else "Unknown"
            organisms.append(organism)

            description = extract_protein_info(hit)
            descriptions.append(description)

        # Calculate percent identity
        identity = list(map(int, identity))  # Convert to integers
        align_length = list(map(int, align_length))  # Convert to integers
        percent_identity = [
            (id_val / align_len) * 100
            for id_val, align_len in zip(identity, align_length)
        ]

        data = {
            "sequences": sequences,
            "score": scores,
            "max_score": max_scores,
            "hsp_query_from": hsp_query_from,
            "hsp_query_to": hsp_query_to,
            "e_values": e_values,
            "accession": accession,
            "percent_identity": percent_identity,
            "acc_len": acc_len,
            "description": descriptions,
            "organisms": organisms,
        }
        df = pd.DataFrame(data)

        df["score"] = df["score"].astype(int)
        df["max_score"] = df["max_score"].astype("float64")
        df["hsp_query_from"] = df["hsp_query_from"].astype(int)
        df["hsp_query_to"] = df["hsp_query_to"].astype(int)
        df["e_values"] = df["e_values"].astype("float64")
        df["acc_len"] = df["acc_len"].astype(int)
        df["length"] = df["sequences"].apply(len)
        df["query_cover"] = (
            (df["hsp_query_to"] - df["hsp_query_from"] + 1) / df["length"]
        ) * 100
        df["Id"] = [str(ObjectId()) for _ in range(len(df))]
        df["is_selected"] = [True for _ in range(len(df))]

        filtered_df = df[
            (df["query_cover"] > hsp_cov) & (df["length"] < seq_length)
        ].dropna(subset=["query_cover"])
        if filtered_df.empty:
            logger.warning(
                f"job id {jobId}: no hits with query_cover>{hsp_cov} and "
                f"length<{seq_length}; falling back to the cover filter only"
            )
            filtered_df = df[(df["query_cover"] > hsp_cov)].dropna(
                subset=["query_cover"]
            )

        if filtered_df.empty:
            logger.error(f"job id {jobId}: error run blast: No sequence found")
            message = JobStatusEventMessage(
                service_name="blast-microservice",
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

        query_result = filtered_df.to_dict(orient="records")

        query_resultJson = filtered_df.to_json(orient="split")
        results = {"query_results": query_resultJson, "randomState": randomState}
        resultsJson = json.dumps(results)

        logger.info(f"job id {jobId}: Uploading results to object storage")
        upload_status = uploadToBucket("similar_protein", jobId, resultsJson)
        logger.info(f"job id {jobId}: Upload status: {upload_status}")

        message = JobStatusEventMessage(
            service_name="blast-microservice",
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
            f"job id {jobId}: error run blast: Unexpected {err=}, {type(err)=}"
        )
        message = JobStatusEventMessage(
            service_name="blast-microservice",
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


def extract_protein_info(hit_def):
    protein_description = re.split(r"\s?\[", hit_def)[
        0
    ].strip()  # Protein name and description
    return protein_description
