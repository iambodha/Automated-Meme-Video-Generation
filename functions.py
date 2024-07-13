import os
import csv
import shutil
import subprocess
import pandas as pd
import hashlib
import re
from tqdm import tqdm
import time
import random
from PIL import Image
import cv2
import pytesseract
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import requests
from moviepy.editor import VideoFileClip, concatenate_videoclips
from PIL import Image
from pydub import AudioSegment
import imageio
from watermark import File, Watermark, apply_watermark, Position
import uuid
from variables import databaseCSV,newVideosDir,videosDir,webdriver_path,makingStage1,makingStage2,makingStage3,makingStage4,makingStage5,makingStage6,makingStage7,makingStage8,makingStage9,outputDir,waterMark

pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

def safe_move(src_path, dest_path, max_retries=3, delay=5):
    retries = 0
    while retries < max_retries:
        try:
            shutil.move(src_path, dest_path)
            return True
        except PermissionError as e:
            print(f"PermissionError: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
            retries += 1
    return False

def generateRandomTitle():
    uid = str(uuid.uuid4())[:7]
    return uid + ".mp4"

def databaseNewFileHandling(databaseCSV, newVideosDir, videosDir):
    existing_data = []

    with open(databaseCSV, 'r') as file:
        reader = csv.reader(file)
        existing_data = list(reader)

    new_files = [f for f in os.listdir(newVideosDir) if os.path.isfile(os.path.join(newVideosDir, f))]

    progress_bar_update = tqdm(new_files, desc="Updating CSV", unit="file")

    for new_file in progress_bar_update:
        file_path = os.path.join(newVideosDir, new_file)

        if os.path.splitext(new_file)[1].lower() == '.mp4':
            try:
                while True:
                    random_title = generateRandomTitle()
                    if not any(row[0] == random_title for row in existing_data):
                        break

                video_clip = VideoFileClip(file_path)
                video_length = int(video_clip.duration)
                existing_data.append([random_title, 0, video_length, 0])
                video_clip.close()

                os.rename(file_path, os.path.join(videosDir, random_title))

            except Exception as e:
                print(f"Error processing file {new_file}: {e}")
                os.remove(file_path)
                new_files.remove(new_file)
        else:
            print(f"Skipped non-MP4 file: {new_file}")
            os.remove(file_path)
            new_files.remove(new_file)

    with open(databaseCSV, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(existing_data)

def databaseDuplicateHandlingCSV(databaseCSV):
    df = pd.read_csv(databaseCSV)
    df.drop_duplicates(subset='Title', keep='first', inplace=True)
    df.to_csv(databaseCSV, index=False)

def databaseDuplicateHandlingFolder(videosDir):
    file_hashes = {}

    for filename in os.listdir(videosDir):
        filepath = os.path.join(videosDir, filename)

        if os.path.isfile(filepath) and filename.lower().endswith('.mp4'):
            with open(filepath, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            if file_hash in file_hashes:
                print(f"Deleting duplicate file: {filename}")
                os.remove(filepath)
            else:
                file_hashes[file_hash] = filename

def checkIfAllFilesPresent(databaseCSV, videosDir):
    df = pd.read_csv(databaseCSV)

    for index, row in df.iterrows():
        video_title = row['Title']
        video_path = os.path.join(videosDir, video_title)

        if not os.path.isfile(video_path):
            df = df.drop(index)

    df.to_csv(databaseCSV, index=False)


def pickRandomVideos(databaseCSV, videosDir, makingStage1):
    df = pd.read_csv(databaseCSV)
    available_videos = df[df['Used'] == 0]
    available_videos = available_videos.sample(frac=1)
    total_length = 0
    selected_videos = []
    max_tries = 100
    try_count = 0

    for index, row in available_videos.iterrows():
        video_title = row['Title']
        video_length = row['Length']

        if total_length + video_length <= 50:
            src_path = os.path.join(videosDir, video_title)
            dest_path = os.path.join(makingStage1, video_title)
            shutil.copyfile(src_path, dest_path)

            df.at[index, 'Used'] = 0
            total_length += video_length
            selected_videos.append(video_title)
        else:
            try_count += 1

            if try_count >= max_tries:
                break

    df.to_csv(databaseCSV, index=False)

    return selected_videos

def resizeVideos(makingStage1, makingStage2):
    if not os.path.exists(makingStage2):
        os.makedirs(makingStage2)

    for filename in os.listdir(makingStage1):
        if filename.endswith(".mp4") or filename.endswith(".avi"):
            input_path = os.path.join(makingStage1, filename)
            output_path = os.path.join(makingStage2, filename)

            command = [
                "ffmpeg",
                "-i", input_path,
                "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
                "-c:a", "copy",
                output_path
            ]

            subprocess.run(command, capture_output=True, text=True)

def getFirstFrame(makingStage2, makingStage3):
    if not os.path.exists(makingStage2) or not os.path.exists(makingStage3):
        print("Error: Input or output directory does not exist.")
        return

    for video_file in os.listdir(makingStage2):
        if video_file.endswith(".mp4") or video_file.endswith(".avi") or video_file.endswith(".mkv"):
            video_path = os.path.join(makingStage2, video_file)
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                print(f"Error: Unable to open video file {video_file}")
                continue

            ret, frame = cap.read()

            if ret:
                frame_path = os.path.join(makingStage3, f"{os.path.splitext(video_file)[0]}.jpg")
                cv2.imwrite(frame_path, frame)

            cap.release()


def getAllCoveredFrames(makingStage3,makingStage4):
 if not os.path.exists(makingStage4):
  os.makedirs(makingStage4)
 for filename in os.listdir(makingStage3):
  if filename.endswith(".jpg"):
   img_path=os.path.join(makingStage3,filename)
   img=cv2.imread(img_path)
   img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
   print(img.shape)
   hImg,wImg,_=img.shape
   boxes=pytesseract.image_to_data(img)
   for a,b in reversed(list(enumerate(boxes.splitlines()))):
    if a!=0:
     b=b.split()
     print(b)
     if len(b)==12 and float(b[10])>=0.90:
      x,y,w,h=map(int,b[6:10])
      new_w=int(w*1.15)
      new_h=int(h*1.15)
      new_x=max(0,x-int((new_w-w)/2))
      new_y=max(0,y-int((new_h-h)/2))
      img[new_y:new_y+new_h,new_x:new_x+new_w]=[255,255,255]
      img=cv2.cvtColor(img,cv2.COLOR_RGB2BGR)
      output_path=os.path.join(makingStage4,f'{a}_{filename}')
      cv2.imwrite(output_path,img)
      img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)

def getTextList(makingStage3):
 if not makingStage3.endswith('/'):
  makingStage3+='/'
 textDict={}
 files=[f for f in os.listdir(makingStage3)if f.lower().endswith('.jpg')]
 for file in files:
  file_path=makingStage3+file
  img=cv2.imread(file_path)
  img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
  textBox=pytesseract.image_to_data(img)
  text=""
  for a,b in enumerate(textBox.splitlines()):
   if a!=0:
    b=b.split()
    if len(b)==12 and float(b[10])>=0.90:
     text+=b[11]+" "
  text=re.sub(r'\|','I',text)
  image_title=os.path.splitext(file)[0]
  textDict[image_title]=text
 print(textDict)
 return textDict

def getAudioFiles(textDict,makingStage5):
 chrome_options=Options()
 chrome_options.add_argument("--headless")
 driver=webdriver.Chrome(executable_path=webdriver_path,options=chrome_options)
 url='https://beta.meetaugie.com/sign-in'
 driver.get(url)
 email_input=driver.find_element(By.ID,'email')
 email_input.send_keys('your@gmail.com')
 password_input=driver.find_element(By.ID,'password')
 password_input.send_keys('password')
 login_button=driver.find_element(By.XPATH,"//button[contains(.,'Login')]")
 login_button.click()
 time.sleep(2)
 create_url="https://beta.meetaugie.com/create"
 driver.get(create_url)
 time.sleep(2)
 script_button=driver.find_element(By.XPATH,"//button[contains(.,'I have a script that I want to turn into a video')]")
 script_button.click()
 go_button=driver.find_element(By.XPATH,"//button[contains(.,"LET'S GO")]")
 go_button.click()
 editing_button=driver.find_element(By.XPATH,"//button[@aria-label='Enable text editing']")
 editing_button.click()
 textarea=driver.find_element(By.ID,'scriptEditorTextArea')
 textarea.clear()
 textarea.send_keys('Test')
 done_button=driver.find_element(By.XPATH,"//button[@class='bg-[#442C6B] w-[94px] h-6 text-tActive text-[15px] py-2 px-4 rounded-full inline-flex justify-center items-center w-48']")
 done_button.click()
 voice_button=driver.find_element(By.XPATH,"//button[@aria-label='Choose a Voice']")
 voice_button.click()
 time.sleep(15)
 option_voice=driver.find_element(By.XPATH,"//div[text()='Jeremy']")
 option_voice.click()
 for image_title,text in textDict.items():
  if not text:
   print(f"Skipping empty text for image {image_title}")
   continue
  editing_button=driver.find_element(By.XPATH,"//button[@aria-label='Enable text editing']")
  editing_button.click()
  textarea=driver.find_element(By.ID,'scriptEditorTextArea')
  textarea.clear()
  textarea.send_keys(text)
  done_button=driver.find_element(By.XPATH,"//button[@class='bg-[#442C6B] w-[94px] h-6 text-tActive text-[15px] py-2 px-4 rounded-full inline-flex justify-center items-center w-48']")
  done_button.click()
  finish_button=driver.find_element(By.XPATH,"//button[@class='w-[210px] h-[30px] mt-4 !text-surface1 rounded-lg font-bold !bg-highlight1 justify-center text-center']")
  finish_button.click()
  time.sleep(10)
  audio_element=driver.find_element(By.XPATH,'//audio')
  audio_src=audio_element.get_attribute('src')
  response=requests.get(audio_src,stream=True)
  filename=f'{makingStage5}{image_title}.mp3'
  with open(filename,'wb')as file:
   shutil.copyfileobj(response.raw,file)
 driver.quit()

def makeVideoAudioSection(makingStage4,makingStage5,makingStage6):
 for audio_file in os.listdir(makingStage5):
  if audio_file.endswith(".mp3"):
   audio_path=os.path.join(makingStage5,audio_file)
   filename=os.path.splitext(audio_file)[0]
   image_files=[f for f in os.listdir(makingStage4)if f.endswith(f"{filename}.jpg")]
   image_files=sorted(image_files,key=lambda x:int(x.split('_')[0]))
   image_files_with_paths=[(f,os.path.join(makingStage4,f))for f in image_files]
   audio_duration=len(AudioSegment.from_file(audio_path))/1000
   num_images=len(image_files)
   image_duration=audio_duration/num_images if num_images>0 else 0
   fps=30
   output_video_path=os.path.join(makingStage6,f"{filename}.mp4")
   video_writer=imageio.get_writer(output_video_path,fps=fps)
   for image_file,image_path in image_files_with_paths:
    img=imageio.imread(image_path)
    for _ in range(int(fps*image_duration)):
     video_writer.append_data(img)
   video_writer.close()

def combineVideoAudioPart1(makingStage5,makingStage6,makingStage7,fp3=30):
 if not os.path.exists(makingStage7):
  os.makedirs(makingStage7)
 for mp4_file in os.listdir(makingStage6):
  if mp4_file.endswith(".mp4"):
   mp4_path=os.path.join(makingStage6,mp4_file)
   video_title=os.path.splitext(mp4_file)[0]
   mp3_file=f"{video_title}.mp3"
   mp3_path=os.path.join(makingStage5,mp3_file)
   if os.path.exists(mp3_path):
    video_clip=VideoFileClip(mp4_path)
    audio_clip=AudioFileClip(mp3_path)
    video_clip=video_clip.set_audio(audio_clip)
    video_clip=video_clip.set_fps(fp3)
    output_path=os.path.join(makingStage7,f"{video_title}.mp4")
    video_clip.write_videofile(output_path,codec="libx264",audio_codec="aac")
    video_clip.close()
    audio_clip.close()

def combineIntroMain(makingStage2,makingStage7,makingStage8):
 if not os.path.exists(makingStage8):os.makedirs(makingStage8)
 stage7_clips=[clip for clip in os.listdir(makingStage7)if clip.endswith('.mp4')]
 for clip_name in stage7_clips:
  stage7_path=os.path.join(makingStage7,clip_name)
  stage2_path=os.path.join(makingStage2,clip_name)
  if os.path.exists(stage2_path):
   clip_stage7=VideoFileClip(stage7_path)
   clip_stage2=VideoFileClip(stage2_path)
   combined_clip=concatenate_videoclips([clip_stage7,clip_stage2],method="compose")
   combined_clip=combined_clip.set_fps(30)
   output_path=os.path.join(makingStage8,clip_name)
   combined_clip.write_videofile(output_path,codec="libx264",audio_codec="aac")
   clip_stage7.close()
   clip_stage2.close()

def combineAllClips(makingStage8,makingStage9):
 os.makedirs(makingStage9,exist_ok=True)
 stage8_files=[f for f in os.listdir(makingStage8)if f.endswith(".mp4")]
 video_clips=[VideoFileClip(os.path.join(makingStage8,file))for file in stage8_files]
 final_clip=concatenate_videoclips(video_clips,method="compose")
 final_clip.write_videofile(os.path.join(makingStage9,"combined_video.mp4"),codec="libx264",audio_codec="aac")
 final_clip.close()
 for clip in video_clips:clip.close()

def addWaterMark(folder_path,waterMark):
 files=os.listdir(folder_path)
 video_file=next((file for file in files if file.lower().endswith('.mp4')),None)
 if video_file:
  input_video_path=os.path.join(folder_path,video_file)
  output_video_path=os.path.join(folder_path,'output.mp4')
  ffmpeg_command=(f"ffmpeg -i {input_video_path} -i {waterMark} "f"-filter_complex [1]scale=iw/2.5:ih/2.5[scaled];[0][scaled]overlay=10:(H-h)/2 "f"{output_video_path}")
  os.system(ffmpeg_command)
  os.remove(input_video_path)
  os.rename(output_video_path,input_video_path)

def finishUp(databaseCSV,makingStage1,makingStage2,makingStage3,makingStage4,makingStage5,makingStage6,makingStage7,makingStage8,makingStage9,outputDir):
 df=pd.read_csv(databaseCSV)
 highest_video_id=df['VideoID'].max()
 for filename in os.listdir(makingStage1):
  if filename.endswith('.mp4'):
   file_path=os.path.join(makingStage1,filename)
   row=df[df['Title']==filename]
   if not row.empty:
    df.loc[df['Title']==filename,'Used']=1
    df.loc[df['Title']==filename,'VideoID']=highest_video_id+1
 for filename in os.listdir(makingStage9):
  if filename.endswith('.mp4'):
   file_path=os.path.join(makingStage9,filename)
   new_filename=f"MemeCompliation{highest_video_id+1}.mp4"
   print(new_filename)
   new_filepath=os.path.join(outputDir,new_filename)
   shutil.move(file_path,new_filepath)
 df.to_csv(databaseCSV,index=False)
 for making_stage_dir in [makingStage1,makingStage2,makingStage3,makingStage4,makingStage5,makingStage6,makingStage7,makingStage8]:
  for file in os.listdir(making_stage_dir):
   file_path=os.path.join(making_stage_dir,file)
   try:
    if os.path.isfile(file_path):os.unlink(file_path)
   except Exception as e:print(f"Error deleting {file_path}: {e}")

def retry_function_until_success():
 max_retries=10
 retries=0
 while retries<max_retries:
  try:
   getAudioFiles(getTextList(makingStage3),makingStage5)
   break
  except Exception as e:
   print(f"Error: {e}")
   retries+=1
   if retries<max_retries:print(f"Retrying... (Attempt {retries}/{max_retries})")
   else:print("Maximum retries reached. Exiting.")

newVideos=input("Are there any videos? (1 for Yes, 0 for No): ")
numVideos=int(input("How many videos to generate? :"))

if newVideos=='1':
 databaseDuplicateHandlingFolder(newVideosDir)
 databaseNewFileHandling(databaseCSV,newVideosDir,videosDir)

databaseDuplicateHandlingCSV(databaseCSV)
databaseDuplicateHandlingFolder(videosDir)
checkIfAllFilesPresent(databaseCSV,videosDir)

for _ in range(numVideos):
 pickRandomVideos(databaseCSV,videosDir,makingStage1)
 resizeVideos(makingStage1,makingStage2)
 getFirstFrame(makingStage2,makingStage3)
 getAllCoveredFrames(makingStage3,makingStage4)
 retry_function_until_success()
 makeVideoAudioSection(makingStage4,makingStage5,makingStage6)
 combineVideoAudioPart1(makingStage5,makingStage6,makingStage7,fp3=30)
 combineIntroMain(makingStage2,makingStage7,makingStage8)
 combineAllClips(makingStage8,makingStage9)
 addWaterMark(makingStage9,waterMark)
 finishUp(databaseCSV,makingStage1,makingStage2,makingStage3,makingStage4,makingStage5,makingStage6,makingStage7,makingStage8,makingStage9,outputDir)