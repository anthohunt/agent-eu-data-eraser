"""Every text the agent sends, in each supported language (fr, en).

French is the original template, based on the CNIL model and validated by its first user; English is its
translation, valid for brokers anywhere (the GDPR does not impose a language on the data subject).
The data protection authority named in the emails is the user's own, read from autorites.json.
"""
import json
from pathlib import Path

ICI = Path(__file__).resolve().parent
LANGUES = ("fr", "en")


def autorite(pays):
    """The user's supervisory authority (by ISO country code), from autorites.json; CNIL by default."""
    try:
        for a in json.loads((ICI / "autorites.json").read_text(encoding="utf-8")):
            if a["pays"] == pays:
                return a
    except FileNotFoundError:
        pass
    return {"pays": "FR", "autorite": "Commission nationale de l'informatique et des libertés (CNIL)",
            "autorite_en": "Commission nationale de l'informatique et des libertés (CNIL)",
            "plainte_url": "https://www.cnil.fr/fr/plaintes"}


def langue(ident):
    """Language of the emails and of the report: the user's choice, else French for France, English elsewhere."""
    l = ident.get("langue") or ("fr" if ident.get("pays", "FR") == "FR" else "en")
    return l if l in LANGUES else "en"


def nom_autorite(ident):
    a = autorite(ident.get("pays", "FR"))
    return a["autorite"] if langue(ident) == "fr" else a.get("autorite_en") or a["autorite"]


OBJET = {"fr": "Demande d'effacement de données personnelles (article 17 du RGPD)",
         "en": "Request for erasure of personal data (Article 17 GDPR)"}
PREFIXE_RELANCE = {"fr": "Relance : ", "en": "Follow-up: "}


def liste_donnees(ident, l):
    m = {"fr": ("adresse électronique", "numéro de téléphone", "adresse postale"),
         "en": ("email address", "phone number", "postal address")}[l]
    morceaux = [ident["nom"]]
    morceaux += [f"{m[0]} {x}" for x in ident["mails"]]
    morceaux += [f"{m[1]} {x}" for x in ident.get("telephones", [])]
    morceaux += [f"{m[2]} {x}" for x in ident.get("adresses", [])]
    return ", ".join(morceaux)


def demande(ident, relance_du=None):
    """The request (docs/modele-demande.md). The French text is the validated template: do not change it without
    a new validation."""
    l, aut = langue(ident), nom_autorite(ident)
    if l == "en":
        tete = (f"On {relance_du} I sent you a request for erasure of my personal data, which has not been answered "
                "to date. I am renewing it below.\n\n") if relance_du else ""
        return ("Dear Sir or Madam,\n\n" + tete +
                "Pursuant to Article 17(1) of the General Data Protection Regulation (GDPR), I ask you to erase from "
                f"your files the following personal data concerning me: {liste_donnees(ident, l)}, and any data linked "
                "to them.\n\n"
                "I ask for this erasure because I withdraw any consent I may have given to their processing "
                "(Article 17(1)(b)) and I object to their use for direct marketing (Articles 21(2) and 17(1)(c) GDPR).\n\n"
                "Please also notify this erasure to any recipients to whom you have disclosed them (Article 19 GDPR).\n\n"
                "Please inform me without undue delay and at the latest within one month of receipt of this request "
                f"(Article 12(3) GDPR). Failing a reply within that period, or in case of an incomplete reply, I will "
                f"lodge a complaint with the {aut}.\n\n"
                "Yours faithfully,\n\n"
                f"{ident['nom']}\n")
    tete = (f"Je vous ai adressé le {relance_du} une demande d'effacement de mes données personnelles, "
            "restée sans réponse à ce jour. Je la renouvelle ci-dessous.\n\n") if relance_du else ""
    return ("Madame, Monsieur,\n\n" + tete +
            "En application de l'article 17.1 du Règlement général sur la protection des données (RGPD), "
            "je vous prie d'effacer de vos fichiers les données personnelles suivantes me concernant : "
            f"{liste_donnees(ident, l)}, ainsi que toute donnée qui y est rattachée.\n\n"
            "Je demande que ces informations soient supprimées car je retire tout consentement que j'aurais pu "
            "donner à leur traitement (article 17.1.b) et je m'oppose à leur utilisation à des fins de prospection "
            "(articles 21.2 et 17.1.c du RGPD).\n\n"
            "Vous voudrez bien également notifier cette demande d'effacement aux organismes auxquels vous les auriez "
            "communiquées (article 19 du RGPD).\n\n"
            "Je vous prie de m'informer de ces éléments dans les meilleurs délais et au plus tard dans un délai d'un "
            "mois à compter de la réception de ce courrier (article 12.3 du RGPD). À défaut de réponse de votre part "
            f"dans ce délai ou en cas de réponse incomplète, je saisirai la {aut} d'une réclamation.\n\n"
            "Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.\n\n"
            f"{ident['nom']}\n")


def rappel_canal(ident, depuis):
    """Reply to a broker that points to its web form: email is enough (EDPB Guidelines 01/2022, points 52-53)."""
    l, aut = langue(ident), nom_autorite(ident)
    if l == "en":
        return ("Dear Sir or Madam,\n\n"
                f"You invite me to use your web form. My erasure request of {depuis} was sent to the address you publish "
                "for the exercise of data protection rights: it is valid as it stands.\n\n"
                "The GDPR imposes no form for a request, and the data subject is not required to use the channel you "
                "prefer: a request made through another channel provided by the controller is in general effective and "
                "must be handled (European Data Protection Board, Guidelines 01/2022, points 52 and 53; Article 12(2) GDPR).\n\n"
                "I therefore ask you to handle my request within one month of its receipt (Article 12(3) GDPR). "
                f"Failing that, I will lodge a complaint with the {aut}.\n\n"
                "Yours faithfully,\n\n"
                f"{ident['nom']}\n")
    return ("Madame, Monsieur,\n\n"
            f"Vous m'invitez à passer par votre formulaire. Ma demande d'effacement du {depuis} a été adressée à l'adresse "
            "que vous publiez pour l'exercice des droits : elle est valable telle quelle.\n\n"
            "Le RGPD n'impose aucune forme à une demande, et la personne concernée n'est pas tenue d'utiliser le canal "
            "que vous préférez : une demande faite par un autre canal fourni par l'organisme est en général effective et "
            "doit être traitée (Comité européen de la protection des données, lignes directrices 01/2022, points 52 et 53 ; "
            "article 12.2 du RGPD).\n\n"
            "Je vous remercie donc de traiter ma demande dans le délai d'un mois à compter de sa réception (article 12.3 du "
            f"RGPD). À défaut, je saisirai la {aut} d'une réclamation.\n\n"
            "Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.\n\n"
            f"{ident['nom']}\n")


def refus_info(ident, depuis, piece=False):
    """Reply to a broker that asks for more information about the person (LinkedIn link, phone, employer...) before
    handling the request: refuse, the request already identifies the person (Articles 5(1)(c), 11(2), 12(2), 12(6)
    GDPR), formal notice with the one-month deadline and the complaint. User's decision of 12/11/2026."""
    l, aut = langue(ident), nom_autorite(ident)
    cnil_en = (" The French data protection authority (CNIL) also recalls that exercising one's rights does not, as a "
               "rule, require a copy of an identity document.") if piece else ""
    cnil_fr = (" La CNIL rappelle d'ailleurs que l'exercice des droits ne nécessite pas, en principe, de fournir une "
               "copie de pièce d'identité.") if piece else ""
    if l == "en":
        return ("Dear Sir or Madam,\n\n"
                f"You ask me for additional information before handling my erasure request of {depuis}. I refuse to provide "
                "any further information.\n\n"
                "My request gives my name and the email address you are writing to: that is enough to find, in your own "
                "files, the data you hold about me. Under Article 12(6) GDPR, additional information may only be requested "
                "where there are reasonable doubts about the identity of the person making the request, which you do not "
                f"claim.{cnil_en} Asking for more data than is needed breaches the principle of data minimisation (Article 5(1)(c)) "
                "and your duty to facilitate the exercise of my rights (Article 12(2)). If you consider that you cannot "
                "identify me, Article 11(2) requires you to tell me so, not to collect more data about me.\n\n"
                "I therefore give you formal notice to erase all personal data concerning me (Article 17 GDPR) and to "
                "confirm it in writing within one month of receipt of my request (Article 12(3)). Without a reply within "
                f"that period, I will lodge a complaint with the {aut}, attaching this exchange.\n\n"
                "Yours faithfully,\n\n"
                f"{ident['nom']}\n")
    return ("Madame, Monsieur,\n\n"
            f"Vous me demandez des informations supplémentaires avant de traiter ma demande d'effacement du {depuis}. "
            "Je refuse de vous fournir quelque autre information que ce soit.\n\n"
            "Ma demande indique mon nom et l'adresse électronique à laquelle vous m'écrivez : cela suffit pour retrouver, "
            "dans vos propres fichiers, les données que vous détenez sur moi. Selon l'article 12.6 du RGPD, des "
            "informations supplémentaires ne peuvent être demandées qu'en cas de doutes raisonnables sur l'identité de la "
            f"personne qui fait la demande, ce que vous n'invoquez pas.{cnil_fr} Demander plus de données que nécessaire méconnaît le "
            "principe de minimisation (article 5.1.c) et votre obligation de faciliter l'exercice de mes droits (article "
            "12.2). Si vous estimez ne pas pouvoir m'identifier, l'article 11.2 vous impose de me le dire, et non de "
            "collecter davantage de données sur moi.\n\n"
            "Je vous mets donc en demeure d'effacer toutes les données personnelles me concernant (article 17 du RGPD) et "
            "de me le confirmer par écrit dans le délai d'un mois à compter de la réception de ma demande (article 12.3). "
            f"Sans réponse dans ce délai, je saisirai la {aut} d'une réclamation, en y joignant cet échange.\n\n"
            "Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.\n\n"
            f"{ident['nom']}\n")


def piece(ident):
    if langue(ident) == "en":
        return ("Dear Sir or Madam,\n\n"
                "Following your message, please find attached a copy of my identity document, bearing a watermark that "
                "limits its use, to verify my identity for my erasure request (Article 12(6) GDPR).\n\n"
                "This copy may only be used for that verification: please delete it once the verification is done, and "
                "confirm the erasure of my data within the period set by Article 12(3).\n\n"
                "Yours faithfully,\n\n"
                f"{ident['nom']}\n")
    return ("Madame, Monsieur,\n\n"
            "Suite à votre message, vous trouverez ci-joint une copie de ma pièce d'identité, portant un filigrane qui en "
            "limite l'usage, afin de vérifier mon identité pour ma demande d'effacement (article 12.6 du RGPD).\n\n"
            "Cette copie ne peut servir qu'à cette vérification : je vous demande de la supprimer dès la vérification faite, "
            "et de me confirmer l'effacement de mes données dans le délai prévu à l'article 12.3.\n\n"
            "Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.\n\n"
            f"{ident['nom']}\n")


def plainte(ident, organisme, dates):
    """Complaint text to paste in the authority's online form. Some authorities require their national language."""
    if langue(ident) == "en":
        return ("Subject: no reply to a request for erasure of personal data (Article 17 GDPR)\n\n"
                f"Organisation: {organisme}\n\n"
                "Dear Sir or Madam,\n\n"
                "I asked this organisation to erase my personal data and objected to their use for direct marketing "
                f"(Articles 17 and 21 GDPR):\n{dates}\n\n"
                "I have received no satisfactory reply beyond the one-month period set by Article 12(3) GDPR, despite "
                "my follow-up. I ask you to intervene so that the organisation acts on my request.\n\n"
                "Attachments: copies of my requests and of the exchanges, numbered in chronological order.\n\n"
                f"{ident['nom']}\n")
    return ("Objet : absence de réponse à une demande d'effacement de données personnelles (article 17 du RGPD)\n\n"
            f"Organisme : {organisme}\n\n"
            "Madame, Monsieur,\n\n"
            "J'ai demandé à cet organisme d'effacer mes données personnelles et je me suis opposé à leur utilisation "
            f"à des fins de prospection (articles 17 et 21 du RGPD) :\n{dates}\n\n"
            "Je n'ai reçu aucune réponse satisfaisante, au-delà du délai d'un mois prévu par l'article 12.3 du RGPD, "
            "malgré ma relance. Je vous demande d'intervenir pour que l'organisme donne suite à ma demande.\n\n"
            "Pièces jointes : copies de mes demandes et des échanges, numérotées dans l'ordre chronologique.\n\n"
            f"{ident['nom']}\n")


# Words of the weekly report, per language.
POINT = {
    "fr": {"objet": "[Effacement] Point du {date} : {ok}/{total} effacements confirmés",
           "score": "Effacements confirmés (ou aucune donnée détenue) : {ok} sur {total} (objectif : 80 % sous trois mois).",
           "a_toi": "À toi de voir :", "etat": "État de chaque courtier :", "dernier": "dernier envoi",
           "nouveaux": "Nouveaux courtiers proposés par l'agent de recherche ({n}) :", "source": "source",
           "corrections": "Adresses changées :", "valider": "Réponds « OUI » à ce mail pour tout valider ; sans réponse, rien ne change.",
           "plaintes": "Réclamations prêtes, en pièces jointes : à déposer sur {url} (coller le texte 00, joindre les autres pièces).",
           "jamais": "jamais",
           "spams": "Spams retirés de ta boîte de réception cette semaine ({n}) : rangés dans le dossier « {dossier} », effacés pour de bon {jours} jours après. Pour en garder un, remets-le dans ta boîte de réception."},
    "en": {"objet": "[Eraser] Report of {date}: {ok}/{total} erasures confirmed",
           "score": "Erasures confirmed (or no data held): {ok} of {total} (goal: 80% within three months).",
           "a_toi": "Needs you:", "etat": "Status of each broker:", "dernier": "last sent",
           "nouveaux": "New brokers proposed by the research agent ({n}):", "source": "source",
           "corrections": "Changed addresses:", "valider": "Reply \"YES\" (or « OUI ») to this email to approve them all; without a reply, nothing changes.",
           "plaintes": "Complaints ready, attached: file them at {url} (paste text 00, attach the other files; some authorities require their national language).",
           "jamais": "never",
           "spams": "Spam removed from your inbox this week ({n}): moved to the folder \"{dossier}\", deleted for good {jours} days later. To keep one, move it back to your inbox."}}

# Broker states as shown in the English report (the journal keeps the French names).
ETATS_EN = {"à envoyer": "to send", "envoyé": "sent", "relancé": "followed up", "effacement confirmé": "erasure confirmed",
            "aucune donnée détenue": "no data held", "vérification à faire": "verification needed",
            "pièce demandée": "ID requested", "pièce d'identité envoyée": "ID sent", "renvoie vers son formulaire": "points to its form",
            "accusé de réception": "acknowledged", "refus": "refused", "réponse à lire": "reply to read",
            "réclamation CNIL prête": "complaint ready"}


def etat(ident, e):
    return ETATS_EN.get(e, e) if langue(ident) == "en" else e
