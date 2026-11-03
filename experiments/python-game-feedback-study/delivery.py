"""Immediate functional adapter; finite pipeline separately charges services."""
from pathlib import Path
import sys
import transport

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'python-game-codec-study'))
import game_codec as codec


def decode_completed(complete,ingress,receiver):
    ingress._owned(complete)
    try:
        if complete.frame<=ingress.committed:raise ValueError('stale delivered frame')
        if len(complete.data)<codec.HEADER.size:raise ValueError('truncated GM01')
        fields=codec.HEADER.unpack_from(complete.data)
        if fields[0]!=codec.MAGIC or fields[3:5]!=(complete.epoch,complete.frame):
            raise ValueError('GF02/GM01 identity mismatch')
        if transport.content_crc(complete.data)!=complete.frame_crc:
            raise ValueError('GF02/GM01 content tag mismatch')
        rgb,info=receiver.receive(complete.data)
    except ValueError as error:
        ingress.reject(complete)
        feedback=transport.feedback_datagram(complete.epoch,complete.frame,transport.NACK,complete.frame_crc,4)
        return None,None,feedback,str(error)
    ingress.commit(complete)
    feedback=transport.feedback_datagram(complete.epoch,complete.frame,transport.ACK,complete.frame_crc,0)
    return rgb,info,feedback,None
