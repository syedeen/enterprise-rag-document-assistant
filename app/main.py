from fastapi import FastAPI , File , UploadFile
import shutil

app = FastAPI()

@app.get("/test")
def get():
    return "reached server"

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    file_loc = f"./{file.filename}"
    with open(file_loc,"wb") as buffer:
        shutil.copyfileobj(file.file,buffer)
    return {"filename": file.filename}
