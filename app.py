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
            observacoes TEXT,
            resultado TEXT DEFAULT 'Pendente'
        )
    """)
    conn.commit()
    conn.close()


init_db()


# Funções de manipulação de dados
def adicionar_lead(
    nome, telefone, status, tipo_acao, observacoes, resultado="Pendente"
):
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO leads (nome, telefone, status, tipo_acao, observacoes, resultado)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (nome, telefone, status, tipo_acao, observacoes, resultado),
    )
    conn.commit()
    conn.close()


def carregar_leads():
    conn = sqlite3.connect("leads.db")
    df = pd.read_sql_query(
        "SELECT id, nome, telefone, status, tipo_acao, resultado, observacoes FROM leads",
        conn,
    )
    conn.close()
    return df


def atualizar_lead(id_lead, status, resultado, observacoes):
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE leads 
        SET status = ?, resultado = ?, observacoes = ?
        WHERE id = ?
    """,
        (status, resultado, observacoes, id_lead),
    )
    conn.commit()
    conn.close()


# --- NOVA FUNÇÃO PARA DELETAR LEAD ---
def deletar_lead(id_lead):
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leads WHERE id = ?", (id_lead,))
    conn.commit()
    conn.close()


# Interface Principal
st.title("📋 Gerenciador de Leads")

menu = ["Cadastrar Lead", "Visualizar e Atualizar", "Importar Planilha"]
escolha = st.sidebar.radio("Navegação", menu)

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
        resultado = st.selectbox(
            "Resultado Inicial",
            ["Pendente", "aprov", "repro"],
        )
        observacoes = st.text_area("Observações")

        submetido = st.form_submit_button("Salvar Lead")

        if submetido:
            if nome and telefone:
                adicionar_lead(
                    nome, telefone, status, tipo_acao, observacoes, resultado
                )
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

        # --- TABELA COM ROLAGEM E LARGURAS AJUSTADAS ---
        st.dataframe(
            df_filtrado,
            use_container_width=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "nome": st.column_config.TextColumn("Nome", width="medium"),
                "telefone": st.column_config.TextColumn("Telefone", width="medium"),
                "status": st.column_config.TextColumn("Status", width="medium"),
                "tipo_acao": st.column_config.TextColumn("Tipo de Ação", width="medium"),
                "resultado": st.column_config.SelectboxColumn(
                    "Resultado",
                    help="Status de aprovação do lead",
                    width="small",
                    options=["aprov", "repro", "Pendente"],
                    required=True,
                ),
                "observacoes": st.column_config.TextColumn("Observações", width="large"),
            },
        )

        # Botão de exportação
        if not df_filtrado.empty:
            csv = df_filtrado.to_csv(index=False, sep=";", encoding="utf-8-sig")
            st.download_button(
                label="📥 Exportar Tabela Atual em CSV",
                data=csv,
                file_name="leads_exportados.csv",
                mime="text/csv",
            )

        st.divider()
        st.subheader("Gerenciar / Editar Lead")

        col1, col2 = st.columns(2)

        with col1:
            lead_id = st.selectbox(
                "Selecione o Lead (por ID/Nome)",
                options=df_leads["id"],
                format_func=lambda x: f"ID {x} - {df_leads[df_leads['id'] == x]['nome'].values[0]}",
            )

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

            resultado_atual = dados_atuais.get("resultado", "Pendente")
            opcoes_resultado = ["Pendente", "aprov", "repro"]
            index_res = (
                opcoes_resultado.index(resultado_atual)
                if resultado_atual in opcoes_resultado
                else 0
            )

            novo_resultado = st.selectbox(
                "Resultado da Avaliação",
                opcoes_resultado,
                index=index_res,
            )

            novas_obs = st.text_area(
                "Editar Observações", value=dados_atuais["observacoes"]
            )

            # --- BOTÕES DE ATUALIZAR E EXCLUIR LADO A LADO ---
            btn_col1, btn_col2 = st.columns(2)

            with btn_col1:
                if st.button("💾 Atualizar Lead", use_container_width=True):
                    atualizar_lead(lead_id, novo_status, novo_resultado, novas_obs)
                    st.success("Lead atualizado com sucesso!")
                    st.rerun()

            with btn_col2:
                if st.button("🗑️ Excluir Lead", type="primary", use_container_width=True):
                    deletar_lead(lead_id)
                    st.warning("Lead excluído com sucesso!")
                    st.rerun()

    else:
        st.info("Nenhum lead cadastrado ainda.")

elif escolha == "Importar Planilha":
    st.subheader("📥 Importar Planilha de Leads / Clientes")
    st.info(
        "Você pode subir a planilha em formato Excel (`.xlsx`) ou CSV. "
        "O sistema reconhece automaticamente as colunas de nome, telefone, etiqueta e observações."
    )

    arquivo_enviado = st.file_uploader(
        "Escolha o arquivo (.xlsx ou .csv)", type=["xlsx", "xls", "csv"]
    )

    if arquivo_enviado is not None:
        try:
            if arquivo_enviado.name.endswith(".csv"):
                try:
                    df_import = pd.read_csv(arquivo_enviado, sep=";")
                except Exception:
                    df_import = pd.read_csv(arquivo_enviado, sep=",")
            else:
                df_import = pd.read_excel(arquivo_enviado)

            st.write("Preview dos dados encontrados na planilha:")
            st.dataframe(df_import.head(10), use_container_width=True)

            if st.button("Confirmar Importação de Todos os Leads"):
                colunas_upper = [str(c).strip().upper() for c in df_import.columns]
                df_import.columns = colunas_upper

                qtd_sucesso = 0

                for _, row in df_import.iterrows():
                    nome = str(row.get("NOME", row.get("NOME DA PESSOA", ""))).strip()
                    telefone = str(
                        row.get("NÚMERO", row.get("TELEFONE", row.get("NUMERO", "")))
                    ).strip()
                    etiqueta = str(row.get("ETIQUETA", row.get("STATUS", ""))).strip().upper()

                    obs_extra = ""
                    for col in df_import.columns:
                        if "OBSERVA" in col or "UNNAMED: 3" in col:
                            val = str(row[col]).strip()
                            if val and val.lower() != "nan" and val.upper() != "OBSERVAÇÃO":
                                obs_extra = val

                    if not nome or nome.upper() in ["NOME", "NAN", "NONE"]:
                        continue

                    if "CLIENTE" in etiqueta:
                        status = "Fechado"
                    elif any(k in etiqueta for k in ["VISITA", "ACOMPANHAMENTO"]):
                        status = "Aguardando Retorno"
                    elif "SEM RESPOSTA" in etiqueta:
                        status = "Contato Realizado"
                    else:
                        status = "Ainda não contatei"

                    if any(k in etiqueta for k in ["NÃO APROVADO", "DESISTIU", "REPROVADO"]):
                        resultado = "repro"
                    elif "CLIENTE" in etiqueta:
                        resultado = "aprov"
                    else:
                        resultado = "Pendente"

                    observacoes = f"Etiqueta: {etiqueta}" if etiqueta and etiqueta != "NAN" else ""
                    if obs_extra:
                        observacoes = f"{observacoes} | Obs: {obs_extra}".strip(" |")

                    adicionar_lead(
                        nome=nome,
                        telefone=telefone,
                        status=status,
                        tipo_acao="Receptivo / Atendimento",
                        observacoes=observacoes,
                        resultado=resultado,
                    )
                    qtd_sucesso += 1

                st.success(f"🎉 Importação concluída! {qtd_sucesso} leads foram adicionados ao CRM.")
                st.rerun()

        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
