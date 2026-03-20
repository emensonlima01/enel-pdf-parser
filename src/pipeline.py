# -*- coding: utf-8 -*-
from __future__ import annotations

from .coords import build_regions
from .detector import detect_layout
from .mappers import valor_pagar as mapper_valor_pagar
from .mappers import periodo_faturamento as mapper_periodo_faturamento
from .mappers import classificacao_unidade_consumidora as mapper_classificacao_unidade_consumidora
from .mappers import leitura_atual as mapper_leitura_atual
from .mappers import numero_cliente as mapper_numero_cliente
from .mappers import data_vencimento as mapper_data_vencimento
from .mappers import mensagem_importante as mapper_mensagem_importante
from .mappers import numero_instalacao as mapper_numero_instalacao
from .mappers import itens_fatura as mapper_itens_fatura
from .mappers import itens_medidor as mapper_itens_medidor
from .mappers import proxima_leitura as mapper_proxima_leitura
from .mappers import dados_pessoais as mapper_dados_pessoais
from .mappers import dias_leitura as mapper_dias_leitura
from .mappers import responsavel_pela_iluminacao as mapper_responsavel_pela_iluminacao
from .mappers import tipo_fornecimento as mapper_tipo_fornecimento
from .mappers import periodos_bandeira_tarifaria as mapper_periodos_bandeira_tarifaria
from .mappers import informacoes_credito as mapper_informacoes_credito
from .mappers import informacoes_tributarias as mapper_informacoes_tributarias
from .mappers import tributos as mapper_tributos
from .mappers import leitura_anterior as mapper_leitura_anterior
from . import models
from .models import FaturaEnel
from .ocr.engine import run_ocr
from .ocr.pdf import PdfPageRegionExtractor

def run_pipeline(pdf_bytes: bytes, ocr) -> FaturaEnel:
    with PdfPageRegionExtractor(pdf_bytes, page_number=1) as extrator:
        native_text_cache: dict[tuple[int, int, int, int], list[str]] = {}
        ocr_cache: dict[
            tuple[int, int, int, int], tuple[list[str], list[list[list[float]]]]
        ] = {}

        def _read_native_texts(coord: tuple[int, int, int, int]) -> list[str]:
            cached = native_text_cache.get(coord)
            if cached is not None:
                return cached
            texts = extrator.extract_text_lines(coord)
            native_text_cache[coord] = texts
            return texts

        def _read_ocr(coord: tuple[int, int, int, int]) -> tuple[list[str], list[list[list[float]]]]:
            cached = ocr_cache.get(coord)
            if cached is not None:
                return cached
            imagem_recortada = extrator.render_region_to_ndarray(coord)
            textos, caixas, _scores = run_ocr(ocr, imagem_recortada)
            result = (textos, caixas)
            ocr_cache[coord] = result
            return result

        def _read_ocr_texts(coord: tuple[int, int, int, int]) -> list[str]:
            textos, _caixas = _read_ocr(coord)
            return textos

        identificador_layout = detect_layout(_read_native_texts, _read_ocr_texts)
        regioes = build_regions(identificador_layout)

        classificacao_unidade_consumidora = ""
        tipo_fornecimento = ""
        numero_instalacao = ""
        numero_cliente = ""
        periodo_faturamento = ""
        data_vencimento = ""
        valor_pagar = ""
        leitura_atual = ""
        leitura_anterior = ""
        proxima_leitura = ""
        dias_leitura = 0
        informacoes_tributarias = None
        itens_fatura = []
        itens_medidor = []
        tributos = []
        nome_cliente = ""
        cpf_cnpj = ""
        responsavel_pela_iluminacao = ""
        mensagem_importante = ""
        periodos_bandeira_tarifaria = []
        informacoes_credito = models.InformacoesCredito(
            energia_injetada_hfp_kwh=0.0,
            saldo_utilizado_kwh=0.0,
            saldo_atualizado_kwh=0.0,
            creditos_expirar_proximo_mes_kwh=0.0,
        )

        def _handle_descricao_faturamento(texts, boxes) -> None:
            nonlocal itens_fatura, itens_medidor
            itens_fatura = mapper_itens_fatura.map(texts, boxes)
            itens_medidor = mapper_itens_medidor.map(texts, boxes)

        def _handle_tributos(texts, boxes) -> None:
            nonlocal tributos
            tributos = mapper_tributos.map(texts, boxes)

        def _handle_classificacao_unidade(texts, _boxes) -> None:
            nonlocal classificacao_unidade_consumidora
            classificacao_unidade_consumidora = (
                mapper_classificacao_unidade_consumidora.map(texts)
            )

        def _handle_tipo_fornecimento(texts, _boxes) -> None:
            nonlocal tipo_fornecimento
            tipo_fornecimento = mapper_tipo_fornecimento.map(texts)

        def _handle_numero_instalacao(texts, _boxes) -> None:
            nonlocal numero_instalacao
            numero_instalacao = mapper_numero_instalacao.map(
                texts, layout_id=identificador_layout
            )

        def _handle_numero_cliente(texts, _boxes) -> None:
            nonlocal numero_cliente
            numero_cliente = mapper_numero_cliente.map(
                texts, layout_id=identificador_layout
            )

        def _handle_periodo_faturamento(texts, _boxes) -> None:
            nonlocal periodo_faturamento
            periodo_faturamento = mapper_periodo_faturamento.map(texts)

        def _handle_data_vencimento(texts, _boxes) -> None:
            nonlocal data_vencimento
            data_vencimento = mapper_data_vencimento.map(texts)

        def _handle_valor_pagar(texts, _boxes) -> None:
            nonlocal valor_pagar
            valor_pagar = mapper_valor_pagar.map(texts)

        def _handle_leitura_atual(texts, _boxes) -> None:
            nonlocal leitura_atual
            leitura_atual = mapper_leitura_atual.map(texts)

        def _handle_leitura_anterior(texts, _boxes) -> None:
            nonlocal leitura_anterior
            leitura_anterior = mapper_leitura_anterior.map(texts)

        def _handle_proxima_leitura(texts, _boxes) -> None:
            nonlocal proxima_leitura
            proxima_leitura = mapper_proxima_leitura.map(texts)

        def _handle_dias_leitura(texts, _boxes) -> None:
            nonlocal dias_leitura
            dias_leitura = mapper_dias_leitura.map(texts)

        def _handle_dados_pessoais(texts, _boxes) -> None:
            nonlocal nome_cliente, cpf_cnpj
            nome_cliente, cpf_cnpj = mapper_dados_pessoais.map(texts)

        def _handle_responsavel_iluminacao(texts, _boxes) -> None:
            nonlocal responsavel_pela_iluminacao
            responsavel_pela_iluminacao = mapper_responsavel_pela_iluminacao.map(texts)

        def _handle_informacoes_tributarias(texts, boxes) -> None:
            nonlocal informacoes_tributarias
            informacoes_tributarias = mapper_informacoes_tributarias.map(texts, boxes)

        def _handle_mensagem_importante(texts, _boxes) -> None:
            nonlocal mensagem_importante
            mensagem_importante = mapper_mensagem_importante.map(texts)

        tratadores = {
            "DESCRICAO_FATURAMENTO": _handle_descricao_faturamento,
            "TRIBUTOS": _handle_tributos,
            "CLASSIFICACAO_UNIDADE_CONSUMIDORA": _handle_classificacao_unidade,
            "TIPO_FORNECIMENTO": _handle_tipo_fornecimento,
            "NUMERO_INSTALACAO": _handle_numero_instalacao,
            "NUMERO_CLIENTE": _handle_numero_cliente,
            "PERIODO_FATURAMENTO": _handle_periodo_faturamento,
            "DATA_VENCIMENTO": _handle_data_vencimento,
            "VALOR_PAGAR": _handle_valor_pagar,
            "LEITURA_ATUAL": _handle_leitura_atual,
            "LEITURA_ANTERIOR": _handle_leitura_anterior,
            "PROXIMA_LEITURA": _handle_proxima_leitura,
            "DIAS_LEITURA": _handle_dias_leitura,
            "DADOS_PESSOAIS": _handle_dados_pessoais,
            "RESPONSAVEL_PELA_ILUMINACAO": _handle_responsavel_iluminacao,
            "INFORMACOES_TRIBUTARIAS": _handle_informacoes_tributarias,
            "MENSAGEM_IMPORTANTE": _handle_mensagem_importante,
        }

        for regiao in regioes:
            tratador = tratadores.get(regiao.description)
            if not tratador:
                continue

            coordenadas = (regiao.x, regiao.y, regiao.width, regiao.height)
            if regiao.source == "ocr":
                textos, caixas = _read_ocr(coordenadas)
            else:
                textos = _read_native_texts(coordenadas)
                caixas = []
                if not textos:
                    textos, caixas = _read_ocr(coordenadas)

            tratador(textos, caixas)

        if mensagem_importante:
            periodos_bandeira_tarifaria = mapper_periodos_bandeira_tarifaria.map(
                mensagem_importante
            )
            informacoes_credito = mapper_informacoes_credito.map(mensagem_importante)

        base_informacoes_tributarias = (
            informacoes_tributarias
            or mapper_informacoes_tributarias.InformacoesTributarias(
                numero_nota_fiscal="",
                data_emissao_nota_fiscal="",
                chave_acesso="",
                cfop="",
                data_apresentacao="",
                tributos=[],
            )
        )
        if tributos:
            base_informacoes_tributarias = (
                mapper_informacoes_tributarias.InformacoesTributarias(
                    numero_nota_fiscal=base_informacoes_tributarias.numero_nota_fiscal,
                    data_emissao_nota_fiscal=base_informacoes_tributarias.data_emissao_nota_fiscal,
                    chave_acesso=base_informacoes_tributarias.chave_acesso,
                    cfop=base_informacoes_tributarias.cfop,
                    data_apresentacao=base_informacoes_tributarias.data_apresentacao,
                    tributos=tributos,
                )
            )
        return FaturaEnel(
            itens_fatura=itens_fatura,
            itens_medidor=itens_medidor,
            classificacao_unidade_consumidora=classificacao_unidade_consumidora,
            tipo_fornecimento=tipo_fornecimento,
            numero_instalacao=numero_instalacao,
            numero_cliente=numero_cliente,
            nome_cliente=nome_cliente,
            cpf_cnpj=cpf_cnpj,
            responsavel_pela_iluminacao=responsavel_pela_iluminacao,
            periodo_faturamento=periodo_faturamento,
            data_vencimento=data_vencimento,
            valor_pagar=valor_pagar,
            datas_leitura=models.DatasLeitura(
                leitura_anterior=leitura_anterior,
                leitura_atual=leitura_atual,
                dias_leitura=dias_leitura,
                proxima_leitura=proxima_leitura,
            ),
            informacoes_tributarias=base_informacoes_tributarias,
            mensagem_importante=mensagem_importante,
            periodos_bandeira_tarifaria=periodos_bandeira_tarifaria,
            informacoes_credito=informacoes_credito,
        )
