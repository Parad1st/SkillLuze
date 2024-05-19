# SkillLuze
SkillLuze is a neural network-based aim assist system that uses real-time pattern search accelerated by CUDA on Nvidia GPU.

## About

SkillLuze can work with other FPS shooters, but it is currently configured for Fortnite. Apart from its general purpose, the main advantage of using SkillLuze is that it does not interfere with the gameplay, which ensures that you will not get banned.

SkillLuze's player detection is based on [YOLOv5](https://github.com/ultralytics/yolov5), written in PyTorch.

## Installation

1. Install a version of [Python](https://www.python.org/downloads/) 3.8 or later.

2. Open the Install.bat file or enter into the console:

```
pip install -r requirements.txt
```

## Usage

Open the Start.bat file or enter into the console:

```           
python SkillLuze.py
```
To update sensitivity settings, delete the config folder (located in the lib folder) or enter into the console:
```           
python SkillLuze.py setup
```
To collect image data for training, enter in the console:
```           
python SkillLuze.py collect_data
```



## License
This project is licensed under the [GNU General Public License v3.0](https://github.com/Parad1st/SkillLuze/blob/main/LICENSE).

## Поддержите проект
Поддержать проект пока что нельзя :(
