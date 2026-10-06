def convertTwoArraysToDict(array1, array2):
    if len(array1) != len(array2):
        raise ValueError("Array lengths do not match")
    return {array1[i]: array2[i] for i in range(len(array1))}
