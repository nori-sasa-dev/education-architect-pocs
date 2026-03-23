from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    name: str = ""
    current_job: str = ""
    career_change_reason: str = ""
    values: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    things_to_avoid: list[str] = Field(default_factory=list)

    def is_sufficient(self) -> bool:
        return (
            bool(self.current_job)
            and bool(self.career_change_reason)
            and len(self.values) >= 1
            and len(self.skills) >= 1
        )

    def summary(self) -> str:
        lines = ["=== あなたのプロフィール ==="]
        if self.name:
            lines.append(f"名前         : {self.name}")
        if self.current_job:
            lines.append(f"現職         : {self.current_job}")
        if self.career_change_reason:
            lines.append(f"転職理由     : {self.career_change_reason}")
        if self.values:
            lines.append(f"大切にしたいこと: {', '.join(self.values)}")
        if self.interests:
            lines.append(f"興味・関心   : {', '.join(self.interests)}")
        if self.skills:
            lines.append(f"スキル・強み : {', '.join(self.skills)}")
        if self.things_to_avoid:
            lines.append(f"避けたいこと : {', '.join(self.things_to_avoid)}")
        return "\n".join(lines)
