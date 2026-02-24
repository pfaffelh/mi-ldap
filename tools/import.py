# Load data from mi-ldap.json into the MongoDB

from pymongo import MongoClient
import json

cluster = MongoClient("mongodb://127.0.0.1:27017")
mongo_db = cluster["vvz"]

per = mongo_db["person"]
geb = mongo_db["gebaeude"]
ck = mongo_db["personencodekategorie"]
code = mongo_db["personencode"]

# street
E1 = geb.find_one({"name_de" : "Ernst-Zermelo-Str. 1"})["_id"]
HH10 = geb.find_one({"name_de" : "Hermann-Herder-Str. 10"})["_id"]
l = geb.find_one({"name_de": "-"})["_id"]

abt = ck.find_one({"name_de" : "Abteilung"})["_id"]
codes = list(code.find({"codekategorie" : abt}))
abteilungs_id = {c["name"] : c["_id"] for c in codes}

stat = ck.find_one({"name_de" : "Statusgruppe"})["_id"]
codes = list(code.find({"codekategorie" : stat}))
statusgruppe_id = {c["name"] : c["_id"] for c in codes}
j=0

with open('mi-ldap.json', 'r') as json_file:
    data = json.load(json_file)

data = [d for d in data if d["sn"] is not None]
for item in data:
    for key in item:
        if item[key] == None:
            item[key]=""
        if isinstance(item[key], list):
            item[key] = ", ".join(item[key])

# ou -> abteilung
# eduPersonAffiliation -> status

# Telefonnummern löschen
per.update_many({}, {"$set": {"tel1" : "", "tel2" : ""}})
per.update_many({}, {"$set": {"email1" : "", "email2" : ""}})

for item in data:
        p = per.find_one({"name" : item.get("sn"), "vorname" : item["givenName"]})
        if p:
            update = {}
            if p["raum1"] == "" and item.get("roomNumber", "") != "":
                update["raum1"] = item.get("roomNumber", "")
            if item.get("street") in ["E1", "HH10"]:
                update["gebaeude1"] = E1 if item.get("street") == "E1" else HH10
            if p["url"] == "" and item.get("labeledURI", "") != "":
                update["url"] = item.get("labeledURI", "")
            if p["email1"] != "" and p["email2"] == "" and item.get("mail", "") != "":
                if item.get("mail", "") != p["email1"]:
                    update["email2"] = item.get("mail", "")
            if p["email1"] == "" and item.get("mail", "") != "":
                update["email1"] = item.get("mail", "")
            if p["tel1"] != "" and p["tel2"] == "" and item.get("telephoneNumber", "") != "":
                if item.get("telephoneNumber", "") != p["tel1"]:
                    update["tel2"] = f"{item.get('telephoneNumber')}"
            if p["tel1"] == "" and item.get("telephoneNumber", "") != "":
                update["tel1"] = f"{item.get('telephoneNumber')}"
            if p["titel"] == "" and item.get("personalTitle", "") not in ["", "M.Sc.", "MSc.", "M.Sc. ", "Dipl.-Math.", "B.A.", "Dipl.-Math."]:
                update["titel"] = item.get("personalTitle", "")
            per.update_one({ "name" : item.get("sn"), "vorname" : item["givenName"]}, {"$set" : update })
        else:
#        "required": ["name", "name_en", "vorname", "name_prefix", "titel", "kennung", "rang", "tel1", "email1", "raum1", "gebaeude1", "tel2", "email2", "raum2", "gebaeude2", "sichtbar", "hp_sichtbar", "einstiegsdatum", "ausstiegsdatum", "semester", "code", "veranstaltung", "kommentar"],
            per.insert_one(
                {
                    "name" : item.get("sn"),
                    "name_en" : "",
                    "vorname" : item.get("givenName"),
                    "name_prefix" : "",
                    "titel": item.get("personalTitle") if item.get("personalTitle") not in [None, "M.Sc.", "MSc.", "M.Sc. ", "Dipl.-Math.", "B.A.", "Dipl.-Math."] else "",
                    "kennung" : "", 
                    "rang" : 200 + j,
                    "tel1" : f"{item.get('telephoneNumber')}" if item.get('telephoneNumber') is not None else "",
                    "email1" : item.get("mail") if item.get("mail") is not None else "",
                    "raum1" : item.get("roomNumber", ""),
                    "gebaeude1": l if item.get("street", "") == "" else (E1 if item.get("street") == "E1" else HH10), 
                    "tel2" : "",
                    "email2" : "",
                    "raum2" : "",
                    "gebaeude2": l, 
                    "url" : item.get("labeledURI", ""),
                    "sichtbar" : False,
                    "hp_sichtbar" : False,
                    "ldap" : True,
                    "einstiegsdatum" : None, 
                    "ausstiegsdatum" : None,
                    "gender" : "kA", 
                    "vorgesetzte" : [], 
                    "abwesend_start" : None, 
                    "abwesend_ende" : None,
                    "semester" : [],
                    "code" : [], 
                    "veranstaltung" : [],
                    "kommentar" : "",                    
                    "kommentar_html" : "",
                    "bearbeitet" : "Initialer Eintrag.", 
                })
            j = j + 1
        if item.get("ou") in abteilungs_id.keys():
            per.update_one({"name" : item["sn"], "vorname" : item["givenName"]}, {"$addToSet" : {"code" : abteilungs_id[item.get("ou")]}})
        aff = [item.get("eduPersonPrimaryAffiliation")] + (item.get("eduPersonAffiliation") if isinstance(item.get("eduPersonAffiliation"), list) else [item.get("eduPersonAffiliation")])
        for s in [x for x in statusgruppe_id.keys() if x in aff]:
            per.update_one(
                {
                    "vorname" : item["givenName"],
                    "name" : item["sn"]
                }, 
                {   
                    "$addToSet" : {
                        "code" : statusgruppe_id[s]
                    }
                }
            )
