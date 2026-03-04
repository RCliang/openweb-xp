import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from open_webui.models.episodes import (
    EpisodeForm,
    EpisodeGenerateForm,
    EpisodeModel,
    EpisodeResponse,
    EpisodeListResponse,
    Episodes,
)
from open_webui.models.users import UserModel
from open_webui.utils.auth import get_verified_user
from open_webui.internal.db import get_session

log = logging.getLogger(__name__)

router = APIRouter()

############################
# GetEpisodes
############################


@router.get("/", response_model=EpisodeListResponse)
async def get_episodes(
    request: Request,
    skip: int = 0,
    limit: int = 30,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    """
    获取 Episode 列表。
    返回用户自己创建的 + 同部门的 Episode。
    """
    user_department = getattr(user, "department", None)
    return Episodes.get_episodes_by_user_id(
        user_id=user.id,
        user_department=user_department,
        skip=skip,
        limit=limit,
        db=db,
    )


############################
# CreateEpisode
############################


@router.post("/", response_model=EpisodeResponse)
async def create_episode(
    request: Request,
    form_data: EpisodeForm,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    """
    创建 Episode。
    """
    user_department = getattr(user, "department", None)
    episode = Episodes.insert_new_episode(
        user_id=user.id,
        form_data=form_data,
        department=user_department,
        db=db,
    )
    if episode:
        return episode
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建 Episode 失败",
        )


############################
# GetEpisodeById
############################


@router.get("/{id}", response_model=EpisodeResponse)
async def get_episode_by_id(
    id: str,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    """
    获取单个 Episode。
    """
    episode = Episodes.get_episode_by_id(id=id, db=db)
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode 不存在",
        )

    # 权限检查：用户必须是创建者或同部门
    user_department = getattr(user, "department", None)
    if episode.user_id != user.id:
        if not (user_department and episode.department == user_department):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此 Episode",
            )

    return episode


############################
# UpdateEpisode
############################


@router.post("/{id}", response_model=EpisodeResponse)
async def update_episode(
    id: str,
    form_data: EpisodeForm,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    """
    更新 Episode。
    """
    episode = Episodes.get_episode_by_id(id=id, db=db)
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode 不存在",
        )

    # 权限检查：只有创建者可以更新
    if episode.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权更新此 Episode",
        )

    episode = Episodes.update_episode_by_id(id=id, form_data=form_data, db=db)
    if episode:
        return episode
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新 Episode 失败",
        )


############################
# DeleteEpisode
############################


@router.delete("/{id}")
async def delete_episode(
    id: str,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    """
    删除 Episode。
    """
    episode = Episodes.get_episode_by_id(id=id, db=db)
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode 不存在",
        )

    # 权限检查：只有创建者可以删除
    if episode.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此 Episode",
        )

    success = Episodes.delete_episode_by_id(id=id, db=db)
    if success:
        return {"success": True}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除 Episode 失败",
        )


############################
# GenerateEpisode (AI 半自动提取)
############################


@router.post("/generate", response_model=EpisodeForm)
async def generate_episode_draft(
    request: Request,
    form_data: EpisodeGenerateForm,
    user=Depends(get_verified_user),
):
    """
    AI 生成 Episode 草稿。
    根据对话内容，自动提取问题、推理过程、解决方案和引用来源。
    """
    try:
        # 构建提示词
        messages = form_data.messages

        # 提取对话内容
        conversation = ""
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                conversation += f"用户: {content}\n\n"
            elif role == "assistant":
                conversation += f"助手: {content}\n\n"

        # 构建 AI 提示词
        prompt = f"""请分析以下对话，提取结构化经验（Episode）。

对话内容：
{conversation}

请按以下格式输出（JSON）：
{{
    "title": "简短标题（可选）",
    "question": "用户遇到的问题描述",
    "reasoning": "解决问题的推理过程",
    "solution": "最终解决方案",
    "references": ["引用的文档或资料（如有）"]
}}

注意：
1. question 应该清晰描述用户遇到的问题
2. reasoning 应该包含分析过程和关键步骤
3. solution 应该是可操作的具体步骤
4. references 列出对话中提到的参考文档

只输出 JSON，不要有其他内容。"""

        # 调用 OpenAI API 生成草稿
        from open_webui.utils.misc import get_openai_client

        client = get_openai_client(request)

        response = client.chat.completions.create(
            model=request.app.state.config.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的知识管理助手，擅长从对话中提取结构化经验。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )

        import json

        result_text = response.choices[0].message.content.strip()

        # 尝试解析 JSON
        try:
            # 移除可能的 markdown 代码块标记
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1]
            if result_text.endswith("```"):
                result_text = result_text.rsplit("\n", 1)[0]

            result = json.loads(result_text)
        except json.JSONDecodeError:
            # 如果解析失败，返回原始文本作为 solution
            result = {
                "title": "从对话提取的经验",
                "question": "请手动编辑问题",
                "reasoning": "",
                "solution": result_text,
                "references": [],
            }

        return EpisodeForm(
            title=result.get("title"),
            question=result.get("question", ""),
            reasoning=result.get("reasoning"),
            solution=result.get("solution", ""),
            references=result.get("references"),
            chat_id=form_data.chat_id,
            status="draft",
        )

    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成 Episode 草稿失败: {str(e)}",
        )
