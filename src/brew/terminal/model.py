"""WebSocket control-frame models.

Bytes flow over the WS as binary frames; structured control messages (resize)
arrive as text frames containing JSON. This module defines the schema for those
JSON frames.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ResizeFrame(BaseModel):
    """Sent by the frontend when the terminal container is resized.

    Maps to a TIOCSWINSZ ioctl on the PTY master.
    """

    type: Literal["resize"]
    rows: int = Field(gt=0)
    cols: int = Field(gt=0)
