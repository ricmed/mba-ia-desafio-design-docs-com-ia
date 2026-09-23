#!/usr/bin/env python3
"""
Verificador de rastreabilidade do pacote de design docs.

Roda a partir da raiz do repositório:

    python docs/verificar-rastreabilidade.py

Faz quatro checagens mecânicas sobre docs/*.md e docs/adrs/*.md:

1. Todo timestamp citado no formato [hh:mm] Nome existe em TRANSCRICAO.md,
   com o falante correto.
2. Todo caminho de arquivo do código citado existe no repositório — exceto
   os dois artefatos que a feature cria, que precisam estar marcados.
3. Todo link relativo entre documentos aponta para um arquivo existente.
4. O TRACKER.md atinge os limiares de cobertura exigidos pelo desafio.

Sai com código 1 se qualquer checagem falhar.
"""

import glob
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSCRICAO = os.path.join(RAIZ, "TRANSCRICAO.md")

# Os dois únicos caminhos que a documentação cita e que ainda não existem:
# são exatamente os artefatos que esta feature cria.
A_CRIAR = {"src/worker.ts", "src/modules/webhooks", "src/modules/webhooks/"}

falhas = []


def docs():
    return sorted(glob.glob(os.path.join(RAIZ, "docs", "*.md"))) + sorted(
        glob.glob(os.path.join(RAIZ, "docs", "adrs", "*.md"))
    )


def rel(caminho):
    return os.path.relpath(caminho, RAIZ).replace("\\", "/")


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        return f.read()


def checar_timestamps():
    falas = set(re.findall(r"^\[(\d{2}:\d{2})\] (\w+):", ler(TRANSCRICAO), re.M))
    invalidos = []
    total = 0
    for doc in docs():
        for ts, nome in re.findall(r"\[(\d{2}:\d{2})\]\s+(\w+)", ler(doc)):
            total += 1
            if (ts, nome) not in falas:
                invalidos.append(f"{rel(doc)}: [{ts}] {nome}")
    print(f"1. Timestamps verificados: {total}")
    if invalidos:
        falhas.append("timestamps sem correspondência na transcrição")
        for i in sorted(set(invalidos)):
            print(f"   INVÁLIDO  {i}")
    else:
        print("   todos correspondem a uma fala real de TRANSCRICAO.md")


def checar_caminhos():
    inexistentes, encontrados = [], set()
    for doc in docs():
        for p in re.findall(r"(?:src|prisma|tests)/[A-Za-z0-9_./\-]+", ler(doc)):
            p = p.rstrip(".,;:)")
            if p in A_CRIAR:
                continue
            encontrados.add(p)
            alvo = os.path.join(RAIZ, p)
            if not (os.path.isfile(alvo) or os.path.isdir(alvo)):
                inexistentes.append(f"{rel(doc)}: {p}")
    print(f"2. Caminhos de código citados: {len(encontrados)} distintos")
    if inexistentes:
        falhas.append("caminhos de código inexistentes")
        for i in sorted(set(inexistentes)):
            print(f"   INEXISTENTE  {i}")
    else:
        print("   todos existem no repositório")


def checar_links():
    quebrados, total = [], 0
    for doc in docs():
        base = os.path.dirname(doc)
        for alvo in re.findall(r"\]\(([^)#:]+\.md)\)", ler(doc)):
            total += 1
            if not os.path.isfile(os.path.normpath(os.path.join(base, alvo))):
                quebrados.append(f"{rel(doc)} -> {alvo}")
    print(f"3. Links entre documentos: {total}")
    if quebrados:
        falhas.append("links quebrados entre documentos")
        for q in sorted(set(quebrados)):
            print(f"   QUEBRADO  {q}")
    else:
        print("   todos resolvem")


def checar_tracker():
    linhas = [
        [c.strip() for c in l.strip().strip("|").split("|")]
        for l in ler(os.path.join(RAIZ, "docs", "TRACKER.md")).splitlines()
        if l.startswith("|") and l.count("|") >= 7
    ]
    itens = [c for c in linhas if len(c) >= 6 and c[4] in ("TRANSCRICAO", "CODIGO")]
    transcricao = [c for c in itens if c[4] == "TRANSCRICAO"]
    codigo = [c for c in itens if c[4] == "CODIGO"]
    pct = len(transcricao) / len(itens) * 100 if itens else 0
    print(f"4. Tracker: {len(itens)} itens | TRANSCRICAO {len(transcricao)} ({pct:.1f}%) | CODIGO {len(codigo)}")

    if pct < 70:
        falhas.append(f"cobertura TRANSCRICAO em {pct:.1f}%, abaixo dos 70% exigidos")
    else:
        print("   cobertura TRANSCRICAO >= 70%  OK")

    if len(codigo) < 5:
        falhas.append(f"apenas {len(codigo)} linhas com Fonte=CODIGO, mínimo 5")
    else:
        print("   linhas com Fonte=CODIGO >= 5  OK")

    ids = [c[0] for c in itens]
    duplicados = {i for i in ids if ids.count(i) > 1}
    if duplicados:
        falhas.append(f"IDs duplicados no tracker: {sorted(duplicados)}")
    else:
        print("   IDs únicos  OK")


def main():
    print("Verificação de rastreabilidade — pacote de design docs\n")
    checar_timestamps()
    print()
    checar_caminhos()
    print()
    checar_links()
    print()
    checar_tracker()
    print()
    if falhas:
        print("RESULTADO: FALHOU")
        for f in falhas:
            print(f" - {f}")
        return 1
    print("RESULTADO: todas as verificações passaram")
    return 0


if __name__ == "__main__":
    sys.exit(main())
