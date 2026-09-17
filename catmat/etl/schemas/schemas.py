from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        coerce_numbers_to_str=True,
    )


class GroupDTO(ApiModel):
    group_code: int = Field(alias="codigoGrupo")
    group_name: str = Field(alias="nomeGrupo")
    group_status: bool = Field(alias="statusGrupo")
    updated_at: datetime = Field(alias="dataHoraAtualizacao")


class ClassDTO(ApiModel):
    class_code: int = Field(alias="codigoClasse")
    group_code: int = Field(alias="codigoGrupo")
    class_name: str = Field(alias="nomeClasse")
    class_status: bool = Field(alias="statusClasse")
    updated_at: datetime = Field(alias="dataHoraAtualizacao")


class PdmDTO(ApiModel):
    pdm_code: int = Field(alias="codigoPdm")
    class_code: int = Field(alias="codigoClasse")
    pdm_name: str = Field(alias="nomePdm")
    pdm_status: bool = Field(alias="statusPdm")
    updated_at: datetime = Field(alias="dataHoraAtualizacao")


class ItemDTO(ApiModel):
    item_code: int = Field(alias="codigoItem")
    pdm_code: int = Field(alias="codigoPdm")
    item_description: str = Field(alias="descricaoItem")
    item_status: bool = Field(alias="statusItem")
    is_sustainable: bool = Field(alias="itemSustentavel")
    ncm_code: str | None = Field(default=None, alias="codigo_ncm")
    ncm_description: str | None = Field(default=None, alias="descricao_ncm")
    applies_preference_margin: bool | None = Field(
        default=None, alias="aplica_margem_preferencia"
    )
    updated_at: datetime = Field(alias="dataHoraAtualizacao")

    pdm_name: str | None = Field(default=None, alias="nomePdm")
    class_code: int | None = Field(default=None, alias="codigoClasse")
    class_name: str | None = Field(default=None, alias="nomeClasse")
    group_code: int | None = Field(default=None, alias="codigoGrupo")
    group_name: str | None = Field(default=None, alias="nomeGrupo")


class ExpenseNatureDTO(ApiModel):
    pdm_code: int = Field(alias="codigoPdm")
    expense_nature_code: str = Field(alias="codigoNaturezaDespesa")
    expense_nature_name: str | None = Field(
        default=None, alias="nomeNaturezaDespesa"
    )
    expense_nature_status: bool | None = Field(
        default=None, alias="statusNaturezaDespesa"
    )


class SupplyUnitDTO(ApiModel):
    pdm_code: int = Field(alias="codigoPdm")
    supply_unit_sequence: int = Field(alias="numeroSequencialUnidadeFornecimento")
    supply_unit_acronym: str | None = Field(
        default=None, alias="siglaUnidadeFornecimento"
    )
    supply_unit_name: str | None = Field(default=None, alias="nomeUnidadeFornecimento")
    supply_unit_description: str | None = Field(
        default=None, alias="descricaoUnidadeFornecimento"
    )
    measure_unit_acronym: str | None = Field(default=None, alias="siglaUnidadeMedida")
    measure_unit_capacity: str | None = Field(
        default=None, alias="capacidadeUnidadeFornecimento"
    )
    supply_unit_pdm_status: bool | None = Field(
        default=None, alias="statusUnidadeFornecimentoPdm"
    )
    supply_unit_status: bool | None = Field(
        default=None, alias="statusUnidadeFornecimento"
    )
    supply_unit_updated_at: datetime | None = Field(
        default=None, alias="dataHoraAtualizacao"
    )
