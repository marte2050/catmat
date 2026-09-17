from __future__ import annotations

import asyncio
import logging

import typer

from catmat.etl.loaders import RESOURCES
from catmat.etl.pipelines import ETLPipeline

app = typer.Typer(
    help="ETL dos dados de CATMAT da API de dados abertos do Compras.gov.br.",
    add_completion=False,
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """Comandos de carga (população) das tabelas do CATMAT."""


@app.command()
def sync(
    resource: str = typer.Argument(
        "all",
        help=f"Recurso a carregar: all, {', '.join(RESOURCES)}.",
    ),
    page_size: int | None = typer.Option(
        None, "--page-size", help="Registros por página da API (10-500)."
    ),
    concurrency: int | None = typer.Option(
        None, "--concurrency", help="Páginas buscadas em paralelo."
    ),
    request_interval: float | None = typer.Option(
        None, "--request-interval", help="Intervalo mínimo (s) entre requisições."
    ),
    max_retries: int | None = typer.Option(
        None, "--max-retries", help="Tentativas por página em caso de 429/5xx."
    ),
    batch_size: int | None = typer.Option(
        None, "--batch-size", help="Linhas por lote de upsert."
    ),
    limit_pages: int | None = typer.Option(
        None, "--limit-pages", help="Limite de páginas por recurso (debug)."
    ),
    log_level: str = typer.Option("INFO", "--log-level", help="Nível de log."),
) -> None:
    logging.basicConfig(
        level=log_level.upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    normalized = resource.replace("_", "-").lower()
    if normalized != "all" and normalized not in RESOURCES:
        raise typer.BadParameter(
            f"Recurso inválido: '{resource}'. Use: all, {', '.join(RESOURCES)}."
        )

    targets = list(RESOURCES) if normalized == "all" else [normalized]

    pipeline = ETLPipeline(
        page_size=page_size,
        concurrency=concurrency,
        request_interval=request_interval,
        batch_size=batch_size,
        retries=max_retries,
        limit_pages=limit_pages,
    )

    try:
        counts = asyncio.run(pipeline.run(targets))
    except (RuntimeError, ValueError) as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error

    typer.secho("Carga concluída:", fg=typer.colors.GREEN)
    for name, total in counts.items():
        typer.echo(f"  {name}: {total}")
