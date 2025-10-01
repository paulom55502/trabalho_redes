
---

# `RELATORIO_TECNICO.md` 

```markdown
# Relatório Técnico — Dashboard de Análise de Tráfego (CSV + Google Planilhas)

## 1. Objetivo
Construir um sistema que capture e agregue tráfego de rede direcionado a um servidor-alvo e permita visualização interativa em janelas de **5 segundos**, apresentando volume por **IP cliente** e detalhamento por **protocolo**. Para este trabalho optou-se por gerar um CSV que é importado no **Google Planilhas** (interface cliente).

## 2. Arquitetura geral
O sistema é composto por:
- **capture_to_csv.py** (script Python):
  - Modo `simulate`: gera eventos sintéticos representando pacotes entre clientes e servidor.
  - Modo `live`: (opcional) captura pacotes reais via pcap/scapy (requer sudo).
  - Agrega eventos em memória por janelas fixas e persiste agregados parciais/definitivos em `output.csv`.
- **Google Planilhas**:
  - Importa o CSV.
  - Cria Tabelas Dinâmicas e Gráficos (colunas empilhadas, linhas temporais).
  - Usa Segmentação de dados (Slicers) para drill-down por `cliente_ip` e `protocolo`.

Fluxo: captura/simulação → agregação por janela → escrita incremental no CSV → importação no Planilhas → visualização.

## 3. Lógica de agregação (janelas de tempo)
- Janela fixa de tamanho `W = 5s`.
- Para cada evento (packet simulated/real), extrai-se:
  - `ts` (timestamp em segundos), `src_ip`, `dst_ip`, `protocol`, `length`.
- A janela é calculada como `window_start = floor(ts / W) * W` e armazenada como datetime (ex.: `2025-09-30 10:00:05`).
- Chave de agregação: `(window_start, cliente_ip, protocolo)`.
  - `cliente_ip` = endereço IP que não é o `SERVER_IP` (o outro extremo da comunicação).
  - `protocolo` = heurística (HTTP/HTTPS/FTP/TCP_OTHER/UDP_OTHER).
- Valores agregados: `bytes_entrada` (cliente → servidor) e `bytes_saida` (servidor → cliente).
- Implementação: dicionário `dict[WindowKey] -> [bytes_entrada, bytes_saida]` protegido por um `lock` (thread-safe) durante atualizações.
- Escrita no CSV: periodicamente (loop a cada 1s), o agregador *flush* janelas que já expiraram e escreve linhas no CSV em modo append, garantindo que os dados armazenados representem janelas completas.

## 4. Heurística de classificação de protocolo
- Em modo simulate: protocolos escolhidos aleatoriamente (`HTTP`, `HTTPS`, `FTP`, `TCP_OTHER`, `UDP_OTHER`).
- Em modo live: inferência simples a partir de portas TCP/UDP (p.ex. 80/8080 → HTTP; 443 → HTTPS; 21/2121 → FTP). Observação: identificação por porta é limitada (server uses non-standard ports, encrypted payloads).

## 5. Testes e validação
- Para a entrega foi usado **modo simulate** com duração controlada (ex.: 120s) gerando múltiplos clientes e protocolos.
- Validações realizadas:
  - Confirmação de que o CSV contém cabeçalho e linhas para janelas esperadas.
  - Somas por cliente e por protocolo batem com números gerados pela simulação.
  - No Google Planilhas, tabelas dinâmicas e gráficos respondem adequadamente aos filtros.

## 6. Visualização (implementação no Planilhas)
- Tabela Dinâmica: linhas = `cliente_ip` (com `protocolo` em sub-nível), valores = `SOMA(bytes_entrada)` e `SOMA(bytes_saida)`.
- Gráfico principal: colunas empilhadas com `cliente_ip` no eixo X e stacks por `protocolo`. Isto permite identificar rapidamente quais protocolos dominam o tráfego por IP.
- Drill-down: realizado com (a) sub-nível `protocolo` na pivot e (b) **Segmentação de dados** (`cliente_ip` e `protocolo`) para filtros interativos.
- Evolução temporal: pivot com `timestamp_window_start` como eixo temporal e `bytes_total` como valor, gerando gráfico de linha/área.

## 7. Desafios encontrados
- **Captura real (live)**: exige permissões root e interface correta; captura em redes com porta espelhada requer configuração do switch. Para evitar essas barreiras a entrega foi feita com modo `simulate`.
- **Identificação precisa de protocolo**: heurística por porta é limitada (tráfego encapsulado/porta não padrão). Uma solução mais robusta exigiria inspeção do payload (problemático para tráfego TLS/HTTPS) ou logs de aplicação.
- **Sincronia CSV ↔ Planilhas**: o Google Planilhas não se atualiza automaticamente a cada append no CSV — recomenda-se reimportar ou usar Power Query/Apps Script para automação. Para avaliação acadêmica, o `sample_output.csv` está incluso e demonstra o funcionamento.
- **Concorrência/Thread-safety**: o agregador usa um `lock` para evitar race conditions entre threads de captura/simulação e flush.

## 8. Conclusão
A solução entrega o principal objetivo do trabalho: captura/geração de dados, agregação por janelas de 5s, exportação em CSV e visualização interativa com drill-down por IP e protocolo. A escolha do Google Planilhas torna o projeto acessível para alunos sem experiência em frontend, preservando os requisitos de análise e interatividade solicitados pelo professor.

---
