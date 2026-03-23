from enum import Enum
from dataclasses import dataclass, field
from models import UserProfile


class Phase(Enum):
    INTERVIEW = "interview"
    COMPLETE = "complete"


@dataclass
class SessionState:
    phase: Phase = Phase.INTERVIEW
    profile: UserProfile = field(default_factory=UserProfile)
    messages: list[dict] = field(default_factory=list)
    turn_count: int = 0
    interview_complete: bool = False
