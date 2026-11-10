# =============================================================================
# OBSERVATORIO INTEGRADO DE INDICADORES SOCIOECONÓMICOS DE COLOMBIA
# Aplicación Streamlit – Fase 4
# =============================================================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# -----------------------------------------------------------------------------
# Configuración de página
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Observatorio Socioeconómico Colombia",
    page_icon="🇨🇴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos visuales
st.markdown("""
<style>
    .main-header { font-size: 1.9rem; font-weight: 700; color: #1a365d; margin-bottom: 0.25rem; }
    .sub-header { font-size: 1.0rem; color: #4a5568; margin-bottom: 1.5rem; }
    .metric-card { background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem; }
    .stMetric { background: #f7fafc; padding: 0.75rem; border-radius: 8px; }
    div[data-testid="stSidebar"] { background: #f8fafc; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Carga de datos (cacheada)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner="Cargando panel de indicadores...")
def cargar_datos():
    base = Path("data")
    candidatos = [
        base / "panel_observatorio_fase2.parquet",
        Path("panel_observatorio_fase2.parquet"),
    ]
    panel_path = next((p for p in candidatos if p.exists()), None)
    if panel_path is None:
        st.error("No se encontró `panel_observatorio_fase2.parquet`. Colócalo en `/data` o en la raíz del proyecto.")
        st.stop()
    
    panel = pd.read_parquet(panel_path)
    panel["anio"] = pd.to_numeric(panel["anio"], errors="coerce")
    panel["valor"] = pd.to_numeric(panel["valor"], errors="coerce")
    
    cat_path = base / "catalogo_indicadores.csv"
    if not cat_path.exists():
        cat_path = Path("catalogo_indicadores.csv")
    catalogo = pd.read_csv(cat_path) if cat_path.exists() else None
    
    return panel, catalogo

panel, catalogo = cargar_datos()
deptos = panel[panel["departamento_canonico"] != "Total nacional"].copy()

# Listas auxiliares
LISTA_DEPTOS = sorted(deptos["departamento_canonico"].dropna().unique())
LISTA_INDICADORES = sorted(deptos["indicador"].dropna().unique())
ANIOS = sorted(deptos["anio"].dropna().unique())

INDICADORES_SOCIALES = [
    "incidencia_pobreza_monetaria", "IPM", "coeficiente_gini",
    "Tasa de Desocupación (TD)", "Tasa de Subocupación (TS)",
]

def serie_ultimo(df, indicador, desag="Total"):
    sub = df[(df["indicador"] == indicador) & (df["desagregacion"] == desag)].dropna(subset=["valor"])
    if sub.empty:
        return None, None
    anio = sub["anio"].max()
    return sub[sub["anio"] == anio].copy(), int(anio)

def filtrar(df, indicador=None, anio=None, depto=None, desag="Total"):
    out = df.copy()
    if indicador:
        out = out[out["indicador"] == indicador]
    if anio is not None:
        out = out[out["anio"] == anio]
    if depto:
        out = out[out["departamento_canonico"] == depto]
    if desag:
        out = out[out["desagregacion"] == desag]
    return out.dropna(subset=["valor"])

# -----------------------------------------------------------------------------
# Sidebar – navegación
# -----------------------------------------------------------------------------
st.sidebar.markdown("## 🇨🇴 Observatorio Colombia")
st.sidebar.caption("Indicadores socioeconómicos departamentales")
pagina = st.sidebar.radio(
    "Navegación",
    [
        "Inicio",
        "Explorador de indicadores",
        "Rankings territoriales",
        "Evolución temporal",
        "Comparar departamentos",
        "Correlaciones",
        "Ficha departamental",
        "Brecha urbana–rural (IPM)",
        "Metodología y fuentes",
    ],
)
st.sidebar.markdown("---")
st.sidebar.caption("Datos: DANE · CPC · Panel construido en Fases 1–3")
st.sidebar.caption("Cobertura aproximada 2005–2026 (varía por indicador)")

# =============================================================================
# PÁGINAS DE LA APLICACIÓN
# =============================================================================
if pagina == "Inicio":
    st.markdown('<p class="main-header">Observatorio Integrado de Indicadores Socioeconómicos de Colombia</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Panel departamental · Fuentes oficiales · Exploración interactiva</p>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Observaciones", f"{len(panel):,}")
    c2.metric("Indicadores", panel["indicador"].nunique())
    c3.metric("Territorios", panel["departamento_canonico"].nunique())
    c4.metric("Rango temporal", f"{int(panel['anio'].min())} – {int(panel['anio'].max())}")
    
    st.markdown("### ¿Qué puedes hacer aquí?")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""- Explorar cualquier indicador por año y departamento  
- Ver **rankings** (mejores / peores)  
- Seguir la **evolución temporal**  
- Comparar hasta 6 departamentos""")
    with col_b:
        st.markdown("""- Revisar **correlaciones** ecológicas  
- Consultar la **ficha** de un departamento  
- Analizar la **brecha rural–urbana** del IPM  
- Leer notas metodológicas y limitaciones""")
        
    st.info(
        "**Nota:** Las correlaciones son a nivel departamental (ecológicas). "
        "Pobreza monetaria y Gini corresponden a 2021–2025 y no son empalmables con series anteriores. "
        "El GEIH no cubre todos los departamentos."
    )
    
    if catalogo is not None:
        st.markdown("### Catálogo de indicadores")
        mostrar = catalogo.copy()
        if "descripcion" in mostrar.columns:
            cols = ["indicador", "descripcion", "unidad", "fuente", "anio_min", "anio_max", "n_territorios"]
            cols = [c for c in cols if c in mostrar.columns]
            st.dataframe(mostrar[cols], use_container_width=True, hide_index=True)
        else:
            st.dataframe(mostrar, use_container_width=True, hide_index=True)

elif pagina == "Explorador de indicadores":
    st.markdown("## Explorador de indicadores")
    c1, c2, c3 = st.columns(3)
    with c1:
        ind = st.selectbox("Indicador", LISTA_INDICADORES, index=LISTA_INDICADORES.index("IPM") if "IPM" in LISTA_INDICADORES else 0)
    with c2:
        anios_ind = sorted(deptos.loc[deptos["indicador"] == ind, "anio"].dropna().unique())
        anio = st.selectbox("Año", anios_ind, index=len(anios_ind) - 1)
    with c3:
        desags = sorted(deptos.loc[deptos["indicador"] == ind, "desagregacion"].dropna().unique())
        desag = st.selectbox("Desagregación", desags, index=0)
        
    data = filtrar(deptos, indicador=ind, anio=anio, desag=desag)
    if data.empty:
        st.warning("No hay datos para esa combinación.")
    else:
        unidad = data["unidad"].iloc[0]
        fuente = data["fuente"].iloc[0]
        st.caption(f"Unidad: **{unidad}** · Fuente: **{fuente}** · n = {len(data)}")
        fig = px.bar(
            data.sort_values("valor", ascending=True),
            x="valor",
            y="departamento_canonico",
            orientation="h",
            labels={"valor": unidad, "departamento_canonico": ""},
            title=f"{ind} — {int(anio)} ({desag})",
            color="valor",
            color_continuous_scale="Teal",
        )
        fig.update_layout(height=max(420, len(data) * 18), showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("Ver tabla"):
            st.dataframe(
                data[["departamento_canonico", "codigo_divipola", "anio", "valor", "unidad", "marca_calidad"]]
                .sort_values("valor", ascending=False),
                use_container_width=True,
                hide_index=True,
            )

elif pagina == "Rankings territoriales":
    st.markdown("## Rankings territoriales")
    c1, c2, c3 = st.columns(3)
    with c1:
        ind = st.selectbox("Indicador", LISTA_INDICADORES, key="rank_ind")
    with c2:
        anios_ind = sorted(deptos.loc[deptos["indicador"] == ind, "anio"].dropna().unique())
        anio = st.selectbox("Año", anios_ind, index=len(anios_ind) - 1, key="rank_anio")
    with c3:
        orden = st.radio("Orden", ["Mayor a menor", "Menor a mayor"], horizontal=True)
        
    data = filtrar(deptos, indicador=ind, anio=anio, desag="Total")
    if data.empty:
        data = filtrar(deptos, indicador=ind, anio=anio, desag=None)
        data = data[data["desagregacion"] == data["desagregacion"].iloc[0]] if not data.empty else data
    if data.empty:
        st.warning("Sin datos.")
    else:
        asc = orden == "Menor a mayor"
        data = data.sort_values("valor", ascending=asc).reset_index(drop=True)
        data["puesto"] = range(1, len(data) + 1)
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("#### Top 10")
            st.dataframe(data.head(10)[["puesto", "departamento_canonico", "valor"]], hide_index=True, use_container_width=True)
        with col_r:
            st.markdown("#### Últimos 10")
            st.dataframe(data.tail(10)[["puesto", "departamento_canonico", "valor"]], hide_index=True, use_container_width=True)
        fig = px.bar(
            data,
            x="valor",
            y="departamento_canonico",
            orientation="h",
            color="valor",
            color_continuous_scale="RdYlGn_r" if ind in INDICADORES_SOCIALES else "Blues",
            title=f"Ranking — {ind} ({int(anio)})",
        )
        fig.update_layout(height=max(420, len(data) * 16), coloraxis_showscale=False, yaxis={"categoryorder": "total ascending" if not asc else "total descending"})
        st.plotly_chart(fig, use_container_width=True)

elif pagina == "Evolución temporal":
    st.markdown("## Evolución temporal")
    c1, c2 = st.columns([1, 2])
    with c1:
        ind = st.selectbox("Indicador", LISTA_INDICADORES, key="evo_ind")
        desags = sorted(deptos.loc[deptos["indicador"] == ind, "desagregacion"].dropna().unique())
        desag = st.selectbox("Desagregación", desags, key="evo_desag")
        default_deptos = [d for d in ["Bogotá D.C.", "Antioquia", "Valle del Cauca", "Chocó", "La Guajira"] if d in LISTA_DEPTOS]
        sel_deptos = st.multiselect("Departamentos", LISTA_DEPTOS, default=default_deptos)
    with c2:
        if not sel_deptos:
            st.info("Selecciona al menos un departamento.")
        else:
            sub = deptos[
                (deptos["indicador"] == ind)
                & (deptos["desagregacion"] == desag)
                & (deptos["departamento_canonico"].isin(sel_deptos))
            ].dropna(subset=["valor"])
            fig = px.line(
                sub,
                x="anio",
                y="valor",
                color="departamento_canonico",
                markers=True,
                labels={"valor": sub["unidad"].iloc[0] if len(sub) else "", "anio": "Año"},
                title=f"{ind} — {desag}",
            )
            fig.update_layout(legend_title_text="Departamento", height=480)
            st.plotly_chart(fig, use_container_width=True)

elif pagina == "Comparar departamentos":
    st.markdown("## Comparar departamentos")
    anio = st.selectbox("Año de comparación", ANIOS, index=len(ANIOS) - 1, key="cmp_anio")
    sel = st.multiselect("Departamentos (máx. 6)", LISTA_DEPTOS, default=LISTA_DEPTOS[:3], max_selections=6)
    inds = st.multiselect(
        "Indicadores",
        LISTA_INDICADORES,
        default=[i for i in ["PIB_per_capita", "IDC", "IPM", "incidencia_pobreza_monetaria", "Tasa de Desocupación (TD)"] if i in LISTA_INDICADORES],
    )
    if sel and inds:
        sub = deptos[
            (deptos["anio"] == anio)
            & (deptos["departamento_canonico"].isin(sel))
            & (deptos["indicador"].isin(inds))
            & (deptos["desagregacion"] == "Total")
        ].dropna(subset=["valor"])
        wide = sub.pivot_table(index="departamento_canonico", columns="indicador", values="valor")
        st.dataframe(wide.style.format("{:.2f}"), use_container_width=True)
        if len(inds) >= 3 and len(sel) >= 2:
            norm = wide.copy()
            for c in norm.columns:
                rng = norm[c].max() - norm[c].min()
                norm[c] = (norm[c] - norm[c].min()) / rng if rng > 0 else 0.5
                if c in INDICADORES_SOCIALES:
                    norm[c] = 1 - norm[c]
            fig = go.Figure()
            for dep in norm.index:
                fig.add_trace(go.Scatterpolar(
                    r=norm.loc[dep].values.tolist() + [norm.loc[dep].values[0]],
                    theta=norm.columns.tolist() + [norm.columns[0]],
                    name=dep,
                    fill="toself",
                    opacity=0.6,
                ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                title=f"Perfil comparado (normalizado) — {int(anio)}",
                height=520,
            )
            st.plotly_chart(fig, use_container_width=True)

elif pagina == "Correlaciones":
    st.markdown("## Correlaciones departamentales")
    anio = st.selectbox("Año", ANIOS, index=min(len(ANIOS) - 1, ANIOS.index(2023) if 2023 in ANIOS else len(ANIOS) - 1))
    inds = st.multiselect(
        "Indicadores a correlacionar",
        LISTA_INDICADORES,
        default=[i for i in ["PIB_per_capita", "IDC", "IPM", "incidencia_pobreza_monetaria", "coeficiente_gini", "Tasa de Desocupación (TD)"] if i in LISTA_INDICADORES],
    )
    sub = deptos[(deptos["anio"] == anio) & (deptos["desagregacion"] == "Total") & (deptos["indicador"].isin(inds))]
    wide = sub.pivot_table(index="departamento_canonico", columns="indicador", values="valor")
    if wide.shape[1] < 2:
        st.warning("Selecciona al menos dos indicadores con datos en ese año.")
    else:
        corr = wide.corr()
        fig = px.imshow(
            corr,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title=f"Correlación de Pearson — {int(anio)}",
            aspect="auto",
        )
        fig.update_layout(height=520)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("### Dispersión")
        c1, c2 = st.columns(2)
        with c1:
            x = st.selectbox("Eje X", inds, key="sc_x")
        with c2:
            y = st.selectbox("Eje Y", [i for i in inds if i != x] or inds, key="sc_y")
        if x in wide.columns and y in wide.columns:
            tmp = wide[[x, y]].dropna().reset_index()
            fig2 = px.scatter(
                tmp,
                x=x,
                y=y,
                text="departamento_canonico",
                trendline="ols",
                title=f"{x} vs {y} ({int(anio)})",
            )
            fig2.update_traces(textposition="top center", textfont_size=9)
            st.plotly_chart(fig2, use_container_width=True)

elif pagina == "Ficha departamental":
    st.markdown("## Ficha departamental")
    depto = st.selectbox("Departamento", LISTA_DEPTOS)
    sub = deptos[deptos["departamento_canonico"] == depto].dropna(subset=["valor"])
    codigo = sub["codigo_divipola"].dropna().iloc[0] if sub["codigo_divipola"].notna().any() else "—"
    st.markdown(f"### {depto}  ·  DIVIPOLA `{codigo}`")
    claves = [i for i in [
        "PIB_per_capita", "IDC", "IPM", "incidencia_pobreza_monetaria",
        "coeficiente_gini", "Tasa de Desocupación (TD)", "Tasa de Ocupación (TO)"
    ] if i in LISTA_INDICADORES]
    cols = st.columns(min(4, len(claves)))
    for i, ind in enumerate(claves):
        s, anio = serie_ultimo(sub, ind)
        if s is not None and len(s):
            val = s["valor"].iloc[0]
            unidad = s["unidad"].iloc[0]
            cols[i % len(cols)].metric(f"{ind} ({anio})", f"{val:,.2f}", help=unidad)
    st.markdown("#### Series temporales")
    ind_evo = st.multiselect("Indicadores a graficar", LISTA_INDICADORES, default=claves[:4], key="ficha_evo")
    if ind_evo:
        splot = sub[(sub["indicador"].isin(ind_evo)) & (sub["desagregacion"] == "Total")]
        fig = px.line(splot, x="anio", y="valor", color="indicador", markers=True, facet_col="indicador", facet_col_wrap=2)
        fig.update_yaxes(matches=None, showticklabels=True)
        fig.update_layout(height=520, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with st.expander("Tabla completa del departamento"):
        st.dataframe(
            sub[["anio", "indicador", "desagregacion", "valor", "unidad", "fuente", "marca_calidad"]]
            .sort_values(["indicador", "anio"]),
            use_container_width=True,
            hide_index=True,
        )

elif pagina == "Brecha urbana–rural (IPM)":
    st.markdown("## Brecha urbana–rural del IPM")
    ipm = deptos[deptos["indicador"] == "IPM"].dropna(subset=["valor"])
    anios_ipm = sorted(ipm["anio"].unique())
    anio = st.selectbox("Año", anios_ipm, index=len(anios_ipm) - 1)
    piv = ipm[ipm["anio"] == anio].pivot_table(
        index="departamento_canonico",
        columns="desagregacion",
        values="valor",
    )
    if "Cabeceras" in piv.columns and "Centros poblados y rural disperso" in piv.columns:
        piv["brecha"] = piv["Centros poblados y rural disperso"] - piv["Cabeceras"]
        piv = piv.dropna(subset=["brecha"]).sort_values("brecha", ascending=True)
        fig = px.bar(
            piv.reset_index(),
            x="brecha",
            y="departamento_canonico",
            orientation="h",
            color="brecha",
            color_continuous_scale="Oranges",
            labels={"brecha": "Rural − Cabecera (p.p.)", "departamento_canonico": ""},
            title=f"Brecha IPM rural–urbana — {int(anio)}",
        )
        fig.update_layout(height=max(420, len(piv) * 16), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(
            piv[["Cabeceras", "Centros poblados y rural disperso", "brecha"]].round(1),
            use_container_width=True,
        )
    else:
        st.warning("No se encontraron desagregaciones Cabeceras / Rural para ese año.")

elif pagina == "Metodología y fuentes":
    st.markdown("## Metodología y fuentes")
    st.markdown("""### Fuentes
| Familia | Fuente | Periodo aproximado |
|---|---|---|
| PIB / PIB per cápita | DANE – Cuentas nacionales | 2005–2025 |
| IDC | Consejo Privado de Competitividad | 2019–2026 |
| Mercado laboral (GEIH) | DANE – GEIH | 2007–2025 |
| Pobreza monetaria / Gini | DANE – GEIH | 2021–2025 |
| IPM / IPM por sexo | DANE – ENCV | 2018–2025 |

### Limitaciones importantes
- **Pobreza monetaria y Gini (2021–2025)** no son empalmables con series anteriores (cambio de marco muestral CNPV 2018).
- **GEIH** cubre 23 departamentos.
- **Subocupación 2020** no disponible por COVID-19.
- **IPM 2020 y 2021** tienen notas metodológicas específicas.
- **IDC** usa escala propia (CPC).
""")
