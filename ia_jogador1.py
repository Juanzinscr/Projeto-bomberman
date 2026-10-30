
import random
from collections import deque

ACOES_MOVIMENTO = {
    "cima": (0, -1),
    "baixo": (0, 1),
    "esquerda": (-1, 0),
    "direita": (1, 0)
}

direcao_atual = "baixo"


def decidir_acao(
    player, mapa, jogadores, bombas,
    tempo_restante, pontos, hud_info, self_state
):
    global direcao_atual

    x = self_state["grid_x"]
    y = self_state["grid_y"]
    linhas = hud_info["rows"]
    colunas = hud_info["cols"]

    # Casas ocupadas por bombas e outros jogadores
    posicoes_bombas = {
        (b.x, b.y) for b in bombas if not b.explodida
    }

    posicoes_jogadores = {
        (p.grid_x, p.grid_y)
        for p in jogadores
        if p is not player and p.ativo
    }

    def pode_andar(nx, ny):
        if not (0 <= nx < colunas and 0 <= ny < linhas):
            return False

        if mapa[ny][nx] not in [0, 3, 4]:
            return False

        if (nx, ny) in posicoes_bombas:
            return False

        if (nx, ny) in posicoes_jogadores:
            return False

        return True

    # Calcula as casas atingidas por uma explosão
    def calcular_explosao(bx, by, nivel):
        casas = {(bx, by)}
        alcance = 1 + (nivel - 1) * 2

        for dx, dy in ACOES_MOVIMENTO.values():
            for distancia in range(1, alcance + 1):
                nx = bx + dx * distancia
                ny = by + dy * distancia

                if not (0 <= nx < colunas and 0 <= ny < linhas):
                    break

                if mapa[ny][nx] == 2:
                    break

                casas.add((nx, ny))

                if mapa[ny][nx] == 1:
                    break

        return casas

    # Identifica áreas perigosas de bombas existentes
    casas_perigosas = set()

    for bomba in bombas:
        if bomba.explodida:
            if bomba.tempo_fogo > 0:
                casas_perigosas.update(bomba.fogo)
        else:
            casas_perigosas.update(
                calcular_explosao(bomba.x, bomba.y, bomba.nivel)
            )

    # Encontra um caminho até uma das casas desejadas.
    # Retorna a primeira direção desse caminho.
    def encontrar_caminho(destinos, perigos, permitir_perigo=False):
        destinos = set(destinos)

        if not destinos:
            return None

        fila = deque([(x, y, None)])
        visitadas = {(x, y)}

        while fila:
            atual_x, atual_y, primeira_acao = fila.popleft()

            if (atual_x, atual_y) in destinos:
                return primeira_acao

            for acao, (dx, dy) in ACOES_MOVIMENTO.items():
                nx = atual_x + dx
                ny = atual_y + dy

                if (nx, ny) in visitadas:
                    continue

                if not pode_andar(nx, ny):
                    continue

                if not permitir_perigo and (nx, ny) in perigos:
                    continue

                visitadas.add((nx, ny))

                if primeira_acao is None:
                    proxima_acao = acao
                else:
                    proxima_acao = primeira_acao

                fila.append((nx, ny, proxima_acao))

        return None

   
    # PRIORIDADE: fugir das próprias bombas
    if player.bombas:

        # Se ainda estiver em uma área perigosa,
        # procurar uma rota até uma casa segura.
        if (x, y) in casas_perigosas:

            casas_seguras = [
                (cx, cy)
                for cy in range(linhas)
                for cx in range(colunas)
                if mapa[cy][cx] in [0, 3, 4]
                and (cx, cy) not in casas_perigosas
                and (cx, cy) not in posicoes_bombas
                and (cx, cy) not in posicoes_jogadores
            ]

            fuga = encontrar_caminho(
                casas_seguras,
                casas_perigosas
            )

            if fuga is not None:
                print(
                    f"[FUGA] Posição: ({x}, {y}) | "
                    f"Ação escolhida: {fuga}"
                )
                direcao_atual = fuga
                return fuga

            print(f"[ERRO FUGA] Nenhuma rota segura a partir de ({x}, {y})")

            # Se não encontrar uma rota completa,
            # tentar ao menos um movimento fora do perigo.
            saidas = [
                acao
                for acao, (dx, dy) in ACOES_MOVIMENTO.items()
                if pode_andar(x + dx, y + dy)
                and (x + dx, y + dy) not in casas_perigosas
            ]

            if saidas:
                direcao_atual = random.choice(saidas)
                return direcao_atual

            return "parado"

        # Já chegou a uma casa segura.
        # Esperar a bomba explodir e o fogo desaparecer.
        return "parado"


    # 2. Procurar power-ups: 3 = bomba, 4 = alcance
    powerups = [
        (cx, cy)
        for cy in range(linhas)
        for cx in range(colunas)
        if mapa[cy][cx] in [3, 4]
        and (cx, cy) not in casas_perigosas
    ]

    caminho_powerup = encontrar_caminho(powerups, casas_perigosas)

    if caminho_powerup is not None:
        direcao_atual = caminho_powerup
        return caminho_powerup

    # 3. Procurar posições ao lado de blocos destrutíveis (valor 1)
    posicoes_para_atacar = set()

    for by in range(linhas):
        for bx in range(colunas):
            if mapa[by][bx] != 1:
                continue

            for dx, dy in ACOES_MOVIMENTO.values():
                nx = bx + dx
                ny = by + dy

                if not pode_andar(nx, ny):
                    continue

                if (nx, ny) in casas_perigosas:
                    continue

                posicoes_para_atacar.add((nx, ny))

    # Se já está ao lado de um bloco, avaliar colocar uma bomba
    if (x, y) in posicoes_para_atacar:
        bombas_ativas = self_state["bombas_ativas"]
        max_bombas = self_state["max_bombas"]

        bomba_no_local = any(
            (b.x, b.y) == (x, y) and not b.explodida
            for b in bombas
        )

        if bombas_ativas < max_bombas and not bomba_no_local:
            explosao_nova = calcular_explosao(
                x, y, self_state["bomba_nivel"]
            )

            perigo_total = casas_perigosas | explosao_nova

            casas_de_fuga = [
                (cx, cy)
                for cy in range(linhas)
                for cx in range(colunas)
                if mapa[cy][cx] in [0, 3, 4]
                and (cx, cy) not in perigo_total
                and (cx, cy) not in posicoes_bombas
                and (cx, cy) not in posicoes_jogadores
            ]

            rota_de_fuga = encontrar_caminho(
                casas_de_fuga,
                perigo_total,
                permitir_perigo=True
            )

            if rota_de_fuga is not None:
                return "bomba"
            print(
                f"[ATAQUE] Posição: ({x}, {y}) | "
                f"Bombas ativas: {self_state['bombas_ativas']} | "
                f"Posições de ataque: {len(posicoes_para_atacar)}"
            )

    # Se não estiver ao lado de um bloco, caminhar até uma posição de ataque
    caminho_bloco = encontrar_caminho(
        posicoes_para_atacar, casas_perigosas
    )

    if caminho_bloco is not None:
        direcao_atual = caminho_bloco
        return caminho_bloco

    # 4. Explorar: continuar na direção atual se for possível
    dx, dy = ACOES_MOVIMENTO[direcao_atual]
    proximo_x = x + dx
    proximo_y = y + dy

    if (
        pode_andar(proximo_x, proximo_y)
        and (proximo_x, proximo_y) not in casas_perigosas
    ):
        return direcao_atual

    # Se a direção estiver bloqueada, escolher uma alternativa
    movimentos_validos = [
        acao
        for acao, (dx, dy) in ACOES_MOVIMENTO.items()
        if pode_andar(x + dx, y + dy)
        and (x + dx, y + dy) not in casas_perigosas
    ]

    if not movimentos_validos:
        movimentos_validos = [
            acao
            for acao, (dx, dy) in ACOES_MOVIMENTO.items()
            if pode_andar(x + dx, y + dy)
        ]

    if movimentos_validos:
        direcao_atual = random.choice(movimentos_validos)
        return direcao_atual

    return "parado"
