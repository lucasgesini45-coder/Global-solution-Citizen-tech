"""Contratos entre módulos e fluxo ponta a ponta, sem rede externa.

Cada teste protege uma promessa que um módulo faz aos outros. Se um deles mudar
o formato da resposta, estes testes quebram antes da demonstração.
"""
from unittest.mock import patch

import pytest

from backend.src.sessoes import MODAIS_VALIDOS
from backend.tests.fixtures.rede_demo import ponto

O = ponto(0.0, -100.0)
D = ponto(4000.0, 300.0)
PEDIDO_ROTA = {
    "origem": {"lat": O[0], "lon": O[1]},
    "destino": {"lat": D[0], "lon": D[1]},
    "partida": "2026-11-09T08:00:00",
}
ROTA_REAL = {
    "tipo": "rota_real", "fonte": "Transitous", "modal": "ferroviario", "tempo_min": 29,
    "trechos": [{"modal": "SUBWAY", "linha": "Linha 2 - Verde", "de": "Paraiso",
                 "para": "Consolacao", "trajeto": [[-23.55, -46.63], [-23.56, -46.64]]}],
    "trajeto": [[-23.55, -46.63], [-23.56, -46.64]],
    "aviso": "Tempo sujeito a mudancas",
}


# ---------------------------------------------- 1 - Dados e fontes
def test_temas_devolve_grafo_com_vizinhos_validos(cliente):
    grafo = cliente.get("/temas").json()
    assert len(grafo) >= 3
    for tema, vizinhos in grafo.items():
        assert vizinhos and tema not in vizinhos
        assert set(vizinhos) <= set(grafo)


def test_consultar_sempre_traz_as_quatro_chaves_do_contrato(cliente):
    for pergunta in ("", "   ", "xyzqw asdfg", "como pedir gratuidade?"):
        r = cliente.post("/consultar", json={"pergunta": pergunta})
        assert r.status_code == 200
        assert {"status", "resposta", "fontes", "relacionados"} <= set(r.json())
        assert r.json()["status"] in {"ok", "sem_resposta", "ambiguo", "entrada_invalida"}


def test_resposta_ok_sempre_vem_com_fonte_e_data(cliente):
    registros = [{"id": 1, "tema": "cartoes", "perguntas": ["Como emitir cartao?"],
                  "orientacao": "Texto de teste.", "referencia": "Fonte de teste",
                  "data_verificacao": "2026-11-10", "status": "verificado"}]
    with patch("backend.src.api.carregar", return_value=registros):
        r = cliente.post("/consultar", json={"pergunta": "Como emitir cartao?"}).json()
    assert r["status"] == "ok"
    assert r["fontes"] == [{"referencia": "Fonte de teste", "data_verificacao": "2026-11-10"}]


def test_registro_rascunho_nunca_gera_resposta(cliente):
    registros = [{"id": 1, "tema": "cartoes", "perguntas": ["Como emitir cartao?"],
                  "orientacao": "", "referencia": "", "data_verificacao": "", "status": "rascunho"}]
    with patch("backend.src.api.carregar", return_value=registros):
        r = cliente.post("/consultar", json={"pergunta": "Como emitir cartao?"}).json()
    assert r["status"] == "sem_resposta" and r["fontes"] == []


def test_base_ausente_vira_422_e_nao_500(cliente):
    with patch("backend.src.api.carregar", side_effect=ValueError("Base ausente ou inválida")):
        r = cliente.post("/consultar", json={"pergunta": "gratuidade"})
    assert r.status_code == 422


def test_consultar_valida_entrada(cliente):
    assert cliente.post("/consultar", json={"pergunta": "x" * 501}).status_code == 422
    assert cliente.post("/consultar", json={"pergunta": "oi", "modelo": "Z"}).status_code == 422
    assert cliente.post("/consultar", json={}).status_code == 422


# ---------------------------------------------- 2 - Rotas e tarifas
def test_rotas_exemplo_cumpre_o_contrato_e_se_declara_simulado(cliente):
    r = cliente.get("/rotas/exemplo").json()
    assert r["modo"] == "demonstracao"
    assert "ficticios" in r["origem_dados"] and r["aviso"]
    rotas = r["resultado"]["rotas"]
    assert 1 <= len(rotas) <= 3
    assert [x["ordem"] for x in rotas] == list(range(1, len(rotas) + 1))
    for rota in rotas:
        assert {"tempo_total_min", "custo", "seguranca", "acessibilidade", "trechos", "fontes"} <= set(rota)
        assert rota["trechos"] and rota["seguranca"]["status"]


def test_rotas_rejeita_coordenadas_invalidas_e_pedido_incompleto(cliente):
    ruim = {**PEDIDO_ROTA, "origem": {"lat": 100, "lon": 0}}
    assert cliente.post("/rotas", json=ruim).status_code == 422
    assert cliente.post("/rotas", json={"origem": PEDIDO_ROTA["origem"]}).status_code == 422


def test_rotas_partida_invalida_vira_erro_estruturado_sem_rotas(cliente):
    """Contrato do módulo 2: erro de domínio volta com HTTP 200 e `resultado.erro`."""
    r = cliente.post("/rotas", json={**PEDIDO_ROTA, "partida": "ontem"})
    assert r.status_code == 200
    resultado = r.json()["resultado"]
    assert resultado["rotas"] == [] and resultado["n_rotas"] == 0
    assert resultado["erro"]["codigo"] == "partida_invalida" and resultado["erro"]["mensagem"]


# ---------------------------------------------- 3 - Acessibilidade e segurança
def test_dado_desconhecido_nao_vira_acessibilidade_confirmada_no_motor(cliente):
    corpo = {**PEDIDO_ROTA, "necessidades": {"acessibilidade": ["sem_degraus"]}}
    rotas = cliente.post("/rotas", json=corpo).json()["resultado"]["rotas"]
    assert rotas
    assert {r["acessibilidade"] for r in rotas} == {"NAO_VERIFICADA"}


def test_avaliacao_com_trecho_desconhecido_fica_nao_verificada(cliente):
    r = cliente.post("/acessibilidade/avaliar", json={"trechos": [
        {"id": "T1", "descricao": "Entrada", "passagem_sem_degraus": True},
        {"id": "T2", "descricao": "Plataforma", "passagem_sem_degraus": None},
    ]}).json()
    assert r["status"] == "NAO_VERIFICADA" and r["pendencias"] == ["T2 - Plataforma"]
    assert r["verificacao_em_campo"] is False and r["aviso"]


def test_barreira_comprovada_torna_o_percurso_incompativel(cliente):
    r = cliente.post("/acessibilidade/avaliar", json={"trechos": [
        {"id": "T1", "descricao": "Escada fixa", "passagem_sem_degraus": False},
        {"id": "T2", "descricao": "Plataforma", "passagem_sem_degraus": None},
    ]}).json()
    assert r["status"] == "INCOMPATIVEL" and r["barreiras"] == ["T1 - Escada fixa"]


def test_somente_todos_os_trechos_confirmados_resultam_compativel(cliente):
    r = cliente.post("/acessibilidade/avaliar", json={"trechos": [
        {"id": "T1", "descricao": "A", "passagem_sem_degraus": True},
    ]}).json()
    assert r["status"] == "COMPATIVEL" and r["verificacao_em_campo"] is False


def test_rota_real_nunca_afirma_acessibilidade_mesmo_se_pedida(cliente):
    corpo = {"origem": {"lat": -23.55, "lon": -46.63}, "destino": {"lat": -23.56, "lon": -46.64},
             "modal": "ferroviario", "evitar_escadas": True}
    with patch("backend.src.transitous_api.consultar_transitous", return_value=dict(ROTA_REAL)):
        r = cliente.post("/rotas/reais", json=corpo).json()
    assert r["acessibilidade"]["status"] == "NAO_VERIFICADA"
    assert r["acessibilidade"]["solicitou_sem_degraus"] is True
    assert "Não é possível garantir" in r["acessibilidade"]["aviso"]


# ---------------------------------------------- 4 - Interface e mapa
def test_sugestoes_exigem_ao_menos_4_caracteres(cliente):
    assert cliente.get("/enderecos/sugestoes", params={"q": "ab"}).status_code == 422


def test_rota_real_falha_do_provedor_vira_503_com_mensagem(cliente):
    from fastapi import HTTPException
    corpo = {"origem": {"lat": -23.55, "lon": -46.63}, "destino": {"lat": -23.56, "lon": -46.64},
             "modal": "onibus"}
    erro = HTTPException(status_code=503, detail="Não foi possível conectar ao Transitous.")
    with patch("backend.src.transitous_api.consultar_transitous", side_effect=erro):
        r = cliente.post("/rotas/reais", json=corpo)
    assert r.status_code == 503 and "Transitous" in r.json()["detail"]


@pytest.mark.parametrize("modal", MODAIS_VALIDOS)
def test_chat_e_sessao_aceitam_os_mesmos_modais(cliente, modal):
    chat = cliente.post("/agente/conversar", json={"pergunta": "Como chegar à Paulista?", "modal": modal})
    assert chat.status_code == 200
    s = cliente.post("/sessoes", json={}).json()
    r = cliente.post(f"/sessoes/{s['codigo']}/estado", json={"token": s["token"], "modal": modal})
    assert r.status_code == 200


def test_chat_e_sessao_recusam_o_mesmo_modal_invalido(cliente):
    assert cliente.post("/agente/conversar",
                        json={"pergunta": "Como chegar à Paulista?", "modal": "carro"}).status_code == 422
    s = cliente.post("/sessoes", json={}).json()
    assert cliente.post(f"/sessoes/{s['codigo']}/estado",
                        json={"token": s["token"], "modal": "carro"}).status_code == 422


def test_sessao_e_rotas_reais_validam_coordenadas_do_mesmo_modo(cliente):
    s = cliente.post("/sessoes", json={}).json()
    ruim = {"lat": 91, "lon": 0}
    assert cliente.post("/rotas/reais", json={"origem": ruim, "destino": ruim}).status_code == 422
    assert cliente.post(f"/sessoes/{s['codigo']}/estado",
                        json={"token": s["token"], "origem": ruim}).status_code == 422


def test_chat_sem_pontos_pede_origem_e_destino_sem_chamar_o_motor(cliente):
    with patch("backend.src.agente_api.rota_real") as motor:
        r = cliente.post("/agente/conversar", json={"pergunta": "Como chegar à Paulista?"}).json()
    motor.assert_not_called()
    assert r["rota"] is None and r["origem_resposta"] == "orientacao_do_app"


def test_chat_sem_base_verificada_nao_inventa_direitos_nem_fontes(cliente):
    with patch("backend.src.agente_api.carregar", return_value=[]), patch(
            "backend.src.agente_api.responder", return_value={"status": "sem_resposta", "fontes": []}):
        r = cliente.post("/agente/conversar", json={"pergunta": "Quem tem direito à gratuidade?"}).json()
    assert r["origem_resposta"] == "sem_resposta_verificada"
    assert r["fontes"] == [] and r["rota"] is None


def test_chat_com_falha_de_rota_responde_200_com_aviso(cliente):
    from fastapi import HTTPException
    corpo = {"pergunta": "Qual metrô pegar para chegar à Paulista?",
             "origem": {"lat": -23.55, "lon": -46.63}, "destino": {"lat": -23.56, "lon": -46.64}}
    with patch("backend.src.agente_api.rota_real", side_effect=HTTPException(503, "Provedor fora do ar")):
        r = cliente.post("/agente/conversar", json=corpo)
    assert r.status_code == 200
    assert r.json()["origem_resposta"] == "rota_indisponivel" and r.json()["rota"] is None


def test_erros_de_validacao_usam_o_formato_detail_do_fastapi(cliente):
    """O frontend lê `detail`; todos os módulos devem manter esse formato."""
    for caminho, corpo in (("/consultar", {}), ("/rotas", {}), ("/acessibilidade/avaliar", {}),
                           ("/rotas/reais", {}), ("/agente/conversar", {}), ("/sessoes/AAAAAA/entrar", {"x": 1})):
        r = cliente.post(caminho, json=corpo)
        assert r.status_code == 422, caminho
        assert "detail" in r.json(), caminho


# ---------------------------------------------- fluxo ponta a ponta
def test_fluxo_colaborativo_ponta_a_ponta(cliente):
    """Ana e Bia planejam juntas: busca de endereço, rota real, escolha e mudança de plano."""
    sugestoes = [{"nome": "Praça da Sé, São Paulo", "lat": -23.5505, "lon": -46.6333,
                  "fonte": "OpenStreetMap/Photon"}]
    with patch("backend.src.enderecos_api._buscar_cache", return_value=sugestoes):
        achado = cliente.get("/enderecos/sugestoes", params={"q": "Praça da Sé"}).json()["resultados"][0]
    destino = {"lat": -23.5614, "lon": -46.6559, "rotulo": "Avenida Paulista"}

    ana = cliente.post("/sessoes", json={"apelido": "Ana"}).json()
    cod = ana["codigo"]
    bia = cliente.post(f"/sessoes/{cod}/entrar", json={"apelido": "Bia"}).json()
    cliente.post(f"/sessoes/{cod}/estado", json={
        "token": ana["token"], "origem": {"lat": achado["lat"], "lon": achado["lon"], "rotulo": achado["nome"]},
        "destino": destino, "modal": "ferroviario", "evitar_escadas": True})

    # Bia lê o plano compartilhado e consulta a rota com exatamente esses dados
    plano = cliente.post(f"/sessoes/{cod}/sincronizar", json={"token": bia["token"]}).json()["estado"]
    pedido = {"origem": {k: plano["origem"][k] for k in ("lat", "lon")},
              "destino": {k: plano["destino"][k] for k in ("lat", "lon")},
              "modal": plano["modal"], "evitar_escadas": plano["evitar_escadas"]}
    with patch("backend.src.transitous_api.consultar_transitous", return_value=dict(ROTA_REAL)) as motor:
        rota = cliente.post("/rotas/reais", json=pedido)
    assert rota.status_code == 200
    assert motor.call_args.args[2] == "ferroviario"
    assert rota.json()["acessibilidade"]["status"] == "NAO_VERIFICADA"

    # Bia escolhe a alternativa 0; Ana enxerga a escolha sem reenviar nada
    cliente.post(f"/sessoes/{cod}/estado", json={"token": bia["token"], "rota_selecionada": 0})
    ana_ve = cliente.post(f"/sessoes/{cod}/sincronizar", json={"token": ana["token"]}).json()
    assert ana_ve["estado"]["rota_selecionada"] == 0

    # Ana muda o destino: a escolha anterior deixa de valer para as duas
    cliente.post(f"/sessoes/{cod}/estado", json={"token": ana["token"], "destino": None})
    bia_ve = cliente.post(f"/sessoes/{cod}/sincronizar", json={"token": bia["token"]}).json()
    assert bia_ve["estado"]["destino"] is None and bia_ve["estado"]["rota_selecionada"] is None
    assert [p["apelido"] for p in bia_ve["participantes"]] == ["Ana", "Bia"]

    # Encerrar apaga tudo; nenhum dado da sessão sobrevive
    assert cliente.post(f"/sessoes/{cod}/encerrar", json={"token": ana["token"]}).status_code == 200
    assert cliente.post(f"/sessoes/{cod}/sincronizar", json={"token": bia["token"]}).status_code == 404
    assert cliente.get("/integracao/status").json()["sessoes_ativas"] == 0
