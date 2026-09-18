from __future__ import annotations

import asyncio
import logging

import typer

from catmat.embeddings.pipelines import EmbeddingPipeline

app = typer.Typer(
    help="Geração de embeddings dos itens do CATMAT e envio para o Qdrant.",
    add_completion=False,
    no_args_is_help=True,
)

@app.callback()
def main() -> None: ...

@app.command()
def sync(
    resource: str = typer.Argument(
        "items",
        help="Recurso a embedar (por enquanto: items ou all).",
    ),
    batch_size: int | None = typer.Option(
        None, "--batch-size", help="Itens por lote de embedding."
    ),
    scan_batch_size: int = typer.Option(
        1000, "--scan-batch-size", help="Itens lidos do Postgres por lote."
    ),
    limit: int | None = typer.Option(
        None, "--limit", help="Máximo de itens a processar (debug)."
    ),
    recreate: bool = typer.Option(
        False, "--recreate", help="Recria a coleção no Qdrant antes de embedar."
    ),
    log_level: str = typer.Option("INFO", "--log-level", help="Nível de log."),
) -> None:

    logging.basicConfig(
        level=log_level.upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    for noisy in ("httpx", "httpcore", "huggingface_hub", "urllib3", "filelock"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    normalized = resource.replace("_", "-").lower()
    if normalized not in ("items", "all"):
        raise typer.BadParameter("Recurso inválido. Use: items ou all.")

    pipeline = EmbeddingPipeline(
        scan_batch_size=scan_batch_size,
        embed_batch_size=batch_size,
        max_items=limit,
        recreate=recreate,
    )

    try:
        stats = asyncio.run(pipeline.run())
    except Exception as error:
        typer.secho(f"Erro: {error}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from error

    typer.secho("Embeddings concluídos:", fg=typer.colors.GREEN)
    for key, value in stats.items():
        typer.echo(f"  {key}: {value}")
