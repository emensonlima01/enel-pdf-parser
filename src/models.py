# -*- coding: ascii -*-
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


def _text(value: str) -> str:
    return value.upper()


def _decimal(value: Decimal) -> str:
    return str(value)


@dataclass(frozen=True)
class ItemFatura:
    descricao: str
    competencia: str
    unidade: str
    quantidade: Decimal
    preco_unitario_com_tributos: Decimal
    preco_unitario_com_tributos_original: str
    valor: Decimal
    pis_cofins: Decimal
    base_calculo_icms: Decimal
    aliquota_icms: Decimal
    valor_icms: Decimal
    tarifa_unitaria: Decimal
    colunas_ocr: dict[str, str]

    def to_dict(self) -> dict:
        return {
            "descricao": _text(self.descricao),
            "competencia": _text(self.competencia),
            "unidade": _text(self.unidade),
            "quantidade": _decimal(self.quantidade),
            "preco_unitario_com_tributos": _decimal(self.preco_unitario_com_tributos),
            "preco_unitario_com_tributos_original": _text(self.preco_unitario_com_tributos_original),
            "valor": _decimal(self.valor),
            "pis_cofins": _decimal(self.pis_cofins),
            "base_calculo_icms": _decimal(self.base_calculo_icms),
            "aliquota_icms": _decimal(self.aliquota_icms),
            "valor_icms": _decimal(self.valor_icms),
            "tarifa_unitaria": _decimal(self.tarifa_unitaria),
            "colunas_ocr": {k: _text(v) for k, v in self.colunas_ocr.items()},
        }


@dataclass(frozen=True)
class ItemMedidor:
    numero_medidor: str
    horario_segmento: str
    data_leitura_1: str
    leitura_1: Decimal
    data_leitura_2: str
    leitura_2: Decimal
    fator_multiplicador: Decimal
    consumo_kwh: Decimal
    numero_dias: int

    def to_dict(self) -> dict:
        return {
            "numero_medidor": _text(self.numero_medidor),
            "horario_segmento": _text(self.horario_segmento),
            "data_leitura_1": _text(self.data_leitura_1),
            "leitura_1": _decimal(self.leitura_1),
            "data_leitura_2": _text(self.data_leitura_2),
            "leitura_2": _decimal(self.leitura_2),
            "fator_multiplicador": _decimal(self.fator_multiplicador),
            "consumo_kwh": _decimal(self.consumo_kwh),
            "numero_dias": self.numero_dias,
        }


@dataclass(frozen=True)
class TributoFatura:
    nome_tributo: str
    base_calculo: Decimal
    aliquota: Decimal
    valor: Decimal

    def to_dict(self) -> dict:
        return {
            "nome_tributo": _text(self.nome_tributo),
            "base_calculo": _decimal(self.base_calculo),
            "aliquota": _decimal(self.aliquota),
            "valor": _decimal(self.valor),
        }


@dataclass(frozen=True)
class InformacoesTributarias:
    numero_nota_fiscal: str
    data_emissao_nota_fiscal: str
    chave_acesso: str
    cfop: str
    data_apresentacao: str
    tributos: list[TributoFatura]

    def to_dict(self) -> dict:
        return {
            "numero_nota_fiscal": _text(self.numero_nota_fiscal),
            "data_emissao_nota_fiscal": _text(self.data_emissao_nota_fiscal),
            "chave_acesso": _text(self.chave_acesso),
            "cfop": _text(self.cfop),
            "data_apresentacao": _text(self.data_apresentacao),
            "tributos": [t.to_dict() for t in self.tributos],
        }


@dataclass(frozen=True)
class InformacoesCredito:
    energia_injetada_hfp_kwh: float
    saldo_utilizado_kwh: float
    saldo_atualizado_kwh: float
    creditos_expirar_proximo_mes_kwh: float

    def to_dict(self) -> dict:
        return {
            "energia_injetada_hfp_kwh": self.energia_injetada_hfp_kwh,
            "saldo_utilizado_kwh": self.saldo_utilizado_kwh,
            "saldo_atualizado_kwh": self.saldo_atualizado_kwh,
            "creditos_expirar_proximo_mes_kwh": self.creditos_expirar_proximo_mes_kwh,
        }


@dataclass(frozen=True)
class DatasLeitura:
    leitura_anterior: str
    leitura_atual: str
    dias_leitura: int
    proxima_leitura: str

    def to_dict(self) -> dict:
        return {
            "leitura_anterior": _text(self.leitura_anterior),
            "leitura_atual": _text(self.leitura_atual),
            "dias_leitura": self.dias_leitura,
            "proxima_leitura": _text(self.proxima_leitura),
        }


@dataclass(frozen=True)
class PeriodoBandeiraTarifaria:
    bandeira: str
    data_inicio: str
    data_fim: str

    def to_dict(self) -> dict:
        return {
            "bandeira": _text(self.bandeira),
            "data_inicio": _text(self.data_inicio),
            "data_fim": _text(self.data_fim),
        }


@dataclass(frozen=True)
class FaturaEnel:
    itens_fatura: list[ItemFatura]
    itens_medidor: list[ItemMedidor]
    classificacao_unidade_consumidora: str
    tipo_fornecimento: str
    numero_instalacao: str
    numero_cliente: str
    nome_cliente: str
    cpf_cnpj: str
    responsavel_pela_iluminacao: str
    periodo_faturamento: str
    data_vencimento: str
    valor_pagar: Decimal
    datas_leitura: DatasLeitura
    informacoes_tributarias: InformacoesTributarias
    mensagem_importante: str
    periodos_bandeira_tarifaria: list[PeriodoBandeiraTarifaria]
    informacoes_credito: InformacoesCredito

    def to_dict(self) -> dict:
        return {
            "itens_fatura": [item.to_dict() for item in self.itens_fatura],
            "itens_medidor": [item.to_dict() for item in self.itens_medidor],
            "classificacao_unidade_consumidora": _text(self.classificacao_unidade_consumidora),
            "tipo_fornecimento": _text(self.tipo_fornecimento),
            "numero_instalacao": _text(self.numero_instalacao),
            "numero_cliente": _text(self.numero_cliente),
            "nome_cliente": _text(self.nome_cliente),
            "cpf_cnpj": _text(self.cpf_cnpj),
            "responsavel_pela_iluminacao": _text(self.responsavel_pela_iluminacao),
            "periodo_faturamento": _text(self.periodo_faturamento),
            "data_vencimento": _text(self.data_vencimento),
            "valor_pagar": _decimal(self.valor_pagar),
            "datas_leitura": self.datas_leitura.to_dict(),
            "informacoes_tributarias": self.informacoes_tributarias.to_dict(),
            "mensagem_importante": _text(self.mensagem_importante),
            "periodos_bandeira_tarifaria": [p.to_dict() for p in self.periodos_bandeira_tarifaria],
            "informacoes_credito": self.informacoes_credito.to_dict(),
        }
