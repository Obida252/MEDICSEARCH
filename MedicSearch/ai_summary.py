import os
import re
from dotenv import load_dotenv
import time
import logging
from mistralai import Mistral

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')

# Cache duration in seconds (10 minutes)
CACHE_DURATION = 600

def generate_medicine_summary(medicine):
    """
    Generate an AI summary of the medicine using Mistral AI
    
    Args:
        medicine (dict): Medicine data
        
    Returns:
        str: AI-generated summary of the medicine
    """
    # Check if API key is available
    if not MISTRAL_API_KEY:
        return "<p>Erreur: Clé API non trouvée. Impossible de générer un résumé.</p>"
    
    # Extract basic information for the summary
    title = medicine.get('title', 'Médicament inconnu')
    substances = medicine.get('medicine_details', {}).get('substances_actives', [])
    forme = medicine.get('medicine_details', {}).get('forme', 'Non spécifié')
    laboratoire = medicine.get('medicine_details', {}).get('laboratoire', 'Non spécifié')
    dosages = medicine.get('medicine_details', {}).get('dosages', [])
    
    # Extract ALL content from sections
    all_sections_text = ""
    
    if 'sections' in medicine:
        for section in medicine['sections']:
            section_title = section.get('title', '')
            all_sections_text += f"\n### {section_title}\n"
            
            # Get content from this section
            if 'content' in section and section['content']:
                for content_item in section['content']:
                    if 'text' in content_item:
                        all_sections_text += content_item['text'] + "\n"
            
            # Get content from subsections
            if 'subsections' in section:
                for subsection in section['subsections']:
                    subsection_title = subsection.get('title', '')
                    all_sections_text += f"\n#### {subsection_title}\n"
                    
                    if 'content' in subsection and subsection['content']:
                        for content_item in subsection['content']:
                            if 'text' in content_item:
                                all_sections_text += content_item['text'] + "\n"
    
    # Limit the total content length to avoid exceeding API limits
    if len(all_sections_text) > 5000:
        all_sections_text = all_sections_text[:5000] + "...[contenu tronqué]"
    
    # Create a prompt for the API
    prompt = f"""
    Génère un résumé concis en français pour le médicament suivant:
    
    Nom: {title}
    Substances actives: {', '.join(substances) if substances else 'Non spécifié'}
    Forme pharmaceutique: {forme}
    Laboratoire: {laboratoire}
    Dosages: {', '.join(str(d) for d in dosages) if dosages else 'Non spécifié'}
    
    Informations détaillées sur le médicament:
    {all_sections_text}
    
    Le résumé doit inclure:
    1. Les utilisations principales de ce médicament
    2. Comment il fonctionne en termes simples
    3. Mention brève des effets secondaires courants le cas échéant
    4. Précautions d'emploi importantes
    
    INSTRUCTIONS DE FORMATAGE IMPORTANTES:
    - Utilise UNIQUEMENT du HTML simple (pas de Markdown)
    - Format: paragraphes avec balises <p> </p>
    - Pour le texte en gras, utilise <strong> </strong>
    - Pour l'italique, utilise <em> </em>
    - Mets en gras (<strong>) les noms de maladies, symptômes et termes médicaux importants
    - Mets également en gras les précautions d'emploi cruciales
    - Maximum 3-4 paragraphes
    - Ton: Informatif et accessible, adapté à un large public
    - N'UTILISE PAS de balises de code comme ```html au début ou à la fin
    """
    
    try:
        # Initialize Mistral client
        client = Mistral(api_key=MISTRAL_API_KEY)
        
        # Make the API request using the Mistral client - using the exact format as our successful test
        chat_response = client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # Extract the generated summary
        summary = chat_response.choices[0].message.content
        
        # Clean up the formatting
        summary = clean_summary_format(summary)
        
        # Ensure the summary has proper HTML formatting
        if not summary.strip().startswith('<p>'):
            summary = "<p>" + summary.replace("\n\n", "</p><p>") + "</p>"
            summary = summary.replace("<p></p>", "")
        
        return summary
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du résumé IA: {e}")
        return f"<p>Impossible de générer un résumé pour le moment. Veuillez réessayer plus tard. Erreur: {str(e)}</p>"

def clean_summary_format(summary):
    """Clean up any markdown or code block formatting from the summary"""
    # Remove code block markers with language specifiers (like ```html, ```markdown, etc.)
    summary = re.sub(r'```[a-zA-Z]*', '', summary)
    
    # Remove closing code block markers
    summary = re.sub(r'```', '', summary)
    
    # Remove inline code markers
    summary = re.sub(r'`', '', summary)
    
    # Convert Markdown bold (**text**) to HTML bold (<strong>text</strong>)
    summary = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', summary)
    
    # Convert Markdown italic (*text*) to HTML italic (<em>text</em>)
    summary = re.sub(r'\*([^\*]+)\*', r'<em>\1</em>', summary)
    
    return summary.strip()

def get_or_generate_summary(medicine, db=None):
    """
    Get cached summary from database or generate a new one
    
    Args:
        medicine (dict): Medicine data
        db (pymongo.database.Database, optional): MongoDB database connection
        
    Returns:
        str: AI-generated or cached summary
    """
    medicine_id = medicine.get('_id')
    current_time = int(time.time())
    
    # Check if we already have a summary in the medicine object
    if medicine.get('ai_summary'):
        # If we have summary_timestamp and it's less than 10 minutes old, use it
        if medicine.get('summary_timestamp') and (current_time - medicine.get('summary_timestamp') < CACHE_DURATION):
            return medicine['ai_summary']
    
    # If db is provided, check if summary exists in database and is recent enough
    if db is not None:
        try:
            # Find the medicine and check if it has an ai_summary field
            stored_medicine = db.medicines.find_one(
                {"_id": medicine_id}, 
                {"ai_summary": 1, "summary_timestamp": 1}
            )
            
            if stored_medicine and 'ai_summary' in stored_medicine:
                # Check if summary is less than 10 minutes old
                if 'summary_timestamp' in stored_medicine and (current_time - stored_medicine['summary_timestamp'] < CACHE_DURATION):
                    return stored_medicine['ai_summary']
                    
        except Exception as e:
            logger.error(f"Error checking for cached summary: {e}")
    
    # Generate new summary
    summary = generate_medicine_summary(medicine)
    
    # Save to database if possible with timestamp
    if db is not None:
        try:
            db.medicines.update_one(
                {"_id": medicine_id},
                {"$set": {
                    "ai_summary": summary,
                    "summary_timestamp": current_time
                }}
            )
        except Exception as e:
            logger.error(f"Error saving summary to database: {e}")
    
    return summary
