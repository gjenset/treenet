import unittest
import treenet as tnt


class TestRemovePhraseDetails(unittest.TestCase):
    def runTest(self):
        self.assertEqual(tnt.remove_phrase_details('NP-SBJ-1-D-N'), 'NP-SBJ', 'Phrase simplification test assertion failed')
        

        
class TestReplaceCoIndex(unittest.TestCase):
    def runTest(self):
        self.assertEqual(tnt.replace_coindex('NP-SBJ-1'), 'NP-SBJ-n', 'Coindex replacement test assertion failed')
        

class TestCleanElementsNarrow(unittest.TestCase):
    def runTest(self):
        wo_list_test = ["(IP-MAT (ADVP-TMP (ADV Thenne)", "(BED was)", "(NP-SBJ (D the) (N kyng))", "(ADJP (ADVR wonderly) (ADJ wroth))"]
        self.assertEqual(" ".join(tnt.clean_elements(wo_list_test)[0]), "ADVP-TMP BED NP-SBJ-D-N ADJP", "Narrow pattern extraction failed")
        
class TestCleanElementsBroad(unittest.TestCase):
    def runTest(self):
        wo_list_test = ["(IP-MAT (ADVP-TMP (ADV Thenne)", "(BED was)", "(NP-SBJ (D the) (N kyng))", "(ADJP (ADVR wonderly) (ADJ wroth))"]
        self.assertEqual(" ".join(tnt.clean_elements(wo_list_test)[1]), "ADVP-TMP BE NP-SBJ ADJP", "Broad pattern extraction failed")

class TestCalcRelFreq(unittest.TestCase):
    def runTest(self):
        x = "a b c"
        y = 5
        z = 10
        w = 20
        v = {'a': 2, 'b': 3, 'c': 4}
        # y/z
        self.assertEqual(round(tnt.calculate_cx_total_correlation(x, y, z, w, v)[0], 2), 0.5, 'Relative frequency calculation failed')
        
class TestCalcCorrelation(unittest.TestCase):
    def runTest(self):
        x = "a b c"
        y = 5
        z = 10
        w = 20
        v = {'a': 2, 'b': 3, 'c': 4}
        # round(log(0.5/(2/20 * 3/20 * 4/20)), 2)
        self.assertEqual(round(tnt.calculate_cx_total_correlation(x, y, z, w, v)[1], 2), 5.12, 'Correlation calculation failed')
        
        
unittest.main()