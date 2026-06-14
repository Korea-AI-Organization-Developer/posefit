from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """API 입출력 공통 베이스.

    - 내부 필드는 snake_case(ORM 과 동일), JSON 은 camelCase(openapi 와 동일).
      FastAPI 는 응답을 by_alias 로 직렬화하므로 출력이 camelCase 가 된다.
    - 요청은 alias(camelCase)와 필드명(snake_case) 둘 다 허용(populate_by_name).
    - from_attributes: ORM 객체에서 바로 model_validate 가능.
    - protected_namespaces=(): `model_version` 같은 필드명 경고 방지.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        protected_namespaces=(),
    )
