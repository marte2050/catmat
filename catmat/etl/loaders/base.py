from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from catmat.etl.client import ComprasApiClient
from catmat.etl.repository import bulk_upsert
from catmat.etl.schemas import ApiModel


class BaseLoader(ABC):
    """
        Classe responsável por fornecer a estrutura base para os loaders que interagem com a API do ComprasNet e 
        realizam operações de carregamento de dados no banco de dados. Cada loader específico deve herdar desta classe 
        e implementar o método `to_model` para converter os DTOs recebidos da API em instâncias do modelo SQLAlchemy correspondente.
    """
    
    name: str
    endpoint: str
    dto_cls: type[ApiModel]
    model: type[DeclarativeBase]
    index_elements: Sequence[str]

    @abstractmethod
    def to_model(self, dto: ApiModel) -> DeclarativeBase: 
        """Método abstrado a ser implementado pelas subclasses para converter um DTO em uma instância do modelo 
        SQLAlchemy correspondente.

        :param dto: Instância do DTO a ser convertida.
        :return: Instância do modelo SQLAlchemy correspondente ao DTO.        
        """

    async def process_batch(
        self,
        session: AsyncSession,
        dtos: Sequence[ApiModel],
        *,
        batch_size: int,
    ) -> int:
        instances = [self.to_model(dto) for dto in dtos]
        return await bulk_upsert(
            session,
            self.model,
            instances,
            index_elements=self.index_elements,
            chunk_size=batch_size,
        )

    async def load(
        self,
        session: AsyncSession,
        client: ComprasApiClient,
        *,
        batch_size: int,
        limit_pages: int | None = None,
    ) -> int:
        total = 0
        page_index = 0
        async for records in client.iter_pages(self.endpoint):
            page_index += 1
            if records:
                dtos = [self.dto_cls.model_validate(record) for record in records]
                total += await self.process_batch(session, dtos, batch_size=batch_size)
                await session.commit()
            if limit_pages is not None and page_index >= limit_pages:
                break
        return total
