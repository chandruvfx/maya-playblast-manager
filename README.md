# Maya playblast manager

## Overview

![image](https://github.com/chandruvfx/maya-playblast-manager/assets/45536998/a6aa15c9-567b-49cd-bcf1-b03249da7225)



A maya playblast manager is an battery included alternative approach of native maya playblasting, which opens the door for an artist to create maya based text HUDs for a given camera. It also, facilitates the artist to submit the HUD based setup into the farm to generate exr using maya hardware rendering 2.0, make mov with the resulting
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
 
 Clicking the Double dotted button open the file browser dialog, Artist alternatively allowed to select a folder path from here
 
 ![playblast_12](https://github.com/chandruvfx/maya-playblast-manager/assets/45536998/48af98d3-4ba2-493c-acc1-581049f33462)

### Camera List

Maya scene cameras listed here

![playblast_5](https://github.com/chandruvfx/maya-playblast-manager/assets/45536998/40d724f9-ea36-42f6-a50c-2ea7b97daf7d)

### Constant HUDs

User selected checkbox HUDs, created into scene file

![playblast_6](https://github.com/chandruvfx/maya-playblast-manager/assets/45536998/69c386be-f825-4108-aef9-73648b1f4525)

### Custom HUD Text

Enable the check box allows the user to add or remove rows in the widget. Once added users can able to enter text of HUD label and HUD text. It gonna created as HUD text

![playblast_7](https://github.com/chandruvfx/maya-playblast-manager/assets/45536998/1ca2d452-33c6-43d1-b223-2c9463d7c8c2)

### Generate/update and Delete

Push buttons generate/update the HUD text For updating and deleting a specific camera HUD you need to choose primary group handle of the camera.

![playblast_8](https://github.com/chandruvfx/maya-playblast-manager/assets/45536998/e0ec2814-61de-425a-860a-aa575b50422b)

Example, image showing here for a user need to select the following node to update or delete the hud for camera1
![playblast_9](https://github.com/chandruvfx/maya-playblast-manager/assets/45536998/671425e3-e25a-4c96-a91c-99da582da8be)

### Deadline Section

![playblast_10](https://github.com/chandruvfx/maya-playblast-manager/assets/45536998/3c0ad861-5229-46e8-a8df-c66c0646ddf6)
  
  - Job Name - Deadline job name. Default it is the cache name plus version name. Artist can enter his own preferred name
  - Comment - Valid textual deadline comments
  - Pool & Secondary pool - Drop-Down consist of deadline pools.
  - Group - Deadline Groups
  - Start Frame & End Frame - Specify the start and end frame of the scene to render
  - Priority - Determine Deadline Priority
  - Frames-Per-Task - Determine Chunk size aka the split of frame ranges into the machines

### Submission

![playblast_11](https://github.com/chandruvfx/maya-playblast-manager/assets/45536998/2c2a8a91-a825-4f44-b390-0a26c59ce396)

   - Local Render Hardware 2.0 - If enabled render the exr files through a commandline else it submitted to deadline
   - Publish Mov - Draft job for mov creation and publishing the generated mov to the shotgrid job created.
   - Submit to Deadline - clicking this submits the configuration to the farm

### RV Controls

Click the double dotted button and select the master folder contains all the playblast version from the dialog box. It loads all the folders inside it. Artist can able to select one or multiple folder item and press play. This action opens up the RV with loaded exrs

![playblast_13](https://github.com/chandruvfx/maya-playblast-manager/assets/45536998/67c8d523-1ca7-4053-9c94-53291ec629fd)
