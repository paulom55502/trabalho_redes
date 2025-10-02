 Dashboard de Análise de Tráfego (CSV → Google Planilhas)

**Entrega:** versão usando CSV como interface cliente e Google Planilhas para visualização.

---

## Resumo do projeto
Este projeto captura ou simula tráfego de rede direcionado a um servidor-alvo, agrega os bytes em janelas fixas de **5 segundos** por `(timestamp_window_start, cliente_ip, protocolo)` e gera um arquivo **CSV** (`output.csv`) que é importado no **Google Planilhas** para montar tabelas dinâmicas e gráficos (drill-down por IP → protocolo).

**Modo de trabalho recomendado para entrega:** `--mode simulate` (não precisa de permissões root).  

---

## Estrutura do repositório
/
├─ capture_to_csv.py # script principal (simulate / live)

├─ sample_output.csv # (opcional) CSV de exemplo gerado por simulate

├─ README.md # este arquivo

├─ RELATORIO_TECNICO.md # relatório técnico (1-2 páginas)

├─ excel_instrucoes.md # (opcional) instruções detalhadas para planilha

O script usa --server-ip apenas para decidir quais pacotes (ou eventos simulados) pertencem ao servidor que você está "monitorando".
No modo simulate, use um IP fictício da sua rede local, por exemplo 192.168.0.5 ou 10.0.0.5.

Executando o script (modo simulate)

Entre na pasta do projeto.

Ative o venv (opcional).

Rode o script no modo simulate por N segundos:

Para gerar dados de teste e criar o arquivo `output.csv`, rode o seguinte comando no terminal (estando na pasta do projeto):

Comando:  
`python capture_to_csv.py --server-ip 192.168.0.5 --mode simulate --duration 120 --output output.csv.`

python capture_to_csv.py \
  --server-ip 192.168.0.5 \
  --mode simulate \
  --duration 120 \
  --output output.csv \
  --window 5


--duration 120 : duração da simulação em segundos (aqui 2 minutos).

--window 5 : tamanho da janela em segundos (padrão 5).

--output output.csv : caminho do CSV gerado.

O script irá criar (ou acrescentar) output.csv. Cada linha representa o agregado de uma janela de window segundos para um cliente_ip e protocolo.

Formato do CSV

O arquivo possui o cabeçalho:

timestamp_window_start,cliente_ip,protocolo,bytes_entrada,bytes_saida

timestamp_window_start é o início da janela (datetime, sem milissegundos).
bytes_entrada = soma de bytes do cliente → servidor (entrada no servidor).
bytes_saida = soma de bytes do servidor → cliente (saída do servidor).

Importando para o Google Planilhas
Abra o Google Drive e faça upload de output.csv (ou no Planilhas: Arquivo → Importar → Upload).
Ao importar escolha "Substituir planilha" ou "Inserir nova aba".
Crie uma Tabela Dinâmica:
Inserir → Tabela dinâmica.
Linhas: cliente_ip (coloque protocolo abaixo se quiser drill-down interno).
Valores: SOMA de bytes_entrada, SOMA de bytes_saida (ou crie coluna auxiliar bytes_total).
Filtros: timestamp_window_start para controlar janela temporal.
Criar gráficos (Inserir → Gráfico):
Gráfico de colunas empilhadas por cliente_ip com protocolo como série para drill-down visual.
Gráfico de linhas/área para evolução temporal (usar timestamp_window_start como eixo X).
Adicionar Segmentação de dados:
Clique na Tabela Dinâmica, em seguida Dados → Segmentação de dados.
Escolha cliente_ip e/ou protocolo. Os botões criados permitem filtrar interativamente o dashboard.
(obs: eu usei o google planilhas pois nao tenho acesso ao excel pois não comprei o pacote office.)

Para fazer os testes de segurança:
Use esse comando para instalar os verificadores 
Comando:
``python -m pip install flake8 bandit``
Primeiro use esse comando 
``python -m flake8 capture_to_csv.py``
que gera uma lista de avisos e sugestões de melhoria para o seu código.
O segundo comando e esse
``python -m bandit capture_to_csv.py`` 
que analisa o codigo-fonte do Python sem executá-lo e procura por vulnerabilidades de segurança.

