# Enel PDF Parser

REST API that extracts structured data from **Enel electricity invoices** (PDF) and returns a JSON response. It combines native PDF text extraction (PyMuPDF) with OCR (PaddleOCR) to parse billing line items, meter readings, taxes, customer data, and more.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Response Schema](#response-schema)
- [How It Works](#how-it-works)
- [License](#license)

## Features

- Parses Enel electricity invoices (Brazilian distributor)
- Extracts 17+ data fields from a single PDF page
- Dual extraction strategy: native PDF text first, OCR fallback for complex regions
- Supports multiple invoice layouts with automatic detection
- Handles masked CPF/CNPJ (e.g. `***.123.456-**`)
- Returns clean, typed JSON with Decimal precision
- Bearer token authentication
- Production-ready Docker image with Gunicorn

## Architecture

```
PDF upload ──► Native text extraction (PyMuPDF)
                    │
                    ▼
             Layout detection (v1 / v2)
                    │
                    ▼
             Region-based extraction
             ┌──────┴──────┐
         Native text     OCR fallback
             │           (PaddleOCR)
             └──────┬──────┘
                    ▼
              21 field mappers
                    │
                    ▼
             FaturaEnel model ──► JSON response
```

## Project Structure

```
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── src/
    ├── api.py              # Flask REST endpoint
    ├── pipeline.py         # Orchestrates extraction across all regions
    ├── detector.py         # Auto-detects invoice layout version
    ├── coords.py           # Loads region coordinates from JSON layouts
    ├── models.py           # Frozen dataclasses with to_dict() serialization
    ├── layouts/
    │   ├── headers.json    # Anchor rules for layout detection
    │   ├── v1.json         # Region coordinates for layout v1
    │   └── v2.json         # Region coordinates for layout v2
    ├── mappers/            # 21 field-specific extraction modules
    │   ├── itens_fatura.py
    │   ├── itens_medidor.py
    │   ├── dados_pessoais.py
    │   ├── informacoes_tributarias.py
    │   ├── tributos.py
    │   ├── valor_pagar.py
    │   └── ...
    └── ocr/
        ├── engine.py       # PaddleOCR initialization and inference
        ├── pdf.py          # PDF page rendering (PyMuPDF)
        ├── image.py        # Image byte conversion
        └── crop.py         # Region cropping utilities
```

## Quick Start

### Docker Compose (recommended)

```bash
cp .env.example .env
docker compose up -d --build
```

### Docker CLI

```bash
docker build -t enel-pdf-parser .
docker run --rm -p 8000:8000 enel-pdf-parser
```

### Send a PDF

```bash
curl -X POST http://localhost:8000/enel \
  -H "Content-Type: application/pdf" \
  -H "Authorization: Bearer dev-local-token" \
  --data-binary @invoice.pdf
```

## API Reference

### `POST /enel`

Parses an Enel electricity invoice PDF and returns structured JSON.

**Headers:**

| Header | Required | Description |
|--------|----------|-------------|
| `Content-Type` | Yes | Must be `application/pdf` |
| `Authorization` | Conditional | `Bearer <token>` — required when `API_TOKEN` is set |

**Request body:** Raw PDF bytes.

**Responses:**

| Status | Description |
|--------|-------------|
| `200` | Success — returns parsed invoice JSON |
| `400` | Invalid request (not PDF, empty body, corrupted file) |
| `401` | Unauthorized (missing or invalid token) |

**Error format:**

```json
{ "error": "description" }
```

## Configuration

All settings are configured via environment variables. Copy `.env.example` to `.env` and adjust as needed.

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | HTTP listen port |
| `API_TOKEN` | *(empty)* | Bearer token for authentication. When empty, auth is disabled |
| `WEB_CONCURRENCY` | `1` | Gunicorn worker count |
| `WEB_THREADS` | `1` | Threads per worker |
| `GUNICORN_TIMEOUT` | `300` | Request timeout in seconds |
| `PDF_DPI` | `300` | DPI for PDF-to-image rendering (OCR regions) |
| `PADDLE_PDX_MODEL_SOURCE` | `BOS` | PaddleOCR model download source |
| `OMP_NUM_THREADS` | `1` | OpenMP thread limit |
| `OPENBLAS_NUM_THREADS` | `1` | OpenBLAS thread limit |

## Response Schema

<details>
<summary>Full JSON response structure</summary>

```jsonc
{
  // Customer info
  "nome_cliente": "JOHN DOE",
  "cpf_cnpj": "123.***.***-**",
  "numero_cliente": "1234567",
  "numero_instalacao": "1234567",
  "classificacao_unidade_consumidora": "B1 RESIDENCIAL",
  "tipo_fornecimento": "TRIFÁSICO",
  "responsavel_pela_iluminacao": "PREFEITURA MUNICIPAL ...",

  // Billing
  "periodo_faturamento": "2026-03",
  "data_vencimento": "2026-03-26",
  "valor_pagar": "374.52",

  // Meter readings
  "datas_leitura": {
    "leitura_anterior": "2026-02-11",
    "leitura_atual": "2026-03-12",
    "dias_leitura": 29,
    "proxima_leitura": "2026-04-14"
  },

  // Invoice line items
  "itens_fatura": [
    {
      "descricao": "ENERGIA CONSUMIDA FATURADA TE",
      "competencia": "",
      "unidade": "KWH",
      "quantidade": "228",
      "preco_unitario_com_tributos": "0.32899",
      "preco_unitario_com_tributos_original": "0,32899",
      "valor": "75.01",
      "pis_cofins": "3.92",
      "base_calculo_icms": "75.01",
      "aliquota_icms": "20.00",
      "valor_icms": "15.00",
      "tarifa_unitaria": "0.24519",
      "colunas_ocr": { /* raw OCR values */ }
    }
  ],

  // Meter data
  "itens_medidor": [
    {
      "numero_medidor": "3772424-NAN-280",
      "horario_segmento": "HFP",
      "data_leitura_1": "2026-02-12",
      "leitura_1": "97405.0",
      "data_leitura_2": "2026-03-12",
      "leitura_2": "97969.0",
      "fator_multiplicador": "1.0",
      "consumo_kwh": "564.0",
      "numero_dias": 29
    }
  ],

  // Tax info
  "informacoes_tributarias": {
    "numero_nota_fiscal": "206589360",
    "data_emissao_nota_fiscal": "2026-03-13",
    "chave_acesso": "3232603...",
    "cfop": "5258",
    "data_apresentacao": "2026-03-17",
    "tributos": [
      {
        "nome_tributo": "PIS/PASEP",
        "base_calculo": "236.66",
        "aliquota": "1.17",
        "valor": "2.79"
      },
      {
        "nome_tributo": "COFINS",
        "base_calculo": "236.66",
        "aliquota": "5.38",
        "valor": "12.74"
      },
      {
        "nome_tributo": "ICMS",
        "base_calculo": "425.78",
        "aliquota": "20.00",
        "valor": "85.16"
      }
    ]
  },

  // Tariff flags
  "periodos_bandeira_tarifaria": [
    {
      "bandeira": "VERDE",
      "data_inicio": "02-12",
      "data_fim": "03-12"
    }
  ],

  // Distributed generation credits
  "informacoes_credito": {
    "energia_injetada_hfp_kwh": 0.0,
    "saldo_utilizado_kwh": 335.24,
    "saldo_atualizado_kwh": 0.0,
    "creditos_expirar_proximo_mes_kwh": 0.0
  },

  "mensagem_importante": "MENSAGENS IMPORTANTES ..."
}
```

</details>

## How It Works

1. **PDF Upload** — The client sends a raw PDF to `POST /enel`.

2. **Layout Detection** — The detector reads anchor text from predefined regions and matches it against rules in `headers.json` to determine the layout version (`v1` or `v2`).

3. **Region Extraction** — Each layout defines 17 coordinate regions. For each region, the pipeline first attempts native PDF text extraction (fast, precise). If no text is found, it falls back to OCR via PaddleOCR.

4. **Field Mapping** — Each region is processed by a dedicated mapper module that uses regex, decimal parsing, and text normalization to extract structured data.

5. **Response** — All extracted fields are assembled into a `FaturaEnel` dataclass and serialized to JSON via `to_dict()`.

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Native text first, OCR fallback | Native extraction is 10-100x faster and more accurate for typed text |
| Region-based coordinate system | Invoice layouts are fixed; coordinates avoid full-page OCR overhead |
| Frozen dataclasses | Immutable models prevent accidental mutation during extraction |
| Thread lock on OCR | PaddleOCR is not thread-safe; lock ensures safe concurrent usage |
| DPI fixed at 300 | Industry standard for OCR; lower loses quality, higher wastes resources |

## License

[MIT](LICENSE) — Copyright (c) 2026 Emenson Lima
