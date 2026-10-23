import csv
import io
from collections import Counter

COUNTS = {"registered": 3, "abstentions": 4, "voters": 6, "blank": 8, "invalid": 11, "valid": 14}
RATES = {5: ("abstentions", "registered"), 7: ("voters", "registered"), 9: ("blank", "registered"), 10: ("blank", "voters"), 12: ("invalid", "registered"), 13: ("invalid", "voters"), 15: ("valid", "registered"), 16: ("valid", "voters")}

def parse_results(raw):
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Unsupported encoding / encodage non pris en charge")
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    rows = [row for row in rows if any(cell.strip() for cell in row)]
    if len(rows) < 2 or rows[0][0].strip() != "Code du département":
        raise ValueError("Expected departmental header / en-tête départemental attendu")
    territories, results, issues, rosters = [], [], [], []
    def integer(value):
        number = int(value.strip())
        if number < 0:
            raise ValueError("Negative count / effectif négatif")
        return number
    def percent(value):
        number = float(value.strip().replace(",", "."))
        if not 0 <= number <= 100:
            raise ValueError("Invalid percentage / pourcentage invalide")
        return number
    def check_rate(value, numerator, denominator, label):
        published = percent(value)
        if denominator and abs(published - 100 * numerator / denominator) > 0.020001:
            issues.append(label)
    for line, original in enumerate(rows[1:], 2):
        row = [cell.strip() for cell in original]
        if row[-1] == "" and (len(row)-18) % 6 == 0:
            row = row[:-1]
        if len(row) < 23 or (len(row)-17) % 6:
            raise ValueError(f"Line {line}: expected 17 + 6×N fields / structure invalide ({len(row)})")
        try:
            code, name = row[0], row[1]
            if not code or not name:
                raise ValueError("Missing department / département absent")
            d = {"code":code, "department":name, "status":row[2]}
            d.update({key:integer(row[index]) for key,index in COUNTS.items()})
            if d["registered"] != d["abstentions"] + d["voters"]:
                issues.append(f"{code}: registered != abstentions + voters")
            if d["voters"] != d["blank"] + d["invalid"] + d["valid"]:
                issues.append(f"{code}: voters != blank + invalid + valid")
            if row[2] != "Complet":
                issues.append(f"{code}: status={row[2]}")
            for index,(num,den) in RATES.items():
                check_rate(row[index],d[num],d[den],f"{code}: percentage field {index}")
            candidate_rows=[]
            for start in range(17,len(row),6):
                sex,last,first,votes,share_reg,share_valid=row[start:start+6]
                if not last or not first or sex not in {"F","M"}:
                    raise ValueError("Invalid candidate identity / identité candidat invalide")
                votes=integer(votes)
                candidate=f"{first} {last}"
                check_rate(share_reg,votes,d["registered"],f"{code}: {candidate} / registered")
                check_rate(share_valid,votes,d["valid"],f"{code}: {candidate} / valid")
                candidate_rows.append({"code":code,"department":name,"candidate":candidate,"sex":sex,"votes":votes,"share_valid_published":percent(share_valid),"share_registered_published":percent(share_reg)})
            names=[item["candidate"] for item in candidate_rows]
            if len(names)!=len(set(names)):
                raise ValueError("Duplicate candidate / candidat dupliqué")
            if sum(item["votes"] for item in candidate_rows)!=d["valid"]:
                issues.append(f"{code}: candidate votes sum != valid")
            rosters.append(set(names))
            territories.append(d)
            results.extend(candidate_rows)
        except ValueError as exc:
            raise ValueError(f"Line {line}: {exc}") from exc
    duplicates=[code for code,n in Counter(d["code"] for d in territories).items() if n>1]
    if duplicates:
        raise ValueError(f"Duplicate departments / départements dupliqués: {duplicates}")
    if any(roster != rosters[0] for roster in rosters):
        issues.append("Inconsistent candidate roster / listes de candidats différentes")
    return territories, results, {"encoding":encoding,"issues":issues,"territories":len(territories)}
