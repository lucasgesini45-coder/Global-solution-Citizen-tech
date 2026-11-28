from datetime import date, datetime

from backend.src.base_acessibilidade import (
    consultar_acessibilidade,
    validar_base_acessibilidade,
)
from backend.src.integracao_acessibilidade import (
    criar_verificador_acessibilidade,
)


def criar_verificador_com_base(
    base,
    identificar_trecho,
    data_consulta,
    *,
    permitir_simulada=False,
):
    """
    Conecta a base ao adaptador de acessibilidade.

    identificar_trecho recebe um trecho do motor e devolve
    seu id na base, ou None quando não houver associação.

    O uso da base simulada exige autorização explícita
    no código que chama esta função.
    """
    validar_base_acessibilidade(base)

    if permitir_simulada is not True:
        raise ValueError(
            "Base simulada: use permitir_simulada=True "
            "somente em testes ou demonstrações."
        )

    if not callable(identificar_trecho):
        raise ValueError(
            "identificar_trecho deve ser uma função."
        )

    if isinstance(data_consulta, datetime):
        data_consulta = data_consulta.date()

    if not isinstance(data_consulta, date):
        raise ValueError(
            "data_consulta deve ser date ou datetime."
        )

    def consultar_passagem(trecho):
        identificador = identificar_trecho(trecho)

        # Sem associação, não inventa um registro.
        if identificador is None:
            return None

        if (
            not isinstance(identificador, str)
            or not identificador.strip()
            or identificador != identificador.strip()
        ):
            raise ValueError(
                "O identificador deve ser texto não vazio, "
                "sem espaços nas extremidades, ou None."
            )

        resultado = consultar_acessibilidade(
            base,
            identificador,
            data_consulta,
        )

        return resultado["passagem_sem_degraus"]

    return criar_verificador_acessibilidade(
        consultar_passagem
    )