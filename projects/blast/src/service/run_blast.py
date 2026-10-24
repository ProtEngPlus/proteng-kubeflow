import datetime
import json
import socket

from Bio.Blast import NCBIWWW
from bson import ObjectId
from src.logger import blastLogger as logger
from src.model.model import BlastParams
from src.service.hit_filter import filter_hits
from src.service.hit_parser import (
    attach_full_sequences,
    fetch_fasta,
    parse_fasta_by_accession,
    parse_hits,
)

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

        df = parse_hits(result)
        if not df.empty:
            fasta = fetch_fasta(df["accession"].tolist())
            df, dropped = attach_full_sequences(df, parse_fasta_by_accession(fasta))
            if dropped:
                logger.warning(
                    f"job id {jobId}: dropped {dropped} hits with no full "
                    "sequence from NCBI"
                )

        df["score"] = df["score"].astype(int)
        df["max_score"] = df["max_score"].astype("float64")
        df["hsp_query_from"] = df["hsp_query_from"].astype(int)
        df["hsp_query_to"] = df["hsp_query_to"].astype(int)
        df["e_values"] = df["e_values"].astype("float64")
        df["acc_len"] = df["acc_len"].astype(int)
        df["length"] = df["sequences"].apply(len)
        query_length = len(blastParams.sequence)
        df["query_cover"] = (
            (df["hsp_query_to"] - df["hsp_query_from"] + 1) / query_length
        ) * 100
        df["Id"] = [str(ObjectId()) for _ in range(len(df))]
        df["is_selected"] = [True for _ in range(len(df))]

        filtered_df, fell_back = filter_hits(df, hsp_cov, seq_length)
        if fell_back:
            logger.warning(
                f"job id {jobId}: no hits with query_cover>{hsp_cov} and "
                f"acc_len<={seq_length}; falling back to the cover filter only"
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
