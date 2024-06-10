import time

import onvif
import zeep
from pydantic import BaseModel
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Union, Optional
from zeep import helpers

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Zoom(BaseModel):
    x: Union[int, float]


class PanTilt(BaseModel):
    x: Union[int, float]
    y: Union[int, float]


class Position(BaseModel):
    PanTilt: PanTilt
    Zoom: Zoom


class info(BaseModel):
    flag: bool
    MistakeContext: str = None


class PTZSpeed(BaseModel):
    PanTilt: PanTilt
    Zoom: Zoom


class PTZConfiguration(BaseModel):
    token: str
    Name: str
    UseCount: int
    MoveRamp: int
    PresetRamp: int
    NodeToken: str
    DefaultAbsolutePantTiltPositionSpace: Optional[str] = None
    DefaultAbsoluteZoomPositionSpace: Optional[str] = None
    DefaultRelativePanTiltTranslationSpace: Optional[str] = None
    DefaultRelativeZoomTranslationSpace: Optional[str] = None
    DefaultContinuousPanTiltVelocitySpace: Optional[str] = None
    DefaultContinuousZoomVelocitySpace: Optional[str] = None
    DefaultPTZSpeed: Optional[PTZSpeed] = None
    DefaultPTZTimeout: Optional[float] = None
    PanTiltLimits: Optional[Union[float, int]] = None
    ZoomLimits: Optional[Union[float, int]] = None
    Extension: Optional[Union[list, dict]] = None


class AbsoluteMoveRequest(BaseModel):
    Position: Position
    Speed: Optional[PTZSpeed] = None  # 目前设备不支持


class MoveResponse(BaseModel):
    finish_Status: info
    PTZ_Status: Union[dict, list, str] = None


class ContinuousMoveRequest(BaseModel):
    Velocity: PTZSpeed
    Timeout: Optional[Union[int, str, float]] = None


class ConfigurationResponse(BaseModel):
    finish_Status: info
    ConfigurationContent: Union[dict, list] = None


class GotoHomePositionRequest(BaseModel):
    Speed: Optional[PTZSpeed] = None


class RelativeMoveRequest(BaseModel):
    Translation: Position
    Speed: Optional[PTZSpeed] = None  # 目前设备不支持


class SetConfigurationRequest(BaseModel):
    PTZConfiguration: PTZConfiguration
    ForcePersistence: bool = True


# class StopRequest(BaseModel): # 目前设备不支持
#     PanTilt: Optional[Union[bool, str]] = None
#     Zoom: Optional[Union[bool, str]] = None


@app.post("/ptz/move/AbsoluteMove", response_model=MoveResponse)
async def AbsoluteMove(request: AbsoluteMoveRequest):
    try:
        # device_res = ptz.GetConfigurations()
        # params = ptz.create_type('GetConfiguration')
        # print(device_res)
        # params.PTZConfigurationToken = device_res[0].token
        # Configuration = ptz.GetConfiguration(params)
        params = ptz.create_type('AbsoluteMove')
        params.ProfileToken = media_profile.token
        params.Position = ptz.GetStatus({'ProfileToken': media_profile.token}).Position
        # print(params.Position.Zoom.space)
        params.Position.PanTilt.x = request.Position.PanTilt.x
        params.Position.PanTilt.y = request.Position.PanTilt.y
        params.Position.Zoom.x = request.Position.Zoom.x
        # params.Speed = Configuration.DefaultPTZSpeed
        # print(type(params.Speed))
        # print(params.Speed)
        # params.Speed.PanTilt.x = 0.2
        device_res = ptz.AbsoluteMove(params)
        # time.sleep(0.1)
        # device_res = ptz.GetStatus({'ProfileToken': media_profile.token})
        # print(device_res.MoveStatus.PanTilt)
        # print(type(device_res.MoveStatus.PanTilt))
        # PanTilt = device_res.MoveStatus.PanTilt
        # Zoom = device_res.MoveStatus.Zoom
        # while PanTilt or Zoom =="MOVING":
        while True:
            device_res = ptz.GetStatus({'ProfileToken': media_profile.token})
            print(device_res.MoveStatus.PanTilt)
            print(type(device_res.MoveStatus.PanTilt))
            if device_res.MoveStatus.PanTilt == "IDLE" and device_res.MoveStatus.Zoom == "IDLE":
                device_res_dict = helpers.serialize_object(device_res, dict)
                response = MoveResponse(finish_Status=info(flag=True), PTZ_Status=device_res_dict)
                return response
        # device_res_dict = helpers.serialize_object(device_res, dict)
        # response = MoveResponse(finish_Status=info(flag=True), PTZ_Status=device_res_dict)
        # return response
    except Exception as e:
        response = MoveResponse(finish_Status=info(flag=False, MistakeContext=str(e)))
        return response


@app.post("/ptz/move/ContinuousMove", response_model=MoveResponse)
async def ContinuousMove(request: ContinuousMoveRequest):
    try:
        configurations = ptz.GetConfigurations()
        ConfigurationToken = configurations[0].token
        ConfigurationOptions_params = ptz.create_type('GetConfigurationOptions')
        ConfigurationOptions_params.ConfigurationToken = ConfigurationToken
        ConfigurationOptions = ptz.GetConfigurationOptions(ConfigurationOptions_params)
        params = ptz.create_type('ContinuousMove')
        params.ProfileToken = media_profile.token
        # print(type(params.Timeout))
        params.Velocity = ptz.GetStatus({'ProfileToken': media_profile.token}).Position
        params.Velocity.PanTilt.space = ConfigurationOptions.Spaces.ContinuousPanTiltVelocitySpace[0].URI
        params.Velocity.Zoom.space = ConfigurationOptions.Spaces.ContinuousZoomVelocitySpace[0].URI
        params.Velocity.PanTilt.x = request.Velocity.PanTilt.x
        params.Velocity.PanTilt.y = request.Velocity.PanTilt.y
        params.Velocity.Zoom.x = request.Velocity.Zoom.x
        Onvif_Timeout = str('PT' + str(request.Timeout) + 'S')  # 'PT2S'
        params.Timeout = Onvif_Timeout
        device_res = ptz.ContinuousMove(params)
        while True:
            device_res = ptz.GetStatus({'ProfileToken': media_profile.token})
            print(device_res.MoveStatus.PanTilt)
            print(device_res.MoveStatus.Zoom)
            if device_res.MoveStatus.PanTilt == "IDLE" and device_res.MoveStatus.Zoom == "IDLE":
                print("1")
                device_res_dict = helpers.serialize_object(device_res, dict)
                response = MoveResponse(finish_Status=info(flag=True), PTZ_Status=device_res_dict)
                return response
        # device_res = ptz.GetStatus({'ProfileToken': media_profile.token})
        # device_res_dict = helpers.serialize_object(device_res, dict)
        # response = MoveResponse(finish_Status=info(flag=True), PTZ_Status=device_res_dict)
        # return response
    except Exception as e:
        response = MoveResponse(finish_Status=info(flag=False, MistakeContext=str(e)))
        return response


# @app.post("/ptz/move/GeoMove", response_model=MoveResponse) 要查看PTZ是否支持GeoMove

@app.post("/ptz/Configuration/GetCompatibleConfigurations", response_model=ConfigurationResponse)
async def GetCompatibleConfigurations():
    try:
        params = ptz.create_type('GetCompatibleConfigurations')
        params.ProfileToken = media_profile.token
        device_res = ptz.GetCompatibleConfigurations(params)  # 返回为list值，需要先提取，再做序列转化
        device_res_dict = helpers.serialize_object(device_res[0], dict)
        print(type(device_res_dict))
        response = ConfigurationResponse(finish_Status=info(flag=True), ConfigurationContent=device_res_dict)
        return response
    except Exception as e:
        response = ConfigurationResponse(finish_Status=info(flag=False, MistakeContext=str(e)))
        return response


@app.post("/ptz/Configuration/GetConfigurationOptions", response_model=ConfigurationResponse)
async def GetConfigurationOptions():
    try:
        device_res = ptz.GetConfigurations()
        ConfigurationToken = device_res[0].token
        params = ptz.create_type('GetConfigurationOptions')
        params.ConfigurationToken = ConfigurationToken
        device_res = ptz.GetConfigurationOptions(params)
        device_res_dict = helpers.serialize_object(device_res, dict)
        response = ConfigurationResponse(finish_Status=info(flag=True), ConfigurationContent=device_res_dict)
        return response
    except Exception as e:
        response = ConfigurationResponse(finish_Status=info(flag=False, MistakeContext=str(e)))
        return response


@app.post("/ptz/Configuration/GetConfiguration", response_model=ConfigurationResponse)
async def GetConfiguration():
    try:
        device_res = ptz.GetConfigurations()
        params = ptz.create_type('GetConfiguration')
        print(device_res)
        params.PTZConfigurationToken = device_res[0].token
        device_res = ptz.GetConfiguration(params)
        device_res_dict = helpers.serialize_object(device_res, dict)
        response = ConfigurationResponse(finish_Status=info(flag=True), ConfigurationContent=device_res_dict)
        return response
    except Exception as e:
        response = ConfigurationResponse(finish_Status=info(flag=False, MistakeContext=str(e)))
        return response


@app.post("/ptz/Configuration/GetNode", response_model=ConfigurationResponse)  # "Extension"的内容需要做剔除
async def GetNode():
    try:
        device_res = ptz.GetNodes()
        params = ptz.create_type('GetNode')
        params.NodeToken = device_res[0].token
        device_res = ptz.GetNode(params)
        print(type(device_res))
        device_res_dict = helpers.serialize_object(device_res, dict)
        device_res_dict["Extension"] = None
        response = ConfigurationResponse(finish_Status=info(flag=True), ConfigurationContent=device_res_dict)
        return response
    except Exception as e:
        response = ConfigurationResponse(finish_Status=info(flag=False, MistakeContext=str(e)))
        return response


@app.post("/ptz/Configuration/GetServiceCapabilities", response_model=ConfigurationResponse)
async def GetServiceCapabilities():
    try:
        device_res = ptz.GetServiceCapabilities()
        device_res_dict = helpers.serialize_object(device_res, dict)
        response = ConfigurationResponse(finish_Status=info(flag=True), ConfigurationContent=device_res_dict)
        return response
    except Exception as e:
        response = ConfigurationResponse(finish_Status=info(flag=False, MistakeContext=str(e)))
        return response


@app.post("/ptz/Configuration/GetStatus", response_model=ConfigurationResponse)
async def GetStatus():
    try:
        params = ptz.create_type('GetStatus')
        params.ProfileToken = media_profile.token
        device_res = ptz.GetStatus(params)
        device_res_dict = helpers.serialize_object(device_res, dict)
        response = ConfigurationResponse(finish_Status=info(flag=True), ConfigurationContent=device_res_dict)
        return response
    except Exception as e:
        response = ConfigurationResponse(finish_Status=info(flag=False, MistakeContext=str(e)))
        return response


@app.post("/ptz/move/GotoHomePosition", response_model=MoveResponse)
async def GotoHomePosition(request: GotoHomePositionRequest):
    try:
        params = ptz.create_type('GotoHomePosition')
        params.ProfileToken = media_profile.token
        device_res = ptz.GotoHomePosition(params)
        device_res = ptz.GetStatus({'ProfileToken': media_profile.token})
        device_res_dict = helpers.serialize_object(device_res, dict)
        response = MoveResponse(finish_Status=info(flag=True), PTZ_Status=device_res_dict)
        return response
    except Exception as e:
        response = MoveResponse(finish_Status=info(flag=False, MistakeContext=str(e)))
        return response


# @app.post("/ptz/move/MoveAndStartTracking", response_model=MoveResponse) 待考证
@app.post("/ptz/move/RelativeMove", response_model=MoveResponse)
async def RelativeMove(request: RelativeMoveRequest):
    try:
        configurations = ptz.GetConfigurations()
        ConfigurationToken = configurations[0].token
        ConfigurationOptions_params = ptz.create_type('GetConfigurationOptions')
        ConfigurationOptions_params.ConfigurationToken = ConfigurationToken
        ConfigurationOptions = ptz.GetConfigurationOptions(ConfigurationOptions_params)
        params = ptz.create_type('RelativeMove')
        params.ProfileToken = media_profile.token
        params.Translation = ptz.GetStatus({'ProfileToken': media_profile.token}).Position
        params.Translation.PanTilt.space = ConfigurationOptions.Spaces.RelativePanTiltTranslationSpace[0].URI
        params.Translation.Zoom.space = ConfigurationOptions.Spaces.RelativeZoomTranslationSpace[0].URI
        params.Translation.PanTilt.x = request.Translation.PanTilt.x
        params.Translation.PanTilt.y = request.Translation.PanTilt.y
        params.Translation.Zoom.x = request.Translation.Zoom.x
        # params.Speed = configurations[0].DefaultPTZSpeed
        # params.Speed.PanTilt.x = 0.2
        # params.Speed.PanTilt.y = 0.2
        device_res = ptz.RelativeMove(params)
        while True:
            device_res = ptz.GetStatus({'ProfileToken': media_profile.token})
            print(device_res.MoveStatus.PanTilt)
            print(type(device_res.MoveStatus.PanTilt))
            if device_res.MoveStatus.PanTilt == "IDLE" and device_res.MoveStatus.Zoom == "IDLE":
                device_res_dict = helpers.serialize_object(device_res, dict)
                response = MoveResponse(finish_Status=info(flag=True), PTZ_Status=device_res_dict)
                return response
        # device_res = ptz.GetStatus({'ProfileToken': media_profile.token})
        # device_res_dict = helpers.serialize_object(device_res, dict)
        # response = MoveResponse(finish_Status=info(flag=True), PTZ_Status=device_res_dict)
        # return response
    except Exception as e:
        response = MoveResponse(finish_Status=info(flag=False, MistakeContext=str(e)))
        return response


@app.post("/ptz/Configuration/SetConfiguration", response_model=ConfigurationResponse)
async def SetConfiguration(request: SetConfigurationRequest):
    pass


@app.post("/ptz/Configuration/SetHomePosition", response_model=ConfigurationResponse)
async def SetHomePosition():
    try:
        params = ptz.create_type('SetHomePosition')
        params.ProfileToken = media_profile.token
        device_res = ptz.SetHomePosition(params)
        response = ConfigurationResponse(finish_Status=info(flag=True))
        return response
    except Exception as e:
        response = ConfigurationResponse(finish_Status=info(flag=False, MistakeContext=e))
        return response


@app.post("/ptz/move/Stop", response_model=MoveResponse)
async def Stop():
    try:
        params = ptz.create_type('Stop')
        # print(params)
        params.ProfileToken = media_profile.token
        # print(params.PanTilt)
        # print(type(params.PanTilt))
        # params.PanTilt = ptz.GetStatus({'ProfileToken': media_profile.token}).Position.PanTilt
        # params.Zoom = ptz.GetStatus({'ProfileToken': media_profile.token}).Position.Zoom
        # print(params)
        # params.PanTilt = None
        # params.PanTilt = True
        # params.Zoom = None
        # params.Zoom = True
        # print(params)
        device_res = ptz.Stop(params)
        time.sleep(0.1)
        device_res = ptz.GetStatus({'ProfileToken': media_profile.token})
        device_res_dict = helpers.serialize_object(device_res, dict)
        response = MoveResponse(finish_Status=info(flag=True), PTZ_Status=device_res_dict)
        return response
    except Exception as e:
        print(e)
        response = MoveResponse(finish_Status=info(flag=False, MistakeContext=str(e)))
        return response


# 5个控制类服务，8个设置信息类服务
if __name__ == "__main__":
    def zeep_pythonvalue(self, xmlvalue):
        return xmlvalue


    zeep.xsd.simple.AnySimpleType.pythonvalue = zeep_pythonvalue
    mycam = onvif.ONVIFCamera("192.168.1.64", 80, "admin", "zmh123456", wsdl_dir="./wsdl/",
                              adjust_time=True)  # 登录之后要获取一些临界值，提高代码的不同设备的通用性
    media = mycam.create_media_service()
    ptz = mycam.create_ptz_service()
    media_profile = media.GetProfiles()[0]
    uvicorn.run(app, host='0.0.0.0', port=8889, workers=1)
