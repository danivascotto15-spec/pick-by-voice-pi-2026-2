import speech_recognition as sr
import re
import unicodedata


NUMEROS_UNIDADES = {
    "zero": 0,
    "um": 1,
    "uma": 1,
    "dois": 2,
    "duas": 2,
    "tres": 3,
    "três": 3,
    "quatro": 4,
    "cinco": 5,
    "seis": 6,
    "sete": 7,
    "oito": 8,
    "nove": 9,
    "dez": 10,
    "onze": 11,
    "doze": 12,
    "treze": 13,
    "quatorze": 14,
    "catorze": 14,
    "quinze": 15,
    "dezesseis": 16,
    "dezasseis": 16,
    "dezessete": 17,
    "dezassete": 17,
    "dezoito": 18,
    "dezenove": 19,
    "dezanove": 19,
}

NUMEROS_DEZENAS = {
    "vinte": 20,
    "trinta": 30,
    "quarenta": 40,
    "cinquenta": 50,
    "sessenta": 60,
    "setenta": 70,
    "oitenta": 80,
    "noventa": 90,
}

NUMEROS_CENTENAS = {
    "cem": 100,
    "cento": 100,
    "duzentos": 200,
    "duzentas": 200,
    "trezentos": 300,
    "trezentas": 300,
    "quatrocentos": 400,
    "quatrocentas": 400,
    "quinhentos": 500,
    "quinhentas": 500,
    "seiscentos": 600,
    "seiscentas": 600,
    "setecentos": 700,
    "setecentas": 700,
    "oitocentos": 800,
    "oitocentas": 800,
    "novecentos": 900,
    "novecentas": 900,
}


def numero_por_extenso_para_algarismos(texto):
    """
    Converte números em português por extenso para inteiro.
    Suporta unidades, dezenas, centenas e milhares.
    """
    if not texto:
        return None

    texto = unicodedata.normalize("NFKD", texto.lower().strip())
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    if re.fullmatch(r"\d+", texto):
        return int(texto)

    palavras = texto.split()
    if palavras and all(palavra in NUMEROS_UNIDADES for palavra in palavras):
        digitos = []
        for palavra in palavras:
            valor = NUMEROS_UNIDADES[palavra]
            if valor < 10:
                digitos.append(str(valor))
        if len(digitos) == len(palavras):
            resultado = int("".join(digitos))
            return resultado

    texto = re.sub(r"[^\w]+", " ", texto, flags=re.UNICODE)
    palavras = texto.split()
    if not palavras:
        return None

    total = 0
    subtotal = 0

    for palavra in palavras:
        if palavra == "e":
            continue
        if palavra in NUMEROS_UNIDADES:
            subtotal += NUMEROS_UNIDADES[palavra]
        elif palavra in NUMEROS_DEZENAS:
            subtotal += NUMEROS_DEZENAS[palavra]
        elif palavra in NUMEROS_CENTENAS:
            if palavra == "cem" and subtotal == 0:
                subtotal = 100
            else:
                subtotal += NUMEROS_CENTENAS[palavra]
        elif palavra in ("mil", "milhar", "milhares"):
            if subtotal == 0:
                subtotal = 1
            total += subtotal * 1000
            subtotal = 0
        elif palavra in ("milhao", "milhão", "milhoes", "milhões"):
            if subtotal == 0:
                subtotal = 1
            total += subtotal * 1000000
            subtotal = 0
        else:
            return None

    resultado = total + subtotal
    return resultado if resultado > 0 or "zero" in palavras else None

def ouvir():
    """
    Ativa o microfone, escuta o operador e retorna o texto reconhecido.
    """
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("Ajustando ruído ambiente...")
        # Calibra o microfone para ignorar ruídos de fundo (comum em armazéns)
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        print("Pode falar...")
        audio = recognizer.listen(source)
        
    try:
        # Usa o reconhecedor do Google (requer internet)
        texto = recognizer.recognize_google(audio, language="pt-BR")
        print(f"Operador: {texto}")
        return texto.lower()
        
    except sr.UnknownValueError:
        print("Erro: Não entendi o que foi dito.")
        return None
    except sr.RequestError as e:
        print(f"Erro de conexão com o serviço de reconhecimento: {e}")
        return None

# Teste rápido executando apenas este arquivo
if __name__ == "__main__":
    resultado = ouvir()
    if resultado:
        print(f"Comando recebido: {resultado}")