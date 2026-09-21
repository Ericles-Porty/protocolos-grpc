# gRPC

Sistema de eventos acadêmicos exposto como serviço gRPC, em Python e SQLite.

Este repositório é um de uma série de cinco, o mesmo domínio implementado em cinco protocolos
diferentes para deixar a diferença visível em código, não só em slide:

- [protocolos-grpc](https://github.com/Ericles-Porty/protocolos-grpc) (este repositório)
- [protocolos-rest](https://github.com/Ericles-Porty/protocolos-rest)
- [protocolos-soap](https://github.com/Ericles-Porty/protocolos-soap)
- [protocolos-graphql](https://github.com/Ericles-Porty/protocolos-graphql)
- [protocolos-websocket](https://github.com/Ericles-Porty/protocolos-websocket)

## Domínio

`Aluno`, `Evento`, `Inscricao` e `Pagamento`, cobrindo os três tipos de relacionamento:

- **1:1** — uma inscrição tem no máximo um pagamento.
- **1:N** — um evento tem várias inscrições (e um aluno também).
- **N:M** — um aluno se inscreve em vários eventos, um evento recebe vários alunos, através da
  inscrição.

## Pré-requisitos

- Python 3.10 ou superior

## Como executar

```bash
git clone https://github.com/Ericles-Porty/protocolos-grpc.git
cd protocolos-grpc
pip install -r requirements.txt
cd src

# gera eventos_pb2.py e eventos_pb2_grpc.py a partir do contrato (não vêm versionados)
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. eventos.proto

python servidor.py
```

O banco (`dados.db`) é recriado e semeado do zero a cada vez que o servidor sobe.

## Exemplos de utilização

Em outro terminal, com o servidor no ar:

```bash
cd protocolos-grpc/src
python cliente.py
```

`cliente.py` chama a inscrição semeada (com pagamento aninhado), lista o N:M nos dois sentidos,
cria uma inscrição e paga ela na mesma sessão, e mostra o erro `NOT_FOUND` de um id inexistente.

## Estrutura do projeto

```text
src/
├── eventos.proto   o contrato: service, rpc e message pra cada operação
├── servidor.py     implementa o Servicer gerado a partir do .proto
├── cliente.py      cliente de exemplo
└── banco.py        conexão sqlite3, esquema e seed (igual nos quatro repositórios)
```

## O que observar

- **O cliente chama um método, não uma URL.** `stub.BuscarInscricao(...)` parece uma chamada de
  função local; o HTTP/2 e a serialização binária ficam escondidos atrás do stub gerado.
- **`pagamento` tem presença própria.** Em proto3, um campo do tipo mensagem (`Pagamento
  pagamento = 5`) sabe dizer se veio preenchido ou não (`HasField`) sem precisar de um segundo
  campo booleano pra isso — diferente de um campo escalar comum.
- **Erro tem código próprio.** `NOT_FOUND`, `ALREADY_EXISTS`... não são os status do HTTP, são o
  vocabulário do próprio gRPC, embora o transporte por baixo seja HTTP/2.
