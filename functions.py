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

def databaseDuplicateHandlingFolder(videosDir):
 file_hashes={}
 for filename in os.listdir(videosDir):
  filepath=os.path.join(videosDir,filename)
  if os.path.isfile(filepath)and filename.lower().endswith('.mp4'):
   with open(filepath,'rb')as f:
    file_hash=hashlib.md5(f.read()).hexdigest()
   if file_hash in file_hashes:
    print(f"Deleting duplicate file: {filename}")
    os.remove(filepath)
   else:
    file_hashes[file_hash]=filename

def checkIfAllFilesPresent(databaseCSV,videosDir):
 df=pd.read_csv(databaseCSV)
 for index,row in df.iterrows():
  video_title=row['Title']
  video_path=os.path.join(videosDir,video_title)
  if not os.path.isfile(video_path):
   df=df.drop(index)
 df.to_csv(databaseCSV,index=False)

def pickRandomVideos(databaseCSV,videosDir,makingStage1):
 df=pd.read_csv(databaseCSV)
 available_videos=df[df['Used']==0]
 available_videos=available_videos.sample(frac=1)
 total_length=0
 selected_videos=[]
 max_tries=100
 try_count=0
 for index,row in available_videos.iterrows():
  video_title=row['Title']
  video_length=row['Length']
  if total_length+video_length<=50:
   src_path=os.path.join(videosDir,video_title)
   dest_path=os.path.join(makingStage1,video_title)
   shutil.copyfile(src_path,dest_path)
   df.at[index,'Used']=0
   total_length+=video_length
   selected_videos.append(video_title)
  else:
   try_count+=1
   if try_count>=max_tries:
    break
 df.to_csv(databaseCSV,index=False)
 return selected_videos

def resizeVideos(makingStage1,makingStage2):
 if not os.path.exists(makingStage2):
  os.makedirs(makingStage2)
 for filename in os.listdir(makingStage1):
  if filename.endswith(".mp4")or filename.endswith(".avi"):
   input_path=os.path.join(makingStage1,filename)
   output_path=os.path.join(makingStage2,filename)
   command=["ffmpeg","-i",input_path,"-vf","scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2","-c:a","copy",output_path]
   subprocess.run(command,capture_output=True,text=True)

def getFirstFrame(makingStage2,makingStage3):
 if not os.path.exists(makingStage2)or not os.path.exists(makingStage3):
  print("Error: Input or output directory does not exist.")
  return
 for video_file in os.listdir(makingStage2):
  if video_file.endswith(".mp4")or video_file.endswith(".avi")or video_file.endswith(".mkv"):
   video_path=os.path.join(makingStage2,video_file)
   cap=cv2.VideoCapture(video_path)