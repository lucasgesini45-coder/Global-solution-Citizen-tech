from backend.src.acessibilidade import analisar_acessibilidade
from backend.src.rotas.contratos import (
    ACESS_COMPATIVEL,
    ACESS_INCOMPATIVEL,
    ACESS_NAO_SOLICITADA,
    ACESS_NAO_VERIFICADA,
)


def criar_verificador_acessibilidade(consultar_passagem):
    """
    Cria uma função compatível com o motor de rotas.

    consultar_passagem recebe um trecho e devolve:
    True: passagem sem degraus informada;
    False: barreira informada;
    None: informação desconhecida.

    Esta integração interpreta dados fornecidos.
    Não verifica condições físicas nem atualidade da fonte.
    """
    if not callable(consultar_passagem):
        raise ValueError(
            "consultar_passagem deve ser uma função."
        )

    def verificar(rota, necessidades):
        if not necessidades:
            return ACESS_NAO_SOLICITADA

        # Por enquanto, nosso módulo avalia apenas este requisito.
        if "sem_degraus" not in necessidades:
            return ACESS_NAO_VERIFICADA

        trechos = []

        for numero, trecho in enumerate(rota.trechos, start=1):
            passagem = consultar_passagem(trecho)

            trechos.append({
                "id": f"T{numero}",
                "descricao": (
                    f"{trecho.tipo}: {trecho.de} até {trecho.para}"
                ),
                "passagem_sem_degraus": passagem,
            })

        avaliacao = analisar_acessibilidade(
            trechos,
            {"precisa_sem_degraus": True},
        )

        status = avaliacao["status"]

        if status == "INCOMPATIVEL":
            return ACESS_INCOMPATIVEL

        # Outros requisitos ainda não foram avaliados.
        requisitos_adicionais = (
            set(necessidades) - {"sem_degraus"}
        )

        if requisitos_adicionais:
            return ACESS_NAO_VERIFICADA

        if status == "COMPATIVEL":
            return ACESS_COMPATIVEL

        # Inclui rota vazia, informação ausente e dados inválidos.
        return ACESS_NAO_VERIFICADA

    return verificar