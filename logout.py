import threading

from tkinter import messagebox

import banco
from stt import ouvir
from tts import falar


def consultar_pedidos_em_andamento(nome_colaborador=None):
    conn = banco.conectar()
    cursor = conn.cursor()
    parametros = []
    sql = """
        SELECT id, status, colaborador, data_criacao, data_conclusao
        FROM pedidos
        WHERE status IN ('Em Andamento', 'Pausado')
    """
    if nome_colaborador:
        sql += " AND colaborador = ?"
        parametros.append(nome_colaborador)
    sql += " ORDER BY id ASC"
    cursor.execute(sql, parametros)
    linhas = cursor.fetchall()
    conn.close()
    return linhas


def pausar_pedido(pedido_id, nome_colaborador):
    conn = banco.conectar()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE pedidos SET status = 'Pausado', colaborador = ? WHERE id = ?",
        (nome_colaborador, pedido_id),
    )
    cursor.execute(
        """
        INSERT INTO sessao_operacao
            (pedido_id, colaborador, status, ultimo_item_id)
        VALUES (?, ?, 'Pausado', (
            SELECT id FROM itens_pedido
            WHERE pedido_id = ? AND qtd_conferida = 0
            ORDER BY id ASC LIMIT 1
        ))
        """,
        (pedido_id, nome_colaborador, pedido_id),
    )
    conn.commit()
    conn.close()


def retomar_pedido(pedido_id, nome_colaborador):
    conn = banco.conectar()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE pedidos SET status = 'Em Andamento', colaborador = ? WHERE id = ?",
        (nome_colaborador, pedido_id),
    )
    cursor.execute(
        """
        INSERT INTO sessao_operacao
            (pedido_id, colaborador, status, ultimo_item_id)
        VALUES (?, ?, 'Em Andamento', (
            SELECT id FROM itens_pedido
            WHERE pedido_id = ? AND qtd_conferida = 0
            ORDER BY id ASC LIMIT 1
        ))
        """,
        (pedido_id, nome_colaborador, pedido_id),
    )
    conn.commit()
    conn.close()


def registrar_logout(nome_colaborador, pedido_id=None, acao="Sair"):
    conn = banco.conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO historico_logout
            (pedido_id, colaborador, acao, data_logout)
        VALUES (?, ?, ?, datetime('now', 'localtime'))
        """,
        (pedido_id, nome_colaborador, acao),
    )
    conn.commit()
    conn.close()


def confirmar_saida(janela, nome_colaborador):
    """Implementa o fluxo do diagrama: pausa ou confirma a saída."""
    pedidos = consultar_pedidos_em_andamento(nome_colaborador)
    pedido_id = pedidos[0][0] if pedidos else None

    if pedido_id is not None:
        continuar = messagebox.askyesno(
            "Pausa do pedido",
            f"Há a ordem {pedido_id} em andamento.\nDeseja pausar o pedido?",
            parent=janela,
        )
        if continuar:
            pausar_pedido(pedido_id, nome_colaborador)
            registrar_logout(nome_colaborador, pedido_id, "Pausou e saiu")
            messagebox.showinfo(
                "Sessão encerrada",
                f"Ordem {pedido_id} mantida como PAUSADA.\n"
                "O processo poderá ser consultado e retomado no próximo login.",
                parent=janela,
            )
        else:
            registrar_logout(nome_colaborador, pedido_id, "Cancelou saída")
            return False
    else:
        continuar = messagebox.askyesno(
            "Confirmar saída",
            "Confirmar saída e encerrar a sessão?",
            parent=janela,
        )
        if not continuar:
            return False
        registrar_logout(nome_colaborador, acao="Saiu")

    janela.destroy()

    import login
    login.abrir_login()
    return True


def iniciar_logout_por_voz(janela, nome_colaborador):
    def rotina():
        falar("Diga sair ou logout.")
        resposta = (ouvir() or "").lower()
        palavras = set(resposta.replace("/", " ").replace("-", " ").split())
        if palavras & {"sair", "logout"}:
            janela.after(0, confirmar_saida, janela, nome_colaborador)

    threading.Thread(target=rotina, daemon=True).start()
