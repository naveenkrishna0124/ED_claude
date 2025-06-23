import re
import json
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from enum import Enum

@dataclass
class CPTCode:
    code: str
    description: str
    category: str
    confidence: float

class ProcedureCategory(Enum):
    EVALUATION = "Evaluation and Management"
    PROCEDURES = "Procedures"
    RADIOLOGY = "Radiology"
    LABORATORY = "Laboratory"
    INJECTIONS = "Injections"
    WOUND_CARE = "Wound Care"

class EDCPTExtractor:
    def __init__(self):
        # CPT codes in ranges [10000-69999] and [99100-99199]
        self.cpt_mapping = {
            
            # Wound Repair (12000-12057)
            "12001": {
                "description": "Simple repair of superficial wounds of scalp, neck, axillae, external genitalia, trunk and/or extremities (including hands and feet); 2.5 cm or less",
                "category": ProcedureCategory.WOUND_CARE,
                "keywords": ["simple repair", "superficial wound", "suture", "laceration repair"],
                "patterns": [r"(?i)simple\s+(?:repair|suture)", r"(?i)superficial\s+(?:wound|laceration)", r"(?i)sutur(?:e|ed|ing)"]
            },
            "12002": {
                "description": "Simple repair of superficial wounds; 2.6 cm to 7.5 cm",
                "category": ProcedureCategory.WOUND_CARE,
                "keywords": ["simple repair", "2.6", "7.5", "cm", "suture"],
                "patterns": [r"(?i)simple\s+repair.*(?:[2-7]\.\d+|[3-7])\s*cm", r"(?i)sutur(?:e|ed|ing).*(?:[2-7]\.\d+|[3-7])\s*cm"]
            },
            "12004": {
                "description": "Simple repair of superficial wounds; 7.6 cm to 12.5 cm",
                "category": ProcedureCategory.WOUND_CARE,
                "keywords": ["simple repair", "7.6", "12.5", "cm", "large laceration"],
                "patterns": [r"(?i)simple\s+repair.*(?:[7-9]\.\d+|1[0-2]\.\d+)\s*cm", r"(?i)large.*(?:laceration|wound).*repair"]
            },
            "12011": {
                "description": "Simple repair of superficial wounds of face, ears, eyelids, nose, lips and/or mucous membranes; 2.5 cm or less",
                "category": ProcedureCategory.WOUND_CARE,
                "keywords": ["face", "facial", "lip", "nose", "ear", "simple repair"],
                "patterns": [r"(?i)(?:face|facial|lip|nose|ear).*(?:repair|suture)", r"(?i)simple\s+repair.*(?:face|facial)"]
            },
            "12013": {
                "description": "Simple repair of superficial wounds of face; 2.6 cm to 5.0 cm",
                "category": ProcedureCategory.WOUND_CARE,
                "keywords": ["face", "facial", "2.6", "5.0", "cm", "repair"],
                "patterns": [r"(?i)(?:face|facial).*repair.*(?:[2-5]\.\d+)\s*cm", r"(?i)simple\s+repair.*face.*(?:[2-5])\s*cm"]
            },
            "12031": {
                "description": "Intermediate repair of wounds of scalp, axillae, trunk and/or extremities; 2.5 cm or less",
                "category": ProcedureCategory.WOUND_CARE,
                "keywords": ["intermediate repair", "layered closure", "subcutaneous suture"],
                "patterns": [r"(?i)intermediate\s+repair", r"(?i)layered\s+(?:closure|repair)", r"(?i)subcutaneous.*sutur"]
            },
            "12032": {
                "description": "Intermediate repair of wounds; 2.6 cm to 7.5 cm",
                "category": ProcedureCategory.WOUND_CARE,
                "keywords": ["intermediate repair", "layered", "2.6", "7.5", "cm"],
                "patterns": [r"(?i)intermediate\s+repair.*(?:[2-7]\.\d+)\s*cm", r"(?i)layered.*repair.*(?:[2-7])\s*cm"]
            },
            
            # Excision/Debridement (11000-11047)
            "11000": {
                "description": "Debridement of extensive eczematous or infected skin; up to 10% of body surface",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["debridement", "infected skin", "eczematous", "wound cleaning"],
                "patterns": [r"(?i)debridement", r"(?i)wound\s+(?:cleaning|debridement)", r"(?i)infected\s+skin.*(?:clean|debride)"]
            },
            "11042": {
                "description": "Debridement, subcutaneous tissue; first 20 sq cm or less",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["debridement", "subcutaneous", "tissue", "20 sq cm"],
                "patterns": [r"(?i)debridement.*subcutaneous", r"(?i)subcutaneous.*debridement", r"(?i)tissue\s+debridement"]
            },
            "11043": {
                "description": "Debridement, muscle and/or fascia; first 20 sq cm or less",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["debridement", "muscle", "fascia", "deep debridement"],
                "patterns": [r"(?i)debridement.*(?:muscle|fascia)", r"(?i)(?:muscle|fascia).*debridement", r"(?i)deep\s+debridement"]
            },
            
            # Incision and Drainage (10060-10180)
            "10060": {
                "description": "Incision and drainage of abscess; simple or single",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["incision and drainage", "i&d", "abscess", "drainage"],
                "patterns": [r"(?i)incision\s+and\s+drainage", r"(?i)i\s*&\s*d", r"(?i)abscess.*drain", r"(?i)drain.*abscess"]
            },
            "10061": {
                "description": "Incision and drainage of abscess; complicated or multiple",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["incision and drainage", "complicated", "multiple abscess", "complex i&d"],
                "patterns": [r"(?i)(?:complicated|complex).*(?:i\s*&\s*d|incision.*drainage)", r"(?i)multiple.*abscess.*drain"]
            },
            "10120": {
                "description": "Incision and removal of foreign body, subcutaneous tissues; simple",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["foreign body removal", "subcutaneous", "incision", "removal"],
                "patterns": [r"(?i)foreign\s+body.*remov", r"(?i)subcutaneous.*foreign", r"(?i)incision.*foreign\s+body"]
            },
            "10140": {
                "description": "Incision and drainage of hematoma, seroma or fluid collection",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["hematoma", "seroma", "fluid collection", "drainage"],
                "patterns": [r"(?i)(?:hematoma|seroma).*drain", r"(?i)fluid\s+collection.*drain", r"(?i)drain.*(?:hematoma|seroma)"]
            },
            
            # Fracture Care (25500-25695)
            "25500": {
                "description": "Closed treatment of radial shaft fracture; without manipulation",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["radial shaft fracture", "closed treatment", "without manipulation"],
                "patterns": [r"(?i)radial\s+shaft.*fracture.*closed", r"(?i)closed.*radial\s+shaft", r"(?i)radius.*shaft.*fracture"]
            },
            "25505": {
                "description": "Closed treatment of radial shaft fracture; with manipulation",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["radial shaft", "manipulation", "closed reduction"],
                "patterns": [r"(?i)radial\s+shaft.*manipulation", r"(?i)closed\s+reduction.*radial\s+shaft"]
            },
            "25600": {
                "description": "Closed treatment of distal radial fracture; without manipulation",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["distal radial fracture", "colles fracture", "closed treatment"],
                "patterns": [r"(?i)distal\s+(?:radial|radius).*fracture", r"(?i)colles.*fracture", r"(?i)wrist.*fracture.*closed"]
            },
            "25605": {
                "description": "Closed treatment of distal radial fracture; with manipulation",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["distal radial", "manipulation", "reduction", "closed reduction"],
                "patterns": [r"(?i)distal\s+(?:radial|radius).*manipulation", r"(?i)closed\s+reduction.*(?:radial|radius)", r"(?i)wrist.*reduction"]
            },
            "27750": {
                "description": "Closed treatment of tibial shaft fracture; without manipulation",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["tibial shaft fracture", "tibia fracture", "leg fracture"],
                "patterns": [r"(?i)tibial?\s+(?:shaft\s+)?fracture", r"(?i)tibia.*fracture.*closed", r"(?i)leg.*fracture.*closed"]
            },
            "27752": {
                "description": "Closed treatment of tibial shaft fracture; with manipulation",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["tibial fracture", "manipulation", "reduction"],
                "patterns": [r"(?i)tibial?.*fracture.*manipulation", r"(?i)tibia.*reduction", r"(?i)leg.*fracture.*reduction"]
            },
            
            # Joint Injections/Aspirations (20600-20615)
            "20600": {
                "description": "Arthrocentesis, aspiration and/or injection; small joint or bursa",
                "category": ProcedureCategory.INJECTIONS,
                "keywords": ["arthrocentesis", "small joint", "injection", "aspiration"],
                "patterns": [r"(?i)arthrocentesis.*small", r"(?i)small\s+joint.*(?:injection|aspiration)", r"(?i)finger.*joint.*inject"]
            },
            "20605": {
                "description": "Arthrocentesis, aspiration and/or injection; intermediate joint or bursa",
                "category": ProcedureCategory.INJECTIONS,
                "keywords": ["arthrocentesis", "intermediate joint", "wrist", "ankle", "elbow"],
                "patterns": [r"(?i)arthrocentesis.*(?:intermediate|wrist|ankle|elbow)", r"(?i)(?:wrist|ankle|elbow).*(?:injection|aspiration)"]
            },
            "20610": {
                "description": "Arthrocentesis, aspiration and/or injection; major joint or bursa",
                "category": ProcedureCategory.INJECTIONS,
                "keywords": ["arthrocentesis", "major joint", "knee", "shoulder", "hip"],
                "patterns": [r"(?i)arthrocentesis.*(?:major|knee|shoulder|hip)", r"(?i)(?:knee|shoulder|hip).*(?:injection|aspiration)"]
            },
            
            # Casting/Splinting (29000-29590)
            "29105": {
                "description": "Application of long arm splint",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["long arm splint", "splint", "arm splint"],
                "patterns": [r"(?i)long\s+arm\s+splint", r"(?i)arm.*splint.*applied", r"(?i)splint.*long\s+arm"]
            },
            "29125": {
                "description": "Application of short arm splint; static",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["short arm splint", "wrist splint", "forearm splint"],
                "patterns": [r"(?i)short\s+arm\s+splint", r"(?i)wrist.*splint", r"(?i)forearm.*splint"]
            },
            "29130": {
                "description": "Application of finger splint; static",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["finger splint", "digit splint", "finger immobilization"],
                "patterns": [r"(?i)finger.*splint", r"(?i)digit.*splint", r"(?i)splint.*finger"]
            },
            "29505": {
                "description": "Application of long leg splint",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["long leg splint", "leg splint", "lower extremity splint"],
                "patterns": [r"(?i)long\s+leg\s+splint", r"(?i)leg.*splint.*applied", r"(?i)lower.*extremity.*splint"]
            },
            "29515": {
                "description": "Application of short leg splint",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["short leg splint", "ankle splint", "foot splint"],
                "patterns": [r"(?i)short\s+leg\s+splint", r"(?i)ankle.*splint", r"(?i)foot.*splint"]
            },
            
            # Cardiovascular Procedures (36000-36598)
            "36000": {
                "description": "Introduction of needle or intracatheter, vein",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["venipuncture", "needle", "vein", "blood draw", "iv access"],
                "patterns": [r"(?i)venipuncture", r"(?i)needle.*vein", r"(?i)blood\s+draw", r"(?i)iv.*access"]
            },
            "36400": {
                "description": "Venipuncture, younger than age 3 years, necessitating physician's skill",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["venipuncture", "pediatric", "infant", "child", "younger than 3"],
                "patterns": [r"(?i)venipuncture.*(?:pediatric|infant|child)", r"(?i)(?:infant|child).*venipuncture", r"(?i)younger.*3.*venipuncture"]
            },
            "36415": {
                "description": "Collection of venous blood by venipuncture",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["venous blood", "collection", "venipuncture", "blood collection"],
                "patterns": [r"(?i)venous\s+blood.*collection", r"(?i)blood.*collection.*venipuncture", r"(?i)venipuncture.*blood"]
            },
            "36556": {
                "description": "Insertion of non-tunneled centrally inserted central venous catheter; age 5 years or older",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["central line", "central venous catheter", "cvc", "central access"],
                "patterns": [r"(?i)central\s+(?:line|venous\s+catheter|access)", r"(?i)cvc.*insert", r"(?i)central.*catheter.*insert"]
            },
            "36558": {
                "description": "Insertion of non-tunneled centrally inserted central venous catheter; younger than 5 years",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["central line", "pediatric", "younger than 5", "central venous catheter"],
                "patterns": [r"(?i)central.*catheter.*(?:pediatric|child)", r"(?i)(?:pediatric|child).*central.*line", r"(?i)younger.*5.*central"]
            },
            
            # Respiratory Procedures (31500-31899)
            "31500": {
                "description": "Intubation, endotracheal, emergency procedure",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["intubation", "endotracheal", "emergency intubation", "ett"],
                "patterns": [r"(?i)intubat", r"(?i)endotracheal", r"(?i)ett.*placed", r"(?i)emergency.*intubation"]
            },
            "31505": {
                "description": "Laryngoscopy, indirect; diagnostic",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["laryngoscopy", "indirect laryngoscopy", "larynx examination"],
                "patterns": [r"(?i)laryngoscopy", r"(?i)larynx.*exam", r"(?i)indirect.*laryngoscopy"]
            },
            "31515": {
                "description": "Laryngoscopy direct, with or without tracheoscopy; for aspiration",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["direct laryngoscopy", "aspiration", "foreign body removal"],
                "patterns": [r"(?i)direct\s+laryngoscopy", r"(?i)laryngoscopy.*aspiration", r"(?i)foreign\s+body.*larynx"]
            },
            
            # Gastrointestinal Procedures (43235-43259)
            "43235": {
                "description": "Esophagogastroduodenoscopy, flexible, transoral; diagnostic",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["egd", "endoscopy", "esophagogastroduodenoscopy", "upper endoscopy"],
                "patterns": [r"(?i)egd", r"(?i)esophagogastroduodenoscopy", r"(?i)upper\s+endoscopy", r"(?i)flexible.*endoscopy"]
            },
            "43239": {
                "description": "Esophagogastroduodenoscopy, flexible, transoral; with biopsy",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["egd", "biopsy", "endoscopy with biopsy"],
                "patterns": [r"(?i)egd.*biopsy", r"(?i)endoscopy.*biopsy", r"(?i)biopsy.*(?:egd|endoscopy)"]
            },
            
            # Genitourinary Procedures (51701-51798)
            "51701": {
                "description": "Insertion of non-indwelling bladder catheter",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["straight catheter", "bladder catheter", "urinary catheter", "straight cath"],
                "patterns": [r"(?i)straight\s+(?:catheter|cath)", r"(?i)bladder.*catheter.*(?:insert|plac)", r"(?i)urinary.*catheter.*straight"]
            },
            "51702": {
                "description": "Insertion of temporary indwelling bladder catheter; simple",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["foley catheter", "indwelling catheter", "bladder catheter", "foley"],
                "patterns": [r"(?i)foley.*(?:catheter|insert|plac)", r"(?i)indwelling.*catheter", r"(?i)bladder.*catheter.*indwelling"]
            },
            "51705": {
                "description": "Change of cystostomy tube; simple",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["cystostomy", "suprapubic catheter", "tube change"],
                "patterns": [r"(?i)cystostomy", r"(?i)suprapubic.*(?:catheter|tube)", r"(?i)tube.*change.*cystostomy"]
            },
            
            # Nervous System Procedures (61000-64999)
            "61050": {
                "description": "Cisternal or lateral cervical (C1-C2) puncture; without injection",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["cisternal puncture", "cervical puncture", "spinal tap"],
                "patterns": [r"(?i)cisternal\s+puncture", r"(?i)cervical.*puncture", r"(?i)c1.*c2.*puncture"]
            },
            "62270": {
                "description": "Spinal puncture, lumbar, diagnostic",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["lumbar puncture", "spinal tap", "lp", "csf"],
                "patterns": [r"(?i)lumbar\s+puncture", r"(?i)spinal\s+tap", r"(?i)\blp\b", r"(?i)csf.*obtain"]
            },
            "64400": {
                "description": "Injection, anesthetic agent; trigeminal nerve",
                "category": ProcedureCategory.INJECTIONS,
                "keywords": ["trigeminal nerve", "nerve block", "facial nerve", "anesthetic injection"],
                "patterns": [r"(?i)trigeminal.*(?:nerve|block|injection)", r"(?i)facial.*nerve.*block", r"(?i)nerve\s+block.*trigeminal"]
            },
            "64450": {
                "description": "Injection, anesthetic agent; other peripheral nerve or branch",
                "category": ProcedureCategory.INJECTIONS,
                "keywords": ["peripheral nerve", "nerve block", "anesthetic injection"],
                "patterns": [r"(?i)peripheral\s+nerve.*(?:block|injection)", r"(?i)nerve\s+block.*peripheral", r"(?i)anesthetic.*nerve"]
            },
            
            # Musculoskeletal Procedures (20000-29999)
            "20550": {
                "description": "Injection; single tendon sheath, or ligament, aponeurosis",
                "category": ProcedureCategory.INJECTIONS,
                "keywords": ["tendon injection", "sheath injection", "ligament injection"],
                "patterns": [r"(?i)tendon.*injection", r"(?i)sheath.*injection", r"(?i)ligament.*injection"]
            },
            "20551": {
                "description": "Injection; single tendon origin/insertion",
                "category": ProcedureCategory.INJECTIONS,
                "keywords": ["tendon origin", "tendon insertion", "trigger point"],
                "patterns": [r"(?i)tendon.*(?:origin|insertion).*injection", r"(?i)trigger\s+point.*injection"]
            },
            "20553": {
                "description": "Injection; single or multiple trigger points, 1 or 2 muscle(s)",
                "category": ProcedureCategory.INJECTIONS,
                "keywords": ["trigger point", "muscle injection", "trigger point injection"],
                "patterns": [r"(?i)trigger\s+point.*injection", r"(?i)muscle.*trigger.*point", r"(?i)injection.*trigger\s+point"]
            },
            
            # Anesthesia Modifiers (99100-99199)
            "99100": {
                "description": "Anesthesia for patient of extreme age, younger than 1 year and older than 70",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["extreme age", "anesthesia", "younger than 1", "older than 70"],
                "patterns": [r"(?i)anesthesia.*extreme\s+age", r"(?i)(?:younger.*1|older.*70).*anesthesia"]
            },
            "99116": {
                "description": "Anesthesia complicated by utilization of total body hypothermia",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["hypothermia", "total body hypothermia", "anesthesia"],
                "patterns": [r"(?i)anesthesia.*hypothermia", r"(?i)total\s+body\s+hypothermia", r"(?i)hypothermia.*anesthesia"]
            },
            "99135": {
                "description": "Anesthesia complicated by utilization of controlled hypotension",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["controlled hypotension", "hypotensive anesthesia", "anesthesia"],
                "patterns": [r"(?i)controlled\s+hypotension", r"(?i)hypotensive.*anesthesia", r"(?i)anesthesia.*hypotension"]
            },
            "99140": {
                "description": "Anesthesia complicated by emergency conditions",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["emergency anesthesia", "emergency conditions", "emergent"],
                "patterns": [r"(?i)emergency.*anesthesia", r"(?i)anesthesia.*emergency", r"(?i)emergent.*anesthesia"]
            },         
            # Eye/Ear Procedures (65000-69999)
            "65205": {
                "description": "Removal of foreign body, external eye; conjunctival superficial",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["foreign body", "eye", "conjunctival", "removal"],
                "patterns": [r"(?i)foreign\s+body.*eye", r"(?i)eye.*foreign\s+body", r"(?i)conjunctival.*foreign"]
            },
            "65210": {
                "description": "Removal of foreign body, external eye; conjunctival embedded",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["foreign body", "embedded", "conjunctival", "eye"],
                "patterns": [r"(?i)embedded.*foreign.*eye", r"(?i)conjunctival.*embedded", r"(?i)foreign.*embedded.*eye"]
            },
            "65220": {
                "description": "Removal of foreign body, external eye; corneal, without slit lamp",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["corneal foreign body", "cornea", "foreign body removal"],
                "patterns": [r"(?i)corneal.*foreign", r"(?i)foreign.*cornea", r"(?i)cornea.*foreign\s+body"]
            },
            "65222": {
                "description": "Removal of foreign body, external eye; corneal, with slit lamp",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["corneal foreign body", "slit lamp", "cornea"],
                "patterns": [r"(?i)slit\s+lamp.*foreign", r"(?i)corneal.*slit\s+lamp", r"(?i)foreign.*slit\s+lamp"]
            },
            "69200": {
                "description": "Removal of foreign body from external auditory canal; without general anesthesia",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["ear foreign body", "auditory canal", "ear canal"],
                "patterns": [r"(?i)ear.*foreign\s+body", r"(?i)auditory\s+canal.*foreign", r"(?i)foreign.*ear\s+canal"]
            },
            "69210": {
                "description": "Removal of impacted cerumen, external auditory canal, 1 or both ears",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["cerumen", "ear wax", "impacted", "ear cleaning"],
                "patterns": [r"(?i)cerumen.*remov", r"(?i)ear\s+wax.*remov", r"(?i)impacted.*(?:cerumen|wax)", r"(?i)ear.*clean.*wax"]
            },
            
            # Skin Procedures (17000-17999)
            "17000": {
                "description": "Destruction of premalignant lesions; first lesion",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["destruction", "premalignant", "lesion", "cryotherapy"],
                "patterns": [r"(?i)destruction.*lesion", r"(?i)premalignant.*destruction", r"(?i)cryotherapy.*lesion"]
            },
            "17003": {
                "description": "Destruction of premalignant lesions; second through 14th lesion",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["destruction", "multiple lesions", "additional lesions"],
                "patterns": [r"(?i)destruction.*multiple.*lesions", r"(?i)additional.*lesion.*destruction"]
            },
            "17110": {
                "description": "Destruction of benign lesions other than skin tags or cutaneous vascular lesions; up to 14 lesions",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["benign lesions", "destruction", "wart", "keratosis"],
                "patterns": [r"(?i)benign.*lesion.*destruction", r"(?i)wart.*(?:destruction|removal)", r"(?i)keratosis.*destruction"]
            },
            "17250": {
                "description": "Chemical cauterization of granulation tissue",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["chemical cauterization", "granulation tissue", "cautery"],
                "patterns": [r"(?i)chemical\s+cauteriz", r"(?i)granulation.*cauteriz", r"(?i)cauteriz.*granulation"]
            },
            
            # Emergency Procedures (Additional)
            "43752": {
                "description": "Naso- or oro-gastric tube placement, requiring physician's skill",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["ng tube", "nasogastric", "orogastric", "gastric tube"],
                "patterns": [r"(?i)ng\s+tube", r"(?i)nasogastric.*tube", r"(?i)orogastric.*tube", r"(?i)gastric\s+tube.*plac"]
            },
            "43753": {
                "description": "Gastric intubation and aspiration, therapeutic, necessitating physician's skill",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["gastric lavage", "stomach pump", "gastric aspiration"],
                "patterns": [r"(?i)gastric\s+lavage", r"(?i)stomach\s+pump", r"(?i)gastric.*aspiration", r"(?i)lavage.*gastric"]
            },
            "31720": {
                "description": "Aspiration of trachea, nasotracheal",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["tracheal aspiration", "nasotracheal", "suctioning"],
                "patterns": [r"(?i)tracheal\s+aspiration", r"(?i)nasotracheal.*aspiration", r"(?i)suction.*trachea"]
            },
            "32554": {
                "description": "Thoracentesis, needle or catheter, aspiration of the pleural space",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["thoracentesis", "pleural tap", "chest tap", "pleural aspiration"],
                "patterns": [r"(?i)thoracentesis", r"(?i)pleural\s+tap", r"(?i)chest\s+tap", r"(?i)pleural.*aspiration"]
            },
            "32555": {
                "description": "Thoracentesis, needle or catheter, aspiration of the pleural space; with imaging guidance",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["thoracentesis", "imaging guidance", "ultrasound guided"],
                "patterns": [r"(?i)thoracentesis.*(?:imaging|ultrasound|guided)", r"(?i)(?:ultrasound|imaging).*thoracentesis"]
            },
            "36430": {
                "description": "Transfusion, blood or blood components",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["transfusion", "blood transfusion", "prbc", "packed red blood cells"],
                "patterns": [r"(?i)transfusion", r"(?i)blood.*transfusion", r"(?i)prbc.*transfusion", r"(?i)packed.*red.*blood"]
            },
            "49084": {
                "description": "Peritoneal lavage",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["peritoneal lavage", "dpl", "diagnostic peritoneal lavage"],
                "patterns": [r"(?i)peritoneal\s+lavage", r"(?i)\bdpl\b", r"(?i)diagnostic.*peritoneal.*lavage"]
            },
            "54150": {
                "description": "Circumcision, using clamp or other device; newborn",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["circumcision", "newborn", "clamp"],
                "patterns": [r"(?i)circumcision.*newborn", r"(?i)newborn.*circumcision", r"(?i)circumcision.*clamp"]
            },
            "57452": {
                "description": "Colposcopy of the cervix including upper/adjacent vagina",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["colposcopy", "cervix", "vaginal examination"],
                "patterns": [r"(?i)colposcopy", r"(?i)cervix.*colposcopy", r"(?i)colposcopy.*cervix"]
            },
            "59400": {
                "description": "Routine obstetric care including antepartum care, vaginal delivery and postpartum care",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["delivery", "vaginal delivery", "obstetric care", "childbirth"],
                "patterns": [r"(?i)vaginal\s+delivery", r"(?i)delivery.*vaginal", r"(?i)obstetric.*care.*delivery", r"(?i)childbirth"]
            },
            "59409": {
                "description": "Vaginal delivery only",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["vaginal delivery", "delivery only", "birth"],
                "patterns": [r"(?i)vaginal\s+delivery\s+only", r"(?i)delivery.*only.*vaginal", r"(?i)birth.*vaginal"]
            },
            "59514": {
                "description": "Cesarean delivery only",
                "category": ProcedureCategory.PROCEDURES,
                "keywords": ["cesarean", "c-section", "cesarean delivery", "surgical delivery"],
                "patterns": [r"(?i)cesarean", r"(?i)c.section", r"(?i)surgical\s+delivery", r"(?i)cesarean.*delivery"]
            }
        }
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
        
    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        for code_info in self.cpt_mapping.values():
            code_info['compiled_patterns'] = [re.compile(pattern) for pattern in code_info['patterns']]
    
    def extract_cpt_codes(self, medical_note: str) -> List[CPTCode]:
        """
        Extract CPT codes from medical note text
        
        Args:
            medical_note: Raw medical note text
            
        Returns:
            List of CPTCode objects with confidence scores
        """
        # Clean and normalize the text
        cleaned_note = self._clean_text(medical_note)
        
        # Extract procedures
        found_codes = []
        
        for cpt_code, code_info in self.cpt_mapping.items():
            confidence = self._calculate_confidence(cleaned_note, code_info)
            
            if confidence > 0.3:  # Threshold for inclusion
                found_codes.append(CPTCode(
                    code=cpt_code,
                    description=code_info['description'],
                    category=code_info['category'].value,
                    confidence=confidence
                ))
        
        # Sort by confidence score (highest first)
        found_codes.sort(key=lambda x: x.confidence, reverse=True)
        
        # Apply business rules to refine results
        refined_codes = self._apply_business_rules(found_codes, cleaned_note)
        
        return refined_codes
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize medical note text"""
        # Convert to lowercase for matching
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere with matching
        text = re.sub(r'[^\w\s\-\.\,\:\;\(\)\/]', ' ', text)
        
        return text.strip()
    
    def _calculate_confidence(self, text: str, code_info: Dict) -> float:
        """Calculate confidence score for a CPT code match"""
        confidence = 0.0
        
        # Check keyword matches
        keyword_matches = 0
        for keyword in code_info['keywords']:
            if keyword.lower() in text:
                keyword_matches += 1
        
        if code_info['keywords']:
            keyword_score = keyword_matches / len(code_info['keywords'])
            confidence += keyword_score * 0.6  # 60% weight for keywords
        
        # Check pattern matches
        pattern_matches = 0
        for pattern in code_info.get('compiled_patterns', []):
            if pattern.search(text):
                pattern_matches += 1
        
        if code_info.get('compiled_patterns'):
            pattern_score = min(pattern_matches / len(code_info['compiled_patterns']), 1.0)
            confidence += pattern_score * 0.4  # 40% weight for patterns
        
        return min(confidence, 1.0)
    
    def _apply_business_rules(self, codes: List[CPTCode], text: str) -> List[CPTCode]:
        """Apply medical coding business rules to refine results"""
        refined_codes = []
        
        # Rule 1: Only one E&M code per encounter
        em_codes = [code for code in codes if code.category == ProcedureCategory.EVALUATION.value]
        if em_codes:
            # Keep the highest level E&M code
            highest_em = max(em_codes, key=lambda x: x.confidence)
            refined_codes.append(highest_em)
        
        # Rule 2: Include all procedure codes above threshold
        procedure_codes = [code for code in codes if code.category != ProcedureCategory.EVALUATION.value]
        refined_codes.extend([code for code in procedure_codes if code.confidence > 0.5])
        
        # Rule 3: Remove duplicate categories with lower confidence
        seen_categories = {}
        final_codes = []
        
        for code in refined_codes:
            category_key = f"{code.category}_{code.code[:3]}"  # Group similar codes
            if category_key not in seen_categories or code.confidence > seen_categories[category_key].confidence:
                seen_categories[category_key] = code
        
        final_codes = list(seen_categories.values())
        final_codes.sort(key=lambda x: x.confidence, reverse=True)
        
        return final_codes
    
    def extract_with_details(self, medical_note: str) -> Dict:
        """
        Extract CPT codes with additional analysis details
        
        Returns:
            Dictionary with codes, analysis details, and recommendations
        """
        codes = self.extract_cpt_codes(medical_note)
        
        # Analyze note characteristics
        note_analysis = self._analyze_note_complexity(medical_note)
        
        return {
            'cpt_codes': [
                {
                    'code': code.code,
                    'description': code.description,
                    'category': code.category,
                    'confidence': round(code.confidence, 3)
                }
                for code in codes
            ],
            'note_analysis': note_analysis,
            'total_codes_found': len(codes),
            'highest_confidence': max([code.confidence for code in codes]) if codes else 0,
            'recommendations': self._generate_recommendations(codes, note_analysis)
        }
    
    def _analyze_note_complexity(self, text: str) -> Dict:
        """Analyze the complexity and characteristics of the medical note"""
        word_count = len(text.split())
        
        # Look for complexity indicators
        high_complexity_indicators = [
            'critical', 'life threatening', 'multiple systems', 'extensive',
            'comprehensive', 'complex decision making', 'high risk'
        ]
        
        complexity_score = sum(1 for indicator in high_complexity_indicators if indicator in text.lower())
        
        return {
            'word_count': word_count,
            'complexity_indicators': complexity_score,
            'estimated_complexity': 'High' if complexity_score >= 3 else 'Moderate' if complexity_score >= 1 else 'Low'
        }
    
    def _generate_recommendations(self, codes: List[CPTCode], analysis: Dict) -> List[str]:
        """Generate recommendations for the coding"""
        recommendations = []
        
        if not codes:
            recommendations.append("No CPT codes identified. Consider reviewing documentation for missed procedures or evaluations.")
        
        if analysis['complexity_indicators'] >= 2 and not any(code.code in ['99284', '99285'] for code in codes):
            recommendations.append("Note suggests high complexity but no high-level E&M code identified. Review for appropriate E&M level.")
        
        if len([code for code in codes if code.category == ProcedureCategory.EVALUATION.value]) == 0:
            recommendations.append("No evaluation and management code identified. Every ED visit should have an E&M code.")
        
        if any(code.confidence < 0.6 for code in codes):
            recommendations.append("Some codes have lower confidence scores. Manual review recommended.")
        
        return recommendations

# Example usage and testing
def test_extractor():
    """Test the CPT extractor with sample medical notes"""
    extractor = EDCPTExtractor()
    
    # Sample medical notes
    sample_notes = [
        """
        CHIEF COMPLAINT: Laceration to left hand
        
        HISTORY: 25-year-old male presents with 3 cm laceration to dorsal aspect of left hand 
        sustained while working with glass. Wound is superficial, no tendon involvement.
        
        PHYSICAL EXAM: 3 cm superficial laceration to left hand, clean edges, no foreign body visible.
        No neurovascular compromise.
        
        PROCEDURE: Simple repair of superficial wound with 4-0 nylon sutures x 6.
        
        DISPOSITION: Discharged home with wound care instructions.
        """,
        
        """
        CHIEF COMPLAINT: Chest pain and difficulty breathing
        
        HISTORY: 45-year-old female with acute onset chest pain and shortness of breath.
        
        PHYSICAL EXAM: Patient appears anxious, tachypneic. Decreased breath sounds on right side.
        
        PROCEDURES: Chest X-ray obtained. Thoracentesis performed with needle aspiration of 
        pleural space yielding 200ml serosanguinous fluid. Procedure performed with 
        ultrasound guidance for safety.
        
        DISPOSITION: Admitted to medicine service.
        """,
        
        """
        CHIEF COMPLAINT: Wrist pain after fall
        
        HISTORY: 35-year-old male fell on outstretched hand. Wrist pain and deformity noted.
        
        PHYSICAL EXAM: Obvious deformity of distal radius. Neurovascularly intact.
        
        PROCEDURES: Wrist X-ray obtained showing distal radial fracture. Closed reduction 
        with manipulation performed. Short arm splint applied for immobilization.
        Venipuncture performed for blood draw and IV access established.
        
        DISPOSITION: Orthopedic follow-up arranged.
        """,
        
        """
        CHIEF COMPLAINT: Abdominal pain
        
        HISTORY: 28-year-old female with acute abdominal pain, nausea and vomiting.
        
        PHYSICAL EXAM: Tender abdomen with guarding. Positive pregnancy test.
        
        PROCEDURES: Nasogastric tube placement for decompression. Foley catheter inserted 
        for urine output monitoring. Central venous catheter placed for fluid resuscitation.
        Blood transfusion administered due to hemorrhage.
        
        DISPOSITION: Emergency surgery.
        """,
        
        """
        CHIEF COMPLAINT: Eye pain and foreign body sensation
        
        HISTORY: 32-year-old construction worker with metal fragment in right eye.
        
        PHYSICAL EXAM: Conjunctival injection, foreign body visible on cornea.
        
        PROCEDURES: Corneal foreign body removal performed with slit lamp examination.
        Topical anesthesia applied prior to removal.
        
        DISPOSITION: Ophthalmology follow-up scheduled.
        """
    ]
    
    print("=== ED Medical Notes CPT Extractor Test ===\n")
    
    for i, note in enumerate(sample_notes, 1):
        print(f"--- Sample Note {i} ---")
        result = extractor.extract_with_details(note)
        
        print(f"Found {result['total_codes_found']} CPT codes:")
        for code_info in result['cpt_codes']:
            print(f"  {code_info['code']}: {code_info['description']}")
            print(f"    Category: {code_info['category']}")
            print(f"    Confidence: {code_info['confidence']:.1%}")
        
        print(f"\nNote Analysis:")
        print(f"  Word Count: {result['note_analysis']['word_count']}")
        print(f"  Complexity: {result['note_analysis']['estimated_complexity']}")
        
        if result['recommendations']:
            print(f"\nRecommendations:")
            for rec in result['recommendations']:
                print(f"  • {rec}")
        
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    test_extractor()
