import os,csv,shutil,subprocess,pandas as pd,hashlib,re
from tqdm import tqdm
import time,random
import requests
from moviepy.editor import *
import uuid
from variables import *

pytesseract.pytesseract.tesseract_cmd='C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

def safe_move(src_path,dest_path,max_retries=3,delay=5):
 retries=0
 while retries<max_retries:
  try:
   shutil.move(src_path,dest_path)
   return True
  except PermissionError as e:
   print(f"PermissionError: {e}. Retrying in {delay} seconds...")
   time.sleep(delay)
   retries+=1
 return False

def generateRandomTitle():
 uid=str(uuid.uuid4())[:7]
 return uid+".mp4"

def databaseNewFileHandling(databaseCSV,newVideosDir,videosDir):
 existing_data=[]
 with open(databaseCSV,'r')as file:
  reader=csv.reader(file)
  existing_data=list(reader)
 new_files=[f for f in os.listdir(newVideosDir)if os.path.isfile(os.path.join(newVideosDir,f))]
 progress_bar_update=tqdm(new_files,desc="Updating CSV",unit="file")
 for new_file in progress_bar_update:
  file_path=os.path.join(newVideosDir,new_file)
  if os.path.splitext(new_file)[1].lower()=='.mp4':
   try:
    while True:
     random_title=generateRandomTitle()
     if not any(row[0]==random_title for row in existing_data):
      break
    video_clip=VideoFileClip(file_path)
    video_length=int(video_clip.duration)
    existing_data.append([random_title,0,video_length,0])
    video_clip.close()
    os.rename(file_path,os.path.join(videosDir,random_title))
   except Exception as e:
    print(f"Error processing file {new_file}: {e}")
    os.remove(file_path)
    new_files.remove(new_file)
  else:
   print(f"Skipped non-MP4 file: {new_file}")
   os.remove(file_path)
   new_files.remove(new_file)
 with open(databaseCSV,'w',newline='')as file:
  writer=csv.writer(file)
  writer.writerows(existing_data)

def databaseDuplicateHandlingCSV(databaseCSV):
 df=pd.read_csv(databaseCSV)
 df.drop_duplicates(subset='Title',keep='first',inplace=True)
 df.to_csv(databaseCSV,index=False)