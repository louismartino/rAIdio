import os
import asyncio
import email
from email.policy import default
from imapclient import IMAPClient
from bs4 import BeautifulSoup
from google import genai
import edge_tts
from dotenv import load_dotenv
from datetime import datetime
import time
from telegram import Bot

# Chargement des configurations
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_ADDR = os.getenv("EMAIL_USER")
EMAIL_PWD = os.getenv("EMAIL_PASS")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

gemini_model = 'gemini-2.5-flash'
client = genai.Client(api_key=GEMINI_KEY)

def fetch_newsletters():
    """Récupère les emails et extrait le texte proprement."""
    print("--- Connexion à la boîte mail... ---")
    newsletters = []
    try:
        with IMAPClient('imap.gmail.com', use_uid=True) as imap_client:
            imap_client.login(EMAIL_ADDR, EMAIL_PWD)
            imap_client.select_folder('Newsletters')
            messages = imap_client.search(['ALL'])
            print(f"Trouvé : {len(messages)} newsletter(s).")

            if not messages: return []

            for msg_id, data in imap_client.fetch(messages, ['RFC822']).items():
                try:
                    raw_email = data[b'RFC822']
                    email_message = email.message_from_bytes(raw_email, policy=default)
                    subject = email_message['subject'] or "Sans sujet"
                    print(f"Traitement de : {subject}")
                    
                    body = ""
                    if email_message.is_multipart():
                        for part in email_message.walk():
                            if part.get_content_type() == "text/html":
                                body = part.get_payload(decode=True).decode(errors='ignore')
                                break
                    else:
                        body = email_message.get_payload(decode=True).decode(errors='ignore')

                    soup = BeautifulSoup(body, 'html.parser')
                    clean_text = soup.get_text(separator=' ', strip=True)
                    newsletters.append(f"Sujet: {subject}\nContenu: {clean_text}")
                except Exception as e:
                    print(f"Erreur sur le mail {msg_id}: {e}")
        return newsletters
    except Exception as e:
        print(f"Erreur Mail : {e}")
        return []

def create_script_with_gemini(raw_text):
    """Transforme le texte brut en script radio via Gemini."""
    print("--- Gemini prépare ton script radio... ---")
    prompt = f"""
    Tu es un présentateur de podcast matinal. Voici les newsletters du jour. 
    Ton but est de transformer ce contenu en un script fluide, agréable et facile à comprendre à l'oreille.

    CONSIGNES STRICTES :
    - NE JAMAIS utiliser de symboles comme '*', '#', '_' ou des listes à puces.
    - Réponds uniquement en TEXTE BRUT (pas de gras).
    - Pour séparer les thèmes, utilise des mots de liaison (ex: "Ensuite", "Par ailleurs", "Passons maintenant à...") et une ponctuation claire.
    - Supprime les publicités, les URLs, les codes promos et les mentions légales.
    - Commence par: 'Salut Louis, voici les newsletters du jour'.
    - Si une newsletter est en anglais, traduis-la en français avant de l'inclure dans le script.
    - Annonce chaque changement en disant: "On passe maintenant à la newsletter [Nom de la newsletter]" ("On commence tout d'abord avec la newsletter [Nom de la newsletter]" pour la première).
    - Repère la pub dans les newsletter grâce aux phrases commme "en partenariat", "collaboration avec..." ou "partenaire du jour" et ne les inclue pas dans le script.
    - Dans l'ordre (s'il y a): Aktionnaire, puis la lettre du Figaro, puis the Next Big Shit (Sh*t c'est Shit), puis les titres du matin du Figaro et enfin The Economist.
    - On ne doit pas retrouver la même information deux fois. Donc on donne toute la newsletter de la première puis les news de la deuxième qui ne sont pas dans la première et ainsi de suite.

    CONTENU BRUT :
    {raw_text}
    """
    try:
        response = client.models.generate_content(model=gemini_model, contents=prompt)
        return response.text
    except Exception as e:
        print(f"Erreur Gemini : {e}")
        return "Désolé, je n'ai pas pu préparer le script ce matin."

async def generate_audio(text):
    print("--- Génération de l'audio et envoi Telegram ---")
    
    # Préparation du fichier
    maintenant = datetime.now()
    date_str = maintenant.strftime("%d_%m_%Y")
    filename = f"newsletters_{date_str}.mp3"
    
    # Sur PythonAnywhere, utilise un chemin simple comme /home/ton-user/newsletters/
    folder = "./newsletters/" 
    if not os.path.exists(folder): os.makedirs(folder)
    file_path = os.path.join(folder, filename)

    # Synthèse vocale
    communicate = edge_tts.Communicate(text, "fr-FR-HenriNeural", rate="+15%")
    await communicate.save(file_path)
    
    # Envoi via Telegram
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        image_path = "news.jpg"
        
        print(f"--- Envoi à Louis via rAIdio... ---")
        with open(file_path, 'rb') as audio:
            thumbnail = open(image_path, 'rb') if os.path.exists(image_path) else None
            
            await bot.send_audio(
                chat_id=TELEGRAM_CHAT_ID,
                audio=audio,
                title=f"Radio Matinale du {date_str}",
                performer="Henri l'IA",
                thumbnail=thumbnail,
                caption=f"Voici la rAIdio du jour !"
            )
        print("--- Succès ! Message envoyé sur ton iPhone. ---")
        
        # Optionnel : supprimer le fichier après envoi pour ne pas encombrer le serveur
        # os.remove(file_path)

    except Exception as e:
        print(f"Erreur Telegram : {e}")

async def main_process():
    contents = fetch_newsletters()
    if not contents:
        print("Aucun message trouvé.")
        return

    full_text = "\n\n".join(contents)
    script = create_script_with_gemini(full_text)
    await generate_audio(script)

if __name__ == "__main__":
    asyncio.run(main_process())
