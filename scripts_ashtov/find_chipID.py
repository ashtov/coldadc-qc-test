def find_chipID(filename):
    '''find_chipID(filename) -> str
    Finds chipID string from full filename'''
    index = filename.find('enr_') + 4
    chipID = filename[index:filename.find('_', index)]
    return chipID
