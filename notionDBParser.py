import pandas as pd
from datetime import datetime
import uuid
import os
import hashlib

class NotionParser:
  def __init__(self, data):
    self.data = []
    self.files = {}
    results = data['results']
    for result in results:
      obj = {}
      properties = result['properties']
      for property_name, property in properties.items():
        obj[property_name] = self.get_properties(property)
      self.data.append(obj)
  def get_properties(self, property_obj):
    val_type = property_obj['type']
    raw_val = property_obj[val_type]
    if val_type == 'multi_select':
      val = []
      for i in raw_val:
        val.append(i['name'])
        
    elif val_type == 'select':
      val = raw_val['name'] if raw_val else None
      
    elif val_type == 'title':
      val = raw_val[0]['plain_text'] if raw_val else None
      
    elif val_type == 'url':
      val = raw_val['url'] if raw_val else None
      
    elif val_type == 'files':
      val = []
      for i,v in enumerate(raw_val):
        unique_string = f"{property_obj['id']}{v['name']}{i}"
        hash_key = hashlib.md5(unique_string.encode()).hexdigest()
        _, file_extension = os.path.splitext(v['name'])
        hashed_file_neme = f"{hash_key}{file_extension}"
        val.append(hashed_file_neme)
        self.files[hashed_file_neme] = v
      
    elif val_type == 'checkbox':
      val = raw_val
      
    elif val_type == 'rich_text':
      val = raw_val[0]['plain_text'] if raw_val else None
    else:
      print("error")
      raise Exception(f"val_type not impemented: {val_type}")
    return val

  def parse_results(self):
    records = []
    for result in self.data["results"]:
        record = self.parse_properties(result["properties"])
        records.append(record)
    return records

# Usage
