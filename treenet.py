# script to extract existential subjects from Penn-Helsinki Parsed historical corpora (PPME2 and later)
# author: Gard B. Jenset
# Date: July, 2022
# version: 0.1 


import glob
import re
import os
import sys
import math
import time



### Functions ###

# Support functions

def remove_phrase_details(x):
        '''Remove the finer details, including co-indexing, for a broader type of pattern
        :param x: a string to clean
        '''
        
        if x.count('-') > 1:
            x_split = x.split('-')
            out = "-".join(x_split[:2]) # keep only the first two elements, e.g NP-SBJ
        else:
            out = x
        return out

    
def replace_coindex(x):
    '''Replace the co-index numbers with a generic variable
    :param x: a string to clean
    '''
    return re.sub(r'-\d$', '-n', x)


def clean_elements(element_list):
    '''Clean a list of sentence-level elements
    :param element_list: a list of sentence level elements representing a single PPME2 parse tree
    :return: a tuple with two lists of cleaned elements, one detailed, the other broader
    '''
    # Map inflected variants to uninflected ones
    v_elements_dict = {"MD": "MD", "HVD": "HV", "HVP": "HV", "DOP": "DO", "DOD": "DO", "DO": "DO", "VAN": "VAN", 
    "VBP": "VB", "VBD": "VB", "VB": "VB", "NEG+VBP": "VB", 
    "NEG+VB": "VB", "NEG+VBD": "VB", "BEP": "BE", "BED": "BE", "BE": "BE", 
    "NEG+BE": "BE", "NEG+BEP": "BE", "NEG+BED": "BE"} 
    cleaned_list = []
    cleaned_list_broad = []
    
    for e in element_list:
        # Remove brackets, normalise white space, and split:
        e_no_brackets = e.replace('(', '').replace(')', '').replace('  ', ' ')
        e_split = e_no_brackets.split()
        e_out = ''
        e_out_broad = ''
        try:
            if e_split[0].startswith("IP-MAT"):
                #pick up any sentence level constiuents occurring directly after the IP-MAT* tag
                if e_split[1] not in ("LB", "LATIN", "LS", "META", "REF", "CODE", "QTP", "CONJ"):
                    e_out = replace_coindex(e_split[1])
                    e_out_broad = remove_phrase_details(e_out)
            elif e_split[0] == "PP":
                #e_out = "-".join(e_split) # too noisy - used only PP for now
                e_out = e_split[0]
                e_out_broad = e_out
            elif e_split[0] == "VP":
                e_out = e_split[1]
                e_out_broad = v_elements_dict.get(e_out, "VB")
            elif e_split[0] in v_elements_dict.keys():
                e_out = e_split[0]
                e_out_broad = v_elements_dict.get(e_out, "VB")
            elif e_split[0] in ("NEG", "RP", "Q", "FP", "ADV", "INTJ", "NUM", "W"):
                e_out = e_split[0]
                e_out_broad = e_out
            elif e_split[0].startswith("IP"):
                e_out = replace_coindex(e_split[0])
                e_out_broad = remove_phrase_details(e_out)
            elif e_split[0].startswith("CP"):
                e_out = e_split[0]
                e_out_broad = remove_phrase_details(e_out)
            elif e_split[0].startswith("RRP"):
                e_out = e_split[0]
                e_out_broad = remove_phrase_details(e_out)
            elif e_split[0].startswith("ADVP"):
                e_out = replace_coindex(e_split[0])
                e_out_broad = remove_phrase_details(e_out)
            elif e_split[0].startswith("ADJP"):
                e_out = replace_coindex(e_split[0])
                e_out_broad = remove_phrase_details(e_out)
            elif e_split[0].startswith("NP"):
                # the most complex category, since we want to extract more information
                if len(e_split) == 2:
                    e_out = "-".join([replace_coindex(e) for e in e_split]) # e.g. (NP-SBJ *exp*) -> NP-SBJ-*exp* (same for *con*)
                    e_out_broad = remove_phrase_details(e_out)
                elif len(e_split) > 2:
                    e_out = "-".join([replace_coindex(e) for e in e_split if e.isupper()])
                    e_out_broad = remove_phrase_details(e_out)
            else:
                pass 
                # do not include: CODE, foreign language passages like LATIN, META, quotations, and references
            if e_out:
                cleaned_list.append(e_out)
                cleaned_list_broad.append(e_out_broad)
        except IndexError:
            pass

    return cleaned_list, cleaned_list_broad   


def calculate_cx_total_correlation(cx, freq, cx_totals_sum, elem_totals_sum, elem_totals_dict):

    '''Total correlation as a variant of multivariate mutual information, see van de Cruys 2011 (ACL). Helper function for get_total_correlation() to handle Python 2 and 3  
    :param cx construction
    :param freq: raw count of construction
    :cx_totals_sum: sum of all construction occurrences (token frequency)
    :elem_totals_sum: sum of all phrase element occurrences
    :elem_totals_dict: dictionary mapping phrase elements to their global frequency
    :returns: a tuple with construction relative freq and construction total correlation
    '''
    cx_prob = freq/float(cx_totals_sum) # convert to float to avoid integer division in Python 2.7
    my_elements = cx.split()
    my_elements_prob = []
    for e in my_elements:
        my_element_prob = elem_totals_dict.get(e, 0)/float(elem_totals_sum) # convert to float to avoid integer division in Python 2.7
        my_elements_prob.append(my_element_prob)
    
    total_element_prob = my_elements_prob[0]
    for p in my_elements_prob[1:]:
        total_element_prob *= p
    try:
        total_corr = math.log(cx_prob/total_element_prob)
    except ValueError:
        total_corr = None # in case we try to take the log of 0
    return cx_prob, total_corr
    
    
    

def get_total_correlation(total_counts, cx_counts, py_version=3):
    '''Total correlation as a variant of multivariate mutual information, see van de Cruys 2011 (ACL)
    :param total_counts: dict with individual elements and their global counts
    :param cx_counts: dict with construction patterns and their counts
    :returns: a dict with cx patterns (keys) and a tuple with relative frequency and total correlation scores (val)
    '''
    total_construction_count = sum(cx_counts.values())
    total_element_counts = sum(total_counts.values())
    
    out_dict = {}
    
    if py_version==3:
        for k,v in cx_counts.items():
            cx_rel_freq, cx_total_corr = calculate_cx_total_correlation(cx=k, freq=v, cx_totals_sum=total_construction_count, elem_totals_sum=total_element_counts, elem_totals_dict=total_counts)
            out_dict[k] = cx_rel_freq, cx_total_corr
                              
    else:
        for k,v in cx_counts.iteritems():
            cx_rel_freq, cx_total_corr = calculate_cx_total_correlation(cx=k, freq=v, cx_totals_sum=total_construction_count, elem_totals_sum=total_element_counts, elem_totals_dict=total_counts)
            out_dict[k] = cx_rel_freq, cx_total_corr
        
    return out_dict

    
# *Main function* 

def get_constructions(corpus_files, out_folder, min_freq=5, sep="\t"):

    '''Main function to extract construction candidates from the parsed PPME2 files
    :param corpus files: string with the path to folder containing corpus parsed files (.*psd)
    :param out_folder: string with the path to folder where results are saved
    :param min_freq: int with minimum number of cx occurrences. Defaults to 5
    :param sep: string with output file field separator. "\t" (default) or ";"  
    :return: prints results to two files - aggregated results and individual results with metadata
    '''

    # The safe ouput file field separators are \t and ;
    # Reason: cx patterns contain white space and dashes, tree-token IDs contain commas.
    if sep not in ("\t", ";"):
        sys.exit("Output field separator must be one of tabulator or semi-colon. Other values *will* cause problems.")
    
    # make sure that the minimum frequency threshold is an integer:
    min_freq = int(min_freq)
    
    ### Variables ###
    
    ### Global constants for normalizing metadata 

    # ME data
    # dictionary of files and dialects
    me_dialects = {"cmkentho.m1" : "Kentish", "cmpeterb.m1" : "East Midlands", "cmorm.po.m1" : "East Midlands", "cmvices1.m1" : "East Midlands", "cmtrinit.mx1" : "East Midlands", 
    "cmlambx1.mx1" : "West Midlands", "cmlamb1.m1" : "West Midlands", "cmsawles.m1" : "West Midlands", "cmhali.m1" : "West Midlands", "cmkathe.m1" : "West Midlands", "cmjulia.m1" : "West Midlands", "cmmarga.m1" : "West Midlands", "cmancriw-1.m1" : "West Midlands", "cmancriw-2.m1" : "West Midlands",
    "cmkentse.m2" : "Kentish", "cmayenbi.m2" : "Kentish", "cmearlps.m2" : "East Midlands", "cmaelr3.m23" : "West Midlands", "cmrolltr.m24" : "Northern", "cmrollep.m24" : "Northern",
    "cmpolych.m3" : "Southern", "cmntest.m3" : "Southern", "cmpurvey.m3" : "Southern", "cmhorses.m3" : "Southern", "cmroyal.m34" : "Southern",
    "cmctpars.m3" : "East Midlands", "cmctmeli.m3" : "East Midlands", "cmequato.m3" : "East Midlands", "cmwycser.m3" : "East Midlands", "cmboeth.m3" : "East Midlands", "cmotest.m3" : "East Midlands", "cmcloud.m3" : "East Midlands", "cmmandev.m3" : "East Midlands", "cmastro.m3" : "East Midlands", "cmhilton.m34" : "East Midlands", "cmvices4.m34" : "East Midlands", "cmjulnor.m34" : "East Midlands", "cmedvern.m3" : "West Midlands", "cmbrut3.m3" : "West Midlands", "cmmirk.m34" : "West Midlands", "cmbenrul.m3" : "Northern", "cmedthor.m34" : "Northern", "cmgaytry.m34" : "Northern",
    "cmgregor.m4" : "Southern", "cmaelr4.m4"  : "East Midlands", "cmedmund.m4" : "East Midlands", "cmkempe.m4" : "East Midlands", "cmcapser.m4" : "East Midlands", "cmcapchr.m4" : "East Midlands", "cmreynes.m4" : "East Midlands", "cmreynar.m4" : "East Midlands", "cmfitzja.m4" : "East Midlands", "cminnoce.m4": "East Midlands", "cmmalory.m4" : "West Midlands", "cmsiege.m4" : "West Midlands", "cmthorn.mx4" : "Northern"}

    # dicationary of MS dates   
    me_dates = {"cmkentho.m1" : 1125, "cmpeterb.m1" : 1150, "cmorm.po.m1" : 1200, "cmvices1.m1" : 1225, "cmtrinit.mx1" : 1225, 
    "cmlambx1.mx1" : 1225, "cmlamb1.m1" : 1225, "cmsawles.m1" : 1225, "cmhali.m1" : 1225, "cmkathe.m1" : 1225, "cmjulia.m1" : 1225, "cmmarga.m1" : 1225, "cmancriw-1.m1" : 1230, "cmancriw-2.m1" : 1230,
    "cmkentse.m2" : 1275, "cmayenbi.m2" : 1340, "cmearlps.m2" : 1350, "cmaelr3.m23" : 1400, "cmrolltr.m24" : 1440, "cmrollep.m24" : 1450,
    "cmpolych.m3" : 1387, "cmntest.m3" : 1388, "cmpurvey.m3" : 1388, "cmhorses.m3" : 1450, "cmroyal.m34" : 1450,
    "cmctpars.m3" : 1390, "cmctmeli.m3" : 1390, "cmequato.m3" : 1392, "cmwycser.m3" : 1400, "cmboeth.m3" : 1425, "cmotest.m3" : 1425, "cmcloud.m3" : 1425, "cmmandev.m3" : 1425, "cmastro.m3" : 1450, "cmhilton.m34" : 1450, "cmvices4.m34" : 1450, "cmjulnor.m34" : 1450, "cmedvern.m3" : 1390, "cmbrut3.m3" : 1400, "cmmirk.m34" : 1500, "cmbenrul.m3" : 1425, "cmedthor.m34" : 1440, "cmgaytry.m34" : 1440,
    "cmgregor.m4" : 1475, "cmaelr4.m4"  : 1450, "cmedmund.m4" : 1450, "cmkempe.m4" : 1450, "cmcapser.m4" : 1452, "cmcapchr.m4" : 1464, "cmreynes.m4" : 1485, "cmreynar.m4" : 1481, "cmfitzja.m4" : 1495, "cminnoce.m4": 1497, "cmmalory.m4" : 1470, "cmsiege.m4" : 1500, "cmthorn.mx4" : 1440}

    # dictionary of genres
    me_genres = {"cmkentho.m1" : "Homily", "cmpeterb.m1" : "History", "cmorm.po.m1" : "Homily", "cmvices1.m1" : "Religious Treatise", "cmtrinit.mx1" : "Homily", 
    "cmlambx1.mx1" : "Homily", "cmlamb1.m1" : "Homily", "cmsawles.m1" : "Homily", "cmhali.m1" : "Religious Treatise", "cmkathe.m1" : "Biography, Life of Saint", "cmjulia.m1" : "Biography, Life of Saint", 
    "cmmarga.m1" : "Biography, Life of Saint", "cmancriw-1.m1" : "Religious Treatise", "cmancriw-2.m1" : "Religious Treatise",
    "cmkentse.m2" : "Homily", "cmayenbi.m2" : "Religious Treatise", "cmearlps.m2" : "Bible", "cmaelr3.m23" : "Rule", "cmrolltr.m24" : "Religious Treatise", 
    "cmrollep.m24" : "Religious Treatise",
    "cmpolych.m3" : "History", "cmntest.m3" : "Bible", "cmpurvey.m3" : "Religious Treatise", "cmhorses.m3" : "Handbook", "cmroyal.m34" : "Sermon",
    "cmctpars.m3" : "Religious Treatise", "cmctmeli.m3" : "Fiction", "cmequato.m3" : "Handbook", "cmwycser.m3" : "Sermon", "cmboeth.m3" : "Philosophy", "cmotest.m3" : "Bible", 
    "cmcloud.m3" : "Religious Treatise", "cmmandev.m3" : "Travelogue", "cmastro.m3" : "Handbook", "cmhilton.m34" : "Religious Treatise", "cmvices4.m34" : "Religious Treatise", "cmjulnor.m34" : "Religious Treatise", 
    "cmedvern.m3" : "Religious Treatise", "cmbrut3.m3" : "History", "cmmirk.m34" : "Sermon", "cmbenrul.m3" : "Rule", "cmedthor.m34" : "Religious Treatise", "cmgaytry.m34" : "Sermon",
    "cmgregor.m4" : "History", "cmaelr4.m4"  : "Rule", "cmedmund.m4" : "Biography, Life of Saint", "cmkempe.m4" : "Religious Treatise", "cmcapser.m4" : "Sermon", "cmcapchr.m4" : "History", 
    "cmreynes.m4" : "Handbook", "cmreynar.m4" : "Fiction", "cmfitzja.m4" : "Sermon", "cminnoce.m4": "Sermon", "cmmalory.m4" : "Romance", "cmsiege.m4" : "Romance", 
    "cmthorn.mx4" : "Handbook"}

    
    # dictionary to count construction frequencies
    ## key = construction (string), val = count (int)
    cx_count_dict = {}
    
    # dictionary to map constructions to ids:
    ## key = construction (string), val = corpus tree id
    cx_id_dict = {}
    cx_id_dict_broad = {}
    
    # dictionary to map narrow constructions to broader ones
    cx_narrow_to_broad = {}
    
    # count occurrences of individual elements, e.g. "NP-SBJ", "ADVP"
    elements_global_count = {}

    inTree = False
    filenames_list = []
    sent_count = {}
    
    id_to_file_dict = {}
    
    parsed_files = glob.glob(os.path.join(corpus_files, "*.psd"))
    
    # check that at least 1 corpus file was found:
    if len(parsed_files) == 0:
        sys.exit("No .psd parsed corpus files found in location.")
    
    # iterate over files in directory
    for file in parsed_files :
        myFile = open(file, 'r')
        file_name = os.path.basename(file)
        file_name_clean = file_name.replace(".psd", "")
        filenames_list.append(file_name_clean)
        
        # currently not used:
        # extract EME or ME period from filename, e.g. m1, e2
        myPeriod_match = re.match(r'.*?\.([em]\d\d?)\.psd', file_name)
        if myPeriod_match:
            myPeriod = myPeriod_match.group(1)
            
        # iterate over each line in each file
        for line in myFile :
            beginTree_match = re.match(r'.*?\(IP-MAT.*?(\(ADVP|PP.*?)?', line)
            if beginTree_match:
                print("begin")
                sent_count[file_name_clean] = sent_count.get(file_name_clean, 0) + 1
                inTree = True

                wo_list = []
                wo_list_clean = []

                
                wo_list.append(line.strip())
                beginTree_match = None
                sub_match = None
                
            if inTree:
                # check that we are one tab indentations in
                if len(line.split("\t")) == 2:
                    # TODO:
                    # some trees might have an extra indentation for conjunction phrases (CONJP)
                    # The complement such as a PP or NP continues on the next line
                    # check if the line ends with a CONJP
                    
                    wo_list.append(line.strip())
                    
                else :
                    continue
                # check if reached end of tree:        
                endTree_match = re.match(r'.*?\(ID (CM.*?)\).*?', line)
                if endTree_match:
                    print("end")
                    
                    # Reached end of the current tree. Now process the it
                    wo_list_clean, wo_list_clean_broad = clean_elements(wo_list)
                    wo_list_clean_str = " ".join(wo_list_clean)
                    wo_list_clean_broad_str = " ".join(wo_list_clean_broad)
                    
                    if len(wo_list_clean) > 1 and len(set(wo_list_clean)) > 1:    
                        # update dictionaries
                        id = endTree_match.group(1)
                        
                        id_to_file_dict[id] = file_name_clean
                        cx_id_dict[wo_list_clean_str] = id
                        cx_id_dict_broad[wo_list_clean_broad_str] = id
                        cx_narrow_to_broad[wo_list_clean_str] = wo_list_clean_broad_str
                        
                        for e in wo_list_clean:
                            elements_global_count[e] = elements_global_count.get(e, 0) + 1
                        
                        cx_count_dict[wo_list_clean_str] = cx_count_dict.get(wo_list_clean_str, 0) + 1

                    inTree = False
                    endTree_match = None

    print("done with files")
   
    
    current_time = time.strftime("%Y-%m-%d_%H_%M")
    base_name_out_aggregated = "treenet_aggregated_{}.txt".format(current_time)
    base_name_out_full = "treenet_full_data_{}.txt".format(current_time)
    
    out_agg = open(os.path.join(out_folder, base_name_out_aggregated), 'w')
    out_full = open(os.path.join(out_folder, base_name_out_full), 'w')
    
    # write header:
    out_agg_header_str = sep.join(["cx_broad", "cx_narrow", "freq", "rel_freq", "specific_correlation"])
    out_agg.write("{}\n".format(out_agg_header_str))
    
    out_full_header_str = sep.join(["cx_broad", "cx_narrow", "rel_freq", "specific_correlation", "id",
                "year", "genre", "dialect"])
    out_full.write("{}\n".format(out_full_header_str))
    
    if str(sys.version)[0] == '3':
        cx_pruned_count_dict = {k: v for k, v in cx_count_dict.items() if v >= min_freq} 
        
        cx_metrics = get_total_correlation(total_counts=elements_global_count, cx_counts=cx_pruned_count_dict, py_version=3)
        
        for k,v in cx_pruned_count_dict.items():
            my_id = cx_id_dict.get(k, '')
            my_file = id_to_file_dict.get(my_id, '')
            try:
                my_metrics = cx_metrics[k]
            except KeyError:
                my_metrics = None, None
            
            out_agg_values = [ cx_narrow_to_broad.get(k, ''), k, v, my_metrics[0], my_metrics[1] ]
            out_agg_values_str = sep.join([str(x) for x in out_agg_values])
            out_agg.write("{}\n".format(out_agg_values_str))
            
            out_full_values = [cx_narrow_to_broad.get(k, ''), k, my_metrics[0], my_metrics[1], my_id, me_dates.get(my_file, ''), me_genres.get(my_file, ''), me_dialects.get(my_file, '')]
           
            
            out_full_values_str = sep.join([str(x) for x in out_full_values])       
            
            out_full.write("{}\n".format(out_full_values_str))
            
            
    else:
        cx_pruned_count_dict = {k: v for k, v in cx_count_dict.iteritems() if v >= min_freq} # Python 2.7 requires .iteritems(()
        cx_metrics = get_total_correlation(total_counts=elements_global_count, cx_counts=cx_pruned_count_dict, py_version=2)
        
        for k,v in cx_pruned_count_dict.iteritems():
            my_id = cx_id_dict.get(k, '')
            my_file = id_to_file_dict.get(my_id, '')
            try:
                my_metrics = cx_metrics[k]
            except KeyError:
                my_metrics = None, None
            
            out_agg_values = [ cx_narrow_to_broad.get(k, ''), k, v, my_metrics[0], my_metrics[1] ]

            out_agg_values_str = sep.join([str(x) for x in out_agg_values])
            out_agg.write("{}\n".format(out_agg_values_str))
            
            out_full_values = [cx_narrow_to_broad.get(k, ''), k, my_metrics[0], my_metrics[1],
                        my_id, me_dates.get(my_file, ''), me_genres.get(my_file, ''), me_dialects.get(my_file, '')]
            out_full_values_str = sep.join([str(x) for x in out_full_values])       
            
            out_full.write("{}\n".format(out_full_values_str))
            

    # close filehandles before exiting
    out_agg.close()
    out_full.close()
    
    print("Found {} types and {} tokens".format(len(cx_pruned_count_dict.keys()), sum(cx_pruned_count_dict.values())))
    
    
if __name__ == "__main__":

    user_args = sys.argv[1:]
    if len(user_args) < 2:
        sys.exit("To use script, specify minimum the path to corpus files and an output directory")
    elif len(user_args) == 2:
        get_constructions(corpus_files=user_args[0], out_folder=user_args[1])
    elif len(user_args) == 3:
        get_constructions(corpus_files=user_args[0], out_folder=user_args[1], min_freq=user_args[2])
    else:
        get_constructions(corpus_files=user_args[0], out_folder=user_args[1], min_freq=user_args[2], sep=user_args[3])
