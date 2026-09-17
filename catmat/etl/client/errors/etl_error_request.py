class ETLRequestError(RuntimeError):
    def __init__(
        self,
        endpoint: str,
        page: int,
        attempts: int,
        *,
        status_code: int | None = None,
        cause: Exception | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.page = page
        self.status_code = status_code
        detail = f"HTTP {status_code}" if status_code else "erro de rede"
        super().__init__(
            f"Falha ao obter '{endpoint}' (página {page}) após {attempts} "
            f"tentativas: {detail}. Rode novamente para retomar (upsert idempotente)."
        )
        if cause is not None:
            self.__cause__ = cause