from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import FaceEmbedding, User


class FaceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_embedding(self, user_id: int, embedding: bytes, model_version: str) -> FaceEmbedding:
        existing = await self.db.get(FaceEmbedding, user_id)
        if existing:
            existing.embedding = embedding
            existing.model_version = model_version
        else:
            existing = FaceEmbedding(
                user_id=user_id,
                embedding=embedding,
                model_version=model_version,
            )
            self.db.add(existing)
        return existing

    async def get_all_embeddings(self) -> list[tuple[FaceEmbedding, User]]:
        result = await self.db.execute(
            select(FaceEmbedding, User).join(User, User.id == FaceEmbedding.user_id)
        )
        return result.all()
