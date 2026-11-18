# encoding: utf-8
"""Servidor Python local do Citizen Tech (parte 5 - Servidor e integração).

Uso, a partir da raiz do repositório:

    python app.py                      # servidor em http://127.0.0.1:8000
    python app.py --porta 8010         # outra porta
    python app.py --verificar          # confere os contratos e sai (sem abrir servidor)
    python app.py --host 0.0.0.0       # visível na rede local (celular); sem autenticação

Este arquivo é a "raiz de composição": reaproveita a API de backend/src/api.py,
acrescenta a sessão colaborativa (backend/src/sessoes.py) e o endpoint
GET /integracao/status, que confere se cada módulo expõe os endpoints do
contrato abaixo. O comando antigo `python -m uvicorn backend.src.api:app`
continua funcionando, mas sem sessões nem /integracao/status.
"""
from __future__ import annotations

import argparse
import sys

import uvicorn

from backend.src.api import app as _api_app
from backend.src.config_app import obter_modo
from backend.src.sessoes import AVISO_PRIVACIDADE, router as router_sessoes
from backend.src.sessoes import obter_gerenciador

VERSAO_INTEGRACAO = "1.0"

# Contrato entre módulos: quem é responsável por qual endpoint. Se alguém
# renomear ou remover um deles, /integracao/status e os testes de
# backend/tests/integracao apontam a quebra.
CONTRATOS: dict[str, list[tuple[str, str]]] = {
    "1 - Dados e fontes": [
        ("GET", "/temas"),
        ("POST", "/consultar"),
    ],
    "2 - Rotas e tarifas": [
        ("POST", "/rotas"),
        ("GET", "/rotas/exemplo"),
    ],
    "3 - Acessibilidade e segurança": [
        ("POST", "/acessibilidade/avaliar"),
    ],
    "4 - Interface e mapa (endpoints consumidos pelo frontend)": [
        ("GET", "/enderecos/sugestoes"),
        ("POST", "/rotas/reais"),
        ("POST", "/agente/conversar"),
        ("GET", "/assistente/saude"),
        ("POST", "/assistente/perguntar"),
    ],
    "5 - Servidor e integração": [
        ("GET", "/health"),
        ("GET", "/integracao/status"),
        ("POST", "/sessoes"),
        ("POST", "/sessoes/{codigo}/entrar"),
        ("POST", "/sessoes/{codigo}/sincronizar"),
        ("POST", "/sessoes/{codigo}/estado"),
        ("POST", "/sessoes/{codigo}/sair"),
        ("POST", "/sessoes/{codigo}/encerrar"),
    ],
}

HOSTS_LOCAIS = ("127.0.0.1", "localhost", "::1")


def criar_app():
    """Monta a aplicação final. Pode ser chamada mais de uma vez sem duplicar rotas."""
    app = _api_app
    caminhos = _rotas_registradas(app)
    if ("POST", "/sessoes") not in caminhos:
        app.include_router(router_sessoes)
    if ("GET", "/integracao/status") not in caminhos:
        app.add_api_route("/integracao/status", status_integracao, methods=["GET"],
                          tags=["Integração"])
    app.openapi_schema = None  # força o /docs a incluir as rotas acrescentadas
    return app


def _rotas_registradas(app) -> set[tuple[str, str]]:
    """Pares (MÉTODO, caminho) vindos do OpenAPI, que funciona em qualquer versão do FastAPI."""
    esquema = app.openapi()["paths"]
    return {(m.upper(), caminho) for caminho, ops in esquema.items()
            for m in ops if m.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE"}}


def verificar_contratos(app=None) -> dict:
    """Confere se todos os endpoints do contrato estão registrados."""
    app = app or _api_app
    registrados = _rotas_registradas(app)
    modulos = []
    for nome, endpoints in CONTRATOS.items():
        itens = [{"metodo": m, "caminho": c, "presente": (m, c) in registrados}
                 for m, c in endpoints]
        modulos.append({"modulo": nome, "ok": all(i["presente"] for i in itens),
                        "endpoints": itens})
    return {"ok": all(m["ok"] for m in modulos), "modulos": modulos}


def status_integracao() -> dict:
    """Resumo do servidor: modo, contratos conferidos e sessões ativas."""
    resultado = verificar_contratos()
    return {
        **resultado,
        "versao_integracao": VERSAO_INTEGRACAO,
        "modo": obter_modo(),
        "sessoes_ativas": obter_gerenciador().total_ativas(),
        "aviso": "Protótipo acadêmico; não é canal oficial de órgãos públicos ou operadores.",
    }


app = criar_app()


def _argumentos(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Servidor local do Citizen Tech")
    p.add_argument("--host", default="127.0.0.1",
                   help="endereço de escuta (padrão: 127.0.0.1, só este computador)")
    p.add_argument("--porta", type=int, default=8000, help="porta (padrão: 8000)")
    p.add_argument("--reload", action="store_true",
                   help="reinicia ao salvar arquivos (desenvolvimento)")
    p.add_argument("--verificar", action="store_true",
                   help="confere contratos e base de orientações e sai")
    args = p.parse_args(argv)
    if not 1 <= args.porta <= 65535:
        p.error("a porta deve estar entre 1 e 65535")
    return args


def _verificar_e_imprimir() -> int:
    from backend.src.core import carregar

    resultado = verificar_contratos()
    for modulo in resultado["modulos"]:
        print(f"[{'OK' if modulo['ok'] else 'FALHA'}] {modulo['modulo']}")
        for e in modulo["endpoints"]:
            if not e["presente"]:
                print(f"      ausente: {e['metodo']} {e['caminho']}")
    try:
        registros = carregar()
        print(f"[OK] Base de orientações carregada: {len(registros)} registro(s)")
    except ValueError as exc:
        print(f"[FALHA] Base de orientações: {exc}")
        return 1
    return 0 if resultado["ok"] else 1


def main(argv: list[str] | None = None) -> int:
    args = _argumentos(argv)
    try:
        modo = obter_modo()
    except ValueError as exc:
        print(f"Erro de configuração: {exc}", file=sys.stderr)
        return 2
    if args.verificar:
        return _verificar_e_imprimir()

    if args.host not in HOSTS_LOCAIS:
        print("ATENCAO: o servidor ficará acessível a outros aparelhos da rede, sem "
              "autenticação. Use apenas em rede de confiança.", file=sys.stderr)
    print(f"Citizen Tech em http://{args.host}:{args.porta}  (modo: {modo})")
    print(f"Documentação interativa: http://{args.host}:{args.porta}/docs")
    print(AVISO_PRIVACIDADE)
    if not args.reload:
        # Carrega o classificador antes de aceitar pedidos; se falhar, a API segue de pé.
        from backend.src.assistente.rotas_api import preparar_modelo
        estado = "carregado" if preparar_modelo() is not None else "indisponível (a API segue funcionando)"
        print(f"Assistente (classificador): {estado}")
    try:
        uvicorn.run("app:app" if args.reload else app, host=args.host,
                    port=args.porta, reload=args.reload)
    except OSError as exc:
        print(f"Não foi possível abrir a porta {args.porta}: {exc}. "
              "Feche o outro programa ou use --porta.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
