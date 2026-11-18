"""Sessão colaborativa: regras do gerenciador e contrato HTTP."""
import threading

import pytest

from backend.src.sessoes import (
    APELIDO_MAX, CODIGO_ALFABETO, CODIGO_TAMANHO, ErroSessao, GerenciadorSessoes,
    MAX_PARTICIPANTES, TTL_SESSAO_S,
)

ORIGEM = {"lat": -23.5505, "lon": -46.6333, "rotulo": "Praça da Sé"}
DESTINO = {"lat": -23.5614, "lon": -46.6559}


class Relogio:
    def __init__(self):
        self.t = 1_000_000.0

    def __call__(self):
        return self.t


@pytest.fixture
def relogio():
    return Relogio()


@pytest.fixture
def g(relogio):
    return GerenciadorSessoes(relogio=relogio)


def codigo_status(excecao_info):
    return excecao_info.value.status


# ------------------------------------------------------------ gerenciador
def test_criar_devolve_codigo_token_e_estado_inicial(g):
    s = g.criar("Ana")
    assert len(s["codigo"]) == CODIGO_TAMANHO
    assert set(s["codigo"]) <= set(CODIGO_ALFABETO)
    assert s["token"] and s["participante_id"] == 1
    assert s["estado"]["origem"] is None and s["estado"]["modal"] == "todos"
    assert s["estado"]["rota_selecionada"] is None
    assert s["participantes"] == [{"id": 1, "apelido": "Ana", "criador": True}]


def test_sem_apelido_usa_nome_neutro(g):
    assert g.criar()["participantes"][0]["apelido"] == "Participante 1"
    assert g.criar("   ")["participantes"][0]["apelido"] == "Participante 1"


@pytest.mark.parametrize("apelido", [
    "ana@email.com", "chame 11 98888-7777", "12345678", "x" * (APELIDO_MAX + 1), "ab\x07c",
])
def test_apelido_recusa_dados_pessoais_e_invalidos(g, apelido):
    with pytest.raises(ErroSessao) as e:
        g.criar(apelido)
    assert e.value.status == 422


def test_apelido_repetido_ganha_sufixo(g):
    s = g.criar("Ana")
    s2 = g.entrar(s["codigo"], "ana")
    assert s2["participantes"][1]["apelido"] == "ana (2)"
    s3 = g.entrar(s["codigo"], "Ana")
    assert s3["participantes"][2]["apelido"] == "Ana (3)"


def test_codigo_aceita_minusculas_e_espacos(g):
    s = g.criar("Ana")
    assert g.entrar(f"  {s['codigo'].lower()} ", "Bia")["codigo"] == s["codigo"]


@pytest.mark.parametrize("codigo", ["", "ZZZZZZ", "abc", "OOOOOO", "../../etc"])
def test_codigo_inexistente_ou_malformado_da_404(g, codigo):
    with pytest.raises(ErroSessao) as e:
        g.entrar(codigo, "Bia")
    assert e.value.status == 404


def test_sessao_cheia_recusa_novos_participantes(g):
    s = g.criar("P0")
    for i in range(1, MAX_PARTICIPANTES):
        g.entrar(s["codigo"], f"P{i}")
    with pytest.raises(ErroSessao) as e:
        g.entrar(s["codigo"], "Extra")
    assert e.value.status == 409


def test_limite_de_sessoes_ativas(relogio):
    g = GerenciadorSessoes(relogio=relogio, max_sessoes=2)
    g.criar("A")
    g.criar("B")
    with pytest.raises(ErroSessao) as e:
        g.criar("C")
    assert e.value.status == 503


def test_expira_por_inatividade_e_atividade_renova(g, relogio):
    s = g.criar("Ana")
    relogio.t += TTL_SESSAO_S - 10
    g.atualizar_estado(s["codigo"], s["token"], {"modal": "ape"})  # renova
    relogio.t += TTL_SESSAO_S - 10
    assert g.sincronizar(s["codigo"], s["token"])["estado"]["modal"] == "ape"
    relogio.t += TTL_SESSAO_S + 1
    with pytest.raises(ErroSessao) as e:
        g.sincronizar(s["codigo"], s["token"])
    assert e.value.status == 404
    assert g.total_ativas() == 0


def test_token_invalido_ou_de_outra_sessao_da_403(g):
    a, b = g.criar("A"), g.criar("B")
    for token in ("", "errado", b["token"]):
        with pytest.raises(ErroSessao) as e:
            g.sincronizar(a["codigo"], token)
        assert e.value.status == 403


def test_atualizacao_parcial_e_versionamento(g):
    s = g.criar("Ana")
    v0 = s["versao"]
    r = g.atualizar_estado(s["codigo"], s["token"], {"origem": ORIGEM, "modal": "ferroviario"})
    assert r["alterado"] and r["versao"] == v0 + 1
    assert r["estado"]["origem"] == ORIGEM and r["estado"]["destino"] is None
    assert r["eventos"][-1]["campos"] == ["origem", "modal"]


def test_atualizacao_sem_efeito_nao_muda_versao(g):
    s = g.criar("Ana")
    g.atualizar_estado(s["codigo"], s["token"], {"modal": "ape"})
    r = g.atualizar_estado(s["codigo"], s["token"], {"modal": "ape"})
    assert r["alterado"] is False and r["versao"] == 2


def test_atualizacao_vazia_e_recusada(g):
    s = g.criar("Ana")
    with pytest.raises(ErroSessao) as e:
        g.atualizar_estado(s["codigo"], s["token"], {})
    assert e.value.status == 422


def test_conflito_de_versao_devolve_estado_vigente(g):
    s = g.criar("Ana")
    b = g.entrar(s["codigo"], "Bia")
    g.atualizar_estado(s["codigo"], b["token"], {"destino": DESTINO})
    with pytest.raises(ErroSessao) as e:
        g.atualizar_estado(s["codigo"], s["token"], {"modal": "ape"}, versao_base=s["versao"])
    assert e.value.status == 409
    assert e.value.extra["estado"]["destino"] == DESTINO
    assert e.value.extra["versao_atual"] == 3


def test_mudar_planejamento_zera_rota_selecionada(g):
    s = g.criar("Ana")
    g.atualizar_estado(s["codigo"], s["token"], {"rota_selecionada": 1})
    r = g.atualizar_estado(s["codigo"], s["token"], {"evitar_escadas": True})
    assert r["estado"]["rota_selecionada"] is None
    assert "rota_selecionada" in r["eventos"][-1]["campos"]


def test_escolher_rota_junto_com_planejamento_preserva_escolha(g):
    s = g.criar("Ana")
    r = g.atualizar_estado(s["codigo"], s["token"], {"destino": DESTINO, "rota_selecionada": 2})
    assert r["estado"]["rota_selecionada"] == 2


def test_sincronizar_devolve_so_eventos_novos(g):
    s = g.criar("Ana")
    g.entrar(s["codigo"], "Bia")
    g.atualizar_estado(s["codigo"], s["token"], {"modal": "onibus"})
    tudo = g.sincronizar(s["codigo"], s["token"])
    assert [e["tipo"] for e in tudo["eventos"]] == ["criada", "entrou", "estado"]
    novos = g.sincronizar(s["codigo"], s["token"], desde=2)
    assert [e["tipo"] for e in novos["eventos"]] == ["estado"]
    assert g.sincronizar(s["codigo"], s["token"], desde=tudo["versao"])["eventos"] == []


def test_visao_nunca_expoe_tokens_de_outros(g):
    s = g.criar("Ana")
    b = g.entrar(s["codigo"], "Bia")
    visao = g.sincronizar(s["codigo"], s["token"])
    assert b["token"] not in repr(visao)
    assert all("token" not in p for p in visao["participantes"])


def test_criador_sai_e_cria_heranca(g):
    s = g.criar("Ana")
    b = g.entrar(s["codigo"], "Bia")
    g.sair(s["codigo"], s["token"])
    visao = g.sincronizar(s["codigo"], b["token"])
    assert visao["participantes"] == [{"id": 2, "apelido": "Bia", "criador": True}]
    assert g.encerrar(s["codigo"], b["token"])["encerrada"]


def test_ultimo_a_sair_apaga_a_sessao(g):
    s = g.criar("Ana")
    assert g.sair(s["codigo"], s["token"])["encerrada"] is True
    assert g.total_ativas() == 0


def test_so_criador_encerra(g):
    s = g.criar("Ana")
    b = g.entrar(s["codigo"], "Bia")
    with pytest.raises(ErroSessao) as e:
        g.encerrar(s["codigo"], b["token"])
    assert e.value.status == 403
    g.encerrar(s["codigo"], s["token"])
    with pytest.raises(ErroSessao):
        g.sincronizar(s["codigo"], s["token"])


def test_historico_de_eventos_tem_limite(g):
    s = g.criar("Ana")
    for i in range(150):
        g.atualizar_estado(s["codigo"], s["token"], {"modal": "ape" if i % 2 else "onibus"})
    assert len(g.sincronizar(s["codigo"], s["token"])["eventos"]) == 100


def test_entradas_simultaneas_respeitam_o_limite(g):
    s = g.criar("P0")
    resultados = []

    def entrar(i):
        try:
            g.entrar(s["codigo"], f"T{i}")
            resultados.append("ok")
        except ErroSessao as e:
            resultados.append(e.status)

    threads = [threading.Thread(target=entrar, args=(i,)) for i in range(30)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert resultados.count("ok") == MAX_PARTICIPANTES - 1
    assert resultados.count(409) == 30 - (MAX_PARTICIPANTES - 1)


# ------------------------------------------------------------------- HTTP
def criar_http(cliente, apelido="Ana"):
    r = cliente.post("/sessoes", json={"apelido": apelido})
    assert r.status_code == 201, r.text
    return r.json()


def test_http_fluxo_completo(cliente):
    a = criar_http(cliente)
    cod = a["codigo"]
    assert "memória" in a["aviso"]
    b = cliente.post(f"/sessoes/{cod}/entrar", json={"apelido": "Bia"}).json()
    r = cliente.post(f"/sessoes/{cod}/estado", json={
        "token": a["token"], "origem": ORIGEM, "destino": DESTINO,
        "modal": "ferroviario", "priorizar_menos_caminhada": True})
    assert r.status_code == 200 and r.json()["alterado"] is True
    visto = cliente.post(f"/sessoes/{cod}/sincronizar", json={"token": b["token"], "desde": 2}).json()
    assert visto["estado"]["modal"] == "ferroviario"
    assert visto["estado"]["origem"]["rotulo"] == "Praça da Sé"
    assert [e["tipo"] for e in visto["eventos"]] == ["estado"]
    assert cliente.post(f"/sessoes/{cod}/sair", json={"token": b["token"]}).json()["encerrada"] is False
    assert cliente.post(f"/sessoes/{cod}/encerrar", json={"token": a["token"]}).json()["encerrada"] is True
    assert cliente.post(f"/sessoes/{cod}/sincronizar", json={"token": a["token"]}).status_code == 404


def test_http_erros_compreensiveis(cliente):
    a = criar_http(cliente)
    cod = a["codigo"]
    base = f"/sessoes/{cod}/estado"
    assert cliente.post("/sessoes/ZZZZZZ/entrar", json={}).status_code == 404
    assert cliente.post(base, json={"token": "x", "modal": "ape"}).status_code == 403
    assert cliente.post("/sessoes", json={"apelido": "a@b.com"}).status_code == 422
    # corpo inválido: sem token, coordenadas fora do intervalo, modal inexistente, campo extra, nulos
    for corpo in (
        {"modal": "ape"},
        {"token": a["token"], "origem": {"lat": 100, "lon": 0}},
        {"token": a["token"], "modal": "carro"},
        {"token": a["token"], "rota_selecionada": 3},
        {"token": a["token"], "modal": None},
        {"token": a["token"], "evitar_escadas": None},
        {"token": a["token"], "senha": "x"},
        {"token": a["token"]},
    ):
        assert cliente.post(base, json=corpo).status_code == 422, corpo
    assert cliente.post(f"/sessoes/{cod}/sincronizar", json={"token": a["token"], "desde": -1}).status_code == 422


def test_http_conflito_409_traz_estado_atual(cliente):
    a = criar_http(cliente)
    cod = a["codigo"]
    b = cliente.post(f"/sessoes/{cod}/entrar", json={"apelido": "Bia"}).json()
    cliente.post(f"/sessoes/{cod}/estado", json={"token": b["token"], "modal": "ape"})
    r = cliente.post(f"/sessoes/{cod}/estado", json={
        "token": a["token"], "modal": "onibus", "versao_base": a["versao"]})
    assert r.status_code == 409
    detalhe = r.json()["detail"]
    assert detalhe["estado"]["modal"] == "ape" and detalhe["versao_atual"] == 3


def test_http_origem_pode_ser_limpa_com_null(cliente):
    a = criar_http(cliente)
    cod = a["codigo"]
    cliente.post(f"/sessoes/{cod}/estado", json={"token": a["token"], "origem": ORIGEM})
    r = cliente.post(f"/sessoes/{cod}/estado", json={"token": a["token"], "origem": None})
    assert r.json()["estado"]["origem"] is None
