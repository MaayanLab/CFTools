# libraries ==> programs
# signatures ==> tools

import os
import time
import re
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import uuid
import requests as req
import ast
from pandas.io.json import json_normalize
from os import listdir
from os.path import isfile, join

load_dotenv(verbose=True)
PTH = os.environ.get('PTH_A')

# CF credentials
API_url = os.environ.get('API_URL')
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
credentials_cf = HTTPBasicAuth(username, password)

# biotoolstory credentials
API_url_bio = os.environ.get('API_URL_bio')
username_bio = os.getenv("USERNAME_bio")
password_bio = os.getenv("PASSWORD_bio")
credentials_bio = HTTPBasicAuth(username_bio, password_bio)

# get cfde tools
res = requests.get(API_url%("signatures",""))
tools_CF = res.json()

# get biotoolstory tools
res = requests.get(API_url_bio%("signatures",""))
tools_Bio = res.json()

# get grant numbers
res = requests.get(API_url%("libraries",""))
programs = res.json()
cfde_numbers = []
for i in range(0,len(programs)):
  if 'Grant_Number' in programs[i]['meta'].keys():
    if programs[i]['meta']['Grant_Number'] != None:
      if len(programs[i]['meta']['Grant_Number']) > 3:
        cfde_numbers.append(programs[i]['meta']['Grant_Number'])
cfde_numbers = list(set(cfde_numbers))


pmids_cf = []
for x in tools_CF:
  for y in x['meta']['PMID']:
    pmids_cf.append(y)
#============================================================================================================================================================
#                                            Functions
#============================================================================================================================================================
def empty_cleaner(obj):
  if type(obj) == str:
    obj = obj.strip()
    if obj == "":
      return None
    else:
      return obj
  elif type(obj) == list:
    new_list = []
    for i in obj:
      v = empty_cleaner(i)
      if v or v==0:
        new_list.append(v)
    if len(new_list) > 0:
      return new_list
    else:
      return None
  elif type(obj) == dict:
    new_dict = {}
    for k,v in obj.items():
      val = empty_cleaner(v)
      if val or val == 0:
        new_dict[k] = val
    if len(new_dict) > 0:
      return new_dict
    else:
      return None
  else:
    return obj


def backup():
  res = requests.get(API_url%("signatures",""))
  tools_DB = res.json()
  df = pd.json_normalize(tools_DB)
  df.to_csv(os.path.join(PTH,'data/CF_tools_dump.csv'),index=False)
  # backup CFDE programs
  res = requests.get(API_url%("libraries",""))
  programs = res.json()
  df = pd.json_normalize(programs)
  df.to_csv(os.path.join(PTH,'data/CF_programs_dump.csv'),index=False)


# detect tools from biotoolstory that are funded by CFDE
def FindNewTools():
  # get existing pmids
  cf_pmids = []
  for x in tools_CF:
    for y in x['meta']['PMID']:
      cf_pmids.append(y)
  # search new tools
  cfde_tools =[]
  pmids = []
  for i in range(0,len(tools_Bio)):
    if 'Grant_List' in tools_Bio[i]['meta'].keys():
      for g in tools_Bio[i]['meta']['Grant_List']:
        if 'GrantID' in g.keys():
          for grant in cfde_numbers:
            if grant in g['GrantID']:
              if (tools_Bio[i]['meta']['PMID'][0] not in pmids) and (tools_Bio[i]['meta']['PMID'][0] not in cf_pmids):
                print('grant:',grant,'id:', g['GrantID'])
                tools_Bio[i]['meta']['CFDE_Grant'] = grant
                cfde_tools.append(tools_Bio[i])
                pmids.append(tools_Bio[i]['meta']['PMID'][0])
  # df = pd.json_normalize(cfde_tools)
  # df.to_csv("/home/maayanlab/Tools/CF/data/tools_bio_cf.csv")
  return(cfde_tools)


# delete a single item
def delete_data(data,schema):
  res = requests.delete(API_url%(schema,data["id"]), auth=credentials_cf)
  if not res.ok:
    raise Exception(res.text)
 

# delete all * from Database
def del_all_tools(schema):
  res = requests.get(API_url%(schema,""))
  tools_DB = res.json()
  i=1
  for tool in tools_DB:
    delete_data(tool,schema)
    print(i)
    i=i+1
#del_all_tools('libraries')


# push data (tools or journals) directly to the biotoolstory server
def post_data(data,model):
  time.sleep(0.5)
  res = requests.post(API_url%(model,""), auth=credentials_cf, json=data)
  try:
    if not res.ok:
      raise Exception(res.text)
  except Exception as e:
    print(e)
    if model == "signatures":
      f = open(os.path.join(PTH,"data/fail_to_load.txt"), "a")
      f.write(','.join(map(str, data['meta']['PMID'])) + "\n")
      f.close()


# push new CFDE programs from dump file
def push_libraries():
  df = pd.read_csv(os.path.join(PTH,'data/CF_programs_dump.csv'))
  df = df.fillna('')
  for i in range(0, len(df)):
    print(i)
    data = {}
    data['$validator'] = df.iloc[i]['$validator']
    data['id'] = str(uuid.uuid4())
    data['resource'] = df.iloc[i]['resource']
    data['dataset'] = df.iloc[i]['dataset']
    data['dataset_type'] = df.iloc[i]['dataset_type']
    data['meta'] = {'pid': df.iloc[i]['meta.pid'], 
                    'Icon': df.iloc[i]['meta.Icon'],
                    'name': df.iloc[i]['meta.name'], 
                    'Title': df.iloc[i]['meta.Title'], 
                    '$validator': '/@dcic/signature-commons-schema/core/unknown.json', 
                    'CF_program': df.iloc[i]['meta.CF_program'], 
                    'Institution': df.iloc[i]['meta.Institution'],
                    'Grant_Number': str(df.iloc[i]['meta.Grant_Number'])
                    }
    data = empty_cleaner(data)
    post_data(data,"libraries")


# update tool information in CFDE
def update(tool):
  time.sleep(1)
  res = requests.patch('https://nih-cfde-tools.org/metadata-api/' +"signatures/" + tool['id'], json=tool, auth=credentials_cf)
  if (not res.ok):
    print(res.text)
    time.sleep(2)
    return ("error")

  
def refresh():
res = requests.get("https://maayanlab.cloud/biotoolstory/metadata-api/optimize/refresh", auth=credentials)
  print(res.ok)
  res = requests.get("https://maayanlab.cloud/biotoolstory/metadata-api/"+"optimize/status", auth=credentials)
  while not res.text == "Ready":
    time.sleep(1)
    res = requests.get("https://maayanlab.cloud/biotoolstory/metadata-api"+"/optimize/status", auth=credentials)
  res = requests.get("https://maayanlab.cloud/biotoolstory/metadata-api/"+"summary/refresh", auth=credentials)
  print(res.ok)
  

# ============================================================================================================================================================ 

if __name__ == "__main__":
  newcftools = FindNewTools() # find new tools
  # push new tools to the CFDE website
  res = requests.get(API_url%("libraries",""))
  programs = res.json()
  errors = []
  for tool in newcftools:
    try:
      tool["library"]  = ''
      cfde_program_key = [x['id'] for x in programs if tool['meta']['CFDE_Grant'] in x['meta']['pid'] ]
      if len(cfde_program_key)>0:
        tool["library"] = cfde_program_key[0] # uuid from libraries TABLE
      else:
        print('no CFDE project number was found')
        break
      if tool['meta']['PMID'][0] not in pmids_cf:
        post_data(tool,"signatures")
        pmids_cf.append(tool['meta']['PMID'][0])
      else:
        print("tool exist in CFDE website")
    except Exception as e:
      print(e)
      errors.append(tool)
