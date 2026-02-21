from app.database import Base
from sqlalchemy.orm import Mapped , mapped_column , relationship 
from sqlalchemy import String , Integer , TIMESTAMP , func , ForeignKey
from datetime import datetime

class Files(Base):
    __tablename__ = "files"
    file_id:Mapped[int]  = mapped_column(primary_key=True)
    file_name:Mapped[str] = mapped_column(String(255) , nullable=False)
    file_url:Mapped[str] = mapped_column(String(500) , nullable=False)
    file_size:Mapped[int] = mapped_column(Integer , nullable=False)
    mime_type:Mapped[str] = mapped_column(String(50))
    uploaded_at:Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True) , server_default=func.now())
    user_id:Mapped[int] = mapped_column(ForeignKey("users.user_id"))

    user:Mapped[list["User"]] = relationship(
        secondary="user_files",
        back_populates="file",
        viewonly=True

    )


class User(Base):
    __tablename__ = "users"
    user_id:Mapped[int] = mapped_column(primary_key=True)
    username:Mapped[str] = mapped_column(String(50) , nullable=False , unique=True)
    email:Mapped[str] = mapped_column(String(254) , nullable=False , unique=True)
    password:Mapped[str] = mapped_column(nullable=False)
    is_active:Mapped[bool] = mapped_column(default=True)
    failed_login_attempts:Mapped[int] = mapped_column(default=0)
    locked_until:Mapped[datetime|None] = mapped_column(TIMESTAMP(timezone=True))
    created_at:Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),server_default=func.now())
    last_login : Mapped[datetime|None] = mapped_column(TIMESTAMP(timezone=True),   nullable=True)

    file: Mapped[list["Files"]] = relationship(
        secondary="user_files",
        back_populates="user",
        viewonly=True
    )

class User_Files(Base):
    __tablename__ = "user_files"
    user_id:Mapped[int] = mapped_column(ForeignKey("users.user_id") ,  primary_key=True)
    file_id:Mapped[int] = mapped_column(ForeignKey("files.file_id") , primary_key=True)

