from autotask.utils.log import logger

CHONKIE_AVAILABLE = None

def _get_chunker():
    global CHONKIE_AVAILABLE
    if CHONKIE_AVAILABLE is None:
        try:
            from chonkie import RecursiveChunker, RecursiveRules
            CHONKIE_AVAILABLE = True
            return RecursiveChunker, RecursiveRules
        except ImportError:
            CHONKIE_AVAILABLE = False
            logger.warning("Chonkie library not installed. Smart chunking will be disabled. Install with: pip install chonkie")
            return None, None
    elif CHONKIE_AVAILABLE:
        from chonkie import RecursiveChunker, RecursiveRules
        return RecursiveChunker, RecursiveRules
    else:
        return None, None
