import sys
import Draft
from DraftParamParser import (ReplaceFilenameHashesWithNumber,
                              ParseCommandLine)

expectedTypes = dict()
params = ParseCommandLine( expectedTypes, sys.argv )
mov = params['mov'] 
exr = params['exr'].split("$F4")
exr = exr[0] + '####.exr'
start_frame = int(params['start_frame'])
end_frame = int(params['end_frame'])

encoder = Draft.VideoEncoder( mov,
                                width = 1920,
                                height = 1080,
                                codec='DNXHD',
                                kbitRate= 36000)   # Initialize the video encoder.
for currFrame in range( start_frame, end_frame ):
    currFile = ReplaceFilenameHashesWithNumber( exr, currFrame )
    frame = Draft.Image.ReadFromFile( currFile )
    lut = Draft.LUT.CreateGamma( 1.0 )
    lut.Apply( frame )
    encoder.EncodeNextFrame( frame )    # Add each frame to the video.

encoder.FinalizeEncoding()    # Finalize and save the resulting video.
