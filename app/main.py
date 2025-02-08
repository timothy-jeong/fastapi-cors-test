from fastapi import FastAPI, status, HTTPException, Depends
from fastapi.responses import ORJSONResponse

from app import CommonResponse


app = FastAPI(
    title="FastAPI CORS Test",
    version="0.1.0",
    default_response_class=ORJSONResponse
    )


from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware # same as fastapi.middleware.cors.CORSMiddleware
from app.middleware.cors import CORSMiddleware as CustomCORSMiddleware

app.add_middleware(
    StarletteCORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

###############
# normal case #
###############
@app.get("/health", status_code=status.HTTP_200_OK, response_model=CommonResponse)
async def is_health():
    return CommonResponse(message= "I'm healthy!")

##################
# exception case #
##################
@app.get("/exception", response_model=CommonResponse)
async def throws_exception():
    raise Exception("No!")

#######################
# http exception case #
#######################
@app.get("/exception/http", response_model=CommonResponse)
async def throws_http_exception():
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Go! HttpException!"
    )

##############################
# exception in depends case  #
##############################
async def dependency_exception() -> str:
    raise Exception("Exception raised in dependency!")
    
@app.get("/exception/depend", response_model=CommonResponse)
async def throws_exception_in_depend(
    the_thing = Depends(dependency_exception)
):    
    return CommonResponse(message="how come")

####################################
# http exception  in depends case  #
####################################
async def dependency_exception_http() -> str:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Go! HttpException!"
    )
    
@app.get("/exception/http/depend", response_model=CommonResponse)
async def throws_exception_in_depend(
    the_thing = Depends(dependency_exception_http)
):    
    return CommonResponse(message="how come")



from app import general_exception_handler

app.add_exception_handler(Exception, general_exception_handler)