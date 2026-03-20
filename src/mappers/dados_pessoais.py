# -*- coding: ascii -*-
from __future__ import annotations

import re
from ._utils import normalize_text


def _extrair_nome(linhas: list[str]) -> str:
    for linha in linhas:
        normalized = normalize_text(linha)
        if "cpf" in normalized or "cnpj" in normalized:
            continue
        if "cep" in normalized:
            continue
        if not normalized:
            continue
        return linha.strip()
    return ""


def _extrair_cpf_cnpj(linhas: list[str]) -> str:
    for linha in linhas:
        normalized = normalize_text(linha)
        if "cpf" not in normalized and "cnpj" not in normalized:
            continue
        # CPF/CNPJ completo (sem mascara)
        match = re.search(
            r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b|\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
            linha,
        )
        if match:
            return match.group(0)
        # CPF/CNPJ mascarado (ex: ***.123.456-** ou **.***.***/****-**)
        match = re.search(
            r"[\d*]{2}\.[\d*]{3}\.[\d*]{3}/[\d*]{4}-[\d*]{2}|[\d*]{3}\.[\d*]{3}\.[\d*]{3}-[\d*]{2}",
            linha,
        )
        if match:
            return match.group(0)
        digits = "".join(re.findall(r"\d+", linha))
        if len(digits) in (11, 14):
            return digits
    return ""


def map(texts: list[str]) -> tuple[str, str]:
    linhas = [text.strip() for text in texts if text and text.strip()]
    nome = _extrair_nome(linhas)
    cpf_cnpj = _extrair_cpf_cnpj(linhas)
    return nome.upper(), cpf_cnpj.upper()
