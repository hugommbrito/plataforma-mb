# Histórias de Usuário — Sistema de Gestão Patrimonial
**Holding Familiar · Django + Neon + R2 + Railway**

---

## Atores

| Ator | Descrição |
|---|---|
| **Usuário** | Qualquer membro da família com acesso ao sistema, independente de localização |
| **Sistema** | Tarefas automatizadas via Railway cron jobs / management commands |

---

## 🏠 Épico 1 — Patrimônio & Imóveis

| ID | Como... | Quero... | Para... | Prioridade |
|---|---|---|---|---|
| PAT-01 | Usuário | Cadastrar um imóvel com matrícula, área, IPTU, valor venal e situação | Ter o patrimônio da holding registrado centralmente | Alta |
| PAT-02 | Usuário | Definir múltiplos proprietários com % de participação por imóvel | Refletir a estrutura societária real | Alta |
| PAT-03 | Usuário | Ver valor de mercado, R$/m² e valor líquido estimado calculados automaticamente | Avaliar o portfólio sem planilhas | Média |
| PAT-04 | Usuário | Filtrar imóveis por situação (alugado, vago, em reforma) | Tomar decisões de prioridade rapidamente | Média |
| PAT-05 | Usuário | Registrar histórico de variações do valor de mercado | Acompanhar a valorização ao longo do tempo | Baixa |

---

## 📄 Épico 2 — Contratos

| ID | Como... | Quero... | Para... | Prioridade |
|---|---|---|---|---|
| CON-01 | Usuário | Registrar contratos com imóvel, inquilino, vigência, valor e índice de reajuste | Ter controle centralizado dos acordos | Alta |
| CON-02 | Usuário | Calcular o reajuste anual pelo IGPM/IPCA com um clique (custom action) | Aplicar o novo valor sem cálculo manual | Baixa |
| CON-03 | Usuário | Ver status de cada contrato (vigente, vencendo em 60 dias, encerrado) | Agir antes de expirar | Alta |
| CON-04 | Usuário | Registrar tipo de garantia (caução, fiança, seguro) e seu vencimento | Saber quando renovar a cobertura | Média |
| CON-05 | Usuário | Ver histórico de auditoria de alterações no contrato | Rastrear quem mudou o quê e quando | Média |
| CON-06 | Usuário | Gerar recibo mensal em PDF (custom action) | Enviar ao inquilino sem depender de terceiros | Baixa |

---

## 👥 Épico 3 — Pessoas & Papéis

| ID | Como... | Quero... | Para... | Prioridade |
|---|---|---|---|---|
| PES-01 | Usuário | Cadastrar uma pessoa e associá-la a múltiplos papéis (proprietário, inquilino, fiador) | Evitar duplicidade de dados | Alta |
| PES-02 | Usuário | Que CPF/CNPJ seja validado e único no sistema | Impedir duplicatas silenciosas | Alta |
| PES-03 | Usuário | Arquivar (soft delete) pessoas inativas | Manter histórico sem poluir os dropdowns | Média |
| PES-04 | Usuário | Registrar documentos (RG, comprovante de renda) no perfil do fiador | Ter tudo acessível no mesmo lugar | Baixa |

---

## 💰 Épico 4 — Financeiro (Backlog - Não fará parte do MVP)

| ID | Como... | Quero... | Para... | Prioridade |
|---|---|---|---|---|
| FIN-01 | Usuário | Registrar pagamentos de aluguel com competência, valor, status e comprovante | Conciliar mensalmente sem depender de terceiros | Alta |
| FIN-02 | Usuário | Ver painel consolidado de receitas, inadimplência e despesas por imóvel/mês | Ter visão financeira do portfólio | Alta |
| FIN-03 | Usuário | Exportar relatório de rendimentos formatado para IRPF (custom action) | Declarar o imposto sem montar planilha | Alta |
| FIN-04 | Usuário | Registrar parcelas do IPTU e marcar cada uma como paga | Não perder o controle das guias ao longo do ano | Média |
| FIN-05 | Usuário | Registrar despesas de manutenção vinculadas ao imóvel e dedutíveis no IR | Calcular o custo líquido do portfólio | Média |
| FIN-06 | Usuário | Ver o carnê-leão mensal calculado automaticamente pelos aluguéis recebidos | Saber o DARF a pagar sem cálculo manual | Baixa |

---

## 📁 Épico 5 — Documentos

| ID | Como... | Quero... | Para... | Prioridade |
|---|---|---|---|---|
| DOC-01 | Usuário | Anexar documentos (escritura, contrato, laudo) a qualquer entidade do sistema | Centralizar o arquivo morto digital | Alta |
| DOC-02 | Usuário | Que arquivos sejam armazenados no R2 com acesso por URL assinada | Não expor documentos publicamente | Alta |
| DOC-03 | Usuário | Categorizar documentos por tipo (matrícula, contrato, comprovante, laudo) | Filtrar e encontrar rapidamente | Média |
| DOC-04 | Usuário | Fazer upload de comprovantes de pagamento direto no sistema | Qualquer membro da família veja sem precisar de e-mail | Baixa |
| DOC-05 | Usuário | Registrar data de vencimento de documentos (seguro, procuração) | Receber alertas antes de expirarem | Alta |

---

## 🔧 Épico 6 — Manutenção (Backlog - Não fará parte do MVP)

| ID | Como... | Quero... | Para... | Prioridade |
|---|---|---|---|---|
| MAN-01 | Usuário | Registrar ordens de serviço com data, descrição, custo e fornecedor | Acompanhar o que foi feito em cada imóvel | Média |
| MAN-02 | Usuário | Ver histórico de manutenções por imóvel com custo acumulado | Avaliar custo de manutenção vs. valor de mercado | Média |
| MAN-03 | Usuário | Anexar fotos e notas fiscais a cada ordem de serviço | Comprovar o serviço sem enviar e-mail | Média |
| MAN-04 | Usuário | Categorizar manutenções como preventiva, corretiva ou emergencial | Priorizar e planejar o orçamento anual | Baixa |

---

## 🔔 Épico 7 — Lembretes & Tarefas

| ID | Como... | Quero... | Para... | Prioridade |
|---|---|---|---|---|
| LEM-01 | Sistema | Enviar alerta 60 dias antes do vencimento de contrato | Iniciar negociação de renovação com antecedência | Alta |
| LEM-02 | Sistema | Enviar alerta 30 dias antes da data de reajuste anual | Não deixar passar a janela de aplicação | Alta |
| LEM-03 | Sistema | Enviar alerta das parcelas de IPTU com 10 dias de antecedência | Evitar multas por atraso independente de onde o usuário esteja | Alta |
| LEM-04 | Usuário | Criar tarefas manuais com prazo e relacionamento a imóvel/contrato | Gerenciar pendências pontuais fora dos fluxos automáticos | Média |
| LEM-05 | Sistema | Enviar alerta quando o seguro-fiança vencer em 45 dias | Solicitar renovação antes de o imóvel ficar desprotegido | Baixa |
| LEM-06 | Sistema | Enviar alerta 90 dias antes do ajuste anual no IRPF | Preparar a documentação com antecedência para envio aos clientes | Média |

---

## 📊 Épico 8 — Relatórios & IR

| ID | Como... | Quero... | Para... | Prioridade |
|---|---|---|---|---|
| REL-01 | Usuário | Gerar relatório patrimonial consolidado com todos os imóveis, valores e participações | Ter visão total da holding em um clique | Alta |
| REL-02 | Usuário | Exportar relatório de rendimentos anuais por CPF de proprietário | Preencher o IRPF sem risco de erro | Alta |
| REL-03 | Usuário | Ver DRE simplificado por imóvel (receita, despesas, resultado) | Saber quais imóveis são mais rentáveis | Média |
| REL-04 | Usuário | Ver relatório de inadimplência histórica por inquilino | Embasar decisões em futuros contratos | Baixa |

---

## Resumo por Prioridade

| Prioridade | MVP | Backlog | Total |
|---|---|---|---|
| 🔴 Alta | 14 | 3 | 17 |
| 🟡 Média | 9 | 5 | 14 |
| 🔵 Baixa | 7 | 2 | 9 |
| **Total** | **30** | **10** | **40** |

> Backlog = Épicos FIN e MAN, não fazem parte do MVP.

---

## Escopo do MVP

| Épico | Status |
|---|---|
| 🏠 Patrimônio & Imóveis | ✅ Implementado |
| 📄 Contratos | ✅ Implementado |
| 👥 Pessoas & Papéis | ✅ Implementado |
| 📁 Documentos | ✅ Implementado |
| 🔔 Lembretes & Tarefas | 🔄 Próximo (Fase 5) |
| 📊 Relatórios & IR | 🔄 Backlog (Fase 6) |
| 💰 Financeiro | 🔲 Backlog pós-MVP |
| 🔧 Manutenção | 🔲 Backlog pós-MVP |

---

## Mapeamento para Apps Django

| App | Épicos cobertos | Status |
|---|---|---|
| `imoveis` | PAT | ✅ Implementado |
| `pessoas` | PES | ✅ Implementado |
| `contratos` | CON | ✅ Implementado |
| `documentos` | DOC | ✅ Implementado |
| `core` | LEM (Fase 5) | 🔄 Próximo |
| `financeiro` | FIN | 🔲 Backlog pós-MVP |
| `manutencao` | MAN | 🔲 Backlog pós-MVP |
| Management commands / cron | LEM | 🔄 Próximo (Fase 5) |
| Custom admin actions | CON-02, CON-06, REL-01, REL-02 | 🔲 Backlog |
| Custom admin actions (backlog) | FIN-03 | 🔲 Backlog pós-MVP |
