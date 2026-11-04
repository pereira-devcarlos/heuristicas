"""Exporta o Markdown revisado para HTML paginado e PDF; dependências só de edição."""

import argparse
import html
import json
import re
import unicodedata
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent


def identificador(titulo: str) -> str:
    normalizado = unicodedata.normalize("NFKD", titulo).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", normalizado.lower()).strip("-")


def gerar_html() -> str:
    try:
        import markdown
    except ImportError as erro:
        raise RuntimeError("A exportação requer Markdown; consulte relatorio/fontes/README.md.") from erro
    dados = json.loads((RAIZ / "relatorio" / "fontes" / "identificacao.json").read_text(encoding="utf-8"))
    dados = {chave: html.escape(valor) for chave, valor in dados.items()}
    texto = (RAIZ / "relatorio" / "relatorio.md").read_text(encoding="utf-8")
    blocos = re.split(r"^## (.+)$", texto, flags=re.MULTILINE)
    secoes = []
    sumario = []
    numero_tabela = 0
    for titulo, conteudo in zip(blocos[1::2], blocos[2::2]):
        id_secao = identificador(titulo)
        titulo_html = html.escape(titulo)
        corpo = markdown.markdown(conteudo.strip(), extensions=["tables"])

        def tratar_link(match):
            destino, rotulo = match.groups()
            if destino.startswith(("https://", "http://")):
                return match.group(0)
            return f'{rotulo} (arquivo <code>{html.escape(destino)}</code>)'

        corpo = re.sub(r'<a href="([^"]+)"[^>]*>(.*?)</a>', tratar_link, corpo)
        corpo = re.sub(r"<p>((?:Tabela|Quadro) \d+ – .*?)</p>",
                       r'<p class="legenda">\1</p>', corpo)
        corpo = re.sub(r"<p>(Fonte:.*?)</p>", r'<p class="fonte">\1</p>', corpo)
        corpo = re.sub(r"<td>(\d+,\d+) ± (\d+,\d+)</td>",
                       r'<td><span class="valor">\1</span><span class="desvio">± \2</span></td>', corpo)

        def tratar_tabela(match):
            nonlocal numero_tabela
            numero_tabela += 1
            classe = "tabela-numerica" if numero_tabela == 1 else "quadro"
            return f'<table class="{classe}">{match.group(1)}</table>'

        corpo = re.sub(r"<table>(.*?)</table>", tratar_tabela, corpo, flags=re.DOTALL)
        classe = "principal referencias" if titulo == "Referências" else "principal"
        secoes.append(f'<section class="{classe}" id="{id_secao}"><h2>{titulo_html}</h2>{corpo}</section>')
        sumario.append(f'<li><a href="#{id_secao}">{titulo_html}</a></li>')

    resumo = " ".join((RAIZ / "relatorio" / "fontes" / "resumo.md").read_text(encoding="utf-8").split())
    abstract = " ".join((RAIZ / "relatorio" / "fontes" / "abstract.md").read_text(encoding="utf-8").split())
    css = (RAIZ / "relatorio" / "fontes" / "relatorio.css").read_text(encoding="utf-8")
    autor = f'<p>{dados["autor"]}</p><p>Matrícula: {dados["matricula"]}</p>'
    local = f'<div class="rodape-local"><p>{dados["cidade"]}</p><p>{dados["ano"]}</p></div>'
    return f'''<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="author" content="{dados['autor']}"><title>{dados['titulo']}</title>
<style>{css}</style></head><body>
<section class="capa">
<p class="instituicao">{dados['instituicao']}</p><p>{dados['curso']}</p>
<div class="autor">{autor}</div><div class="titulo">{dados['titulo']}</div>{local}
</section>
<section class="pre-textual folha-rosto">
<div class="autor">{autor}</div><div class="titulo">{dados['titulo']}</div>
<div class="natureza"><p>Relatório da segunda etapa do trabalho final apresentado à
{dados['instituicao']}, no curso de {dados['curso']}, como parte da avaliação da
disciplina {dados['disciplina']}.</p><p>Professor: {dados['professor']}.</p></div>{local}
</section>
<section class="pre-textual resumo"><h2>Resumo</h2><p>{html.escape(resumo)}</p>
<p class="palavras-chave"><strong>Palavras-chave:</strong> alocação de microsserviços;
otimização multiobjetivo; algoritmo genético; NSGA-II; nuvem heterogênea.</p></section>
<section class="pre-textual resumo"><h2>Abstract</h2><p>{html.escape(abstract)}</p>
<p class="palavras-chave"><strong>Keywords:</strong> microservice allocation;
multiobjective optimization; genetic algorithm; NSGA-II; heterogeneous cloud.</p></section>
<nav class="pre-textual sumario"><h2>Sumário</h2><ul>{''.join(sumario)}</ul></nav>
{''.join(secoes)}</body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=RAIZ / "relatorio")
    parser.add_argument("--somente-html", action="store_true")
    args = parser.parse_args()
    try:
        documento = gerar_html()
        args.saida.mkdir(parents=True, exist_ok=True)
        caminho_html = args.saida / "relatorio.html"
        caminho_html.write_text(documento, encoding="utf-8")
        print(f"HTML: {caminho_html}")
        if not args.somente_html:
            try:
                from weasyprint import HTML
            except ImportError as erro:
                raise RuntimeError("Para exportar PDF, instale WeasyPrint; veja relatorio/fontes/README.md.") from erro
            caminho_pdf = args.saida / "relatorio.pdf"
            HTML(string=documento, base_url=str(RAIZ)).write_pdf(caminho_pdf)
            print(f"PDF: {caminho_pdf}")
    except (OSError, RuntimeError) as erro:
        parser.exit(2, f"Erro: {erro}\n")


if __name__ == "__main__":
    main()
