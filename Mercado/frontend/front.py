from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from decimal import Decimal, InvalidOperation

try:
    import customtkinter as ctk
except ImportError as error:
    raise SystemExit("Instale a dependência com 'pip install customtkinter' para executar a interface.") from error

from main import (
    ClienteError,
    MercadoError,
    ValidacaoError,
    buscar_produto_por_codigo,
    cadastrar_produto,
    criar_tabelas,
    listar_clientes,
    listar_produtos,
    registrar_venda,
    relatorio_clientes_mais_compraram,
    relatorio_estoque_baixo,
    relatorio_estoque_vazio,
    relatorio_vendas_dia,
)


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

COLORS = {
    "bg": "#10151d",
    "panel": "#161c26",
    "panel_alt": "#1d2633",
    "border": "#273243",
    "accent": "#1f9d74",
    "accent_hover": "#187e5d",
    "text": "#f4f7fb",
    "muted": "#93a1b5",
    "danger": "#dc5b5b",
    "warning": "#f0b35c",
}
FONT = "Segoe UI"


def money(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def parse_decimal(value: str, field_name: str) -> float:
    normalized = (value or "").strip()
    if "," in normalized and "." in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif "," in normalized:
        normalized = normalized.replace(",", ".")
    try:
        return float(Decimal(normalized))
    except (InvalidOperation, ValueError):
        raise ValidacaoError(f"Informe um valor válido para {field_name}.")


def parse_int(value: str, field_name: str) -> int:
    raw = (value or "").strip()
    if not raw.isdigit():
        raise ValidacaoError(f"Informe um número inteiro válido para {field_name}.")
    return int(raw)


class AppTheme:
    configured = False

    @classmethod
    def configure_treeview(cls, root: tk.Misc) -> None:
        if cls.configured:
            return
        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Market.Treeview",
            background=COLORS["panel"],
            foreground=COLORS["text"],
            fieldbackground=COLORS["panel"],
            bordercolor=COLORS["border"],
            rowheight=32,
            font=(FONT, 11),
        )
        style.configure(
            "Market.Treeview.Heading",
            background=COLORS["panel_alt"],
            foreground=COLORS["text"],
            relief="flat",
            font=(FONT, 11, "bold"),
        )
        style.map(
            "Market.Treeview",
            background=[("selected", COLORS["accent"])],
            foreground=[("selected", COLORS["text"])],
        )
        cls.configured = True


class StatusBanner(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=COLORS["panel_alt"], corner_radius=14)
        self.grid_columnconfigure(0, weight=1)
        self.label = ctk.CTkLabel(
            self,
            text="Pronto para uso.",
            text_color=COLORS["muted"],
            anchor="w",
            font=(FONT, 12),
        )
        self.label.grid(row=0, column=0, sticky="ew", padx=14, pady=10)

    def show(self, message: str, level: str = "info") -> None:
        colors = {
            "info": COLORS["muted"],
            "success": "#78d9b8",
            "error": COLORS["danger"],
            "warning": COLORS["warning"],
        }
        self.label.configure(text=message, text_color=colors.get(level, COLORS["muted"]))


class TableCard(ctk.CTkFrame):
    def __init__(self, master, title: str, columns: list[str], headings: list[str]):
        super().__init__(master, fg_color=COLORS["panel"], corner_radius=20, border_width=1, border_color=COLORS["border"])
        AppTheme.configure_treeview(self)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=title,
            font=(FONT, 18, "bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 10))

        table_frame = ctk.CTkFrame(self, fg_color="transparent")
        table_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Market.Treeview",
        )
        for column, heading in zip(columns, headings):
            self.tree.heading(column, text=heading)
            self.tree.column(column, anchor="center", stretch=True, width=110)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def clear(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

    def set_rows(self, rows: list[tuple]) -> None:
        self.clear()
        for row in rows:
            self.tree.insert("", "end", values=row)


class StatCard(ctk.CTkFrame):
    def __init__(self, master, title: str, value: str, accent: str = COLORS["accent"]):
        super().__init__(master, fg_color=COLORS["panel"], corner_radius=20, border_width=1, border_color=COLORS["border"])
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=title, font=(FONT, 13), text_color=COLORS["muted"]).grid(
            row=0, column=0, sticky="w", padx=18, pady=(18, 8)
        )
        self.value_label = ctk.CTkLabel(self, text=value, font=(FONT, 28, "bold"), text_color=accent)
        self.value_label.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 18))

    def update_value(self, value: str) -> None:
        self.value_label.configure(text=value)


class BasePage(ctk.CTkFrame):
    def __init__(self, master, title: str, subtitle: str):
        super().__init__(master, fg_color="transparent")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text=title, font=(FONT, 30, "bold"), text_color=COLORS["text"]).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkLabel(header, text=subtitle, font=(FONT, 13), text_color=COLORS["muted"]).grid(
            row=1, column=0, sticky="w", pady=(6, 0)
        )

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew")

    def on_show(self) -> None:
        pass


class ProductsPage(BasePage):
    def __init__(self, master):
        super().__init__(master, "Produtos", "Cadastre e acompanhe o estoque em tempo real.")
        self.body.grid_rowconfigure(1, weight=1)
        self.body.grid_columnconfigure(0, weight=3)
        self.body.grid_columnconfigure(1, weight=2)

        self.status = StatusBanner(self.body)
        self.status.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))

        self.table = TableCard(
            self.body,
            "Listagem de Produtos",
            ["codigo", "nome", "marca", "preco", "quantidade", "tipo"],
            ["Código", "Nome", "Marca", "Preço", "Quantidade", "Tipo"],
        )
        self.table.grid(row=1, column=0, sticky="nsew", padx=(0, 12))

        form_card = ctk.CTkFrame(
            self.body,
            fg_color=COLORS["panel"],
            corner_radius=20,
            border_width=1,
            border_color=COLORS["border"],
        )
        form_card.grid(row=1, column=1, sticky="nsew", padx=(12, 0))
        form_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(form_card, text="Novo Produto", font=(FONT, 20, "bold"), text_color=COLORS["text"]).grid(
            row=0, column=0, sticky="w", padx=20, pady=(18, 8)
        )
        ctk.CTkLabel(
            form_card,
            text="Preencha os campos para cadastrar no backend existente.",
            font=(FONT, 12),
            text_color=COLORS["muted"],
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 18))

        self.entries: dict[str, ctk.CTkEntry] = {}
        fields = [
            ("codigo", "Código"),
            ("nome", "Nome"),
            ("marca", "Marca"),
            ("preco", "Preço"),
            ("quantidade", "Quantidade"),
            ("tipo", "Tipo"),
        ]
        for index, (key, label) in enumerate(fields, start=2):
            ctk.CTkLabel(form_card, text=label, font=(FONT, 12), text_color=COLORS["muted"]).grid(
                row=index * 2, column=0, sticky="w", padx=20, pady=(0, 6)
            )
            entry = ctk.CTkEntry(
                form_card,
                height=40,
                corner_radius=12,
                border_color=COLORS["border"],
                fg_color=COLORS["panel_alt"],
                font=(FONT, 13),
                placeholder_text=f"Informe {label.lower()}",
            )
            entry.grid(row=index * 2 + 1, column=0, sticky="ew", padx=20, pady=(0, 12))
            self.entries[key] = entry

        buttons = ctk.CTkFrame(form_card, fg_color="transparent")
        buttons.grid(row=20, column=0, sticky="ew", padx=20, pady=(10, 20))
        buttons.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            buttons,
            text="Salvar Produto",
            height=42,
            corner_radius=14,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.save_product,
            font=(FONT, 13, "bold"),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            buttons,
            text="Limpar Campos",
            height=42,
            corner_radius=14,
            fg_color=COLORS["panel_alt"],
            hover_color="#243040",
            command=self.clear_form,
            font=(FONT, 13, "bold"),
        ).grid(row=0, column=1, sticky="ew", padx=(8, 0))

    def validate_fields(self) -> dict:
        data = {key: entry.get().strip() for key, entry in self.entries.items()}
        missing = [name for name, value in data.items() if not value]
        if missing:
            raise ValidacaoError("Preencha todos os campos obrigatórios do produto.")
        return {
            "codigo": data["codigo"],
            "nome": data["nome"],
            "marca": data["marca"],
            "preco": parse_decimal(data["preco"], "preço"),
            "quantidade": parse_int(data["quantidade"], "quantidade"),
            "tipo": data["tipo"],
        }

    def save_product(self) -> None:
        try:
            payload = self.validate_fields()
            cadastrar_produto(
                payload["codigo"],
                payload["nome"],
                payload["marca"],
                payload["preco"],
                payload["quantidade"],
                payload["tipo"],
            )
            self.clear_form()
            self.refresh_products()
            self.status.show("Produto cadastrado com sucesso.", "success")
        except MercadoError as error:
            self.status.show(str(error), "error")
        except Exception as error:
            self.status.show(f"Falha inesperada ao cadastrar: {error}", "error")

    def clear_form(self) -> None:
        for entry in self.entries.values():
            entry.delete(0, "end")
        self.status.show("Campos limpos.", "info")

    def refresh_products(self) -> None:
        products = listar_produtos()
        rows = [
            (
                item["codigo"],
                item["produto"],
                item["marca"],
                money(item["preco"]),
                item["quant"],
                item["tipo"],
            )
            for item in products
        ]
        self.table.set_rows(rows)

    def on_show(self) -> None:
        self.refresh_products()


class CashierPage(BasePage):
    def __init__(self, master):
        super().__init__(master, "Caixa", "Adicione itens por código e finalize vendas com rapidez.")
        self.cart: list[dict] = []
        self.body.grid_rowconfigure(2, weight=1)
        self.body.grid_columnconfigure(0, weight=3)
        self.body.grid_columnconfigure(1, weight=2)

        self.status = StatusBanner(self.body)
        self.status.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))

        action_card = ctk.CTkFrame(
            self.body,
            fg_color=COLORS["panel"],
            corner_radius=20,
            border_width=1,
            border_color=COLORS["border"],
        )
        action_card.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        action_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(action_card, text="Código do produto", font=(FONT, 12), text_color=COLORS["muted"]).grid(
            row=0, column=0, sticky="w", padx=18, pady=(18, 6)
        )
        self.code_entry = ctk.CTkEntry(
            action_card,
            height=42,
            corner_radius=12,
            border_color=COLORS["border"],
            fg_color=COLORS["panel_alt"],
            font=(FONT, 13),
            placeholder_text="Digite ou leia o código",
        )
        self.code_entry.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 18))

        ctk.CTkLabel(action_card, text="Quantidade", font=(FONT, 12), text_color=COLORS["muted"]).grid(
            row=0, column=1, sticky="w", padx=18, pady=(18, 6)
        )
        self.quantity_entry = ctk.CTkEntry(
            action_card,
            height=42,
            corner_radius=12,
            border_color=COLORS["border"],
            fg_color=COLORS["panel_alt"],
            font=(FONT, 13),
            placeholder_text="1",
        )
        self.quantity_entry.insert(0, "1")
        self.quantity_entry.grid(row=1, column=1, sticky="ew", padx=18, pady=(0, 18))

        ctk.CTkButton(
            action_card,
            text="Adicionar",
            height=42,
            width=140,
            corner_radius=14,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.add_item,
            font=(FONT, 13, "bold"),
        ).grid(row=1, column=2, sticky="e", padx=18, pady=(0, 18))

        self.table = TableCard(
            self.body,
            "Itens da Compra",
            ["codigo", "nome", "qtd", "preco", "subtotal"],
            ["Código", "Produto", "Qtd", "Preço", "Subtotal"],
        )
        self.table.grid(row=2, column=0, sticky="nsew", padx=(0, 12))

        summary = ctk.CTkFrame(
            self.body,
            fg_color=COLORS["panel"],
            corner_radius=20,
            border_width=1,
            border_color=COLORS["border"],
        )
        summary.grid(row=2, column=1, sticky="nsew", padx=(12, 0))
        summary.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(summary, text="Resumo", font=(FONT, 20, "bold"), text_color=COLORS["text"]).grid(
            row=0, column=0, sticky="w", padx=20, pady=(18, 8)
        )
        ctk.CTkLabel(summary, text="Forma de pagamento", font=(FONT, 12), text_color=COLORS["muted"]).grid(
            row=1, column=0, sticky="w", padx=20
        )

        self.payment_var = ctk.StringVar(value="dinheiro")
        ctk.CTkSegmentedButton(
            summary,
            values=["dinheiro", "pix", "cartao"],
            variable=self.payment_var,
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["panel_alt"],
            unselected_hover_color="#243040",
        ).grid(row=2, column=0, sticky="ew", padx=20, pady=(8, 16))

        ctk.CTkLabel(summary, text="CPF do cliente (opcional)", font=(FONT, 12), text_color=COLORS["muted"]).grid(
            row=3, column=0, sticky="w", padx=20
        )
        self.cpf_entry = ctk.CTkEntry(
            summary,
            height=40,
            corner_radius=12,
            border_color=COLORS["border"],
            fg_color=COLORS["panel_alt"],
            font=(FONT, 13),
            placeholder_text="Somente se houver cadastro",
        )
        self.cpf_entry.grid(row=4, column=0, sticky="ew", padx=20, pady=(8, 16))

        ctk.CTkLabel(summary, text="Total da compra", font=(FONT, 12), text_color=COLORS["muted"]).grid(
            row=5, column=0, sticky="w", padx=20
        )
        self.total_label = ctk.CTkLabel(summary, text=money(0), font=(FONT, 34, "bold"), text_color=COLORS["accent"])
        self.total_label.grid(row=6, column=0, sticky="w", padx=20, pady=(4, 20))

        ctk.CTkButton(
            summary,
            text="Remover Selecionado",
            height=42,
            corner_radius=14,
            fg_color=COLORS["panel_alt"],
            hover_color="#243040",
            command=self.remove_selected,
            font=(FONT, 13, "bold"),
        ).grid(row=7, column=0, sticky="ew", padx=20, pady=(0, 10))

        ctk.CTkButton(
            summary,
            text="Finalizar Venda",
            height=44,
            corner_radius=14,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.finish_sale,
            font=(FONT, 14, "bold"),
        ).grid(row=8, column=0, sticky="ew", padx=20, pady=(0, 20))

    def add_item(self) -> None:
        try:
            code = self.code_entry.get().strip()
            quantity = parse_int(self.quantity_entry.get().strip() or "1", "quantidade")
            product = buscar_produto_por_codigo(code)
            if not product:
                raise ValidacaoError("Produto não encontrado para o código informado.")
            if quantity <= 0:
                raise ValidacaoError("Quantidade deve ser maior que zero.")
            if product["quant"] < quantity:
                raise ValidacaoError(f"Estoque insuficiente. Disponível: {product['quant']}.")

            existing = next((item for item in self.cart if item["produto_id"] == product["id"]), None)
            if existing:
                if existing["quantidade"] + quantity > product["quant"]:
                    raise ValidacaoError(f"Estoque insuficiente. Disponível: {product['quant']}.")
                existing["quantidade"] += quantity
            else:
                self.cart.append(
                    {
                        "produto_id": product["id"],
                        "codigo": product["codigo"],
                        "nome": product["produto"],
                        "quantidade": quantity,
                        "preco": product["preco"],
                    }
                )
            self.code_entry.delete(0, "end")
            self.quantity_entry.delete(0, "end")
            self.quantity_entry.insert(0, "1")
            self.refresh_cart()
            self.status.show(f"{product['produto']} adicionado ao caixa.", "success")
        except MercadoError as error:
            self.status.show(str(error), "error")
        except Exception as error:
            self.status.show(f"Falha ao adicionar item: {error}", "error")

    def refresh_cart(self) -> None:
        rows = []
        total = 0.0
        for item in self.cart:
            subtotal = round(item["quantidade"] * item["preco"], 2)
            total += subtotal
            rows.append(
                (
                    item["codigo"],
                    item["nome"],
                    item["quantidade"],
                    money(item["preco"]),
                    money(subtotal),
                )
            )
        self.table.set_rows(rows)
        self.total_label.configure(text=money(total))

    def remove_selected(self) -> None:
        selected = self.table.tree.selection()
        if not selected:
            self.status.show("Selecione um item da lista para remover.", "warning")
            return
        values = self.table.tree.item(selected[0], "values")
        code = values[0]
        self.cart = [item for item in self.cart if item["codigo"] != code]
        self.refresh_cart()
        self.status.show("Item removido do caixa.", "info")

    def finish_sale(self) -> None:
        if not self.cart:
            self.status.show("Adicione ao menos um item antes de finalizar.", "warning")
            return
        items = [
            {
                "produto_id": item["produto_id"],
                "quantidade": item["quantidade"],
                "preco": item["preco"],
            }
            for item in self.cart
        ]
        cpf = self.cpf_entry.get().strip() or None
        try:
            sale_id = registrar_venda(items, cpf=cpf, forma_pagamento=self.payment_var.get())
            total = sum(item["quantidade"] * item["preco"] for item in self.cart)
            self.cart.clear()
            self.cpf_entry.delete(0, "end")
            self.refresh_cart()
            self.status.show(f"Venda #{sale_id} finalizada com total de {money(total)}.", "success")
        except MercadoError as error:
            self.status.show(str(error), "error")
        except Exception as error:
            self.status.show(f"Falha ao finalizar venda: {error}", "error")


class ClientsPage(BasePage):
    def __init__(self, master):
        super().__init__(master, "Clientes", "Visualize rapidamente os clientes cadastrados.")
        self.body.grid_rowconfigure(1, weight=1)
        self.body.grid_columnconfigure(0, weight=1)

        self.status = StatusBanner(self.body)
        self.status.grid(row=0, column=0, sticky="ew", pady=(0, 18))

        self.table = TableCard(
            self.body,
            "Clientes Ativos",
            ["cpf", "nome", "nascimento", "telefone", "email", "situacao"],
            ["CPF", "Nome", "Nascimento", "Telefone", "E-mail", "Situação"],
        )
        self.table.grid(row=1, column=0, sticky="nsew")

    def on_show(self) -> None:
        customers = listar_clientes(ativos=True)
        rows = [(cpf, nome, nascimento, telefone, email or "-", situacao) for _, cpf, nome, nascimento, telefone, _, email, situacao in customers]
        self.table.set_rows(rows)
        self.status.show(f"{len(rows)} clientes ativos carregados.", "info")


class ReportsPage(BasePage):
    def __init__(self, master):
        super().__init__(master, "Relatórios", "Indicadores rápidos para acompanhar vendas e estoque.")
        self.body.grid_rowconfigure(2, weight=1)
        self.body.grid_columnconfigure((0, 1, 2), weight=1)

        self.date_label = ctk.CTkLabel(
            self.body,
            text="",
            font=(FONT, 12),
            text_color=COLORS["muted"],
        )
        self.date_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 14))

        self.sales_card = StatCard(self.body, "Vendas do Dia", "0")
        self.sales_card.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 18))

        self.revenue_card = StatCard(self.body, "Faturamento", money(0))
        self.revenue_card.grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 18))

        self.ticket_card = StatCard(self.body, "Ticket Médio", money(0))
        self.ticket_card.grid(row=1, column=2, sticky="ew", padx=(10, 0), pady=(0, 18))

        self.low_stock_table = TableCard(
            self.body,
            "Estoque Baixo",
            ["codigo", "nome", "marca", "quantidade"],
            ["Código", "Produto", "Marca", "Quantidade"],
        )
        self.low_stock_table.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=(0, 10))

        self.top_clients_table = TableCard(
            self.body,
            "Clientes com Mais Compras",
            ["nome", "cpf", "vendas", "gasto"],
            ["Nome", "CPF", "Vendas", "Total Gasto"],
        )
        self.top_clients_table.grid(row=2, column=2, sticky="nsew", padx=(10, 0))

    def on_show(self) -> None:
        report = relatorio_vendas_dia()
        low_stock = relatorio_estoque_baixo()
        zero_stock = relatorio_estoque_vazio()
        top_clients = relatorio_clientes_mais_compraram()

        self.date_label.configure(
            text=f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')} | Itens zerados: {len(zero_stock)}"
        )
        self.sales_card.update_value(str(report["total_vendas"]))
        self.revenue_card.update_value(money(report["total_vendido"]))
        self.ticket_card.update_value(money(report["ticket_medio"]))

        self.low_stock_table.set_rows([(codigo, produto, marca, quant) for _, codigo, produto, marca, quant in low_stock])
        self.top_clients_table.set_rows(
            [(nome, cpf, total_vendas, money(float(total_gasto or 0))) for _, nome, cpf, total_vendas, total_gasto in top_clients]
        )


class SidebarButton(ctk.CTkButton):
    def __init__(self, master, text: str, command):
        super().__init__(
            master,
            text=text,
            height=46,
            corner_radius=14,
            fg_color="transparent",
            hover_color=COLORS["panel_alt"],
            anchor="w",
            font=(FONT, 14, "bold"),
            command=command,
        )

    def set_active(self, active: bool) -> None:
        self.configure(fg_color=COLORS["accent"] if active else "transparent")


class MarketApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        criar_tabelas()
        self.title("Sistema de Mercado")
        self.configure(fg_color=COLORS["bg"])
        self.minsize(1200, 720)
        self.after(50, self.maximize_window)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_buttons: dict[str, SidebarButton] = {}
        self.pages: dict[str, BasePage] = {}

        self.build_sidebar()
        self.build_content()
        self.show_page("Caixa")

    def maximize_window(self) -> None:
        try:
            self.state("zoomed")
        except tk.TclError:
            width = self.winfo_screenwidth()
            height = self.winfo_screenheight()
            self.geometry(f"{width}x{height}+0+0")

    def build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(
            self,
            width=250,
            fg_color=COLORS["panel"],
            corner_radius=0,
            border_width=0,
        )
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(
            sidebar,
            text="Mercado Pro",
            font=(FONT, 24, "bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(28, 6))
        ctk.CTkLabel(
            sidebar,
            text="Painel operacional",
            font=(FONT, 12),
            text_color=COLORS["muted"],
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 28))

        for row, name in enumerate(["Caixa", "Produtos", "Clientes", "Relatórios"], start=2):
            button = SidebarButton(sidebar, name, command=lambda page=name: self.show_page(page))
            button.grid(row=row, column=0, sticky="ew", padx=18, pady=6)
            self.sidebar_buttons[name] = button

        ctk.CTkLabel(
            sidebar,
            text="CustomTkinter • modo escuro",
            font=(FONT, 11),
            text_color=COLORS["muted"],
        ).grid(row=7, column=0, sticky="sw", padx=24, pady=24)

    def build_content(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "Produtos": ProductsPage(container),
            "Caixa": CashierPage(container),
            "Clientes": ClientsPage(container),
            "Relatórios": ReportsPage(container),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

    def show_page(self, name: str) -> None:
        for page_name, button in self.sidebar_buttons.items():
            button.set_active(page_name == name)
        page = self.pages[name]
        page.tkraise()
        page.on_show()


if __name__ == "__main__":
    app = MarketApp()
    app.mainloop()
