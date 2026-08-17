import sqlite3
import pandas as pd
import streamlit as st

# Configuração da página
st.set_page_config(page_title="CRM de Leads", page_icon="📋", layout="wide")


# Inicialização do Banco de Dados SQLite
def init_db():
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT NOT NULL,
            status TEXT NOT NULL,
            tipo_acao TEXT NOT NULL,
            observacoes TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


# Funções de manipulação de dados
def adicionar_lead(nome, telefone, status, tipo_acao, observacoes):
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO leads (nome, telefone, status, tipo_acao, observacoes)
        VALUES (?, ?, ?, ?, ?)
    """,
        (nome, telefone, status, tipo_acao, observacoes),
    )
    conn.commit()
    conn.close()


def carregar_leads():
    conn = sqlite3.connect("leads.db")
    df = pd.read_sql_query(
        "SELECT id, nome, telefone, status, tipo_acao, observacoes FROM leads",
        conn,
    )
    conn.close()
    return df


def atualizar_lead(id_lead, status, observacoes):
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE leads 
        SET status = ?, observacoes = ?
        WHERE id = ?
    """,
        (status, observacoes, id_lead),
    )
    conn.commit()
    conn.close()


# Interface Principal
st.title("📋 Gerenciador de Leads")

menu = ["Cadastrar Lead", "Visualizar e Atualizar"]
escolha = st.sidebar.selectbox("Navegação", menu)

if escolha == "Cadastrar Lead":
    st.subheader("Novo Lead")

    with st.form("form_lead", clear_on_submit=True):
        nome = st.text_input("Nome do Lead")
        telefone = st.text_input("Telefone / WhatsApp")
        status = st.selectbox(
            "Status Atual",
            [
                "Ainda não contatei",
                "Contato Realizado",
                "Aguardando Retorno",
                "Fechado",
            ],
        )
        tipo_acao = st.selectbox(
            "Tipo de Ação Necessária",
            ["Contato Ativo Pendente", "Receptivo / Atendimento"],
        )
        observacoes = st.text_area("Observações")

        submetido = st.form_submit_button("Salvar Lead")

        if submetido:
            if nome and telefone:
                adicionar_lead(nome, telefone, status, tipo_acao, observacoes)
                st.success(f"Lead **{nome}** cadastrado com sucesso!")
            else:
                st.warning("Preencha pelo menos Nome e Telefone.")

elif escolha == "Visualizar e Atualizar":
    st.subheader("Base de Leads")

    df_leads = carregar_leads()

    if not df_leads.empty:
        # Filtro rápido por status
        filtro_status = st.multiselect(
            "Filtrar por Status",
            options=df_leads["status"].unique(),
            default=df_leads["status"].unique(),
        )
        df_filtrado = df_leads[df_leads["status"].isin(filtro_status)]

        st.dataframe(df_filtrado, use_container_width=True)

        st.divider()
        st.subheader("Atualizar Informações de um Lead")

        col1, col2 = st.columns(2)

        with col1:
            lead_id = st.selectbox(
                "Selecione o Lead (por ID/Nome)",
                options=df_leads["id"],
                format_func=lambda x: f"ID {x} - {df_leads[df_leads['id'] == x]['nome'].values[0]}",
            )

            # Preencher com os dados atuais do lead selecionado
            dados_atuais = df_leads[df_leads["id"] == lead_id].iloc[0]

        with col2:
            novo_status = st.selectbox(
                "Novo Status",
                [
                    "Ainda não contatei",
                    "Contato Realizado",
                    "Aguardando Retorno",
                    "Fechado",
                ],
                index=[
                    "Ainda não contatei",
                    "Contato Realizado",
                    "Aguardando Retorno",
                    "Fechado",
                ].index(dados_atuais["status"]),
            )
            novas_obs = st.text_area(
                "Editar Observações", value=dados_atuais["observacoes"]
            )

            if st.button("Atualizar Lead"):
                atualizar_lead(lead_id, novo_status, novas_obs)
                st.success("Lead atualizado!")
                st.rerun()
    else:
        st.info("Nenhum lead cadastrado ainda.")