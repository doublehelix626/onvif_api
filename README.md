# 这是一个关于使用onvif1.0协议来查看和配置海康威视摄像头的api项目
## 两个不同的api文件
### 两个api文件的主要区别:文件名末尾为yibu的api文件为，每次向设备发送控制请求后，需要等待onvif协议相关功能执行完毕后才返回response及当前的相对坐标的信息；而另一个api文件为发送控制类型请求后不必等待onvif协议相关功能完毕就可以直接返回response
