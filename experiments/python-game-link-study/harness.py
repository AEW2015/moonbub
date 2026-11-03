"""GM01/GF01 lab adapter. No sockets, installed service or firmware changes."""
from pathlib import Path
import struct
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'python-game-codec-study'))
import game_codec as codec


def decode_complete(completed,ingress,receiver):
    # Validate ownership and the outer identity before any codec-state mutation.
    ingress._owned(completed)
    try:
        if completed.frame<=ingress.committed:raise ValueError('stale delivered frame')
        if len(completed.data)<codec.HEADER.size:raise ValueError('truncated GM01 header')
        fields=codec.HEADER.unpack_from(completed.data)
        if fields[0]!=codec.MAGIC or fields[3:5]!=(completed.epoch,completed.frame):
            raise ValueError('GF01/GM01 identity mismatch')
        rgb,info=receiver.receive(completed.data)
    except (ValueError,struct.error):
        ingress.reject(completed)
        raise
    ingress.commit(completed)
    return rgb,info
