from common.db import downloadFromBucket

def getSequencesFromDB(bucketName, fileName):
    # TODO: implement
    # sequences = downloadFromBucket(bucketName, folderName, fileName)
    sequences = {
        "train_set": ["HASTA", "VISTA", "ALAVA", "LIMED", "HAST", "HAS", "HASVASTA"] * 5, 
        "out_domain_val_set": ["HASTA", "VISTA", "ALAVA", "LIMED", "HAST", "HASVALTA"] * 5
        }
    return sequences