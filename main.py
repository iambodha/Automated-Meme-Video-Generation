newVideos = input("Are there any videos? (1 for Yes, 0 for No): ")
numVideos = int(input("How many videos to generate? :"))

if newVideos == '1':
    databaseDuplicateHandlingFolder(newVideosDir)
    databaseNewFileHandling(databaseCSV, newVideosDir, videosDir)

databaseDuplicateHandlingCSV(databaseCSV)
databaseDuplicateHandlingFolder(videosDir)
checkIfAllFilesPresent(databaseCSV, videosDir)

for _ in range(numVideos):
    pickRandomVideos(databaseCSV, videosDir, makingStage1)
    resizeVideos(makingStage1, makingStage2)
    getFirstFrame(makingStage2, makingStage3)
    getAllCoveredFrames(makingStage3, makingStage4)
    retry_function_until_success()
    makeVideoAudioSection(makingStage4, makingStage5, makingStage6)
    combineVideoAudioPart1(makingStage5, makingStage6, makingStage7, fp3=30)
    combineIntroMain(makingStage2, makingStage7, makingStage8)
    combineAllClips(makingStage8, makingStage9)
    addWaterMark(makingStage9, waterMark)
    finishUp(databaseCSV, makingStage1, makingStage2, makingStage3, makingStage4, makingStage5, makingStage6, makingStage7, makingStage8, makingStage9, outputDir)