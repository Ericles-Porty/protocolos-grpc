"""Cliente de exemplo. Com o servidor rodando, chame:  python cliente.py"""

from __future__ import annotations

import grpc

import eventos_pb2
import eventos_pb2_grpc


def principal() -> None:
    with grpc.insecure_channel("localhost:50051") as canal:
        stub = eventos_pb2_grpc.EventosAcademicosStub(canal)

        print("--- BuscarInscricao(1): a inscrição semeada, com pagamento aninhado ---")
        print(stub.BuscarInscricao(eventos_pb2.BuscarInscricaoRequest(id=1)))

        print("--- EventosDoAluno(1) / AlunosDoEvento(1): o N:M nos dois sentidos ---")
        print(stub.EventosDoAluno(eventos_pb2.EventosDoAlunoRequest(aluno_id=1)))
        print(stub.AlunosDoEvento(eventos_pb2.AlunosDoEventoRequest(evento_id=1)))

        print("--- Inscrever + RegistrarPagamento: pagamento aprovado confirma sozinho ---")
        inscricao = stub.Inscrever(eventos_pb2.InscreverRequest(aluno_id=2, evento_id=2))
        print(inscricao)
        pagamento = stub.RegistrarPagamento(
            eventos_pb2.RegistrarPagamentoRequest(inscricao_id=inscricao.id, valor=30)
        )
        print(pagamento)

        print("--- BuscarInscricao(999): erro vira grpc.StatusCode.NOT_FOUND, não uma exceção genérica ---")
        try:
            stub.BuscarInscricao(eventos_pb2.BuscarInscricaoRequest(id=999))
        except grpc.RpcError as erro:
            print(erro.code(), "-", erro.details())


if __name__ == "__main__":
    principal()
