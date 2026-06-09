from sqlalchemy.ext.asyncio import AsyncSession

from ai.face.detector import MODEL, extract_embedding, is_same_person
from app.models.user import FaceEmbedding, User
from app.repositories.face import FaceRepository

MODEL_VERSION = f"{MODEL}-v1"


class FaceService:
    def __init__(self, db: AsyncSession):
        self.repo = FaceRepository(db)
        self.db = db

    async def register(self, user_id: int, base64_image: str) -> None:
        """얼굴 임베딩 추출 후 DB 저장."""
        embedding = extract_embedding(base64_image)
        await self.repo.save_embedding(user_id, embedding, MODEL_VERSION)
        await self.db.commit()

    async def identify(self, base64_image: str) -> User | None:
        """전체 등록 얼굴과 비교해 일치하는 유저 반환. 없으면 None."""
        rows: list[tuple[FaceEmbedding, User]] = await self.repo.get_all_embeddings()
        best_user: User | None = None
        best_distance = float("inf")

        for face_emb, user in rows:
            try:
                matched, distance = is_same_person(face_emb.embedding, base64_image)
                if matched and distance < best_distance:
                    best_distance = distance
                    best_user = user
            except Exception:
                continue

        return best_user
