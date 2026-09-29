import random
import streamlit as st
import unicodedata
import importlib.util
from pathlib import Path


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower().strip())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def esta_certa(resposta, pergunta):
    if not resposta:
        return False
    validas = [pergunta["certa"]] + pergunta.get("aceites", [])
    return normalizar(resposta) in [normalizar(v) for v in validas]


def carregar_categorias():
    pasta = Path(__file__).parent / "perguntas"
    categorias = {}
    for ficheiro in sorted(pasta.glob("*.py")):
        spec = importlib.util.spec_from_file_location(ficheiro.stem, ficheiro)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        if modulo.PERGUNTAS:
            categorias[modulo.NOME] = modulo.PERGUNTAS
    return categorias


def preparar_jogo(listas, quantas):
    """Sorteia de forma equilibrada entre categorias e baralha as opções."""
    listas = [random.sample(l, len(l)) for l in listas]
    sorteadas = []
    while len(sorteadas) < quantas and any(listas):
        for l in listas:
            if l and len(sorteadas) < quantas:
                sorteadas.append(l.pop())
    random.shuffle(sorteadas)

    prontas = []
    for p in sorteadas:
        q = dict(p)
        opcoes = list(p["opcoes"])
        random.shuffle(opcoes)
        q["opcoes"] = opcoes
        prontas.append(q)
    return prontas


CATEGORIAS = carregar_categorias()

# Logo (opcional): só aparece se existir o ficheiro logo.png
imagem = Path(__file__).parent / "logo.png"
if imagem.exists():
    st.image(str(imagem), width=150)
st.title("🦉 Quiz aprendizes 🦉")

if not CATEGORIAS:
    st.info("Ainda não há perguntas.")
    st.stop()

if "a_jogar" not in st.session_state:
    st.session_state.a_jogar = False


# ---------- ECRÃ 1: ESCOLHER CATEGORIAS, NÍVEL E QUANTIDADE ----------
if not st.session_state.a_jogar:
    nomes = list(CATEGORIAS)

    geral = st.checkbox("🎯 Geral (todas as categorias)")
    if geral:
        escolhidas = nomes
        st.caption("Perguntas sorteadas de todas as categorias.")
    else:
        escolhidas = st.multiselect(
            "Categorias (podes escolher várias)", nomes, default=nomes[:1]
        )

    nivel = st.radio("Nível", ["Fácil", "Difícil"], horizontal=True)

    total_cat = sum(len(CATEGORIAS[c]) for c in escolhidas)

    if total_cat == 0:
        st.info("Escolhe pelo menos uma categoria.")
    else:
        if total_cat > 1:
            quantas = st.slider("Número de perguntas", 1, total_cat, min(10, total_cat))
        else:
            quantas = 1
            st.caption("Só há 1 pergunta nesta seleção.")

        if st.button("Começar"):
            for k in list(st.session_state.keys()):
                if k.startswith("resp_"):
                    del st.session_state[k]

            st.session_state.perguntas = preparar_jogo(
                [CATEGORIAS[c] for c in escolhidas], quantas
            )
            st.session_state.modo = "Geral" if geral else ", ".join(escolhidas)
            st.session_state.nivel = nivel
            st.session_state.i = 0
            st.session_state.pontos = 0
            st.session_state.revisao = []
            st.session_state.a_jogar = True
            st.rerun()
            
# ---------- ECRÃ 2: UMA PERGUNTA DE CADA VEZ ----------
elif st.session_state.i < len(st.session_state.perguntas):
    perguntas = st.session_state.perguntas
    i = st.session_state.i
    p = perguntas[i]

    st.progress(i / len(perguntas))
    st.caption(f"Pergunta {i + 1} de {len(perguntas)}")
    st.subheader(p["texto"])

    if st.session_state.nivel == "Fácil":
        resposta = st.radio("Escolhe uma opção:", p["opcoes"], index=None, key=f"resp_{i}")
    else:
        resposta = st.text_input("Escreve a resposta:", key=f"resp_{i}")

    if st.button("Responder"):
        if not resposta:
            st.warning("Responde primeiro à pergunta.")
        else:
            certa = esta_certa(resposta, p)
            if certa:
                st.session_state.pontos += 1
            st.session_state.revisao.append((p, resposta, certa))
            st.session_state.i += 1
            st.rerun()


# ---------- ECRÃ 3: RESULTADO ----------
else:
    total = len(st.session_state.perguntas)
    pontos = st.session_state.pontos
    percentagem = round(pontos / total * 100)

    st.header(f"Acertaste {pontos} de {total}")
    st.progress(percentagem / 100)
    st.write(f"**{percentagem}%** de respostas certas")

    if percentagem == 100:
        st.success("Perfeito! Tuno/a de mão cheia 🎉")
        st.balloons()
    elif percentagem >= 60:
        st.info("Muito bem, quase lá!")
    else:
        st.warning("Ainda há ensaios para fazer 😄")

    st.subheader("Revisão")
    for n, (p, r, certa) in enumerate(st.session_state.revisao):
        if certa:
            st.success(f"{n + 1}. {p['texto']}  \n✔ {p['certa']}")
        else:
            st.error(f"{n + 1}. {p['texto']}  \n✘ Respondeste: {r}  \n✔ Certa: {p['certa']}")

    if st.button("Jogar outra vez"):
        st.session_state.a_jogar = False
        st.rerun()
