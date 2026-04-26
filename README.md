# 🛒 Sistema de Mercado

Um sistema completo de gerenciamento de mercado desenvolvido em **Python** com SQLite, interface gráfica moderna e funcionalidades avançadas de vendas, estoque e relacionamento com clientes.

---

## 📋 Sobre o Projeto

O **Sistema de Mercado** é uma aplicação desktop que permite gerenciar:
- **Produtos** e seu estoque em tempo real
- **Vendas** com múltiplas formas de pagamento
- **Clientes** com histórico de compras e sistema de desconto progressivo
- **Relatórios** de desempenho, estoque e clientes
- **Movimentação de estoque** com rastreabilidade completa

O projeto segue uma arquitetura **cliente-servidor** com:
- **Backend**: Lógica de negócio e gerenciamento de banco de dados
- **Frontend**: Interface gráfica moderna com Tkinter customizado

---

## 🎯 Funcionalidades Principais

### 1. **Gestão de Produtos**
- Cadastro de novos produtos com código, nome, marca, preço e tipo
- Validação de duplicidade (case-insensitive)
- Listagem com ordenação
- Busca por código

### 2. **Sistema de Caixa**
- Adição de produtos por código com quantidade
- Carrinho de compras interativo
- Suporte a múltiplas formas de pagamento:
  - **Dinheiro** (com cálculo de troco)
  - **Pix**
  - **Cartão**
- Sistema de desconto progressivo por cliente

### 3. **Gestão de Clientes**
- Cadastro com validação de CPF
- Sistema de **níveis de desconto** baseado em histórico:
  - **Nível 1**: 10 compras ≥ R$100 → 10% desconto
  - **Nível 2**: 50 compras ≥ R$200 → 20% desconto
  - **Nível 3**: 100 compras ≥ R$1000 → 30% desconto
- Desativação de clientes (soft delete)
- Listagem com filtro de ativos/inativos

### 4. **Controle de Estoque**
- Registros de entrada/saída/ajuste com histórico
- Verificação automática de estoque suficiente antes de venda
- Devolução de estoque em caso de cancelamento
- Rastreabilidade completa de movimentações

### 5. **Relatórios**
- **Vendas do dia**: Total de vendas, faturamento e ticket médio
- **Estoque baixo**: Produtos com quantidade menor ou igual a um limite
- **Estoque vazio**: Produtos sem quantidade
- **Top clientes**: Clientes que mais compraram ordenados por gasto total

---

## 🏗️ Arquitetura

### Backend (`Mercado/backend/main.py`)

```
├── Gerenciamento de Banco de Dados
│   ├── get_connection() - Context manager para conexões
│   └── criar_tabelas() - Inicialização das tabelas
│
├── Camada de Validação
│   ├── validar_cpf()
│   ├── validar_forma_pagamento()
│   ├── validar_dados_cliente()
│   └── validar_itens()
│
├── Operações de Produtos
│   ├── cadastrar_produto()
│   ├── existe_produto()
│   └── registrar_movimentacao_estoque()
│
├── Operações de Clientes
│   ├── cadastrar_cliente()
│   ├── atualizar_cliente()
│   ├── listar_clientes()
│   ├── desativar_cliente()
│   ├── buscar_cliente_por_cpf()
│   ├── calcular_nivel_cliente()
│   └── aplicar_desconto()
│
├── Operações de Vendas
│   ├── registrar_venda()
│   └── cancelar_venda()
│
└── Relatórios
    ├── relatorio_vendas_dia()
    ├── relatorio_estoque_baixo()
    ├── relatorio_estoque_vazio()
    └── relatorio_clientes_mais_compraram()
```

### Frontend (`Mercado/frontend/front.py`)

```
├── Interface Customizada (CustomTkinter)
│   ├── Tema dark com cores personalizadas
│   └── Componentes reutilizáveis
│
├── Páginas Principais
│   ├── ProductsPage - Gestão de produtos
│   ├── CashierPage - Sistema de caixa
│   ├── ClientsPage - Listagem de clientes
│   └── ReportsPage - Relatórios e indicadores
│
└── Componentes
    ├── StatusBanner - Feedback de ações
    ├── TableCard - Tabelas com scroll
    ├── StatCard - Cards de estatísticas
    └── SidebarButton - Navegação
```

---

## 📦 Estrutura do Banco de Dados

### Tabelas

#### `produtos`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER (PK) | Identificador único |
| codigo | TEXT (UNIQUE) | Código do produto |
| produto | TEXT | Nome do produto |
| marca | TEXT | Marca do produto |
| preco | REAL | Preço unitário |
| quant | INTEGER | Quantidade em estoque |
| tipo | TEXT | Tipo/categoria |

#### `clientes`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER (PK) | Identificador único |
| cpf | TEXT (UNIQUE) | CPF do cliente |
| nome | TEXT | Nome completo |
| data_nascimento | TEXT | Data de nascimento |
| telefone | TEXT | Telefone de contato |
| endereco | TEXT | Endereço residencial |
| email | TEXT | E-mail (opcional) |
| situacao | TEXT | 'ativo' ou 'inativo' |

#### `vendas`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER (PK) | Identificador único |
| data | TEXT | Data e hora da venda |
| total | REAL | Valor total com descontos |
| cliente_id | INTEGER (FK) | Cliente da venda |
| status | TEXT | 'concluida' ou 'cancelada' |
| forma_pagamento | TEXT | 'dinheiro', 'pix' ou 'cartao' |
| valor_pago | REAL | Valor entregue |
| troco | REAL | Troco da venda |

#### `itens_venda`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER (PK) | Identificador único |
| venda_id | INTEGER (FK) | Venda associada |
| produto_id | INTEGER (FK) | Produto vendido |
| quantidade | INTEGER | Qtd vendida |
| preco | REAL | Preço unitário no momento |
| subtotal | REAL | quantidade × preco |

#### `movimentacoes_estoque`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER (PK) | Identificador único |
| produto_id | INTEGER (FK) | Produto movimentado |
| tipo | TEXT | 'entrada', 'saida' ou 'ajuste' |
| quantidade | REAL | Qtd movimentada |
| data | TEXT | Data e hora |
| referencia | INTEGER | ID da venda/motivo |
| observacao | TEXT | Descrição adicional |

---

## 🚀 Como Usar

### Pré-requisitos

```bash
# Python 3.8+
# Dependências necessárias:
pip install customtkinter
```

### Instalação

```bash
# Clonar o repositório
git clone https://github.com/gustavo-silva7/Sistema-de-mercado.git
cd Sistema-de-mercado

# Instalar dependência
pip install customtkinter
```

### Execução

```bash
# Inicializar o sistema
cd Mercado/frontend
python front.py
```

### Primeiro Uso

1. **Criar produtos**: Acesse "Produtos" e cadastre itens com código único
2. **Registrar clientes**: Use "Clientes" para cadastrar (opcional para vendas)
3. **Realizar vendas**: Em "Caixa", adicione produtos por código
4. **Acompanhar**: Monitore via "Relatórios"

---

## 💡 Fluxos Principais

### Fluxo de Venda

```
1. Usuário busca produto por código
2. Sistema valida existência e estoque
3. Produto é adicionado ao carrinho
4. Ao finalizar:
   - CPF do cliente é opcional
   - Se informado, desconto é calculado automaticamente
   - Estoque é reduzido
   - Movimentação de saída é registrada
   - Venda é persistida no BD
```

### Fluxo de Desconto por Cliente

```
1. Cliente faz compras e acumula histórico
2. Sistema calcula nível baseado em:
   - Quantidade de compras
   - Valores mínimos por compra
3. Desconto é aplicado automaticamente na próxima venda
4. Cliente pode ser consultado em "Relatórios"
```

### Fluxo de Cancelamento

```
1. Venda com status 'concluida' pode ser cancelada
2. Estoque é devolvido automaticamente
3. Movimentação de entrada é registrada
4. Status da venda muda para 'cancelada'
```

---

## 🎨 Interface

### Paleta de Cores
- **Background**: `#10151d` (azul escuro)
- **Painel**: `#161c26` (cinza escuro)
- **Acento**: `#1f9d74` (verde)
- **Perigo**: `#dc5b5b` (vermelho)
- **Aviso**: `#f0b35c` (amarelo)

### Componentes
- **Tabelas**: Com scroll vertical e seleção de linhas
- **Entradas**: Com placeholder e validação em tempo real
- **Botões**: Com hover color e feedback visual
- **Cards**: Com bordas arredondadas e sombra sutil

---

## 🛡️ Tratamento de Erros

O sistema usa exceções personalizadas:

- **`MercadoError`**: Base para todos os erros
- **`ValidacaoError`**: Erros de validação de dados
- **`EstoqueError`**: Problemas com estoque
- **`ClienteError`**: Problemas com clientes

Todas as operações críticas usam **transações** (`BEGIN/COMMIT/ROLLBACK`) para garantir integridade.

---

## 📊 Recursos Avançados

### Validação Case-Insensitive
- Produtos duplicados evitados com `UPPER()` em SQL
- Índice único garante integridade

### Otimização de Estoque
- Agrupamento de itens por produto antes de verificação
- Uma única query para validar múltiplos produtos

### Rastreabilidade Completa
- Cada movimentação de estoque é registrada
- Referência a venda ou motivo da movimentação

### Transações ACID
- Garante que todas as operações são atômicas
- Rollback automático em caso de erro

---

## 📝 Exemplo de Uso - Python

```python
from main import *

# Inicializar banco de dados
criar_tabelas()

# Cadastrar cliente
cliente_id = cadastrar_cliente(
    cpf="12345678901",
    nome="João Silva",
    data_nascimento="1990-05-15",
    telefone="11999999999",
    endereco="Rua A, 123",
    email="joao@email.com"
)

# Cadastrar produto
produto_id = cadastrar_produto(
    codigo="PROD001",
    produto="Arroz",
    marca="Tio João",
    preco=25.50,
    quant=100,
    tipo="Alimento"
)

# Registrar venda
venda_id = registrar_venda(
    itens=[
        {"produto_id": 1, "quantidade": 2, "preco": 25.50}
    ],
    cpf="12345678901",
    forma_pagamento="dinheiro",
    valor_pago=100.00
)

# Obter relatório do dia
relatorio = relatorio_vendas_dia()
print(f"Total vendido: R$ {relatorio['total_vendido']}")
```

---

## 🔄 Status do Projeto

- ✅ Backend funcional
- ✅ Interface gráfica completa
- ✅ Sistema de vendas
- ✅ Gestão de clientes
- ✅ Controle de estoque
- ✅ Relatórios básicos

### Melhorias Futuras
- [ ] Exportação de relatórios (PDF/Excel)
- [ ] Autenticação de usuários
- [ ] Backup automático
- [ ] Migração para banco de dados remoto
- [ ] App mobile

---

## 👨‍💻 Autor

**Gustavo Silva** - [GitHub](https://github.com/gustavo-silva7)

---

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 📞 Suporte

Para dúvidas ou sugestões, abra uma [issue](https://github.com/gustavo-silva7/Sistema-de-mercado/issues) no repositório.
