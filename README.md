# CarbonCheck_homeserver

<h3>카본 체크 팀 홈서버 Repository 입니다. </h3>
</br>

# Requirements

<ul>
    <li> Jetson Nano 4GB with jetpack 4.6.x</li>
    <li> Webcam or CSI camera</li>
    <li> MicroSD 32GB or More</li>
    <li> Intel® Dual Band Wireless-AC 8265</li>
    <li>2 x 6dBi Dual Band M.2 IPEX MHF4 U.fl Cable to RP-SMA Wifi Antenna Set for Intel AC 8265</li>
    <li> <a href"https://github.com/Gaebobman/water_flow_meter" >Arduino water flow meter</a> as UDP client </li>
    <li> mysql </li>
    <li> pip3 </li>
    <li> Python 3.6.x </li>
    <li> face_recognition (follow <a href ="https://medium.com/@ageitgey/build-a-hardware-based-face-recognition-system-for-150-with-the-nvidia-jetson-nano-and-python-a25cb8c891fd">this instruction</a>)</li>
    <li>Tuya api key (if you need smart socket)</li>
</ul>

</br>

# How to run

<br>

1. Set your Jetson Nano as a hotspot (follow <a href="http://1004lucifer.blogspot.com/2015/12/ubuntu.html">this instruction</a>)

<br>

2. install required packages

```
pip3 install -r requirements.txt
```

<br>

3. run carboncheck_master.py

```
python3 carboncheck_master.py
```

<br><br>

---

Copyright (c) 2023 Standard Lee (Gaebobman)
