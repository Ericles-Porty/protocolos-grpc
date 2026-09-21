"""Sistema de eventos acadêmicos exposto como serviço gRPC.

Único ponto de entrada. Antes de rodar, gere o código a partir do .proto (veja o README);
depois sobe com:  python servidor.py
"""

from __future__ import annotations

from concurrent import futures

import banco
import eventos_pb2
import eventos_pb2_grpc
import grpc


def para_aluno(linha: dict) -> eventos_pb2.Aluno:
    return eventos_pb2.Aluno(id=linha["id"], nome=linha["nome"], email=linha["email"])


def para_evento(linha: dict) -> eventos_pb2.Evento:
    return eventos_pb2.Evento(id=linha["id"], titulo=linha["titulo"], data=linha["data"])


def para_pagamento(linha: dict) -> eventos_pb2.Pagamento:
    return eventos_pb2.Pagamento(
        id=linha["id"], inscricao_id=linha["inscricao_id"], valor=linha["valor"], status=linha["status"]
    )


def para_inscricao(linha: dict) -> eventos_pb2.Inscricao:
    inscricao = eventos_pb2.Inscricao(
        id=linha["id"], aluno_id=linha["aluno_id"], evento_id=linha["evento_id"], status=linha["status"]
    )
    if linha.get("pagamento") is not None:
        inscricao.pagamento.CopyFrom(para_pagamento(linha["pagamento"]))
    return inscricao


class ServicoEventos(eventos_pb2_grpc.EventosAcademicosServicer):
    def CriarAluno(self, request, context):
        return para_aluno(banco.criar_aluno(request.nome, request.email))

    def CriarEvento(self, request, context):
        return para_evento(banco.criar_evento(request.titulo, request.data))

    def Inscrever(self, request, context):
        try:
            return para_inscricao(banco.inscrever(request.aluno_id, request.evento_id))
        except ValueError as erro:
            codigo = grpc.StatusCode.ALREADY_EXISTS if "já" in str(erro) else grpc.StatusCode.NOT_FOUND
            context.abort(codigo, str(erro))

    def RegistrarPagamento(self, request, context):
        try:
            return para_pagamento(banco.registrar_pagamento(request.inscricao_id, request.valor))
        except ValueError as erro:
            codigo = grpc.StatusCode.ALREADY_EXISTS if "já" in str(erro) else grpc.StatusCode.NOT_FOUND
            context.abort(codigo, str(erro))

    def BuscarInscricao(self, request, context):
        inscricao = banco.buscar_inscricao(request.id)
        if inscricao is None:
            context.abort(grpc.StatusCode.NOT_FOUND, "inscrição não encontrada")
        return para_inscricao(inscricao)

    def EventosDoAluno(self, request, context):
        eventos = [para_evento(linha) for linha in banco.eventos_do_aluno(request.aluno_id)]
        return eventos_pb2.ListaEventos(eventos=eventos)

    def AlunosDoEvento(self, request, context):
        alunos = [para_aluno(linha) for linha in banco.alunos_do_evento(request.evento_id)]
        return eventos_pb2.ListaAlunos(alunos=alunos)


def servir() -> None:
    banco.inicializar()
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    eventos_pb2_grpc.add_EventosAcademicosServicer_to_server(ServicoEventos(), servidor)
    servidor.add_insecure_port("[::]:50051")
    servidor.start()
    print("gRPC ouvindo em localhost:50051")
    servidor.wait_for_termination()


if __name__ == "__main__":
    servir()
