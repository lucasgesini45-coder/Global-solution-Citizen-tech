from datetime import date, datetime, timedelta

from backend.src.seguranca import avaliar_atualidade


# Referência fixa para tornar os testes reproduzíveis.
referencia = date(2026, 11, 22)

cenarios = [
    (
        "Fato recente",
        referencia - timedelta(days=10),
        referencia - timedelta(days=9),
        True,
        "DENTRO_DA_JANELA",
        10
    ),
    (
        "Exatamente no limite de 90 dias",
        referencia - timedelta(days=90),
        referencia,
        True,
        "DENTRO_DA_JANELA",
        90
    ),
    (
        "Fato antigo registrado recentemente",
        referencia - timedelta(days=91),
        referencia,
        False,
        "FORA_DA_JANELA",
        91
    ),
    (
        "Fato posterior ao registro",
        referencia - timedelta(days=2),
        referencia - timedelta(days=3),
        False,
        "FATO_POSTERIOR_AO_REGISTRO",
        None
    ),
    (
        "Registro futuro",
        referencia,
        referencia + timedelta(days=1),
        False,
        "DATA_FUTURA",
        None
    ),
    (
        "Data ausente",
        None,
        referencia,
        False,
        "DATA_INVALIDA",
        None
    ),
    (
        "Conversão de datetime recebido do Excel",
        datetime(2026, 11, 20, 0, 0),
        datetime(2026, 11, 21, 0, 0),
        True,
        "DENTRO_DA_JANELA",
        2
    )
]

print("\n--- TESTES DE ATUALIDADE ---")

for nome, fato, registro, apta, motivo, idade in cenarios:
    resultado = avaliar_atualidade(
        fato,
        registro,
        referencia,
        janela_dias=90
    )

    assert resultado["apta"] == apta, nome
    assert resultado["motivo"] == motivo, nome
    assert resultado["idade_dias"] == idade, nome

    print("PASSOU:", nome)