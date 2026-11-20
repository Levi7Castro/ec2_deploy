"""App de exemplo em Streamlit para testar o deploy na EC2.

Rodar localmente:
    pip install -r requirements.txt
    streamlit run app.py

Na EC2 (expondo para fora):
    streamlit run app.py --server.address 0.0.0.0 --server.port 8501
"""

import os
import platform
import socket
import time
import urllib.request
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="EC2 Deploy Playground", page_icon="🚀", layout="wide")

START_TIME = st.cache_resource(lambda: time.time())()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def ec2_metadata() -> dict:
    """Lê o metadata da instância (IMDSv2). Fora da AWS retorna vazio."""
    base = "http://169.254.169.254/latest"
    try:
        req = urllib.request.Request(
            f"{base}/api/token",
            method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
        )
        token = urllib.request.urlopen(req, timeout=0.5).read().decode()
        info = {}
        for key in ["instance-id", "instance-type", "placement/availability-zone", "public-ipv4"]:
            r = urllib.request.Request(
                f"{base}/meta-data/{key}", headers={"X-aws-ec2-metadata-token": token}
            )
            try:
                info[key] = urllib.request.urlopen(r, timeout=0.5).read().decode()
            except Exception:
                info[key] = "—"
        return info
    except Exception:
        return {}


@st.cache_data
def fake_sales(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    days = pd.date_range(datetime.today() - timedelta(days=179), periods=180, freq="D")
    regions = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
    products = ["Café", "Pão de queijo", "Açaí", "Brigadeiro", "Coxinha"]
    rows = []
    for d in days:
        season = 1 + 0.3 * np.sin(d.day_of_year / 365 * 2 * np.pi)
        weekend = 1.4 if d.day_of_week >= 5 else 1.0
        for r in regions:
            for p in products:
                qty = rng.poisson(20 * season * weekend * (1 + regions.index(r) * 0.15))
                price = {"Café": 6, "Pão de queijo": 5, "Açaí": 18, "Brigadeiro": 3, "Coxinha": 7}[p]
                rows.append((d, r, p, qty, qty * price))
    return pd.DataFrame(rows, columns=["data", "regiao", "produto", "quantidade", "receita"])


def fmt_brl(v: float) -> str:
    return f"R$ {v:,.0f}".replace(",", ".")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🚀 EC2 Playground")
    st.caption("Um app de exemplo pra validar o deploy.")
    name = st.text_input("Como você se chama?", placeholder="Seu nome")
    if name:
        st.success(f"Fala, {name}! 👋")
    st.divider()
    uptime = int(time.time() - START_TIME)
    st.metric("Uptime do app", f"{uptime // 3600}h {(uptime % 3600) // 60}m {uptime % 60}s")
    st.caption(f"Host: `{socket.gethostname()}`")
    if st.button("🎈 Comemorar o deploy"):
        st.balloons()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_dash, tab_lab, tab_server = st.tabs(["📊 Dashboard", "🎲 Laboratório", "🖥️ Servidor"])

# ---- Dashboard ------------------------------------------------------------
with tab_dash:
    st.header("Vendas da Lanchonete Fictícia")
    df = fake_sales()

    c1, c2, c3 = st.columns([2, 2, 1])
    regions = c1.multiselect("Regiões", sorted(df.regiao.unique()), default=sorted(df.regiao.unique()))
    products = c2.multiselect("Produtos", sorted(df.produto.unique()), default=sorted(df.produto.unique()))
    window = c3.selectbox("Período", [30, 90, 180], index=1, format_func=lambda d: f"Últimos {d} dias")

    cutoff = df.data.max() - pd.Timedelta(days=window)
    f = df[df.regiao.isin(regions) & df.produto.isin(products) & (df.data > cutoff)]
    prev = df[
        df.regiao.isin(regions)
        & df.produto.isin(products)
        & (df.data <= cutoff)
        & (df.data > cutoff - pd.Timedelta(days=window))
    ]

    if f.empty:
        st.warning("Nenhum dado com esses filtros. Escolha pelo menos uma região e um produto.")
    else:
        rev, rev_prev = f.receita.sum(), prev.receita.sum()
        qty, qty_prev = f.quantidade.sum(), prev.quantidade.sum()
        delta = lambda a, b: f"{(a - b) / b:+.1%}" if b else None

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Receita", fmt_brl(rev), delta(rev, rev_prev))
        m2.metric("Itens vendidos", f"{qty:,}".replace(",", "."), delta(qty, qty_prev))
        m3.metric("Ticket médio/item", f"R$ {rev / qty:.2f}")
        m4.metric("Campeão", f.groupby("produto").receita.sum().idxmax())

        st.subheader("Receita diária")
        daily = f.pivot_table(index="data", columns="produto", values="receita", aggfunc="sum")
        smooth = st.toggle("Suavizar (média móvel 7 dias)", value=True)
        st.area_chart(daily.rolling(7).mean() if smooth else daily)

        left, right = st.columns(2)
        with left:
            st.subheader("Por região")
            st.bar_chart(f.groupby("regiao").receita.sum().sort_values(ascending=False))
        with right:
            st.subheader("Por dia da semana")
            dow = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
            by_dow = f.groupby(f.data.dt.day_of_week).receita.sum()
            by_dow.index = [dow[i] for i in by_dow.index]
            st.bar_chart(by_dow, sort=False)

        with st.expander("Ver dados brutos"):
            st.dataframe(f.sort_values("data", ascending=False), width="stretch", hide_index=True)
            st.download_button(
                "⬇️ Baixar CSV", f.to_csv(index=False).encode(), "vendas.csv", "text/csv"
            )

# ---- Laboratório ----------------------------------------------------------
with tab_lab:
    st.header("Simulador de Investimento (Monte Carlo)")
    st.caption("Quanto seu dinheiro pode virar? Simula milhares de futuros possíveis.")

    a, b, c = st.columns(3)
    initial = a.number_input("Aporte inicial (R$)", 0, 10_000_000, 10_000, step=1_000)
    monthly = b.number_input("Aporte mensal (R$)", 0, 1_000_000, 500, step=100)
    years = c.slider("Anos", 1, 40, 10)
    d, e, g = st.columns(3)
    ret = d.slider("Retorno anual esperado (%)", 0.0, 25.0, 10.0, 0.5) / 100
    vol = e.slider("Volatilidade anual (%)", 0.0, 40.0, 15.0, 0.5) / 100
    n_sims = g.select_slider("Simulações", [100, 500, 1000, 5000], value=1000)

    months = years * 12
    rng = np.random.default_rng()
    mu, sigma = ret / 12, vol / np.sqrt(12)
    returns = rng.normal(mu, sigma, size=(n_sims, months))
    wealth = np.empty((n_sims, months + 1))
    wealth[:, 0] = initial
    for m in range(months):
        wealth[:, m + 1] = wealth[:, m] * (1 + returns[:, m]) + monthly

    pct = np.percentile(wealth, [10, 50, 90], axis=0).T
    chart = pd.DataFrame(pct, columns=["Pessimista (P10)", "Mediana", "Otimista (P90)"])
    chart.index = chart.index / 12
    chart.index.name = "anos"
    st.line_chart(chart)

    invested = initial + monthly * months
    final = wealth[:, -1]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total investido", fmt_brl(invested))
    k2.metric("Mediana final", fmt_brl(np.median(final)), f"{np.median(final) / invested - 1:+.0%}")
    k3.metric("Cenário ruim (P10)", fmt_brl(np.percentile(final, 10)))
    k4.metric("Chance de perder dinheiro", f"{(final < invested).mean():.1%}")
    st.caption("⚠️ Apenas um brinquedo estatístico — não é recomendação de investimento.")

# ---- Servidor -------------------------------------------------------------
with tab_server:
    st.header("Onde este app está rodando?")
    meta = ec2_metadata()
    if meta:
        st.success("Rodando em uma instância EC2 ✅")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Instance ID", meta.get("instance-id", "—"))
        s2.metric("Tipo", meta.get("instance-type", "—"))
        s3.metric("AZ", meta.get("placement/availability-zone", "—"))
        s4.metric("IP público", meta.get("public-ipv4", "—"))
    else:
        st.info("Não detectei metadata da AWS — provavelmente rodando localmente. 💻")

    st.subheader("Ambiente")
    st.table(
        pd.DataFrame(
            {
                "Item": ["Hostname", "Sistema", "Python", "Streamlit", "CPUs", "Hora do servidor"],
                "Valor": [
                    socket.gethostname(),
                    f"{platform.system()} {platform.release()}",
                    platform.python_version(),
                    st.__version__,
                    str(os.cpu_count()),
                    datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                ],
            }
        ).set_index("Item")
    )
