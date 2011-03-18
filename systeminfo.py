import os

def is_win64():
    if os.environ.get('PROCESSOR_ARCHITECTURE', None) == 'AMD64':
        return True
    elif os.environ.get('PROCESSOR_ARCHITEW6432', None) == 'AMD64':
        return True
    else:
        return False
