import logging
import time
from typing import Optional
import uuid

from sqlalchemy.orm import Session
from open_webui.internal.db import Base, get_db, get_db_context
from open_webui.models.users import User, UserModel, Users, UserResponse

from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    BigInteger,
    Column,
    String,
    Text,
    JSON,
    or_,
    and_,
)

log = logging.getLogger(__name__)

####################
# Episode DB Schema
####################


class Episode(Base):
    __tablename__ = "episode"

    id = Column(Text, unique=True, primary_key=True)
    user_id = Column(Text, nullable=False)

    title = Column(Text, nullable=True)
    question = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=True)
    solution = Column(Text, nullable=False)
    references = Column(JSON, nullable=True)  # 引用来源数组

    chat_id = Column(Text, nullable=True)  # 来源对话ID
    department = Column(Text, nullable=True)  # 所属部门

    status = Column(Text, default="draft")  # draft, published

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class EpisodeModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str

    title: Optional[str] = None
    question: str
    reasoning: Optional[str] = None
    solution: str
    references: Optional[list[str]] = None

    chat_id: Optional[str] = None
    department: Optional[str] = None

    status: str = "draft"  # draft, published

    created_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch


####################
# Forms
####################


class EpisodeForm(BaseModel):
    title: Optional[str] = None
    question: str
    reasoning: Optional[str] = None
    solution: str
    references: Optional[list[str]] = None
    chat_id: Optional[str] = None
    status: str = "draft"


class EpisodeGenerateForm(BaseModel):
    chat_id: str
    messages: list[dict]  # 对话消息列表


class EpisodeUserModel(EpisodeModel):
    user: Optional[UserResponse] = None


class EpisodeResponse(EpisodeModel):
    pass


class EpisodeListResponse(BaseModel):
    items: list[EpisodeUserModel]
    total: int


####################
# Table
####################


class EpisodeTable:
    def insert_new_episode(
        self,
        user_id: str,
        form_data: EpisodeForm,
        department: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Optional[EpisodeModel]:
        with get_db_context(db) as db:
            episode = EpisodeModel(
                **{
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "title": form_data.title,
                    "question": form_data.question,
                    "reasoning": form_data.reasoning,
                    "solution": form_data.solution,
                    "references": form_data.references,
                    "chat_id": form_data.chat_id,
                    "department": department,
                    "status": form_data.status,
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                }
            )

            try:
                result = Episode(**episode.model_dump())
                db.add(result)
                db.commit()
                db.refresh(result)
                if result:
                    return episode
                else:
                    return None
            except Exception as e:
                log.exception(e)
                return None

    def get_episode_by_id(
        self, id: str, db: Optional[Session] = None
    ) -> Optional[EpisodeModel]:
        try:
            with get_db_context(db) as db:
                episode = db.query(Episode).filter_by(id=id).first()
                return EpisodeModel.model_validate(episode) if episode else None
        except Exception:
            return None

    def get_episodes_by_user_id(
        self,
        user_id: str,
        user_department: Optional[str] = None,
        skip: int = 0,
        limit: int = 30,
        db: Optional[Session] = None,
    ) -> EpisodeListResponse:
        """
        获取用户可见的 Episode 列表：
        - 用户自己创建的
        - 同部门的（如果设置了部门）
        """
        try:
            with get_db_context(db) as db:
                query = db.query(Episode, User).outerjoin(
                    User, User.id == Episode.user_id
                )

                # 权限过滤：自己的或同部门的
                if user_department:
                    query = query.filter(
                        or_(
                            Episode.user_id == user_id,
                            Episode.department == user_department,
                        )
                    )
                else:
                    query = query.filter(Episode.user_id == user_id)

                query = query.order_by(Episode.updated_at.desc(), Episode.id.asc())

                total = query.count()
                if skip:
                    query = query.offset(skip)
                if limit:
                    query = query.limit(limit)

                items = query.all()

                episodes = []
                for episode, user in items:
                    episodes.append(
                        EpisodeUserModel.model_validate(
                            {
                                **EpisodeModel.model_validate(episode).model_dump(),
                                "user": (
                                    UserResponse.model_validate(user).model_dump()
                                    if user
                                    else None
                                ),
                            }
                        )
                    )

                return EpisodeListResponse(items=episodes, total=total)
        except Exception as e:
            log.exception(e)
            return EpisodeListResponse(items=[], total=0)

    def update_episode_by_id(
        self,
        id: str,
        form_data: EpisodeForm,
        db: Optional[Session] = None,
    ) -> Optional[EpisodeModel]:
        try:
            with get_db_context(db) as db:
                db.query(Episode).filter_by(id=id).update(
                    {
                        "title": form_data.title,
                        "question": form_data.question,
                        "reasoning": form_data.reasoning,
                        "solution": form_data.solution,
                        "references": form_data.references,
                        "status": form_data.status,
                        "updated_at": int(time.time()),
                    }
                )
                db.commit()
                return self.get_episode_by_id(id=id, db=db)
        except Exception as e:
            log.exception(e)
            return None

    def delete_episode_by_id(self, id: str, db: Optional[Session] = None) -> bool:
        try:
            with get_db_context(db) as db:
                db.query(Episode).filter_by(id=id).delete()
                db.commit()
                return True
        except Exception:
            return False

    def delete_episodes_by_chat_id(
        self, chat_id: str, db: Optional[Session] = None
    ) -> bool:
        try:
            with get_db_context(db) as db:
                db.query(Episode).filter_by(chat_id=chat_id).delete()
                db.commit()
                return True
        except Exception:
            return False


Episodes = EpisodeTable()
