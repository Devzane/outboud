import re

def extract_email(text):
    if not text: return None
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    valid_emails = [e for e in emails if not e.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.wixpress.com'))]
    return valid_emails[0] if valid_emails else None

def extract_name(text):
    if not text: return None
    roles = ['owner', 'founder', 'ceo', 'principal', 'president', 'co-founder']
    sentences = re.split(r'(?<=[.!?]) +', text[:15000])
    
    for sentence in sentences:
        s_lower = sentence.lower()
        if any(role in s_lower for role in roles):
            names = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', sentence)
            if names:
                return names[0]
    return None

def extract_summary(text):
    if not text: return None
    sentences = re.split(r'(?<=[.!?]) +', text[:20000])
    summary_sentences = []
    keywords = ['we are', 'our company', 'founded', 'since', 'provide', 'specialize', 'history', 'mission']
    
    for sentence in sentences:
        s_lower = sentence.lower()
        if len(sentence.split()) > 7 and len(sentence) < 200:
            if any(k in s_lower for k in keywords):
                summary_sentences.append(sentence.strip())
                if len(summary_sentences) == 2:
                    break
                    
    if not summary_sentences:
        valid_s = [s for s in sentences if 7 < len(s.split()) < 200]
        summary_sentences = valid_s[:2]
        
    res = ' '.join(summary_sentences)
    return res if res else None
