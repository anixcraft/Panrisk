"""Streamlit UI.  Run from project root:  streamlit run app/streamlit_app.py"""
import os
import sys

import pandas as pd
import streamlit as st

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
from i18n import LANGUAGES, tr  # noqa: E402
from predict import _load, predict_case  # noqa: E402
from report import build_report_html  # noqa: E402

st.set_page_config(page_title="Pancreatic Cancer Risk Screening", page_icon="🧬", layout="centered")
lang = st.sidebar.selectbox("Language / भाषा", list(LANGUAGES), format_func=lambda k: LANGUAGES[k])
t = lambda k, **kw: tr(lang, k, **kw)  # noqa: E731

med = _load()["train_medians"]
st.title(t("title"))
st.caption(t("subtitle"))
st.error(t("disclaimer"))

st.subheader(t("inputs"))
c1, c2 = st.columns(2)
age = c1.number_input(t("age"), 18, 110, int(med["age"]))
sex = c2.radio(t("sex"), ["F", "M"], format_func=lambda s: t(f"sex_{s}"), horizontal=True)
creat = c1.number_input(t("creatinine"), 0.0, 20.0, float(round(med["creatinine"], 2)), step=0.05)
lyve1 = c2.number_input(t("LYVE1"), 0.0, 1000.0, float(round(med["LYVE1"], 2)), step=0.1)
reg1b = c1.number_input(t("REG1B"), 0.0, 5000.0, float(round(med["REG1B"], 2)), step=0.5)
tff1 = c2.number_input(t("TFF1"), 0.0, 5000.0, float(round(med["TFF1"], 2)), step=1.0)
has_ca = c1.checkbox(t("measured_ca"), value=False)
ca = c1.number_input(t("plasma_CA19_9"), 0.0, 100000.0, float(round(med["plasma_CA19_9"], 1)),
                     disabled=not has_ca)
has_reg = c2.checkbox(t("measured_reg"), value=False)
reg1a = c2.number_input(t("REG1A"), 0.0, 5000.0, float(round(med["REG1A"], 1)), disabled=not has_reg)

if st.button(t("predict"), type="primary"):
    inputs = {"age": age, "sex": sex, "creatinine": creat, "LYVE1": lyve1, "REG1B": reg1b,
              "TFF1": tff1, "plasma_CA19_9": ca if has_ca else None,
              "REG1A": reg1a if has_reg else None}
    res = predict_case(inputs, lang=lang)
    st.metric(t("risk_estimate"), f"{res['probability'] * 100:.0f}%")
    box = {"high": st.error, "inconclusive": st.warning, "low": st.success}[res["band"]]
    box(f"**{res['band_label']}**  \n{res['guidance']}")
    for w in res["warnings"]:
        st.warning(w)
    st.subheader(t("factors"))
    for f in res["factors"]:
        st.write("• " + f["sentence"])
    st.bar_chart(pd.DataFrame({"contribution": [f["contribution"] for f in res["factors"]]},
                              index=[f["label"] for f in res["factors"]]))
    st.download_button(t("report"), build_report_html(res, inputs, lang),
                       file_name="risk_report.html", mime="text/html")

with st.expander(t("about")):
    st.write(t("about_text"))
    st.image(os.path.join(ROOT, "reports", "shap_importance.png"))
