from bs4 import BeautifulSoup
from selenium import webdriver
#from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
import time
import logging
import pandas as pd

url = 'https://muteindb.genome.tugraz.at/muteindb-web-2.0/faces/search/findMutein/findMutein.seam'


def fill_mutein_field(driver, url,
                      search_val,
                      mutein_code):
    driver.implicitly_wait(20)
    driver.maximize_window()

    driver.get(url)
    mutein_name_field = driver.find_element_by_id(search_val)
    mutein_name_field.send_keys(mutein_code)
    time.sleep(3)
    mutein_name_field.send_keys(Keys.RETURN)
    time.sleep(3)
    mutein_name_field.send_keys(Keys.RETURN)

    try:
        if "no matching" in driver.find_element_by_xpath("/html/body/div[5]/form/div/div/span").get_attribute(
                "innerHTML"):
            print(f'{mutein_code} not found')
            driver.quit()
            return None
    except:
        print(f'{mutein_code} found')
    return driver.current_url


def get_mutant_name(pg_src):
    soup = BeautifulSoup(pg_src, "html.parser")
    chem_info = []
    # a list
    print(soup.find(id='searchMuteinForm:searchResult:tb'))
    chem_table = soup.find(id='searchMuteinForm:searchResult:tb').contents

    mutant_index = 3

    for row in chem_table:
        # entry['wt'] = row.contents[wt_index].text
        mutant = row.contents[mutant_index].text
        break

    # returns a list
    return mutant


def get_info(pg_src):
    soup = BeautifulSoup(pg_src, "html.parser")
    table = soup.find(id='reactionTabForm:mainReactions:tb').contents
    info = []
    substrate_index = 1
    product_index = 2
    rxn_type_index = 3
    rel_activity_index = 7
    activity_index = 8
    activity_unit_index = 9
    EC_index = 4
    co_protein_index = 14
    pm_id = 16
    # print(table)

    for row in table:
        entry = {}
        entry['substrate'] = row.contents[substrate_index].text
        entry['product'] = row.contents[product_index].text
        entry['reaction'] = row.contents[rxn_type_index].text
        entry['EC'] = row.contents[EC_index].text
        entry['co-protein'] = row.contents[co_protein_index].text
        entry['pub-med-id'] = row.contents[pm_id].text
        entry['rel-act'] = row.contents[rel_activity_index].text
        entry['act'] = row.contents[activity_index].text
        entry['act_unit'] = row.contents[activity_unit_index].text
        info.append(entry)

    return info


def process_seq(driver, cyp_wt, cyp_mutant_name):
    seq_tab = driver.find_element_by_xpath('//*[@id="j_id549_lbl"]').click()

    try:
        print("checking tr[2]")
        seq_view = driver.find_element_by_xpath(
            "/html/body/div[5]/table/tbody/tr[2]/td/table/tbody/tr/td/form/table/tbody/tr[2]/td[2]/pre[1]/span")
    except:
        logging.debug("cant find tr[2], trying tr[3] now")

    try:
        print("checking tr[3]")
        seq_view = driver.find_element_by_xpath(
            "/html/body/div[5]/table/tbody/tr[2]/td/table/tbody/tr/td/form/table/tbody/tr[3]/td[2]/pre[1]/span")
    except:
        print("tr[3] has nth, implies tr[2] passes")

    wt_seq = []
    mutant_seq = []
    fasta_seq = seq_view.text
    print(fasta_seq)
    with open("seq.txt", 'w+') as file:
        file.write(fasta_seq)

    with open("seq.txt", 'r') as file:
        line_index = 0
        no_blank_lines = filter(None, (line.rstrip() for line in file))
        for line in no_blank_lines:
            if not any(chr.isdigit() for chr in line):
                seq_with_no_space = "".join(line.split(" "))
                if line_index % 2 == 0:
                    wt_seq.append(seq_with_no_space)
                else:
                    mutant_seq.append(seq_with_no_space)
                    print(seq_with_no_space)
                line_index += 1

    # print(f'mutant seq: {mutant_seq} ')

    with open(f'fasta_data_latest_wt/{cyp_wt}.fasta', 'w+') as output:
        seq = "".join(wt_seq)
        final_seq = "\n".join([">" + cyp_wt, seq])
        wt_aa = seq
        output.write(final_seq)

    with open(f'fasta_data_latest/{cyp_mutant_name}.fasta', 'w+') as output:
        seq = "".join(mutant_seq)
        final_seq = "\n".join([">" + cyp_mutant_name, seq])
        mutant_aa = seq
        output.write(final_seq)

    # print(f'mutant seq: {mutant_seq} mutant_aa: {mutant_aa}')
    return wt_aa, mutant_aa

def get_organism(pg_src):
    soup = BeautifulSoup(pg_src, "html.parser")
    table = soup.find(id='manageMuteinForm:organismDecoration:organism').contents
    organism = ''
    for info in table:
        organism = info

    return organism

import re
from selenium.webdriver.firefox.options import Options
#from selenium.webdriver.chrome.options import Chrome
firefox_options = Options()
#chrome_options.binary_location = 'chromedriver'
firefox_options.add_argument("--headless")
#firefox_options.add_argument("--disable-gpu")
#firefox_options = None

with open("cyp_mt_codes.txt", "r") as in_file:
    wild_type_table = {'wt_code': [], 'wt_seq': []
                       }

    mutant_table = {'mt_code': [], 'wt_code': [], 'mt_seq': [], 'organism': []
                    }

    rxn_table = {'rxn_id': [], 'mt_code': [], 'substrate': [],
                 'product': [], 'type': [], 'EC': [], 'co_protein': []
                 }

    pub_table = {'pubmed_id': [], 'rxn_id': [], 'mt_code': []
                 }

    mt_activity_table = {'rxn_id': [], 'mt_code': [], 'rel_act': [],
                         'act': [], 'act_unit': []
                         }

    rxn_id = 1
    count = 1
    visited_mutant = set()

    for cyp_mutant in in_file:
        time.sleep(10)
        driver = webdriver.Firefox(options=firefox_options)

        fill_mutein_field(driver, url,
                          "findMuteinForm:searchItemName",
                        cyp_mutant)

        actual_mutant = get_mutant_name(driver.page_source)

        if actual_mutant in visited_mutant:
            continue

        else:
            visited_mutant.add(actual_mutant)

        x_path_cyp_mutant = '/html/body/div[5]/form/table/tbody/tr/td[4]/*[count(child::*) = 0]'
        driver.find_element_by_xpath(x_path_cyp_mutant).click()

        info = get_info(driver.page_source)

        cyp_wt_code = re.split('[-.]', cyp_mutant)[0]
        cyp_mutant_ = cyp_mutant.replace("/", "_")

        wt_seq, mutant_seq = process_seq(driver, cyp_wt_code, cyp_mutant_)

        # get organism data
        driver.find_element_by_xpath('//*[@id="j_id13_lbl"]').click()

        organism = get_organism(driver.page_source)





        print(f'mt_seq: {mutant_seq} wt_seq: {wt_seq}')

        # populate wild type table
        if cyp_wt_code not in wild_type_table['wt_code']:
            wild_type_table['wt_code'].append(cyp_wt_code)
            wild_type_table['wt_seq'].append(wt_seq)
            pd.DataFrame(wild_type_table).to_csv(f'wt_{cyp_wt_code}.csv')
            wild_type_table['wt_code'].clear()
            wild_type_table['wt_seq'].clear()

        # populate mutant table
        # if actual_mutant not in mutant_table['mt_code']:
        mutant_table['mt_code'].append(actual_mutant)
        mutant_table['wt_code'].append(cyp_wt_code)
        mutant_table['mt_seq'].append(mutant_seq)
        mutant_table['organism'].append(organism)

        for chem_info in info:
            # populate rxn table with rxn_id, mt_code
            rxn_table['rxn_id'].append(rxn_id)
            rxn_table['mt_code'].append(actual_mutant)

            # populate rxn table with reactants and product, type of rxn
            rxn_table['substrate'].append(chem_info['substrate'])
            rxn_table['product'].append(chem_info['product'])
            rxn_table['type'].append(chem_info['reaction'])

            # populate rxn table with EC & co-protein
            rxn_table['EC'].append(chem_info['EC'])
            rxn_table['co_protein'].append(chem_info['co-protein'])

            # populate pub table
            pub_table['pubmed_id'].append(chem_info['pub-med-id'])
            pub_table['rxn_id'].append(rxn_id)
            pub_table['mt_code'].append(actual_mutant)

            # populate mt activity table
            mt_activity_table['rxn_id'].append(rxn_id)
            mt_activity_table['mt_code'].append(actual_mutant)
            mt_activity_table['rel_act'].append(chem_info['rel-act'])
            mt_activity_table['act'].append(chem_info['act'])
            mt_activity_table['act_unit'].append(chem_info['act_unit'])

            rxn_id += 1
        print(f'count: {count} rxn: {rxn_id}')
        driver.close()
        count += 1

        pd.DataFrame(mutant_table).to_csv(f'mt_table_{cyp_mutant_}.csv')
        pd.DataFrame(rxn_table).to_csv(f'rxn_table_{cyp_mutant_}.csv')
        pd.DataFrame(pub_table).to_csv(f'publication_table_{cyp_mutant_}.csv')
        pd.DataFrame(mt_activity_table).to_csv(f'mt_act_table_{cyp_mutant_}.csv')

        print(f'{actual_mutant} processed, clearing data for next iteration')

        for key in mutant_table.keys():
            mutant_table[key].clear()

        for key in rxn_table.keys():
            rxn_table[key].clear()

        for key in pub_table.keys():
            pub_table[key].clear()

        for key in mt_activity_table.keys():
            mt_activity_table[key].clear()

