# Maya playblast manager

## Overview

![image](https://github.com/chandruvfx/maya-playblast-manager/assets/45536998/a6aa15c9-567b-49cd-bcf1-b03249da7225)



A maya playblast manager is an alternative approach of native maya playblasting, which opens the door for an artist to create maya based text HUDs for a given camera. It also, facilitates the artist to submit the HUD based setup into the farm to generate exr using maya hardware rendering 2.0, make mov with the resulting
exr's and publish it to the shotgrid. 

The Playblast manager splitted into two sections. One section take care HUD creations and deadline submissions. Second sections take cares RV operations likewise
Loading all the folders containing the exrs from the given path and allow users to select multiple items of folders in one time and play it. 

## HUD Text Rig 

Below Image showcases the constraint rig setup of the HUD text with the cameras. 
This is how the tool generate the contrains for HUD text groups to travel the camera always. 

![image](https://github.com/chandruvfx/maya-playblast-manager/assets/45536998/b9628c06-beb7-42af-9864-e6f788d66cef)

## Tool DO's:
 
 The tool can do multiple Jobs. 
 
   1. Create and update text huds for the given camera 
   2. Do Local HW2.0 rendering , submit the Draft mov and publishes 
      the output mov to shotgrid version page of the respective shot 
   3. Farm submit the HW2.0 exr rendering, Draft Movs and publishing
      the output mov to shotgrid version page of the respective shot 


## Video Demo

To explore more about how the tool is working, please click the below link

Click :point_down: [Youtube Link]

[![Maya Playblast Manager Demo Video](https://img.youtube.com/vi/FN4qdxLvBrY/0.jpg)](https://youtu.be/FN4qdxLvBrY)

## Tool Properties 

### Folder Path & File name 
 1. Folder path - maya workspace image path where to dump exrs
 2. File Name - User choice of name to the exrs and sub folders
![playblast_4](https://github.com/chandruvfx/maya-playblast-manager/assets/45536998/71290bd7-2589-4848-a1b6-ede03e007898)

