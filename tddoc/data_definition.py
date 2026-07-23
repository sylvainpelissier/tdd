from datetime import date, time, datetime, timedelta
import re

__doc__ = """

2D-Doc data definitions from
"Specifications techniques 2D-DOC" v 3.3.8 from
France Titres website: https://pub.ants.gouv.fr/2D-DOC/DOCUMENTATION/04_Specifications_Techniques/FranceTitres_DCAT_2D-DOC_V1_04_Specifications_Techniques.pdf.

This only defines perimeter ID 1.

"""

class Format:
    def __init__(self, size_min, size_max):
        self.size_min = size_min
        self.size_max = size_max

    def parse(self, text):
        return text

    def serialize(self, text):
        if self.size_min is not None and len(text) < self.size_min:
            raise ValueError("Too small")
        if self.size_max is not None and len(text) > self.size_max:
            raise ValueError("Too long")
        return text

    def from_spec_test_data(self, text):
        return self.parse(text)
    
class String(Format):
    allowed_format = re.compile(r'.*')
    pad_post = None
    pad_pre = None

    def parse(self, text):
        if self.pad_pre is not None:
            return text.lstrip(self.pad_pre)
        if self.pad_post is not None:
            return text.rstrip(self.pad_post)
        return text

    def serialize(self, text):
        if self.size_min == self.size_max and len(text) != self.size_min:
            if self.pad_pre:
                text = text.rjust(self.size_min, self.pad_pre)
            elif self.pad_post:
                text = text.ljust(self.size_min, self.pad_post)
        if self.size_min is not None and len(text) < self.size_min:
            raise ValueError("Too small")
        if self.size_max is not None and len(text) > self.size_max:
            raise ValueError("Too long")
        return text

class StringAZ(String):
    allowed_format = re.compile(r'[A-Z]*')

class StringAZ09(String):
    allowed_format = re.compile(r'[A-Z0-9]*')

class EORI(String):
    allowed_format = re.compile(r'[A-Z]{2}[0-9]+')
    
class StringAZSp(String):
    allowed_format = re.compile(r'[A-Z ]*')

class StringAZ09Sp(String):
    allowed_format = re.compile(r'[A-Z0-9 ]*')

class StringAZ09SpSl(String):
    allowed_format = re.compile(r'[A-Z0-9 /]*')

class StringAZSpSl(String):
    allowed_format = re.compile(r'[A-Z /]*')

class StringAZ09Dash(String):
    allowed_format = re.compile(r'[A-Z0-9-]*')

class StringAZ09DashSl(String):
    allowed_format = re.compile(r'[A-Z0-9/-]*')

class StringAZ09SpAtDash(String):
    allowed_format = re.compile(r'[A-Z0-9@\' -]*')

class StringAZ09AtDashDot(String):
    allowed_format = re.compile(r'[A-Z0-9@.-]*')

class Numeric(String):
    allowed_format = re.compile(r'[0-9]*')

class Numeric0(String):
    allowed_format = re.compile(r'[0-9]*')
    pad_pre = '0'

class NumericSp(String):
    allowed_format = re.compile(r'[0-9 ]*')

class NumericSl(String):
    allowed_format = re.compile(r'[0-9/]*')

class Hex(String):
    allowed_format = re.compile(r'[0-9A-F -]*')
    pad_pre = '0'

QualName = StringAZ09SpSl
Iso3166_2 = String

class Decimal(String):
    allowed_format = re.compile(r'[0-9,-]*')
    pad_pre = '0'

class PhoneNumber(String):
    allowed_format = re.compile(r'[0-9 ]*')
    pad_pre = ' '
    
class Date4(Format):
    EPOCH = date(2000, 1, 1)

    def parse(self, text):
        v = int(text, 16)
        return self.EPOCH + timedelta(days = v)

    def serialize(self, d):
        return f'{(d - self.EPOCH).days:04X}'

    def from_spec_test_data(self, text):
        return date.fromisoformat(text)
    
class Boolean(Format):
    def parse(self, text):
        return text == "1"

    def serialize(self, v):
        return "1" if v else "0"

class JJMMAAAA(Format):
    def parse(self, text):
        j = int(text[:2], 10)
        m = int(text[2:4], 10)
        a = int(text[4:8], 10)
        return date(a, m, j)

    def serialize(self, d):
        return f'{d.day:02d}{d.month:02d}{d.year:04d}'

    def from_spec_test_data(self, text):
        return date.fromisoformat(text)

class JJMMAAAAHHMM(Format):
    def parse(self, text):
        j = int(text[:2], 10)
        m = int(text[2:4], 10)
        a = int(text[4:8], 10)
        h = int(text[8:10], 10)
        mi = int(text[10:12], 10)
        return datetime(a, m, j, h, mi)

    def serialize(self, d):
        return f'{d.day:02d}{d.month:02d}{d.year:04d}{d.hour:02d}{d.minute:02d}'

    def from_spec_test_data(self, text):
        return datetime.fromisoformat(text)

class HexInt(Format):
    def parse(self, text):
        v = int(text, 16)
        return v

    def serialize(self, v):
        if self.size_min == self.size_max:
            fmt = "%%0%dX" % self.size_min
        else:
            fmt = "%X"
        return fmt % v

    def from_spec_test_data(self, text):
        return int(text)

class Time6(Format):
    def parse(self, text):
        h = int(text[:2], 10)
        m = int(text[2:4], 10)
        s = int(text[4:6], 10)
        return time(h, m, s)

    def serialize(self, d):
        return f'{d.hour:02d}{d.minute:02d}{d.second:02d}'

class HHMM(Format):
    def parse(self, text):
        h = int(text[:2], 10)
        m = int(text[2:4], 10)
        return time(h, m)

    def serialize(self, d):
        return f'{d.hour:02d}{d.minute:02d}'

class StringBase32(Format):
    def parse(self, text):
        from base64 import b32decode
        text = text + '='*((-len(text))%8)
        return b32decode(text)

    def serialize(self, text):
        from base64 import b32encode
        return b32encode(text)

    def from_spec_test_data(self, text):
        return text.encode('ascii', 'ignore')

class Base36(Format):
    def parse(self, text):
        return int(text, 36)

    def serialize(self, text):
        raise NotImplementedError()

class Definition:
    def __init__(self, id, name, size_min, size_max, encoding, description = ""):
        self.id = id
        self.name = name
        self.fixed = size_min if size_min == size_max else None
        self.encoding = encoding(size_min, size_max)
        self.description = description

class Group:
    def __init__(self, name, *definitions):
        self.name = name
        self.definitions = list(definitions)

class Doctype:
    def __init__(self, id, user_type, emitter_type):
        self.id = id
        self.user_type = user_type
        self.emitter_type = emitter_type

class Perimeter:
    def __init__(self, id, *items):
        self.id = id
        self.groups = []
        self.datatypes = {}
        self.doctypes = {}
        for i in items:
            if isinstance(i, Group):
                self.groups.append(i)
                for d in i.definitions:
                    self.datatypes[d.id] = i, d
            elif isinstance(i, Doctype):
                self.doctypes[i.id] = i

    def datatype_get(self, id):
        group, definition = self.datatypes[id]
        return group, definition

    def doctype_get(self, id):
        return self.doctypes[id]

class Definitions:
    def __init__(self, *perimeters):
        self.perimeters = {}
        for p in perimeters:
            self.perimeters[p.id] = p

    def datatype_get(self, perimeter, id):
        try:
            p = self.perimeters[perimeter]
            return p.datatype_get(id)
        except KeyError:
            return Group("Unknown group"), Definition(id, "Unknown "+id, 0, None, String)

    def doctype_get(self, perimeter, id):
        try:
            p = self.perimeters[perimeter]
            return p.doctype_get(id)
        except KeyError:
            return Doctype(id, "Unknown "+id, "Unknown")

c40 = Definitions(
    Perimeter(1,
              Doctype("00", "Justificatif de domicile", "Spécifique"),
              Doctype("01", "Justificatif de domicile", "Facture"),
              Doctype("02", "Justificatif de domicile", "Avis TH"),
              Doctype("03", "Justificatif de domiciliation bancaire", "RIB"),
              Doctype("04", "Justificatif de ressources", "Avis IR"),
              Doctype("05", "Justificatif de domiciliation bancaire", "SEPAmail"),
              Doctype("06", "Justificatif de ressources", "Bulletin de salaire"),
              Doctype("07", "Justificatif d’identité", "Titre d’identité"),
              Doctype("08", "Justificatif d’identité", "MRZ"),
              Doctype("09", "Justificatif fiscal", "Facture étendue"),
              Doctype("10", "Justificatif d’emploi", "Contrat de travail"),
              Doctype("11", "Justificatif de ressources", "Relevé de compte"),
              Doctype("12", "Justificatif juridique/judiciaire", "Acte d’huissier"),
              Doctype("13", "Justificatif d’identité", "Document étranger"),
              Doctype("14", "Justificatif de véhicule", "Attestation DICEM"),
              Doctype("15", "Justificatif d’emploi", "Attestation de décision favorable d’une demande d’autorisation de travail"),
              Doctype("16", "Justificatif d’Asile", "Attestation de Demande d’Asile"),
              Doctype("17", "Justificatif d’Asile", "Attestation de fin de droit à l’allocation pour demandeur d’asile (ADA)"),
              Doctype("18", "Justificatif de ressources", "Avis de Situation Déclarative à l’Impôt sur les Revenus"),
              Doctype("19", "Justificatif fiscal", "Déclarations de dons"),
              Doctype("20", "Justificatif fiscal", "Déclarations de cession de droits sociaux"),
              Doctype("21", "Justificatif fiscal", "Attestation 2041-ASK"),
              Doctype("22", "Justificatif juridique/judiciaire", "Carte Européenne d’Arme à Feu (CEAF)"),
              Doctype("23", "Justificatif de santé", "Certificat de Preuve de Vie"),
              Doctype("24", "Justificatif de ressources", "Avis de Situation Déclarative à l’Impôt sur les Revenus (V2)"),
              Doctype("25", "Justificatif d’emploi", "Autorisation de Travail – AES Métier en Tension"),
              Doctype("26", "Certificat de conformité", "Certificat de conformité sûreté aéroportuaire"),
              Doctype("27", "Justificatif de ressources", "Avis de Situation Déclarative à l’Impôt sur les Revenus (V3)"),
              Doctype("28", "Justificatif de ressources", "Avis d’impôt sur les Revenus (V2)"),
              Doctype("29", "Justificatif d’emploi", "Attestation d’Activité Professionnelle"),
              Doctype("A0", "Justificatif de véhicule", "Certificat de qualité de l’air"),
              Doctype("A1", "Justificatif permis de conduire", "Courrier Permis à points"),
              Doctype("A2", "Justificatif de santé", "Carte Mobilité Inclusion"),
              Doctype("A3", "Justificatif d’activité", "Macaron VTC"),
              Doctype("A4", "Justificatif médical", "Certificat de décès"),
              Doctype("A5", "Justificatif d’activité", "Carte T3P"),
              Doctype("A6", "Justificatif d’activité", "Carte Professionnelle Sapeur-Pompier"),
              Doctype("A7", "Justificatif de véhicule", "Certificat de qualité de l’air (V2)"),
              Doctype("A8", "Certificat d’immatriculation", "Certificat de cession électronique"),
              Doctype("A9", "Justificatif d’activité", "Permis de chasser"),
              Doctype("AA", "Justificatif permis de conduire", "Arrêtés Permis de conduire"),
              Doctype("AB", "Justificatif permis de conduire", "Relevé d’Information Permis de Conduire"),
              Doctype("AC", "Justificatif d’activité", "Licence de conducteur de train"),
              Doctype("AD", "Justificatif permis de conduire", "Certificat de réussite à l’Examen du Permis de Conduire (CEPC)"),
              Doctype("AE", "Justificatif médical", "Certificat de décès V2"),
              Doctype("B0", "Justificatif académique", "Diplôme"),
              Doctype("B1", "Justificatif académique", "Attestation de Versement de la Contribution à la Vie Etudiante"),
              Doctype("B2", "Résultats des tests virologiques", "Test COVID"),
              Doctype("B3", "Résultats des tests virologiques", "Titrage antirabique"),
              Doctype("C1", "Autorisations douanière", "Renseignement Tarifaire Contraignant"),
              Doctype("C2", "Autorisations douanière", "Accord Préalable pour le transfert d’armes"),
              Doctype("C3", "Autorisations douanière", "Permis de transfert d’armes à feu et de munitions"),
              Doctype("C4", "Autorisations douanière", "Autorisation d’importation de matériels de guerre"),
              Doctype("C5", "Autorisations douanière", "Licence d’exportation d’armes à feu"),
              Doctype("C6", "Autorisations douanière", "Agrément de transfert d’armes à feu et de munitions"),
              Doctype("C7", "Autorisations douanière", "Bon de livraison"),
              Doctype("C8", "Autorisations douanière", "Bon de livraison V2"),
              Doctype("C9", "Caducée Infirmier", "Caducée Infirmier"),
              Doctype("L1", "Attestation Vaccinale", "Attestation Vaccinale"),

              Group("Identifiants de données complémentaires du code 2D-DOC",
                    Definition("01", "Identifiant unique du document", 0, None, String),
                    Definition("02", "Catégorie de document", 0, None, String),
                    Definition("03", "Sous-catégorie de document", 0, None, String),
                    Definition("04", "Application de composition", 0, None, String),
                    Definition("05", "Version de l’application de composition", 0, None, String),
                    Definition("06", "Date de l’association entre le document et le code 2D-Doc", 4, 4, Date4),
                    Definition("07", "Heure de l’association entre le document et le code 2D-Doc", 6, 6, Time6),
                    Definition("08", "Date d’expiration du document", 4, 4, Date4),
                    Definition("09", "Nombre de pages du document", 4, 4, Numeric0),
                    Definition("0A", "Editeur du 2D-Doc", 9, 9, Numeric0),
                    Definition("0B", "Intégrateur du 2D-Doc", 9, 9, Numeric0),
                    Definition("0C", "URL du document", 0, None, StringBase32),
                    Definition("0D", "UUID du document", 36, 36, Hex),
              ),

              Group("Identifiants de données propres aux factures",
                    Definition("10", "Ligne 1 de la norme adresse postale du bénéficiaire de la prestation", 0, 38, QualName),
                    Definition("11", "Qualité et/ou titre de la personne bénéficiaire de la prestation", 0, 38, StringAZSp),
                    Definition("12", "Prénom de la personne bénéficiaire de la prestation", 0, 38, StringAZSp),
                    Definition("13", "Nom de la personne bénéficiaire de la prestation", 0, 38, StringAZSp),
                    Definition("14", "Ligne 1 de la norme adresse postale du destinataire de la facture", 0, 38, QualName),
                    Definition("15", "Qualité et/ou titre de la personne destinataire de la facture", 0, 38, StringAZSp),
                    Definition("16", "Prénom de la personne destinataire de la facture", 0, 38, StringAZSp),
                    Definition("17", "Nom de la personne destinataire de la facture", 0, 38, StringAZSp),
                    Definition("18", "Numéro de la facture", 0, None, StringAZ09Sp),
                    Definition("19", "Numéro de client", 0, None, StringAZ09Sp),
                    Definition("1A", "Numéro du contrat", 0, None, StringAZ09Sp),
                    Definition("1B", "Identifiant du souscripteur du contrat", 0, None, StringAZ09Sp),
                    Definition("1C", "Date d‘effet du contrat", 8, 8, JJMMAAAA),
                    Definition("1D", "Montant TTC de la facture", 0, 16, Decimal),
                    Definition("1E", "Numéro de téléphone du bénéficiaire de la prestation", 0, 30, PhoneNumber),
                    Definition("1F", "Numéro de téléphone du destinataire de la facture", 0, 30, PhoneNumber),
                    Definition("1G", "Présence d’un co-bénéficiaire de la prestation non mentionné dans le code", 1, 1, Boolean),
                    Definition("1H", "Présence d’un co-destinataire de la facture non mentionné dans le code", 1, 1, Boolean),
                    Definition("1I", "Ligne 1 de la norme adresse postale du co-bénéficiaire de la prestation", 0, 38, QualName),
                    Definition("1J", "Qualité et/ou titre du co-bénéficiaire de la prestation", 0, 38, StringAZSp),
                    Definition("1K", "Prénom du co-bénéficiaire de la prestation", 0, 38, StringAZSp),
                    Definition("1L", "Nom du co-bénéficiaire de la prestation", 0, 38, StringAZSp),
                    Definition("1M", "Ligne 1 de la norme adresse postale du co-destinataire de la facture", 0, 38, QualName),
                    Definition("1N", "Qualité et/ou titre du co-destinataire de la facture", 0, 38, StringAZSp),
                    Definition("1O", "Prénom du co-destinataire de la facture", 0, 38, StringAZSp),
                    Definition("1P", "Nom du co-destinataire de la facture", 0, 38, StringAZSp),
                    Definition("20", "Ligne 2 de la norme adresse postale du point de service des prestations", 0, 38, StringAZ09Sp),
                    Definition("21", "Ligne 3 de la norme adresse postale du point de service des prestations", 0, 38, StringAZ09Sp),
                    Definition("22", "Ligne 4 de la norme adresse postale du point de service des prestations", 0, 38, StringAZ09Sp),
                    Definition("23", "Ligne 5 de la norme adresse postale du point de service des prestations", 0, 38, StringAZ09Sp),
                    Definition("24", "Code postal ou code cedex du point de service des prestations", 5, 5, Numeric0),
                    Definition("25", "Localité de destination ou libellé cedex du point de service des prestations", 0, 32, StringAZSp),
                    Definition("26", "Pays de service des prestations", 2, 2, Iso3166_2),
                    Definition("27", "Ligne 2 de la norme adresse postale du destinataire de la facture", 0, 38, StringAZ09Sp),
                    Definition("28", "Ligne 3 de la norme adresse postale du destinataire de la facture", 0, 38, StringAZ09Sp),
                    Definition("29", "Ligne 4 de la norme adresse postale du destinataire de la facture", 0, 38, StringAZ09Sp),
                    Definition("2A", "Ligne 5 de la norme adresse postale du destinataire de la facture", 0, 38, StringAZ09Sp),
                    Definition("2B", "Code postal ou code cedex du destinataire de la facture", 5, 5, Numeric0),
                    Definition("2C", "Localité de destination ou libellé cedex du destinataire de la facture", 0, 32, StringAZSp),
                    Definition("2D", "Pays du destinataire de la facture", 2, 2, Iso3166_2),
              ),

              Group("Identifiants de données bancaires",
                    Definition("30", "Qualité Nom et Prénom", 0, 140, QualName),
                    Definition("31", "Code IBAN", 14, 38, StringAZ09),
                    Definition("32", "Code BIC/SWIFT", 8, 11, StringAZ09),
                    Definition("33", "Code BBAN", 0, 30, StringAZ09),
                    Definition("34", "Pays de localisation du compte", 2, 2, Iso3166_2),
                    Definition("35", "Identifiant SEPAmail (QXBAN)", 14, 34, StringAZ09),
                    Definition("36", "Date de début de période", 4, 4, Date4),
                    Definition("37", "Date de fin de période", 4, 4, Date4),
                    Definition("38", "Solde compte début de période", 0, 11, Decimal),
                    Definition("39", "Solde compte fin de période", 0, 11, Decimal),
              ),

              Group("Identifiants de données fiscales",
                    Definition("40", "Numéro fiscal", 13, 13, Numeric0),
                    Definition("41", "Revenu fiscal de référence", 0, 12, Numeric),
                    Definition("42", "Situation du foyer", 0, None, StringAZSp),
                    Definition("43", "Nombre de parts", 0, 5, Decimal),
                    Definition("44", "Référence d’avis d’impôt", 13, 13, StringAZ09Sp),
                    Definition("45", "Année des revenus", 4, 4, Numeric0),
                    Definition("46", "Déclarant 1", 0, 38, StringAZSp),
                    Definition("47", "Numéro fiscal du déclarant 1", 13, 13, Numeric0),
                    Definition("48", "Déclarant 2", 0, 38, StringAZSp),
                    Definition("49", "Numéro fiscal du déclarant 2", 13, 13, Numeric0),
                    Definition("4A", "Date de mise en recouvrement",  8, 8, StringAZ),
                    Definition("4B", "Date de la déclaration",  8, 8, JJMMAAAA),
                    Definition("4C", "Date d’enregistrement",  8, 8, JJMMAAAA),
                    Definition("4D", "Montant du don (en €)",  0, 12, Numeric),
                    Definition("4E", "Montant des droits payés (en €)",  0, 12, Numeric),
                    Definition("4F", "Référence d’enregistrement",  15, 15, StringAZ09),
                    Definition("4G", "Nom du donataire", 0, 38, StringAZ09Dash),
                    Definition("4H", "Nom(s) du(es) donateur(s)", 0, 77, StringAZ09SpSl),
                    Definition("4I", "Montant Taxable (en €)", 0, 12, Numeric),
                    Definition("4J", "Montant de la cession (en €)", 0, 12, Numeric),
                    Definition("4K", "Nom du cessionnaire", 0, 38, StringAZ09SpAtDash),
                    Definition("4L", "Nom du cédant", 0, 38, StringAZ09SpAtDash),
                    Definition("4M", "Taux applicable", 0, 3, Decimal),
                    Definition("4N", "Nom et prénoms du déclarant", 0, 38, StringAZSp),
                    Definition("4O", "Ligne 4 d’adresse du déclarant", 0, 38, StringAZSp),
                    Definition("4P", "Code postal du déclarant", 5, 5, Numeric0),
                    Definition("4Q", "Commune du déclarant", 0, 32, StringAZSp),
                    Definition("4R", "SIP gestionnaire", 0, 30, StringAZSp),
                    Definition("4S", "Millésime", 4, 4, Numeric0),
                    Definition("4T", "Administration cantonale suisse", 0, 30, StringAZSp),
                    Definition("4U", "Dénomination sociale de l’employeur", 0, 38, StringAZ09Sp),
                    Definition("4V", "Impôt sur le revenu net (IR)", 0, 10, Numeric),
                    Definition("4W", "Reste à payer", 0, 10, Numeric),
                    Definition("4X", "Retenue à la source", 0, 10, Numeric),
                    Definition("4Y", "Adresse complète du domicile", 1, 155, StringAZ09SpSl),
                    Definition("4Z", "Prélèvements sociaux nets (PS)", 0, 10, Numeric),
              ),

              Group("Identifiants de données relatives à l’activité professionnelle",
                    Definition("50", "SIRET de l’employeur", 14, 14, Numeric0),
                    Definition("51", "Nombre d’heures travaillées", 6, 6, Decimal),
                    Definition("52", "Cumul du nombre d’heures travaillées", 7, 7, Decimal),
                    Definition("53", "Début de période", 4, 4, Date4),
                    Definition("54", "Fin de période", 4, 4, Date4),
                    Definition("55", "Date de début de contrat", 8, 8, JJMMAAAA),
                    Definition("56", "Date de fin de contrat", 8, 8, JJMMAAAA),
                    Definition("57", "Date de signature du contrat", 8, 8, JJMMAAAA),
                    Definition("58", "Salaire net imposable", 0, 11, Decimal),
                    Definition("59", "Cumul du salaire net imposable", 0, 12, Decimal),
                    Definition("5A", "Salaire brut du mois", 0, 11, Decimal),
                    Definition("5B", "Cumul du salaire brut", 0, 12, Decimal),
                    Definition("5C", "Salaire net", 0, 11, Decimal),
                    Definition("5D", "Ligne 2 de la norme adresse postale de l’employeur", 0, 38, StringAZ09Sp),
                    Definition("5E", "Ligne 3 de la norme adresse postale de l’employeur", 0, 38, StringAZ09Sp),
                    Definition("5F", "Ligne 4 de la norme adresse postale de l’employeur", 0, 38, StringAZ09Sp),
                    Definition("5G", "Ligne 5 de la norme adresse postale de l’employeur", 0, 38, StringAZ09Sp),
                    Definition("5H", "Code postal ou code cedex de l’employeur", 5, 5, Numeric0),
                    Definition("5I", "Localité de destination ou libellé cedex de l’employeur", 0, 32, StringAZSp),
                    Definition("5J", "Pays de l’employeur", 2, 2, Iso3166_2),
                    Definition("5K", "Identifiant Cotisant Prestations Sociales", 0, 50, StringAZ09Sp),
                    Definition("5L", "Numéro de SIRET ou RNA", 9, 14, StringAZ09),
                    Definition("5M", "Dénomination sociale", 0, 38, StringAZ09Sp),
                    Definition("5N", "Numéro de dossier d'autorisation de travail", 21, 21, Numeric0),
                    Definition("5O", "Nom de l'employeur", 0, 38, StringAZSp),
                    Definition("5P", "Prénom de l'employeur", 0, 38, StringAZSp),
                    Definition("5Q", "Nom du déclarant", 0, 38, StringAZSp),
                    Definition("5R", "Prénom du déclarant", 0, 38, StringAZSp),
                    Definition("5S", "Fonction du déclarant", 0, 40, StringAZSp),
                    Definition("5T", "Type de contrat de travail", 1, 1, StringAZ),
                    Definition("5U", "Durée du contrat", 0, 12, StringAZ09Sp),
              ),

              Group("Identifiants de données relatives aux titres d’identité",
                    Definition("60", "Liste des prénoms", 0, 60, StringAZSpSl),
                    Definition("61", "Prénom", 0, 20, StringAZSp),
                    Definition("62", "Nom patronymique", 0, 38, StringAZSp),
                    Definition("63", "Nom d’usage", 0, 38, StringAZSp),
                    Definition("64", "Nom d’épouse/époux", 0, 38, StringAZSp),
                    Definition("65", "Type de pièce d’identité", 2, 2, StringAZSp),
                    Definition("66", "Numéro de la pièce d’identité", 0, 20, StringAZ09),
                    Definition("67", "Nationalité", 2, 2, Iso3166_2),
                    Definition("68", "Genre", 1, 1, StringAZ),
                    Definition("69", "Date de naissance", 8, 8, JJMMAAAA),
                    Definition("6A", "Lieu de naissance", 0, 32, StringAZSp),
                    Definition("6B", "Département du bureau émetteur", 3, 3, StringAZ09),
                    Definition("6C", "Pays de naissance", 2, 2, Iso3166_2),
                    Definition("6D", "Nom et prénom du père", 0, 60, StringAZ09SpSl),
                    Definition("6E", "Nom et prénom de la mère", 0, 60, StringAZ09SpSl),
                    Definition("6F", "Machine Readable Zone (Zone de Lecture Automatique, ZLA)", 0, 90, StringAZ09Sp),
                    Definition("6G", "Nom", 1, 38, StringAZSp),
                    Definition("6H", "Civilité", 1, 10, StringAZSp),
                    Definition("6I", "Pays émetteur", 2, 2, Iso3166_2),
                    Definition("6J", "Type de document étranger", 1, 1, Numeric0),
                    Definition("6K", "Numéro de la demande de document étranger", 19, 19, Numeric0),
                    Definition("6L", "Date de dépôt de la demande", 8, 8, JJMMAAAA),
                    Definition("6M", "Catégorie du titre", 0, 40, StringAZSp),
                    Definition("6N", "Date de début de validité", 8, 8, JJMMAAAA),
                    Definition("6O", "Date de fin de validité", 8, 8, JJMMAAAA),
                    Definition("6P", "Autorisation", 0, 40, StringAZSp),
                    Definition("6Q", "Numéro d’étranger", 0, 10, StringAZ09),
                    Definition("6R", "Numéro de visa", 12, 12, StringAZ09),
                    Definition("6S", "Ligne 2 de l‘adresse postale du domicile", 0, 38, StringAZ09Sp),
                    Definition("6T", "Ligne 3 de l‘adresse postale du domicile", 0, 38, StringAZ09Sp),
                    Definition("6U", "Ligne 4 de l‘adresse postale du domicile", 0, 38, StringAZ09Sp),
                    Definition("6V", "Ligne 5 de l‘adresse postale du domicile", 0, 38, StringAZ09Sp),
                    Definition("6W", "Code postal ou code cedex de l‘adresse postale du domicile", 5, 5, Numeric0),
                    Definition("6X", "Commune de l‘adresse postale du domicile", 0, 32, StringAZSp),
                    Definition("6Y", "Code pays de l‘adresse postale du domicile", 2, 2, Iso3166_2),
                    Definition("6Z", "Numéro d'étranger de l'autorisation de travail", 9, 11, StringAZ09),
              ),

              Group("Identifiants de données relatives aux données de santé",
                    Definition("70", "Date et heure du décès", 12, 12, JJMMAAAAHHMM),
                    Definition("71", "Date et heure du constat de décès", 12, 12, JJMMAAAAHHMM),
                    Definition("72", "Nom du défunt", 1, 38, StringAZSp),
                    Definition("73", "Prénoms du défunt", 0, 60, StringAZSpSl),
                    Definition("74", "Nom de jeune fille du défunt", 0, 38, StringAZSp),
                    Definition("75", "Date de naissance du défunt", 8, 8, JJMMAAAA),
                    Definition("76", "Genre du défunt", 1, 1, StringAZ),
                    Definition("77", "Commune de décès", 0, 45, StringAZSp),
                    Definition("78", "Code postal de la commune de décès", 5, 5, Numeric0),
                    Definition("79", "Adresse du domicile du défunt", 0, 114, StringAZ09Sp),
                    Definition("7A", "Code postal du domicile du défunt", 5, 5, Numeric0),
                    Definition("7B", "Commune du domicile du défunt", 0, 45, StringAZSp),
                    Definition("7C", "Obstacle médico-légal", 1, 1, Boolean),
                    Definition("7D", "Mise en bière", 1, 1, StringAZ),
                    Definition("7E", "Obstacle aux soins de conservation", 1, 1, Boolean),
                    Definition("7F", "Obstacle aux dons du corps", 1, 1, Boolean),
                    Definition("7G", "Recherche de la cause du décès", 1, 1, Boolean),
                    Definition("7H", "Délai de transport du corps", 2, 2, HexInt),
                    Definition("7I", "Prothèse avec pile", 1, 1, Boolean),
                    Definition("7J", "Retrait de la pile de prothèse", 1, 1, Boolean),
                    Definition("7K", "Code NNC", 13, 13, StringAZ09),
                    Definition("7L", "Code Finess de l‘organisme agréé", 9, 9, StringAZ09),
                    Definition("7M", "Identification du médecin", 0, 64, StringAZ09Sp),
                    Definition("7N", "Lieu de validation du certificat de décès", 0, 128, StringAZ09Sp),
                    Definition("7O", "Certificat de décès supplémentaire", 1, 1, Boolean),
                    Definition("7P", "Identifiant du certificat", 16, 16, StringAZ09),
                    Definition("87", "Assuré - Nom patronymique", 0, 63, StringAZSp),
                    Definition("88", "Assuré - Identifiant", 5, 10, Numeric),
                    Definition("89", "Assuré - Email", 1, 64, StringAZ09AtDashDot),
                    Definition("8A", "Assuré - Date de début de campagne", 8, 8, JJMMAAAA),
                    Definition("8B", "Assuré - Identifiant enquête MCE", 5, 10, Numeric),
              ),

              Group("Identifiants relatifs aux activités professionnelles",
                    Definition("80", "Nom", 0, 38, StringAZSp),
                    Definition("81", "Prénoms", 0, 60, StringAZSpSl),
                    Definition("82", "Numéro de carte", 0, 20, StringAZ09Sp),
                    Definition("83", "Organisme de tutelle", 0, 40, StringAZ09Sp),
                    Definition("84", "Profession", 0, 40, StringAZ09Sp),
                    Definition("85", "Numéro de permis de chasser", 17, 17, StringAZ09Dash),
                    Definition("86", "Numéro de licence", 12, 12, StringAZ09),
              ),

              Group("Identifiants relatifs aux données juridiques/judiciaires",
                    Definition("90", "Identité de l‘huissier de justice", 0, 38, StringAZSpSl),
                    Definition("91", "Identité ou raison sociale du demandeur", 0, 38, StringAZSpSl),
                    Definition("92", "Identité ou raison sociale du destinataire", 0, 38, StringAZSpSl),
                    Definition("93", "Identité ou raison sociale de tiers concerné", 0, 38, StringAZSpSl),
                    Definition("94", "Intitulé de l‘acte", 0, 38, StringAZ09Sp),
                    Definition("95", "Numéro de l‘acte", 0, 18, StringAZ09),
                    Definition("96", "Date de signature de l‘acte", 8, 8, JJMMAAAA),
              ),

              Group("Identifiants de données relatives aux véhicules",
                    Definition("A0", "Pays ayant émis l’immatriculation du véhicule", 2, 2, Iso3166_2),
                    Definition("A1", "Immatriculation du véhicule", 0, 17, StringAZ09Dash),
                    Definition("A2", "Marque du véhicule", 0, 17, StringAZ09Sp),
                    Definition("A3", "Nom commercial du véhicule", 0, 17, StringAZ09Sp),
                    Definition("A4", "Numéro de série du véhicule (VIN)", 17, 17, StringAZ09Sp),
                    Definition("A5", "Catégorie du véhicule", 3, 3, StringAZ09Sp),
                    Definition("A6", "Carburant", 2, 2, StringAZ09),
                    Definition("A7", "Taux d’émission de CO2 du véhicule (en g/km)", 3, 3, HexInt),
                    Definition("A8", "Indication de la classe environnementale de réception CE", 0, 12, StringAZ09SpSl),
                    Definition("A9", "Classe d’émission polluante", 3, 3, String),
                    Definition("AA", "Date de première immatriculation du véhicule", 8, 8, JJMMAAAA),
                    Definition("AB", "Type de lettre", 0, 8, StringAZ09),
                    Definition("AC", "N° Dossier", 0, 19, StringAZ09),
                    Definition("AD", "Date Infraction", 4, 4, Date4),
                    Definition("AD", "Date Infraction", 4, 4, Date4),
                    Definition("AE", "Heure de l’infraction", 4, 4, HHMM),
                    Definition("AF", "Nombre de points retirés lors de l’infraction", 1, 1, Base36),
                    Definition("AG", "Solde de points", 1, 1, Base36),
                    Definition("AH", "Numéro de la carte", 0, 30, StringAZ09),
                    Definition("AI", "Date d’expiration initiale", 8, 8, JJMMAAAA),
                    Definition("AJ", "Numéro EVTC", 13, 13, StringAZ09),
                    Definition("AK", "Numéro de macaron", 7, 7, Numeric0),
                    Definition("AL", "Numéro de la carte", 11, 11, StringAZ09),
                    Definition("AM", "Motif de sur-classement", 0, 5, StringAZ09Sp),
                    Definition("AN", "Kilométrage", 8, 8, Numeric0),
                    Definition("AO", "Numéro d’identification", 6, 6, Numeric0),
                    Definition("AP", "Type d’engin", 0, 60, StringAZSp),
                    Definition("AQ", "Numéro de série", 0, 25, StringAZ09),
                    Definition("AR", "Modèle", 0, 35, StringAZ09Sp),
                    Definition("AS", "Couleur dominante", 0, 10, StringAZ),
                    Definition("AT", "Type de propriétaire", 1, 1, Numeric),
                    Definition("AU", "Ligne 2 de l'adresse postale du propriétaire", 0, 38, StringAZ09Sp),
                    Definition("AV", "Ligne 3 de l'adresse postale du propriétaire", 0, 38, StringAZ09Sp),
                    Definition("AW", "Ligne 4 de l'adresse postale du propriétaire", 0, 38, StringAZ09Sp),
                    Definition("AX", "Ligne 5 de l'adresse postale du propriétaire", 0, 38, StringAZ09Sp),
                    Definition("AY", "Code postal ou code cedex de l'adresse postale du propriétaire", 5, 5, Numeric0),
                    Definition("AZ", "Commune de l'adresse postale du propriétaire", 0, 32, StringAZSp),
              ),

              Group("Identifiants de données pour les justificatifs académiques",
                    Definition("B0", "Liste des prénoms", 0, 60, StringAZSpSl),
                    Definition("B1", "Prénom", 0, 20, StringAZSp),
                    Definition("B2", "Nom patronymique", 0, 38, StringAZSp),
                    Definition("B3", "Nom d‘usage", 0, 38, StringAZSp),
                    Definition("B4", "Nom d‘épouse/époux", 0, 38, StringAZSp),
                    Definition("B5", "Nationalité", 2, 2, Iso3166_2),
                    Definition("B6", "Genre", 1, 1, StringAZ),
                    Definition("B7", "Date de naissance", 8, 8, JJMMAAAA),
                    Definition("B8", "Lieu de naissance", 0, 32, StringAZ09Sp),
                    Definition("B9", "Pays de naissance", 2, 2, Iso3166_2),
                    Definition("BA", "Mention obtenue", 1, 1, Numeric),
                    Definition("BB", "Numéro ou code d‘identification de l‘étudiant", 0, 50, StringAZ09Sp),
                    Definition("BC", "Numéro du diplôme", 0, 20, StringAZ09Sp),
                    Definition("BD", "Niveau du diplôme selon la classification CEC", 1, 1, Numeric),
                    Definition("BE", "Crédits ECTS obtenus", 3, 3, Numeric0),
                    Definition("BF", "Année universitaire", 3, 3, HexInt),
                    Definition("BG", "Type de diplôme", 2, 2, StringAZ),
                    Definition("BH", "Domaine", 0, 30, StringAZ09Sp),
                    Definition("BI", "Mention", 0, 30, StringAZ09Sp),
                    Definition("BJ", "Spécialité", 0, 30, StringAZ09Sp),
                    Definition("BK", "Numéro de l‘Attestation de versement de la CVE", 14, 14, StringAZ09Dash),
              ),

              Group("Identifiants de données relatives au certificat de cession électronique",
                    Definition("C0", "Genre du vendeur", 1, 1, StringAZ),
                    Definition("C1", "Nom patronymique du vendeur", 0, 38, StringAZSp),
                    Definition("C2", "Prénom du vendeur", 0, 20, StringAZSp),
                    Definition("C3", "Date et heure de la cession", 12, 12, JJMMAAAAHHMM),
                    Definition("C4", "Date de la signature du vendeur", 8, 8, JJMMAAAA),
                    Definition("C5", "Genre de l’acheteur", 1, 1, StringAZ),
                    Definition("C6", "Nom patronymique de l’acheteur", 0, 38, StringAZSp),
                    Definition("C7", "Prénom de l’acheteur", 0, 20, StringAZSp),
                    Definition("C8", "Ligne 4 de la norme adresse postale du domicile de l’acheteur", 0, 38, StringAZ09Sp),
                    Definition("C9", "Code postal ou code cedex du domicile de l’acheteur", 5, 5, Numeric0),
                    Definition("CA", "Commune du domicile de l’acheteur", 0, 45, StringAZSp),
                    Definition("CB", "N° d’enregistrement", 10, 10, Numeric0),
                    Definition("CC", "Date et heure d‘enregistrement dans le SIV", 12, 12, JJMMAAAAHHMM),
              ),

              Group("Identifiants de données relatives aux autorisations douanières",
                    Definition("D0", "Référence RTC", 17, 17, String),
                    Definition("D1", "Nom du titulaire", 0, 50, String),
                    Definition("D2", "EORI", 0, 20, StringAZ09),
                    Definition("D3", "Date de début de validité", 8, 8, JJMMAAAA),
                    Definition("D4", "Date de fin de validité", 8, 8, JJMMAAAA),
                    Definition("D5", "Code marchandise", 8, 10, String),
                    Definition("D6", "Numéro de décision", 8, 8, Numeric0),
                    Definition("D7", "Date de décision", 8, 8, JJMMAAAA),
                    Definition("D8", "Durée de validité", 2, 2, Numeric0),
                    Definition("D9", "Date de fin de validité de la licence", 8, 8, JJMMAAAA),
                    Definition("DA", "Numéro de licence", 8, 8, Numeric0),
                    Definition("DB", "Nom de l’expéditeur", 0, 50, StringAZSp),
                    Definition("DC", "Prénom de l’expéditeur", 0, 50, StringAZSp),
                    Definition("DD", "Date de naissance de l’expéditeur", 8, 8, JJMMAAAA),
                    Definition("DE", "Raison sociale de l’expéditeur", 0, 50, StringAZ09Sp),
                    Definition("DF", "SIREN de l’expéditeur", 9, 9, Numeric0),
                    Definition("DG", "SIRET de l’expéditeur", 14, 14, Numeric0),
                    Definition("DH", "EORI de l’expéditeur", 0, 20, EORI),
                    Definition("DI", "TIN de l’expéditeur", 4, 30, StringAZ09),
                    Definition("DJ", "Nom de l’exportateur", 0, 50, StringAZSp),
                    Definition("DK", "Prénom de l’exportateur", 0, 50, StringAZSp),
                    Definition("DL", "Date de naissance de l’exportateur", 8, 8, JJMMAAAA),
                    Definition("DM", "Raison sociale de l’exportateur", 0, 50, StringAZ09Sp),
                    Definition("DN", "SIREN de l’exportateur", 9, 9, Numeric0),
                    Definition("DO", "SIRET de l’exportateur", 14, 14, Numeric0),
                    Definition("DP", "EORI de l’exportateur", 0, 20, EORI),
                    Definition("DQ", "Nom du destinataire", 0, 50, StringAZSp),
                    Definition("DR", "Prénom du destinataire", 0, 50, StringAZSp),
                    Definition("DS", "Date de naissance du destinataire", 8, 8, JJMMAAAA),
                    Definition("DT", "Raison sociale du destinataire", 0, 50, StringAZ09Sp),
                    Definition("DU", "SIREN du destinataire", 9, 9, Numeric0),
                    Definition("DV", "SIRET du destinataire", 14, 14, Numeric0),
                    Definition("DW", "EORI du destinataire", 0, 50, EORI),
                    Definition("DX", "TIN du destinataire", 4, 30, StringAZ09),
                    Definition("DY", "Nombre de lignes articles", 3, 3, Numeric0),
                    Definition("DZ", "Numéro du bon de livraison", 0, 10, StringAZ09),
                    Definition("H0", "Commune de l'expéditeur", 0, 38, Numeric0),
                    Definition("H1", "Pays de l'expéditeur", 2, 2, StringAZ),
                    Definition("H2", "Commune du destinataire", 0, 38, StringAZSp),
                    Definition("H3", "Pays du destinataire", 2, 2, StringAZ),
                    Definition("H4", "Date de départ", 8, 8, JJMMAAAA),
                    Definition("H5", "Date prévisionnelle d’arrivée", 8, 8, JJMMAAAA),
                    Definition("H6", "Numéro de plomb", 0, 40, Numeric),
                    Definition("H7", "Codes douaniers", 0, 53, NumericSl),
                    Definition("H8", "Nombre d’emballages articles", 7, 7, Numeric0),
                    Definition("H9", "Poids brut articles", 8, 8, Numeric0),
                    Definition("HA", "Poids net articles", 8, 8, Numeric0),
                    Definition("HB", "Valeur douanière articles", 9, 9, Numeric0),
                    Definition("HC", "But de la livraison", 0, 38, StringAZSp),
                    Definition("HD", "Adresse de l'expéditeur", 0, 38, StringAZSp),
                    Definition("HE", "Code postal et commune de l'expéditeur", 0, 38, StringAZSp),
                    Definition("HF", "Adresse du destinataire", 0, 38, StringAZSp),
                    Definition("HG", "Code postal et commune du destinataire", 0, 38, StringAZSp),
                    Definition("HH", "Numéro d’identification du transport", 0, 20, StringAZ09DashSl),
                    Definition("HI", "Numéro, extension et libellé de voie de l'adresse de résidence", 0, 38, StringAZSp),
                    Definition("HJ", "Code postal de l'adresse de résidence", 5, 5, NumericSp),
                    Definition("HK", "Commune de l'adresse de résidence", 0, 32, StringAZSp),
                    Definition("HL", "Code pays de l'adresse de résidence", 2, 2, StringAZ),
                    Definition("HM", "Numéro de la CEAF", 15, 18, StringAZSp),
                    Definition("HN", "Date et heure d'édition", 12, 12, JJMMAAAAHHMM),
                    Definition("HO", "Date d'expiration", 8, 8, JJMMAAAA),
                    Definition("HP", "Numéro SIA", 12, 12, StringAZSp),
                    Definition("HQ", "Nombre d'armes de catégorie A", 2, 2, Numeric0),
                    Definition("HR", "Nombre d'armes de catégorie B", 2, 2, Numeric0),
                    Definition("HS", "Nombre d'armes de catégorie C", 2, 2, Numeric0),
              ),

              Group("Identifiants de données relatives aux résultats des tests virologiques",
                    Definition("F0", "Liste des prénoms", 0, 38, String),
                    Definition("F1", "Nom patronymique", 0, 60, String),
                    Definition("F2", "Date de naissance", 8, 8, JJMMAAAA),
                    Definition("F3", "Genre", 1, 1, StringAZ),
                    Definition("F4", "Code analyse", 3, 7, StringAZ09),
                    Definition("F5", "Résultat de l’analyse", 1, 1, StringAZ),
                    Definition("F6", "Date et heure du prélèvement", 12, 12, JJMMAAAAHHMM),
              ),

              Group("Identifiants de données relatives à une attestation vaccinale",
                    Definition("L0", "Nom Patronymique du patient", 0, 80, String),
                    Definition("L1", "Liste des prénoms du patient", 0, 80, String),
                    Definition("L2", "Date de naissance du patient", 8, 8, JJMMAAAA),
                    Definition("L3", "Nom de la maladie couverte", 0, 30, String),
                    Definition("L4", "Agent prophylactique", 5, 15, String),
                    Definition("L5", "Nom du vaccin", 5, 30, String),
                    Definition("L6", "Fabricant du vaccin", 5, 30, String),
                    Definition("L7", "Rang du dernier état de vaccination effectué", 1, 1, Numeric0),
                    Definition("L8", "Nombre de doses attendues pour un cycle complet", 1, 1, Numeric0),
                    Definition("L9", "Date du dernier état du cycle de vaccination", 8, 8, JJMMAAAA),
                    Definition("LA", "Etat du cycle de vaccination", 2, 2, StringAZ),
              ),

              Group("Identifiants de données relatives à l’asile",
                    Definition("G0", "Type de procédure", 2, 2, StringAZ),
                    Definition("G1", "Orientation régionale", 2, 2, StringAZ),
                    Definition("G2", "Numéro d’usager", 0, 20, StringAZ09),
                    Definition("G3", "Date de fin des droits", 8, 8, JJMMAAAA),
                    Definition("G4", "Somme des montants versés au titre de l'ADA", 0, 10, Decimal),
                    Definition("G5", "Information de la Direction Territoriale", 0, 45, StringAZ09),
              ),

              Group("Identifiants de données relatives au permis de conduire",
                    Definition("E0", "Type d’arrêtés Permis de conduire", 2, 2, StringAZ09),
                    Definition("E1", "Date édition du document", 4, 4, Date4),
                    Definition("E2", "Date de fin de sanction", 4, 4, Date4),
                    Definition("E3", "Date de notification", 4, 4, Date4),
                    Definition("E4", "Type de relevé de permis de conduire", 3, 3, StringAZ),
                    Definition("E5", "Etat du permis de conduire du conducteur", 2, 2, Numeric0),
                    Definition("E6", "Catégories présentes de permis de conduire", 0, 65, StringAZ09Sp),
                    Definition("E7", "SIREN du demandeur du document", 9, 9, Numeric0),
                    Definition("E8", "Date des données issues du SNCP", 12, 12, JJMMAAAAHHMM),
              ),

              Group("Identifiants de données relatives au caducée infirmier",
                    Definition("I0", "Année du caducée", 4, 4, JJMMAAAA),
                    Definition("I1", "Numéro ordinal", 7, 7, Numeric0),
                    Definition("I2", "Mention spécifique", 16, 16, StringAZ09),
                    Definition("I3", "Nom d’exercice", 1, 54, StringAZ09SpAtDash),
                    Definition("I4", "Prénom d’exercice", 1, 37, StringAZ09SpAtDash),
                    Definition("I5", "Mode d’exercice", 5, 13, StringAZ09Dash),
                    Definition("I6", "Numéro RPPS", 11, 11, Numeric0),
              ),
    ),
)
