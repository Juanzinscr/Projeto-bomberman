
import random

ACOES_MOVIMENTO = {
    "cima": (0, -1),
    "baixo": (0, 1),
    "esquerda": (-1, 0),
    "direita": (1, 0)
}


def decidir_acao(
    player, mapa, jogadores, bombas,
    tempo_restante, pontos, hud_info, self_state
):
    x = self_state["grid_x"]
    y = self_state["grid_y"]

    linhas = hud_info["rows"]
    colunas = hud_info["cols"]

    # Identifica as posições das bombas ativas.
    posicoes_bombas = {
        (b.x, b.y)
        for b in bombas
        if not b.explodida
    }

    # Identifica as posições dos outros jogadores vivos.
    posicoes_jogadores = {
        (p.grid_x, p.grid_y)
        for p in jogadores
        if p is not player and p.ativo
    }

    candidatos = []

    for acao, (dx, dy) in ACOES_MOVIMENTO.items():
        nx = x + dx
        ny = y + dy

        # Verifica os limites do mapa.
        if not (0 <= nx < colunas and 0 <= ny < linhas):
            continue

        # Só permite entrar em espaços livres ou com power-ups.
        if mapa[ny][nx] not in [0, 3, 4]:
            continue

        # Evita bombas e outros jogadores.
        if (nx, ny) in posicoes_bombas:
            continue

        if (nx, ny) in posicoes_jogadores:
            continue

        # Conta quantas saídas livres existem na próxima posição.
        saidas = 0

        for ddx, ddy in ACOES_MOVIMENTO.values():
            sx = nx + ddx
            sy = ny + ddy

            if not (0 <= sx < colunas and 0 <= sy < linhas):
                continue

            if mapa[sy][sx] not in [0, 3, 4]:
                continue

            if (sx, sy) in posicoes_bombas:
                continue

            if (sx, sy) in posicoes_jogadores:
                continue

            saidas += 1

        candidatos.append((acao, saidas))

    # Se não houver movimento válido, fica parado.
    if not candidatos:
        return "parado"

    # Prefere movimentos com mais saídas disponíveis.
    melhor_pontuacao = max(saidas for _, saidas in candidatos)

    melhores_acoes = [
        acao
        for acao, saidas in candidatos
        if saidas == melhor_pontuacao
    ]

    return random.choice(melhores_acoes)