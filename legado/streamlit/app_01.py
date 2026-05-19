import streamlit as st

st.set_page_config(page_title="Faça Cultura", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background-color: #f5f5f5;
    }

    .block-container {
        max-width: 1180px;
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }

    .topbar {
        display: flex;
        justify-content: center;
        gap: 28px;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 20px;
    }

    .page-card {
        background: white;
        border: 1px solid #d9d9d9;
        border-radius: 10px;
        padding: 24px;
    }

    .title-main {
        color: #f97316;
        font-size: 40px;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 8px;
    }

    .subtitle {
        color: #8b5cf6;
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 12px;
    }

    .chip-row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 22px;
    }

    .chip {
        background: #f3f4f6;
        color: #374151;
        border-radius: 999px;
        padding: 6px 12px;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
    }

    .section-title {
        font-size: 20px;
        font-weight: 800;
        margin-top: 24px;
        margin-bottom: 10px;
        color: #111827;
    }

    .summary-item {
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .deadline { color: #dc2626; }
    .value { color: #f97316; }
    .region { color: #4f46e5; }
    .format { color: #4b5563; }

    .body-text {
        font-size: 15px;
        color: #374151;
        line-height: 1.5;
        margin-bottom: 8px;
    }

    .side-card {
        background: #fff;
        border: 1px solid #bfbfbf;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
    }

    .side-title {
        text-align: center;
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 10px;
    }

    .deadline-big {
        text-align: center;
        color: #dc2626;
        font-size: 19px;
        font-weight: 800;
        line-height: 1.2;
        margin-bottom: 14px;
    }

    .badge-ok {
        background: #dff2e8;
        color: #059669;
        border-radius: 999px;
        padding: 8px 14px;
        display: inline-block;
        font-weight: 700;
        margin: 0 auto 14px auto;
    }

    .center {
        text-align: center;
    }

    .compat-title {
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 8px;
        color: #111827;
    }

    .compat-score {
        font-size: 16px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 8px;
    }

    .progress-wrap {
        width: 100%;
        height: 8px;
        background: #e5e7eb;
        border-radius: 999px;
        overflow: hidden;
        margin-bottom: 14px;
    }

    .progress-fill {
        height: 100%;
        width: 82%;
        background: linear-gradient(90deg, #f97316 0%, #22c55e 100%);
        border-radius: 999px;
    }

    .compat-list {
        font-size: 15px;
        color: #4b5563;
        line-height: 1.45;
        font-weight: 700;
    }

    .alert-title {
        text-align: center;
        color: #dc2626;
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 12px;
    }

    .alert-pill {
        background: #ff2b2b;
        color: white;
        border-radius: 999px;
        padding: 12px 18px;
        text-align: center;
        font-size: 16px;
        font-weight: 800;
        line-height: 1.2;
    }

    .small-space {
        margin-top: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="topbar">
        <div>← Voltar</div>
        <div>Faça Cultura</div>
        <div>Salvar ⭐</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="page-card">', unsafe_allow_html=True)

col1, col2 = st.columns([2.2, 1], gap="large")

with col1:
    st.markdown('<div class="title-main">Programa Internacional de<br>Apoio à Animação 2026</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Subtítulo / inFundo Europeu de Desenvolvimento Audiovisual</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="chip-row">
            <span class="chip">Animação</span>
            <span class="chip">Europa</span>
            <span class="chip">Aberto</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Resumo rápido</div>', unsafe_allow_html=True)
    st.markdown('<div class="summary-item deadline">Prazo: 30 de abril de 2026</div>', unsafe_allow_html=True)
    st.markdown('<div class="summary-item value">Valor: até €20.000</div>', unsafe_allow_html=True)
    st.markdown('<div class="summary-item region">Região: Europa</div>', unsafe_allow_html=True)
    st.markdown('<div class="summary-item format">Formato: Série / curta / piloto</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Sobre o edital</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="body-text">Este edital apoia projetos de animação em desenvolvimento.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Requisitos principais</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="body-text">
        Projeto em fase de desenvolvimento<br>
        Proponente com portfólio<br>
        Inscrição em inglês<br>
        Material visual obrigatório
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Documentos necessários</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="body-text">
        sinopse<br>
        orçamento<br>
        carta de intenção<br>
        teaser / moodboard
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="side-card">
            <div class="side-title">Prazo final</div>
            <div class="deadline-big">30 de abril de 2026</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.button("Inscrever", use_container_width=True)
    with c2:
        st.button("Salvar", use_container_width=True)
    with c3:
        st.button("Abrir", use_container_width=True)

    st.markdown('<div class="small-space"></div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="side-card">
            <div class="side-title">Compatibilidade</div>
            <div class="center"><span class="badge-ok">Recomendado</span></div>
            <div class="compat-score">Alta compatibilidade (82%)</div>
            <div class="progress-wrap"><div class="progress-fill"></div></div>
            <div class="compat-list">
                82% compatível<br>
                ✔ área compatível<br>
                ✔ formato compatível<br>
                ⚠ inscrição em inglês
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="side-card">
            <div class="alert-title">ATENÇÃO</div>
            <div class="alert-pill">Faltam 12 dias para o prazo final.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)
