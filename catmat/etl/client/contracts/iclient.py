from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any, Self

import httpx

RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
TRANSPORT_RETRIES = 2


class IComprasApiClient(ABC):
    """Contrato para o adaptador da API de dados abertos do Compras.gov.br."""

    @abstractmethod
    def __init__(
        self,
        *,
        base_url: str | None = None,
        page_size: int | None = None,
        concurrency: int | None = None,
        request_interval: float | None = None,
        timeout: float | None = None,
        retries: int | None = None,
        backoff_base: float | None = None,
        backoff_max: float | None = None,
    ) -> None:
        """
        Construtor do ComprasApiClient.

        :param base_url: URL base da API do Compras.gov.br. Se None, usa o valor padrão.
        :param page_size: Tamanho da página para requisições paginadas. Se None, usa o valor padrão.
        :param concurrency: Número máximo de requisições simultâneas. Se None, usa o valor padrão.
        :param request_interval: Intervalo mínimo entre requisições em segundos. Se None, usa o valor padrão.
        :param timeout: Tempo limite para requisições em segundos. Se None, usa o valor padrão.
        :param retries: Número máximo de tentativas de retry para requisições falhas. Se None, usa o valor padrão.
        :param backoff_base: Base do backoff exponencial para retries. Se None, usa o valor padrão.
        :param backoff_max: Máximo tempo de espera para retries em segundos. Se None, usa o valor padrão.
        """

    @property
    @abstractmethod
    def client(self) -> httpx.AsyncClient:
        """
        Retorna o cliente HTTP assíncrono configurado para interagir com a API do Compras.gov.br.

        :return: Instância de httpx.AsyncClient.
        """

    @abstractmethod
    async def __aenter__(self) -> Self:
        """
        Método de entrada assíncrono para o contexto do cliente.

        :return: Instância de ComprasApiClient.
        """

    @abstractmethod
    async def __aexit__(self, *exc_info: object) -> None:
        """Método de saída assíncrono para o contexto do cliente."""

    @abstractmethod
    async def _throttle(self) -> None:
        """Garante que as requisições à API respeitem o intervalo mínimo configurado entre elas."""

    @staticmethod
    @abstractmethod
    def _retry_after(response: httpx.Response) -> float | None:
        """
        Extrai o valor do cabeçalho 'Retry-After' da resposta HTTP, se presente.

        :return: Tempo em segundos para aguardar antes de tentar novamente, ou None se não houver cabeçalho.
        """

    @abstractmethod
    async def _wait_before_retry(
        self,
        attempt: int,
        *,
        endpoint: str,
        page: int,
        reason: str,
        retry_after: float | None = None,
    ) -> None:
        """
        Aguarda antes de tentar novamente, com base no tempo especificado no cabeçalho 'Retry-After'.

        :param attempt: Número da tentativa.
        :param endpoint: Endpoint da API.
        :param page: Página da requisição.
        :param reason: Motivo para o retry.
        :param retry_after: Tempo em segundos para aguardar antes de tentar novamente.
        """

    @abstractmethod
    async def fetch_page(
        self,
        endpoint: str,
        page: int,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """
        Busca uma página específica de dados da API do Compras.gov.br.

        :param endpoint: Endpoint da API.
        :param page: Número da página a ser buscada.
        :param page_size: Tamanho da página. Se None, usa o valor padrão.
        """

    @abstractmethod
    async def iter_pages(self, endpoint: str) -> AsyncIterator[list[dict[str, Any]]]:
        """
        Itera sobre todas as páginas de dados disponíveis para um determinado endpoint da API do Compras.gov.br.

        :param endpoint: Endpoint da API.
        :yield: Lista de registros de cada página.
        """
