import streamlit as st
import pandas as pd
import weibull
import numpy as np
from collections import namedtuple

# Ustawienia systemowe
st.set_option('deprecation.showPyplotGlobalUse', False)
st.set_page_config(layout="wide", page_title="Reliability assesment acc. Weibull")
hide_default_format = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden}
        </style>
        """
st.markdown(hide_default_format, unsafe_allow_html=True)

# Analiza Weibulla metodą  Szacowania Liniowego LR - linear estimation
def weibull_LR(data):
    analysis = weibull.Analysis(data, unit='godziny')
    analysis.fit()
    eta = analysis.eta
    beta = analysis.beta
    mean = analysis.mean
    return analysis, eta, beta, mean

# Analiza Weibulla metodą MLE - maximum likelihood method
def weibull_MLE(data):
    analysis = weibull.Analysis(data, unit='godziny')
    analysis.fit(method='mle')
    eta = analysis.eta
    beta = analysis.beta
    mean = analysis.mean
    return analysis, eta, beta, mean

# Liczenie poziomu niezawodności przy zadanym czasie
def reliability_index(t):
    re = np.exp(-(t / eta) ** beta)
    return re

# Ustalenie panelu bocznego
with st.sidebar:
    st.image('logo.jpeg')
    st.markdown(''' --- ''')
    opcje = st.radio(label= '', options= ['Wprowadzenie do analizy Weibulla',
                                          'Ręczne wprowadzenie danych',
                                          'Wgranie pliku'])
    st.markdown(''' --- ''')

if opcje == 'Wprowadzenie do analizy Weibulla':
    st.write('Tu będą informacje na temat analizy Weibulla')
if opcje == 'Ręczne wprowadzenie danych':
    st.subheader('Analiza Weibulla dla danych wprowadzanych ręcznie')
    st.markdown(''' --- ''')
    with st.sidebar:
        st.subheader('Wprowadzenie danych do analizy')

        # Określenie ilości danych jakie mają być wprowadzone do analizy
        ilosc_awarii = st.number_input("Ilość danych do wprowadzenia", min_value=0, step=1)

        # Stworzenie listy danych i pętla pozwalająca na wprowadzenie poszczególnych czasów zdefiniowanych wyżej
        dane = []
        for i in range(ilosc_awarii):
            ttf = st.number_input(f"Wprowadź czas między awariami dla {i + 1} zdarzenia")
            dane.append(ttf)

        # Podanie czasu do analizy
        st.subheader("Okres analizy w godzinach")
        tc = st.number_input(label=" ", min_value=1)

        # Przycisk rozpoczynający wyliczenia
        obliczenia = st.button('Dokonaj analizy')

    # Uruchomienie obliczeń
    if obliczenia:
        if len(dane) < 15:
            analysis, eta, beta, mean = weibull_LR(dane)
        else:
            analysis, eta, beta, mean = weibull_MLE(dane)

        # Wyświetlenie parametrów
        col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)
        with col_a:
            st.latex(r'''\beta''')
        with col_b:
            st.metric(label='', value=f' {beta: .02f}')
        with col_c:
            st.latex(r'''\eta''')
        with col_d:
            st.metric(label='', value=f' {eta: .02f}')
        with col_e:
            st.latex('MTBF')
        with col_f:
            st.metric(label='', value=f'{mean: .02f}')

        # wykresy z dokonanych obliczeń rozkładu Weibulla
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Wykres _prawdopodobieństwa_**")
            fig = analysis.probplot()
            st.pyplot()
        with col2:
            st.markdown("**Funkcja _przeżycia_**")
            fig2 = analysis.sf()
            st.pyplot(fig2)
        with col3:
            st.markdown("**Funkcja _zagrożenia_**")
            fig3 = analysis.hazard()
            st.pyplot(fig3)

        # Podanie planowanego czasu pracy dla którego ma być dokonana analiza
        probability = reliability_index(tc)
        st.subheader(f'Niezawodność przy szacowanym czasie {tc} godzin wynosi: ')
        st.metric(label='', value=f'  {probability * 100: .02f} %')
if opcje == 'Wgranie pliku':
    st.subheader('Analiza Weibulla dla danych wgranych z pliku excel')
    st.markdown(''' --- ''')
    with st.sidebar:
        uploaded_file = st.file_uploader(label= 'Wprowadzenie danych do analizy', type= 'xlsx')
    if uploaded_file:
        try:
            # Wgranie pliku Excela
            df = pd.read_excel(uploaded_file)

            # Wybór kolumn z nazwą maszyny i datami awarii
            st.sidebar.write("Wybierz kolumny gdzie znajdują się następujące informacje: Nazwa/numer maszyny, Data zdarzenia")
            kolumny = df.columns
            obiekt = st.sidebar.selectbox(label="Kolumna z nazwą lub numerem maszyny", options= kolumny, index=0)
            data_zdarzenia = st.sidebar.selectbox(label="Kolumna z datą zdarzenia", options= kolumny, index=0)

            #Stworzenie nowej tabeli danych z wybranymni kolumnami
            df_new = df[[obiekt, data_zdarzenia]].copy()
            df_new[data_zdarzenia] = pd.to_datetime(df_new[data_zdarzenia])
            df_new.sort_values(by= data_zdarzenia, ascending= True, inplace= True)

            # Wybór interesującej maszyny do analizy
            maszyna = st.sidebar.selectbox(label='Wybierz maszynę', options=df_new[obiekt].unique())


            # Zatwierdzenie danych
            #wybor_obiektu = st.button(label='Wyliczenia')

            # Rozpoczęcie wyliczeń
            #if wybor_obiektu:

            # Stworzenie nowej ramki danych do analizy
            maszyna_dane = df_new[df_new[obiekt] == maszyna]
            maszyna_dane.sort_values(by= data_zdarzenia, ascending= True, inplace= True)

            # Dodanie nowej kolumny z wyliczonym czasem upływającym pomiędzi zdarzeniami
            maszyna_dane['godziny'] = maszyna_dane[data_zdarzenia].diff().dt.total_seconds()/3600
            maszyna_dane['dni'] = maszyna_dane['godziny']/24

            col_tab, col_sum = st.columns(2)

            with col_tab:
                st.dataframe(maszyna_dane)
            with col_sum:
                st.metric(label='Ilość danych do analizy', value=f'{len(maszyna_dane["godziny"])}')

            # Wczytanie odpowiedniej kolumny do analizy
            dane = maszyna_dane["godziny"]

            # Usunięcie pustych wartości
            dane = dane.dropna()

            # Uruchomienie obliczeń

            if len(dane) < 15:
                analysis, eta, beta, mean = weibull_LR(dane)
            else:
                analysis, eta, beta, mean = weibull_MLE(dane)

            # Wyświetlenie parametrów
            col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)
            with col_a:
                st.latex(r'''\beta''')
            with col_b:
                st.metric(label='', value=f' {beta: .02f}')
            with col_c:
                st.latex(r'''\eta''')
            with col_d:
                st.metric(label='', value=f' {eta: .02f}')
            with col_e:
                st.latex('MTBF')
            with col_f:
                st.metric(label='', value=f'{mean: .02f}')

            # wykresy z dokonanych obliczeń rozkładu Weibulla
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Wykres _)prawdopodobieństwa_**")
                fig = analysis.probplot()
                st.pyplot()
            with col2:
                st.markdown("**Funkcja _przeżycia_**")
                fig2 = analysis.sf()
                st.pyplot(fig2)
            with col3:
                st.markdown("**Funkcja _zagrożenia_**")
                fig3 = analysis.hazard()
                st.pyplot(fig3)

            # Podanie planowanego czasu pracy dla którego ma być dokonana analiza
            # Określenie szacowanego czasu pracy do wyliczenia niezawodności
            tc = st.sidebar.number_input(label='Planowany czas pracy w godzinach', min_value=0, step=1)
            probability = reliability_index(tc)
            st.subheader(f'Niezawodność przy szacowanym czasie {tc} godzin wynosi: ')
            st.metric(label='', value=f'  {probability * 100: .02f} %')

        except ValueError:
            st.header('Należy wybrać odpowiednie kolumny do analizy oraz obiekt.'
                      ' W przypadku wyboru obiektu z małą ilością danych - analiza nie zostanie wykonana.'
                      ' Wówczas należy wybrać inny obiekt z właściwą ilością danych.')




