import PySimpleGUI as psg
import time
import datetime
import requests
import pandas as pd
import sqlalchemy
import re
import sys
from pathlib import Path

list_identifiers = [{"code":17, "symbol":"NIFTY","instr":"index"},
                    {"code":17, "symbol":"BANKNIFTY","instr":"index"},
                    {"code":17, "symbol":"NIFTYINFRA","instr":"index"},
                    {"code":17, "symbol":"NIFTYIT","instr":"index"},
                    {"code":17, "symbol":"NIFTYMID50","instr":"index"},
                    {"code":17, "symbol":"S%26P500","instr":"index"},
                    {"code":17, "symbol":"FTSE100","instr":"index"},
                    {"code":17, "symbol":"NIFTYCPSE","instr":"index"},
                    {"code":242, "symbol":"RELIANCE", "instr":"stock"},
                    {"code":238, "symbol":"SBIN", "instr":"stock"},
                    {"code":1606, "symbol":"ICICIBANK", "instr":"stock"},
                    {"code":1693, "symbol":"AXISBANK", "instr":"stock"},
                    {"code":2143, "symbol":"MARUTI", "instr":"stock"},
                    {"code":180, "symbol":"INFY", "instr":"stock"},
                    {"code":2328, "symbol":"SUZLON", "instr":"stock"},
                    {"code":818, "symbol":"ITC", "instr":"stock"},
                    {"code":2009, "symbol":"PNB", "instr":"stock"},
                    {"code":211, "symbol":"TATAMOTORS", "instr":"stock"},
                    {"code":2143, "symbol":"MARUTI", "instr":"stock"},
                    {"code":797, "symbol":"HDFCBANK", "instr":"stock"},
                    {"code":3691, "symbol":"COALINDIA", "instr":"stock"},
                    {"code":679, "symbol":"M%26M", "instr":"stock"},
                    {"code":2249, "symbol":"NTPC", "instr":"stock"},
                    {"code":2749, "symbol":"BAJAJFINSV", "instr":"stock"},
                    {"code":233, "symbol":"TITAN", "instr":"stock"},
                    {"code":234, "symbol":"TATASTEEL", "instr":"stock"},
                    {"code":818, "symbol":"ITC", "instr":"stock"},
                    {"code":2660, "symbol":"POWERGRID", "instr":"stock"},
                    {"code":1594, "symbol":"GAIL", "instr":"stock"},
                    {"code":854, "symbol":"IOC", "instr":"stock"},
                    {"code":199, "symbol":"BPCL", "instr":"stock"},
                    {"code":221, "symbol":"HINDPETRO", "instr":"stock"},
                    {"code":467, "symbol":"ONGC", "instr":"stock"}
                ]

list_selected = []

dict_urls = {
                "index":
                [
                    "https://nseindia.com/live_market/dynaContent/live_watch/option_chain/optionKeys.jsp?segmentLink=",
                    "&instrument=OPTIDX&symbol=",
                    "&date="
                ],
                "stock":
                [
                    "https://nseindia.com/live_market/dynaContent/live_watch/option_chain/optionKeys.jsp?symbolCode=",
                    "&symbol=",
                    "&date="
                ]
            }

list_crawl_frequency = [5, 10, 15, 30]

str_help_text = "STEP 1: Load symbols from listbox on the left to the listbox on the right. \
                STEP 2: Click validate.\
                STEP 3: Select checkbox. Crawling will happen in N minute intervals. \
                Between crawls, you may de-select the checkbox to pause.\
                While running the window will freeze."

layout = [
            [
                psg.Listbox(values=[item['symbol'] for item in list_identifiers], size=(30, 6), key="_LIST_ALL_SYM_"),
                psg.Button(">>>", key="_ADD_"),
                psg.Button("<<<", key="_REMOVE_"),
                psg.Listbox(values=list_selected, size=(30, 6), key="_LIST_CHOSEN_SYM_")
            ],
            [
                psg.Text("Inactive", key="_INDICATOR_"),
                psg.Checkbox('', key="_LIVE_", default=False, size=(5,1), disabled=True), 
                psg.Combo(list_crawl_frequency, key="_FREQ_", size=(5,1)), 
                psg.Button("Validate", key="_VALIDATE_")
            ],
            [psg.Output(size=(80,20))],            
            [psg.Button("Help Text"), psg.Button("Close")]
        ]

def fetchData(final_url, str_symbol, secType, matDate):
    #INPUT: nseindia.com option chain URL ('https://nseindia.com/live_market/dynaContent/live_watch/option_chain/optionKeys.jsp?segmentLink=17&instrument=OPTIDX&symbol=BANKNIFTY&date=23AUG2018')
    #INPUT: string security type: "stock" or "index"
    #OUTPUT: returns pandas dataframe with scraped table
    while True:
        try:
            page = requests.get(final_url)
        except requests.exceptions.ConnectionError: #in case there's a connection error:
            print(datetime.datetime.now().strftime("[%H:%M:%S]") + " ConnectionError in fetchAndInsert(). Retrying in 15s.")
            time.sleep(15) #wait 15 seconds and try again
            continue
        break
    page.status_code
    page.content
    try:
        y = pd.read_html(page.content)[0][[1]]
    except ValueError as e:
        #in case no table is found
        print(datetime.datetime.now().strftime("[%H:%M:%S]") + str(e))
    pass
    y=y.to_string()
    
    #handle stock/index differently
    if (secType == "index"):
        assetValue = y[y.find("Index: ")+7:y.find(" As on")]
        asset = str_symbol
        assetValue = ''.join([str(elem) for elem in re.findall('[0-9.]',assetValue)])
    if (secType == "stock"):
        assetValue = y[y.find("Stock: ")+7:y.find(" As on")]
        asset = str_symbol
        assetValue = ''.join([str(elem) for elem in re.findall('[0-9.]',assetValue)])
    crawlTimeStamp =  datetime.datetime.now().isoformat(' ')
    
    #take the entire page into 3 dataframes, pick the middle one since it has the table
    raw_table = pd.read_html(page.content)[1]
    
    #give names to all the columns. Note that there are duplicates
    raw_table.columns = ['Chart','OI','Chng in OI','Volume','IV','LTP','Net Chng','BidQty','BidPrice','AskPrice','AskQty','Strike Price','BidQty','BidPrice','AskPrice','AskQty','Net Chng','LTP','IV','Volume','Chng in OI','OI','Chart']
    
    #drop the top two rows as they are not needed
    raw_table=raw_table.drop(raw_table.index[[0,1]])
    #replace all dashes with zeroes
    x = raw_table.replace(to_replace="-", value=0.0)
    #drop the "chart" columns. Since names are duplicated, giving one column name drops both columns with the shared name
    #here "1" means Columns Axis.
    x=x.drop('Chart',1)
    #convert all cells in dataframe to numerical data format
    x.apply(pd.to_numeric, errors='ignore')
    #rename all columns so that there are no duplicates
    x.columns=['CALL_OI', 'CALL_ChngInOI', 'CALL_Volume', 'CALL_IV', 'CALL_LTP', 'CALL_NetChng', 'CALL_BidQty', 'CALL_BidPrice', 'CALL_AskPrice', 'CALL_AskQty', 'StrikePrice', 'PUT_BidQty', 'PUT_BidPrice', 'PUT_AskPrice', 'PUT_AskQty', 'PUT_NetChng', 'PUT_LTP', 'PUT_IV', 'PUT_Volume', 'PUT_ChngInOI', 'PUT_OI']
    #add columns for holding:
    x['Underlying']=asset               #symbol of underlying
    x['UnderlyingValue']=assetValue     #value of underlying at time of crawl
    x['CrawlTimestamp']=crawlTimeStamp  #time of crawl
    x['MaturityDate']=matDate           #maturity of the option

    return x
    
def data2csv(df_x, str_symbol):
    #INPUT: df_x dataframe with options data. last row is removed since it contains a useless summary
    #INPUT: str_symbol symbol of the data, which becomes the file name
    #OUTPUT: nothing returned. If file exists, data is appended without headers, otherwise with headers
    df_x=df_x[:-1]
    if Path(str_symbol+".csv").is_file():
        with open(str_symbol+".csv", 'a') as f:
            df_x.to_csv(f, header=False)
    else:
        with open(str_symbol+".csv", 'a') as f:
            df_x.to_csv(f, header=True)

def getMatDateList(base_url):
    #INPUT: nseindia.com option chain URL ('https://nseindia.com/live_market/dynaContent/live_watch/option_chain/optionKeys.jsp?segmentLink=17&instrument=OPTIDX&symbol=BANKNIFTY')
    #OUTPUT:  [n,1] list of strings of the format DDMMMYYYY ('30AUG2018')
    while True:
        try:
            page = requests.get(base_url)
        except requests.exceptions.ConnectionError: #in case there's a connection error:
            print(datetime.datetime.now().strftime("[%H:%M:%S]") + " ConnectionError in getMatDateList(). Retrying in 15s.")
            time.sleep(15) #wait 15 seconds and try again
            continue
        break
    content=page.text
    x1=content.find('<option value="select"> Select </option>')
    x2=content.find('</select>', x1)
    rawlist=content[x1:x2]
    datelist=re.findall('[0-9]{2}[A-Z]{3}[0-9]{4}', rawlist)
    datelist=list(set(datelist))
    print("base url: ", base_url)
    print("datelist: ",datelist)
    return datelist

def zip_url2(l_select, l_id, d_url):
    #INPUT: l_select - [1,N] list of NSE symbols
    #INPUT: l_id - [1,N] list of dictionaries like {"code":<int>, "symbol":<string>, "instr":<string>}
    #INPUT: dictionary listing URL fragments {<instr name>:[<strings of url fragments>]}
    #OUTPUT: l_id zipped with fragments from d_url, and base url appended as 'url', filtered for l_select symbols
    for d in l_id:
        if d['instr']=="stock":
            d['url_fragment'] = dict_urls['stock']
            d['base_url']=dict_urls['stock'][0] + str(d['code']) +dict_urls['stock'][1] + d['symbol']
        if d['instr']=="index":
            d['url_fragment']=dict_urls["index"]
            d['base_url']=dict_urls['index'][0] + str(d['code']) +dict_urls['index'][1] + d['symbol']
    print("zip url: ",[item for item in list_identifiers if item['symbol'] in l_select])
    return [item for item in list_identifiers if item['symbol'] in l_select]

def zip_url(l_select, l_id):
    #INPUT: l_select - [1,N] list of NSE symbols
    #INPUT: l_id - [1,N] list of dictionaries like {"code":<int>, "symbol":<string>, "instr":<string>}
    #INPUT: dictionary listing URL fragments {<instr name>:[<strings of url fragments>]}
    #OUTPUT: l_id zipped with fragments from d_url, and base url appended as 'url', filtered for l_select symbols
    for d in l_id:
        if d['instr']=="stock":
            d['base_url']="https://www.nseindia.com/live_market/dynaContent/live_watch/option_chain/optionKeys.jsp?symbol=" + d['symbol']
        if d['instr']=="index":
            d['base_url']="https://nseindia.com/live_market/dynaContent/live_watch/option_chain/optionKeys.jsp?segmentLink=17&instrument=OPTIDX&symbol=" + d['symbol']
    print("zip url: ",[item for item in list_identifiers if item['symbol'] in l_select])
    return [item for item in list_identifiers if item['symbol'] in l_select]

def main():
    window_NSEOCE = psg.Window("NSE Option Chain Extractor", layout)
    while True:
        event, values = window_NSEOCE.Read(timeout=100)
        int_frequency = window_NSEOCE.Element('_FREQ_').Get()
        if event in (None, 'Close'):   # if user closes window or clicks cancel
            window_NSEOCE.Close()
            break
        
        if event =="Help Text":
            print(str_help_text)
        
        if event == '_ADD_':
            try:
                if values["_LIST_ALL_SYM_"][0] not in list_selected:
                    list_selected.append(values["_LIST_ALL_SYM_"][0])
                    window_NSEOCE.Element("_LIST_CHOSEN_SYM_").Update(values=list_selected)
                else:
                    psg.popup("The symbol has already been selected.")
                values["_LIST_CHOSEN_SYM_"] = list_selected
            except (ValueError,IndexError):
                psg.popup("Nothing selected!")

        if event == '_REMOVE_':
            try:
                list_selected.remove(values["_LIST_CHOSEN_SYM_"][0])
                window_NSEOCE.Element("_LIST_CHOSEN_SYM_").Update(values=list_selected)
            except (ValueError,IndexError):
                psg.popup("Nothing selected!")

        if event == '_VALIDATE_':
            str_mat = "&date="
            #l_id = zip_url2(list_selected, list_identifiers, dict_urls)
            l_id = zip_url(list_selected, list_identifiers)
            for item in l_id:
                item['mats'] = getMatDateList(item['base_url'])
                item['final_url']=[]
                for mat in item['mats']:
                    item['final_url'] += [item['base_url'] + str_mat + mat]
            print(l_id)
            print([item['final_url'] for item in l_id])
            window_NSEOCE.Element('_LIVE_').Update(disabled=False)

        if values['_LIVE_']==False:
            window_NSEOCE.Element('_INDICATOR_').Update(value="Inactive", text_color="red")

        if values['_LIVE_']==True:
            window_NSEOCE.Element('_INDICATOR_').Update(value="Active", text_color="green")
            if datetime.datetime.now().minute % int(int_frequency) == 0:
                print(datetime.datetime.now())
                for item in l_id:
                    str_sym = item['symbol']
                    for i in range(0,len(item['mats'])):
                        str_mat = item['mats'][i]
                        secType = item['instr']
                        data2csv(fetchData(item['final_url'][i],str_sym, secType , str_mat), str_sym)
                        print("Finished for symbol: {}, for maturity: {}".format(str_sym, str_mat))
                time.sleep(60)

if __name__ == "__main__":
    main()
