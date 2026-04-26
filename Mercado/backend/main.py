# Sistema de Mercado - Python com SQLite
import sqlite3
import re
from contextlib import contextmanager
from datetime import datetime

DATABASE = "DataBase.db"

@contextmanager
def get_connection():
    """Context manager para conexões ao banco de dados."""
    con = sqlite3.connect(DATABASE)
    try:
        yield con
    finally:
        con.close()

# Exceções personalizadas
class MercadoError(Exception):
    """Exceção base para erros do sistema de mercado."""
    pass

class ValidacaoError(MercadoError):
    """Erro de validação de dados."""
    pass

class EstoqueError(MercadoError):
    """Erro relacionado a controle de estoque."""
    pass

class ClienteError(MercadoError):
    """Erro relacionado a clientes."""
    pass

# Funções de criação de tabelas
def criar_tabelas():
    """Cria todas as tabelas necessárias se não existirem."""
    with get_connection() as con:
        cursor = con.cursor()
        # Criar tabelas
        table_produtos(cursor)
        table_clientes(cursor)
        table_vendas(cursor)
        table_itens_venda(cursor)
        table_movimentacoes_estoque(cursor)
        criar_indices(cursor)
        atualizar_schema_vendas(cursor)
        con.commit()

def table_produtos(cursor):
    """Cria a tabela de produtos."""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produtos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        produto TEXT NOT NULL,
        marca TEXT NOT NULL,
        preco REAL NOT NULL,
        quant INTEGER NOT NULL,
        tipo TEXT NOT NULL
    )
    ''')

def table_clientes(cursor):
    """Cria a tabela de clientes."""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clientes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cpf TEXT UNIQUE NOT NULL,
        nome TEXT NOT NULL,
        data_nascimento TEXT NOT NULL,
        telefone TEXT NOT NULL,
        endereco TEXT NOT NULL,
        email TEXT,
        situacao TEXT NOT NULL
    )
    ''')

def table_vendas(cursor):
    """Cria a tabela de vendas."""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        total REAL NOT NULL,
        cliente_id INTEGER,
        status TEXT NOT NULL DEFAULT 'concluida',
        forma_pagamento TEXT NOT NULL DEFAULT 'dinheiro',
        valor_pago REAL,
        troco REAL
    )
    ''')

def table_itens_venda(cursor):
    """Cria a tabela de itens de venda."""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS itens_venda(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venda_id INTEGER NOT NULL,
        produto_id INTEGER NOT NULL,
        quantidade INTEGER NOT NULL,
        preco REAL NOT NULL,
        subtotal REAL NOT NULL
    )
    ''')

def criar_indices(cursor):
    """Cria índices para otimização de performance."""
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_vendas_cliente_id ON vendas(cliente_id)')
    # Índice único case-insensitive para evitar duplicidade de produtos por nome+marca
    cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_produtos_producao_marca ON produtos(UPPER(produto), UPPER(marca))')


def atualizar_schema_vendas(cursor):
    """Atualiza esquema da tabela vendas caso esteja em versão anterior."""
    cursor.execute("PRAGMA table_info(vendas)")
    colunas = {col[1] for col in cursor.fetchall()}
    if 'forma_pagamento' not in colunas:
        cursor.execute("ALTER TABLE vendas ADD COLUMN forma_pagamento TEXT NOT NULL DEFAULT 'dinheiro'")
    if 'valor_pago' not in colunas:
        cursor.execute("ALTER TABLE vendas ADD COLUMN valor_pago REAL")
    if 'troco' not in colunas:
        cursor.execute("ALTER TABLE vendas ADD COLUMN troco REAL")


def table_movimentacoes_estoque(cursor):
    """Cria a tabela de movimentações de estoque."""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS movimentacoes_estoque(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        quantidade REAL NOT NULL,
        data TEXT NOT NULL,
        referencia INTEGER,
        observacao TEXT
    )
    ''')

# Funções de validação
def validar_cpf(cpf):
    """Valida formato básico do CPF (11 dígitos numéricos)."""
    if not cpf:
        return False
    # Remove caracteres não numéricos
    cpf_numerico = re.sub(r'\D', '', cpf)
    return len(cpf_numerico) == 11 and cpf_numerico.isdigit()

def validar_forma_pagamento(forma_pagamento):
    """Valida forma de pagamento."""
    formas_validas = {'dinheiro', 'pix', 'cartao'}
    if forma_pagamento not in formas_validas:
        raise ValidacaoError(f"Forma de pagamento inválida: {forma_pagamento}. Use {formas_validas}.")
    return forma_pagamento

def validar_dados_cliente(cpf, nome, data_nascimento, telefone, endereco):
    """Valida dados básicos do cliente para CRUD."""
    if not cpf or not nome or not data_nascimento or not telefone or not endereco:
        raise ValidacaoError("Todos os campos (cpf, nome, data_nascimento, telefone, endereco) são obrigatórios.")
    if not validar_cpf(cpf):
        raise ClienteError(f"CPF '{cpf}' com formato inválido.")
    return True

# Funções de produto

def normalizar_produto_marca(produto, marca):
    """Normaliza produto/marca para evitar duplicidade de maiúsculas/minúsculas."""
    if not produto or not marca:
        raise ValidacaoError("Os campos produto e marca são obrigatórios.")
    return produto.strip().upper(), marca.strip().upper()


def existe_produto(produto, marca):
    """Retorna True se já existir produto com mesmo produto+marca (case-insensitive)."""
    produto_norm, marca_norm = normalizar_produto_marca(produto, marca)
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute(
            "SELECT id FROM produtos WHERE UPPER(produto)=? AND UPPER(marca)=?",
            (produto_norm, marca_norm),
        )
        return cursor.fetchone() is not None


def cadastrar_produto(codigo, produto, marca, preco, quant, tipo):
    """Cadastra produto com normalização e validação de duplicidade."""
    if preco < 0:
        raise ValidacaoError("Preço do produto deve ser maior ou igual a zero.")
    if quant < 0:
        raise ValidacaoError("Quantidade do produto deve ser maior ou igual a zero.")
    produto_norm, marca_norm = normalizar_produto_marca(produto, marca)

    with get_connection() as con:
        try:
            con.execute("BEGIN")
            cursor = con.cursor()
            if existe_produto(produto_norm, marca_norm):
                raise ValidacaoError(f"Produto '{produto_norm}' da marca '{marca_norm}' já existe.")
            cursor.execute(
                "INSERT INTO produtos (codigo, produto, marca, preco, quant, tipo) VALUES (?, ?, ?, ?, ?, ?)",
                (codigo, produto_norm, marca_norm, preco, quant, tipo),
            )
            produto_id = cursor.lastrowid
            con.commit()
            return produto_id
        except Exception:
            con.rollback()
            raise


def validar_itens(itens):
    """Valida a lista de itens da venda."""
    if not itens:
        raise ValidacaoError("A venda deve ter pelo menos um item.")
    produto_ids = set()
    for item in itens:
        if not isinstance(item, dict):
            raise ValidacaoError("Cada item deve ser um dicionário.")
        required_keys = {'produto_id', 'quantidade', 'preco'}
        if not required_keys.issubset(item.keys()):
            raise ValidacaoError("Cada item deve ter 'produto_id', 'quantidade' e 'preco'.")
        if not isinstance(item['produto_id'], int) or item['produto_id'] <= 0:
            raise ValidacaoError("produto_id deve ser um inteiro positivo.")
        if item['quantidade'] <= 0:
            raise ValidacaoError("Quantidade deve ser maior que zero.")
        if item['preco'] < 0:
            raise ValidacaoError("Preço deve ser maior ou igual a zero.")
        produto_ids.add(item['produto_id'])
    return produto_ids

# Funções de movimentação de estoque
def registrar_movimentacao_estoque(cursor, produto_id, tipo, quantidade, referencia=None, observacao=None):
    """Registra movimentação de estoque em movimentacoes_estoque."""
    if tipo not in ('entrada', 'saida', 'ajuste'):
        raise ValidacaoError("Tipo de movimentação inválido. Use 'entrada', 'saida' ou 'ajuste'.")
    if quantidade <= 0:
        raise ValidacaoError("Quantidade da movimentação deve ser maior que zero.")
    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO movimentacoes_estoque (produto_id, tipo, quantidade, data, referencia, observacao)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (produto_id, tipo, quantidade, data_atual, referencia, observacao))

def adicionar_estoque(produto_id, quantidade, motivo):
    """Adiciona estoque a um produto existente e registra movimentação de entrada."""
    if quantidade <= 0:
        raise ValidacaoError("Quantidade de entrada deve ser maior que zero.")
    if not motivo:
        raise ValidacaoError("Motivo da entrada de estoque é obrigatório.")

    with get_connection() as con:
        try:
            con.execute("BEGIN")
            cursor = con.cursor()
            cursor.execute("SELECT quant FROM produtos WHERE id = ?", (produto_id,))
            row = cursor.fetchone()
            if not row:
                raise EstoqueError(f"Produto ID {produto_id} não encontrado.")

            cursor.execute("UPDATE produtos SET quant = quant + ? WHERE id = ?", (quantidade, produto_id))
            registrar_movimentacao_estoque(cursor, produto_id, 'entrada', quantidade, referencia=None, observacao=motivo)
            con.commit()
        except Exception:
            con.rollback()
            raise

# Funções de negócio

def cadastrar_cliente(cpf, nome, data_nascimento, telefone, endereco, email=None, situacao='ativo'):
    """Cadastra um novo cliente, respeitando CPF único."""
    validar_dados_cliente(cpf, nome, data_nascimento, telefone, endereco)

    with get_connection() as con:
        try:
            con.execute("BEGIN")
            cursor = con.cursor()
            cursor.execute("SELECT id FROM clientes WHERE cpf = ?", (cpf,))
            if cursor.fetchone():
                raise ClienteError(f"CPF '{cpf}' já cadastrado.")

            cursor.execute("""
                INSERT INTO clientes (cpf, nome, data_nascimento, telefone, endereco, email, situacao)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (cpf, nome, data_nascimento, telefone, endereco, email, situacao))
            cliente_id = cursor.lastrowid
            con.commit()
            return cliente_id
        except Exception:
            con.rollback()
            raise

def atualizar_cliente(cliente_id, cpf, nome, data_nascimento, telefone, endereco, email=None, situacao='ativo'):
    """Atualiza um cliente existente."""
    validar_dados_cliente(cpf, nome, data_nascimento, telefone, endereco)

    with get_connection() as con:
        try:
            con.execute("BEGIN")
            cursor = con.cursor()
            cursor.execute("SELECT id FROM clientes WHERE id = ?", (cliente_id,))
            if not cursor.fetchone():
                raise ClienteError(f"Cliente ID {cliente_id} não encontrado.")

            cursor.execute("SELECT id FROM clientes WHERE cpf = ? AND id != ?", (cpf, cliente_id))
            if cursor.fetchone():
                raise ClienteError(f"CPF '{cpf}' já pertence a outro cliente.")

            cursor.execute("""
                UPDATE clientes
                SET cpf = ?, nome = ?, data_nascimento = ?, telefone = ?, endereco = ?, email = ?, situacao = ?
                WHERE id = ?
            """, (cpf, nome, data_nascimento, telefone, endereco, email, situacao, cliente_id))
            con.commit()
            return True
        except Exception:
            con.rollback()
            raise

def listar_clientes(ativos=True):
    """Retorna lista de clientes. Se ativos=True, filtra situacao <> 'inativo'."""
    with get_connection() as con:
        cursor = con.cursor()
        if ativos:
            cursor.execute("SELECT id, cpf, nome, data_nascimento, telefone, endereco, email, situacao FROM clientes WHERE situacao != 'inativo'")
        else:
            cursor.execute("SELECT id, cpf, nome, data_nascimento, telefone, endereco, email, situacao FROM clientes")
        return cursor.fetchall()

def desativar_cliente(cliente_id):
    """Marca cliente como inativo, sem excluir."""
    with get_connection() as con:
        try:
            con.execute("BEGIN")
            cursor = con.cursor()
            cursor.execute("SELECT situacao FROM clientes WHERE id = ?", (cliente_id,))
            row = cursor.fetchone()
            if not row:
                raise ClienteError(f"Cliente ID {cliente_id} não encontrado.")
            if row[0] == 'inativo':
                return False
            cursor.execute("UPDATE clientes SET situacao = 'inativo' WHERE id = ?", (cliente_id,))
            con.commit()
            return True
        except Exception:
            con.rollback()
            raise

def buscar_cliente_por_cpf(cpf):
    """Busca cliente pelo CPF. Retorna o ID do cliente ou None se não encontrado."""
    if not validar_cpf(cpf):
        raise ClienteError(f"CPF '{cpf}' tem formato inválido.")
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute("SELECT id FROM clientes WHERE cpf = ?", (cpf,))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None

def calcular_nivel_cliente(cliente_id):
    """Calcula o nível de desconto do cliente baseado no histórico de compras."""
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute("""
            SELECT
                COUNT(CASE WHEN total >= 1000 THEN 1 END) as count_1000,
                COUNT(CASE WHEN total >= 200 THEN 1 END) as count_200,
                COUNT(CASE WHEN total >= 100 THEN 1 END) as count_100
            FROM vendas
            WHERE cliente_id = ? AND status = 'concluida'
        """, (cliente_id,))
        row = cursor.fetchone()
        if row is None:
            return 0
        count_1000, count_200, count_100 = row

        # Verificar nível 3: 100 compras >= 1000
        if count_1000 >= 100:
            return 3
        # Verificar nível 2: 50 compras >= 200
        elif count_200 >= 50:
            return 2
        # Verificar nível 1: 10 compras >= 100
        elif count_100 >= 10:
            return 1
        # Nível 0: sem desconto
        else:
            return 0

def aplicar_desconto(total, nivel):
    """Aplica o desconto baseado no nível do cliente, se aplicável."""
    if total < 100 or nivel == 0:
        return total
    descontos = {1: 0.10, 2: 0.20, 3: 0.30}
    desconto = descontos.get(nivel, 0)
    return round(total * (1 - desconto), 2)

def verificar_estoque_agrupado(itens, cursor):
    """Verifica estoque agrupando itens por produto_id para eficiência."""
    # Agrupar quantidades por produto_id
    quantidades_necessarias = {}
    for item in itens:
        produto_id = item['produto_id']
        quantidades_necessarias[produto_id] = quantidades_necessarias.get(produto_id, 0) + item['quantidade']

    # Verificar estoques em lote
    produto_ids = list(quantidades_necessarias.keys())
    placeholders = ','.join('?' * len(produto_ids))
    cursor.execute(f"SELECT id, quant FROM produtos WHERE id IN ({placeholders})", produto_ids)
    estoques = {row[0]: row[1] for row in cursor.fetchall()}

    # Verificar se todos os produtos existem e têm estoque suficiente
    for produto_id, quantidade_necessaria in quantidades_necessarias.items():
        if produto_id not in estoques:
            raise EstoqueError(f"Produto ID {produto_id} não encontrado no sistema.")
        estoque_atual = estoques[produto_id]
        if estoque_atual < quantidade_necessaria:
            raise EstoqueError(f"Estoque insuficiente para produto ID {produto_id}. Disponível: {estoque_atual}, Solicitado: {quantidade_necessaria}")

def registrar_venda(itens, cpf=None, forma_pagamento='dinheiro', valor_pago=None):
    """
    Registra uma venda com os itens fornecidos.
    itens: lista de dicionários {'produto_id': int, 'quantidade': int, 'preco': float}
    cpf: CPF do cliente (opcional)
    forma_pagamento: 'dinheiro', 'pix', 'cartao'
    valor_pago: valor entregue pelo cliente (para cálculo de troco)
    Retorna o ID da venda criada.
    """
    # Validar itens e obter produto_ids únicos
    produto_ids = validar_itens(itens)

    # Calcular total bruto
    total_bruto = sum(item['quantidade'] * item['preco'] for item in itens)

    # Verificar cliente e desconto
    cliente_id = None
    nivel = 0
    if cpf:
        cliente_id = buscar_cliente_por_cpf(cpf)
        if not cliente_id:
            raise ClienteError(f"CPF '{cpf}' não encontrado no sistema. Venda não pode ser processada com desconto.")
        nivel = calcular_nivel_cliente(cliente_id)

    # Aplicar desconto se aplicável
    total_final = aplicar_desconto(total_bruto, nivel)

    # Validar forma de pagamento e valor pago
    validar_forma_pagamento(forma_pagamento)
    troco = None
    if valor_pago is not None:
        if valor_pago < total_final:
            raise ValidacaoError(f"valor_pago ({valor_pago}) deve ser >= total_final ({total_final}).")
        troco = round(valor_pago - total_final, 2)

    # Usar transação para garantir integridade
    with get_connection() as con:
        try:
            con.execute("BEGIN")
            cursor = con.cursor()

            # Verificar estoques (agrupados para eficiência)
            verificar_estoque_agrupado(itens, cursor)

            # Inserir venda
            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO vendas (data, total, cliente_id, status, forma_pagamento, valor_pago, troco)
                VALUES (?, ?, ?, 'concluida', ?, ?, ?)
            """, (data_atual, total_final, cliente_id, forma_pagamento, valor_pago, troco))
            venda_id = cursor.lastrowid

            # Inserir itens da venda
            for item in itens:
                subtotal = round(item['quantidade'] * item['preco'], 2)
                cursor.execute("""
                    INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                """, (venda_id, item['produto_id'], item['quantidade'], item['preco'], subtotal))

            # Dar baixa no estoque (agrupada)
            quantidades_para_baixar = {}
            for item in itens:
                produto_id = item['produto_id']
                quantidades_para_baixar[produto_id] = quantidades_para_baixar.get(produto_id, 0) + item['quantidade']
            for produto_id, quantidade in quantidades_para_baixar.items():
                cursor.execute("""
                    UPDATE produtos SET quant = quant - ? WHERE id = ?
                """, (quantidade, produto_id))
                registrar_movimentacao_estoque(cursor, produto_id, 'saida', quantidade, referencia=venda_id, observacao='Venda concluida')

            con.commit()
            return venda_id
        except Exception as e:
            con.rollback()
            raise e


def cancelar_venda(venda_id):
    """Cancela a venda, devolve estoque e registra movimentações de entrada."""
    with get_connection() as con:
        try:
            con.execute("BEGIN")
            cursor = con.cursor()

            cursor.execute("SELECT status FROM vendas WHERE id = ?", (venda_id,))
            venda = cursor.fetchone()
            if not venda:
                raise MercadoError(f"Venda {venda_id} não encontrada.")
            status_atual = venda[0]
            if status_atual == 'cancelada':
                return False
            if status_atual != 'concluida':
                raise MercadoError(f"Venda {venda_id} não pode ser cancelada, status atual: {status_atual}.")

            cursor.execute("UPDATE vendas SET status = 'cancelada' WHERE id = ?", (venda_id,))

            cursor.execute("SELECT produto_id, quantidade FROM itens_venda WHERE venda_id = ?", (venda_id,))
            itens = cursor.fetchall()
            if not itens:
                raise MercadoError(f"Venda {venda_id} não possui itens para estornar.")

            for produto_id, quantidade in itens:
                cursor.execute("UPDATE produtos SET quant = quant + ? WHERE id = ?", (quantidade, produto_id))
                registrar_movimentacao_estoque(cursor, produto_id, 'entrada', quantidade, referencia=venda_id, observacao='Cancelamento de venda')

            con.commit()
            return True
        except Exception:
            con.rollback()
            raise

# Relatórios

def relatorio_vendas_dia(data=None):
    """Retorna total vendido, quantidade de vendas e ticket médio para o dia informado."""
    if data is None:
        data = datetime.now().strftime('%Y-%m-%d')
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_vendas,
                SUM(total) as total_vendido
            FROM vendas
            WHERE status = 'concluida' AND DATE(data) = DATE(?)
        """, (data,))
        row = cursor.fetchone()
        total_vendas = row[0] or 0
        total_vendido = float(row[1] or 0.0)
        ticket_medio = round(total_vendido / total_vendas, 2) if total_vendas > 0 else 0.0
        return {
            'data': data,
            'total_vendas': total_vendas,
            'total_vendido': total_vendido,
            'ticket_medio': ticket_medio
        }

def relatorio_estoque_baixo(limite=10):
    """Retorna produtos com estoque menor ou igual ao limite."""
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute("""
            SELECT id, codigo, produto, marca, quant
            FROM produtos
            WHERE quant <= ? AND quant > 0
            ORDER BY quant ASC
        """, (limite,))
        return cursor.fetchall()

def relatorio_estoque_vazio():
    """Retorna produtos com estoque zerado."""
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute("""
            SELECT id, codigo, produto, marca
            FROM produtos
            WHERE quant = 0
        """)
        return cursor.fetchall()

def relatorio_clientes_mais_compraram(limit=10):
    """Retorna clientes ordenados pela soma total de compras, decrescente."""
    with get_connection() as con:
        cursor = con.cursor()
        cursor.execute("""
            SELECT c.id, c.nome, c.cpf, COUNT(v.id) as total_vendas, SUM(v.total) as total_gasto
            FROM clientes c
            JOIN vendas v ON v.cliente_id = c.id
            WHERE v.status = 'concluida'
            GROUP BY c.id, c.nome, c.cpf
            ORDER BY total_gasto DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()

# Exemplo de uso (para teste)
if __name__ == "__main__":
    criar_tabelas()
    print("Tabelas e índices criados com sucesso.")
