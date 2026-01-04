import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generar_propuesta(job: dict) -> str:
    prompt = f"""
Escribí una propuesta REAL, como si fueras un desarrollador humano llamado Constantino.

Reglas IMPORTANTES:
- Firmá SIEMPRE como: Constantino Di Nisio
- NO uses corchetes [] ni placeholders
- NO digas “puedo adaptar la propuesta”
- NO menciones que sos una IA o bot
- NO seas excesivamente formal
- Usá un tono profesional pero natural, argentino neutral
- Que parezca escrita a mano para ese proyecto
- No exageres con tecnicismos si no son necesarios

Proyecto:
Título: {job.get('title')}
Descripción: {job.get('description')}

Estructura sugerida:
- Saludo corto
- Qué entendiste del proyecto (1 párrafo)
- Cómo lo harías (simple y concreto)
- Cierre corto invitando a conversar
- Firma: Constantino Di Nisio
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Sos Constantino Di Nisio, un desarrollador real con experiencia en desarrollo web, "
                    "frontend y backend con un ¿ desarrollo a medida. Escribís propuestas humanas, "
                    "claras y directas, sin sonar a texto generado."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.25
    )

    texto = response.choices[0].message.content.strip()

    # 🔒 Seguro anti-placeholders (por si acaso)
    texto = texto.replace("[", "").replace("]", "")
    texto = texto.replace("Tu nombre", "Constantino Di Nisio")
    texto = texto.replace("tu nombre", "Constantino Di Nisio")

    return texto
