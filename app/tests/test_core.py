import unittest
from utils.i18n import load_content, normalize_language
from utils.parser import parse_results

HEADER="Code du département;Libellé du département;Etat saisie;Inscrits;Abstentions;% Abs/Ins;Votants;% Vot/Ins;Blancs;% Blancs/Ins;% Blancs/Vot;Nuls;% Nuls/Ins;% Nuls/Vot;Exprimés;% Exp/Ins;% Exp/Vot;Sexe;Nom;Prénom;Voix;% Voix/Ins;% Voix/Exp"
# Synthetic fixture: never loaded by the application as election data.
ROW="01;Test;Complet;100;20;20,00;80;80,00;2;2,00;2,50;1;1,00;1,25;77;77,00;96,25;F;ALPHA;A;40;40,00;51,95;M;BETA;B;37;37,00;48,05"
class Tests(unittest.TestCase):
    def test_json(self):
        content=load_content()
        self.assertEqual(set(content["fr"]),set(content["en"]))
        self.assertEqual(sum(x["points"] for x in content["fr"]["rubric"]),100)
    def test_locale(self):
        self.assertEqual(normalize_language("en-US"),"en")
        self.assertEqual(normalize_language(None),"fr")
    def test_parse(self):
        d,c,r=parse_results((HEADER+"\n"+ROW).encode())
        self.assertEqual(d[0]["code"],"01")
        self.assertEqual(len(c),2)
        self.assertEqual(r["issues"],[])
    def test_duplicate(self):
        with self.assertRaises(ValueError):
            parse_results((HEADER+"\n"+ROW+"\n"+ROW).encode())
    def test_truncated(self):
        with self.assertRaises(ValueError):
            parse_results((HEADER+"\n"+ROW+";x").encode())
    def test_inconsistent(self):
        d,c,r=parse_results((HEADER+"\n"+ROW.replace(";100;20;",";101;20;")).encode())
        self.assertTrue(r["issues"])
    def test_cp1252_and_trailing_separator(self):
        d,c,r=parse_results((HEADER+"\n"+ROW.replace("Test","Démo")+";").encode("cp1252"))
        self.assertEqual(d[0]["department"],"Démo")
        self.assertEqual(r["issues"],[])
if __name__=="__main__":
    unittest.main()
