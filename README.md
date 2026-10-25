# PBJ Scanner — automático via GitHub Actions

Roda o scanner técnico da 1Listão **sozinho, toda sexta-feira**, nos servidores
gratuitos do GitHub. Gera `scan_results.csv` e `relatorio.md` e salva de volta
no próprio repositório — de onde o Claude busca automaticamente para interpretar
e registrar no doc PBJ. **Zero clique por semana.**

## Como ligar (uma vez, ~3 minutos)

1. Crie uma conta gratuita em **github.com** (se ainda não tiver).
2. Clique em **New repository** → dê um nome (ex.: `pbj-scanner`) → marque
   **Public** → **Create repository**.
3. Na página do repo, clique em **“uploading an existing file”** (ou
   *Add file → Upload files*) e **arraste todos os arquivos deste pacote**,
   mantendo a pasta `.github/workflows/` (o GitHub preserva as pastas ao
   arrastar). Confirme com **Commit changes**.
4. Vá na aba **Actions** → se pedir, clique em **“I understand… enable”**.
5. Pronto. Ele roda sozinho toda sexta às 18:10 (Brasília). Para **testar
   agora**, entre em **Actions → Scanner semanal 1Listão → Run workflow**.

Depois de criado, **me mande o endereço do repositório** (ex.:
`github.com/seu-usuario/pbj-scanner`). Eu ajusto o lembrete de sexta para
**buscar o CSV sozinho** — aí o ciclo fica 100% automático: o GitHub roda, salva
o resultado, e eu leio e registro no PBJ sem você tocar em nada.

## O que cada arquivo faz

- `scan.py` — o scanner (1Listão embutida, indicadores e alarmes).
- `.github/workflows/weekly-scan.yml` — o agendamento (sexta 18:10 BRT) e os passos.
- `requirements.txt` — dependências (yfinance, pandas, numpy).

## Onde ver o resultado

- No repositório: os arquivos `relatorio.md` (leitura) e `scan_results.csv`
  (todas as métricas) são atualizados a cada execução; o histórico fica em
  `history/`.
- Na aba **Actions**: cada execução guarda os arquivos como *artifact* para download.

## Ajustes

- **Mudar o horário:** edite a linha `cron:` no `weekly-scan.yml` (está em UTC;
  18:10 BRT = 21:10 UTC).
- **Mudar a lista de ativos:** edite a variável `WATCHLIST` dentro do `scan.py`.
- **Rodar mais vezes:** adicione outra linha de `cron`.

> Observação: o GitHub Actions é gratuito para repositórios públicos. Em repo
> privado, há uma cota mensal de minutos (mais que suficiente para 1 run/semana).
