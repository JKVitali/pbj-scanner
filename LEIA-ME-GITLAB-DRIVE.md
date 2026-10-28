# PBJ scanner: alternativas ao GitHub (pacote autônomo)

Este pacote traz os arquivos do scanner (scan.py, hurst_scan.py, hurst_signals.py, requirements.txt) mais o necessário para rodar fora do GitHub. Funciona mesmo que o GitHub esteja fora do ar.

## Opção 1: GitLab como espelho (cerca de 10 minutos)
1. Crie uma conta gratuita em gitlab.com e um projeto novo, público (Create blank project, nome pbj-scanner).
2. Envie todos os arquivos desta pasta para o projeto (Upload file, incluindo o .gitlab-ci.yml).
3. Em Settings > Access tokens, crie um token com role Maintainer e escopo write_repository. Copie o valor.
4. Em Settings > CI/CD > Variables, crie CI_PUSH_TOKEN com esse valor (marque Mask variable).
5. Em Build > Pipeline schedules, crie dois agendamentos, fuso America/Sao_Paulo:
   - Scanner semanal: cron `10 18 * * 5`, variável SCAN_KIND = scan
   - Hurst diário: cron `30 17 * * 1-5`, variável SCAN_KIND = hurst
6. Clique em "Run" em cada agendamento uma vez para testar. Os arquivos scan_results.csv, relatorio.md e hurst_results.csv aparecem no projeto.
7. Me mande o endereço (gitlab.com/seu-usuario/pbj-scanner). As rotinas passam a ler de lá se o GitHub falhar.

Observações: o GitLab exige verificação da conta para usar o CI gratuito (pode pedir cartão de crédito sem cobrança, dependendo da época); se for um problema, use a opção 2 ou o Codeberg.

## Opção 2: seu computador + Google Drive (cerca de 15 minutos)
1. Instale o Python 3.11 ou mais novo e o app Google Drive para computador. Crie uma pasta PBJ-scanner dentro do seu Google Drive.
2. Copie esta pasta para o computador. Se o Drive não ficar em `~/Google Drive`, defina a variável PBJ_SYNC_DIR com o caminho da pasta PBJ-scanner.
3. Teste: `./run_local.sh all` (Linux/Mac) ou `powershell -File run_local.ps1 -Mode all` (Windows). Os CSVs aparecem na pasta do Drive.
4. Agende (horários de Brasília, com o computador ligado):
   - Linux/Mac, `crontab -e`:
     `30 17 * * 1-5 /caminho/run_local.sh hurst`
     `10 18 * * 5 /caminho/run_local.sh scan`
   - Windows (prompt de comando):
     `schtasks /create /tn "PBJ hurst" /tr "powershell -File C:\caminho\run_local.ps1 -Mode hurst" /sc weekly /d MON,TUE,WED,THU,FRI /st 17:30`
     `schtasks /create /tn "PBJ scan" /tr "powershell -File C:\caminho\run_local.ps1 -Mode scan" /sc weekly /d FRI /st 18:10`
5. As rotinas leem os arquivos pela pasta PBJ-scanner no Drive (conector do Drive).

## Limites
- Fusos: os horários acima estão em Brasília. O GitLab usa o fuso do agendamento, então o 17:30 vale para BRT.
- Se o computador estiver desligado no horário, a execução do dia não ocorre; o plano C (cópias de segurança) cobre.
- O Hurst depende do scan_results.csv: o hurst_scan.py lê a lista de ativos dele. O script local copia da pasta do Drive se o arquivo não existir.
