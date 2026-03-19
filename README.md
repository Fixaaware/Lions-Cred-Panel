# 🦁 Lions Cred — Sistema de Clientes

Sistema web moderno de cadastro e consulta de clientes.

---

## Requisitos

| Ferramenta | Versão Mínima |
|---|---|
| Python | 3.10+ |

> Não é necessário instalar nenhum banco de dados. O SQLite já vem embutido no Python.

---

## Iniciando o Sistema

**Opção 1 — Script automático:**
```
python start.py
```

**Opção 2 — Manual:**
```
pip install -r requirements.txt
python app.py
```

O banco de dados (`database/lions_cred.db`) é criado automaticamente na primeira execução, já com 10 clientes de demonstração.

Acesse no navegador: **http://localhost:5000**

---

## Funcionalidades

- **Dashboard** — Estatísticas em tempo real + busca rápida + últimos cadastros
- **Cadastrar Cliente** — Formulário completo com validação de CPF
- **Consultar** — Busca por nome ou CPF com resultados detalhados
- **Todos os Clientes** — Lista paginada com filtros e edição inline
- **Edição / Exclusão** — Modal de edição e confirmação de exclusão
- Design responsivo (mobile + desktop)
- Máscaras automáticas de CPF e telefone
- Notificações toast em todas as ações

---

## Estrutura

```
Lions Cred/
├── app.py              ← Backend Flask (rotas e API)
├── config.py           ← Configurações (DB, Flask)
├── start.py            ← Script de inicialização
├── requirements.txt    ← Dependências Python
├── database/
│   └── schema.sql      ← Estrutura e dados demo
└── templates/
    └── index.html      ← Frontend (SPA completa)
```
