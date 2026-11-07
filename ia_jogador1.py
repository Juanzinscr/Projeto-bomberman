
import random
from collections import deque

ACOES_MOVIMENTO = {
    "cima": (0, -1),
    "baixo": (0, 1),
    "esquerda": (-1, 0),
    "direita": (1, 0)
}

direcao_atual = "baixo"

estado_bomba = "livre"
destino_fuga = None
alvo_atual = None

def decidir_acao(
    player, mapa, jogadores, bombas,
    tempo_restante, pontos, hud_info, self_state
):
    global direcao_atual, estado_bomba, destino_fuga, alvo_atual

    x = self_state["grid_x"]
    y = self_state["grid_y"]
    linhas = hud_info["rows"]
    colunas = hud_info["cols"]

    print(
    f"[DIAGNOSTICO] Posição: ({x}, {y}) | "
    f"Bombas próprias: {len(player.bombas)} | "
    f"Jogadores ativos: "
    f"{sum(1 for p in jogadores if p is not player and p.ativo)}"
    )

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

        # Verifica se existe uma rota até um abrigo,
    # permitindo atravessar casas que serão atingidas
    def existe_rota_de_fuga(inicio_x, inicio_y, perigos):
        fila = deque([(inicio_x, inicio_y)])
        visitadas = {(inicio_x, inicio_y)}

        while fila:
            atual_x, atual_y = fila.popleft()

            # Encontrou uma casa segura diferente da posição da bomba
            if (
                (atual_x, atual_y) != (inicio_x, inicio_y)
                and (atual_x, atual_y) not in perigos
            ):
                return True

            for dx, dy in ACOES_MOVIMENTO.values():
                nx = atual_x + dx
                ny = atual_y + dy

                if (nx, ny) in visitadas:
                    continue

                if not pode_andar(nx, ny):
                    continue

                visitadas.add((nx, ny))
                fila.append((nx, ny))

        return False
   
   
    # PRIORIDADE 1: fugir de qualquer bomba, inclusive dos adversários
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

        rota_fuga = encontrar_caminho(
            casas_seguras,
            casas_perigosas,
            permitir_perigo=True
        )

        if rota_fuga is not None:

            print(
                f"[FUGA PERIGO] Bomba detectada! "
                f"Posição: ({x}, {y}) | "
                f"Saindo por: {rota_fuga}"
            )

            return rota_fuga

        print(
            f"[ERRO FUGA] Sem rota segura em ({x}, {y})"
        )

        return "parado"

    print("[DIAGNOSTICO] Chegou à seleção de adversários")
    # 2. Identificar e selecionar um adversário como alvo
    
    adversarios = [
        p for p in jogadores
        if p is not player and p.ativo
    ]

    print(f"[DEBUG ALVO] alvo_atual: {alvo_atual}")
    print(f"[DEBUG ALVO] Está vazio? {alvo_atual is None}")
    print(f"[DEBUG ALVO] Adversários encontrados: {len(adversarios)}")
    
    
    # Verifica se precisamos escolher um novo alvo
    if (
            alvo_atual is None
            or not alvo_atual.ativo
            or alvo_atual not in adversarios
        ):
    
            if adversarios:
                # Escolhe o adversário mais próximo
                alvo_atual = min(
                    adversarios,
                    key=lambda p:
                        abs(p.grid_x - x) + abs(p.grid_y - y)
                )

                
                print(
                    f"[ALVO] Adversário selecionado: "
                    f"({alvo_atual.grid_x}, {alvo_atual.grid_y})"
                )
    
            else:
                alvo_atual = None
                print("[ALVO] Nenhum adversário disponível")
                

    # 3. Procurar power-ups: 3 = bomba, 4 = alcance
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

    
    # 4. Perseguir e atacar o adversário selecionado

    if alvo_atual is not None and alvo_atual.ativo:

        alvo_x = alvo_atual.grid_x
        alvo_y = alvo_atual.grid_y

        print(
            f"[DEBUG PERSEGUIÇÃO] Minha posição: ({x}, {y}) | "
            f"Posição do alvo: ({alvo_x}, {alvo_y})"
        )
        # Calcular a distância até o adversário
        distancia_alvo = (
            abs(alvo_x - x) + abs(alvo_y - y)
        )

        # Verificar se a explosão da nossa bomba atingiria o alvo
        explosao_ataque = calcular_explosao(
            x, y, self_state["bomba_nivel"]
        )

        alvo_na_explosao = (alvo_x, alvo_y) in explosao_ataque

        bombas_ativas = self_state["bombas_ativas"]
        max_bombas = self_state["max_bombas"]

        bomba_no_local = any(
            (b.x, b.y) == (x, y) and not b.explodida
            for b in bombas
        )

        print(
            f"[ANALISE ATAQUE] Distância: {distancia_alvo} | "
            f"Alvo no alcance: {alvo_na_explosao} | "
            f"Bombas: {bombas_ativas}/{max_bombas}"
        )

        # PRIORIDADE: atacar se o adversário estiver na explosão
        if (
            alvo_na_explosao
            and bombas_ativas < max_bombas
            and not bomba_no_local
        ):

            perigo_total = casas_perigosas | explosao_ataque

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

                print(
                    f"[ATAQUE JOGADOR] Alvo: ({alvo_x}, {alvo_y}) | "
                    f"Bomba em: ({x}, {y})"
                )

                return "bomba"

            else:
                print("[ATAQUE CANCELADO] Não encontrei abrigo.")

        # Se não conseguimos atacar, continuar perseguindo
        if distancia_alvo == 1:

            print(
                f"[ALVO PROXIMO] Estamos ao lado do adversário "
                f"em ({alvo_x}, {alvo_y})"
            )

        else:

            posicoes_ao_redor_alvo = set()

            for dx, dy in ACOES_MOVIMENTO.values():

                nx = alvo_x + dx
                ny = alvo_y + dy

                if not pode_andar(nx, ny):
                    continue

                if (nx, ny) in casas_perigosas:
                    continue

                posicoes_ao_redor_alvo.add((nx, ny))

            caminho_alvo = encontrar_caminho(
                posicoes_ao_redor_alvo,
                casas_perigosas
            )

            if caminho_alvo is not None:

                direcao_atual = caminho_alvo

                print(
                    f"[PERSEGUINDO] Alvo: ({alvo_x}, {alvo_y}) | "
                    f"Movimento: {caminho_alvo}"
                )

                return caminho_alvo

        # 4. Perseguir o adversário selecionado

        
        
    # 4. Procurar posições ao lado de blocos destrutíveis (valor 1)
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

                # Simula uma bomba nesta posição
                explosao_teste = calcular_explosao(
                    nx, ny, self_state["bomba_nivel"]
                )

                perigo_teste = casas_perigosas | explosao_teste

                # Verifica se existe uma rota completa até um abrigo
                tem_rota = existe_rota_de_fuga(
                    nx,
                    ny,
                    perigo_teste
                )

                if tem_rota:
                    posicoes_para_atacar.add((nx, ny))

    # Se já está ao lado de um bloco, avaliar colocar uma bomba
    if (x, y) in posicoes_para_atacar:
        bombas_ativas = self_state["bombas_ativas"]
        max_bombas = self_state["max_bombas"]

        print(
                    f"[ATAQUE] Posição: ({x}, {y}) | "
                    f"Bombas ativas: {self_state['bombas_ativas']} | "
                    f"Posições de ataque: {len(posicoes_para_atacar)}"
                    )
        
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

    return "parado"
