from common.db import downloadFromBucket

def getSequencesFromDB(bucketName, folderName, fileName):
    # TODO: implement
    # sequences = downloadFromBucket(bucketName, folderName, fileName)
    sequences = {
        "sequences": ["HASTA", "VISTA", "ALAVA", "LIMED", "HAST", "HAS", "HASVASTA"] * 5, 
        "holdoutSequences": ["HASTA", "VISTA", "ALAVA", "LIMED", "HAST", "HASVALTA"] * 5
        }
    return sequences