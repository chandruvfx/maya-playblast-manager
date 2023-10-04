
#
#
# A Maya Custom Playblast manager tool obtain constant and user defined custom huds from the artist
# Create text based HUD displays based upon the camera positioning, also facilitate artist to launch 
# maya hardware 2.0 renders. The tool also facilitate to creatig movs and publish it to shotgrid 
# by submiting the jobs in the deadline renderfarm.
# 
# The tool do multiple responsibilities. 
#   1. Create and update text huds for the given camera 
#   2. Options for Local HW2.0 rendering and submiting Draft mov and publishing 
#    the output mov to shotgrid version page of the respective shot 
#   3. Farm submission of all HW2.0 exr rendering, Draft Movs and publishing
#     the output mov to shotgrid version page of the respective shot 
#
#  EXAMPLE RENDER COMMANDLINE FOR MAYA HW2.0
#  -----------------------------------------
#  "C:\Program Files\Autodesk\Maya2020\bin\Render.exe" -r hw2 -s 1001 -e 1100 -b 1 -pad 4 -of jpeg 
#    -rd "Y:\projects\sgtk_dev\sequences\001\001_002\ANM\work\maya\images" 
#     "Y:\projects\sgtk_dev\sequences\001\001_002\ANM\work\maya\playblast.v001.ma"
#
from __future__ import print_function
import os 
from PySide2.QtUiTools import QUiLoader
from PySide2 import QtWidgets
from PySide2.QtCore import QFile
from PySide2.QtGui import (QStandardItemModel,
                           QStandardItem)
import maya.cmds as cmds
import maya.mel as mel
import sgtk
import subprocess
import re

# GUI ui file path 
__UI_FILE__ = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "plablast_ui.ui"
)

class PlayBlastManager(QtWidgets.QMainWindow):

    """Base Class for maya playblast manager. 

    Do several operations likewise hud creations, 
    place text hud  oriented to camera by creating 
    constraints and passing necessary properties to 
    submit deadline jobs

    Creation/Updation:
      The creation protocol create a dummy fresh camera 
    in maya viewport and generate all the constant/user defined hud texts. 
    A surface shader created and assigned to the hud texts. The hud text created
    in inside a hierarchical groups of handles. The top group handle is 
    used to parent constraint the hud text to the dummy camera and the second
    group handle inside the first handle gives transformation controls to the users. 
    The creation protocol then constraint(parent,orient) the dummy camera to the 
    user selected camera. Several custom defined attributes created for to perform
    updation process

    While in updation, for the given camera all the  constants and user defined HUD texts
    has been recognized through the constraints and custom attributes. The GUI loaded as same
    as last creational state. Artist were allowed to manipulate the HUD text likewise adding 
    new one and deleting old stuff. Once the users manipulation done, the old HUD is deleted 
    and new updated HUD text created with the setup. Here the transformation of the second group handle is 
    preserved as so the newly generated updated text grabs the user transformation values and
    generate the text on it.

    Deletion:
      User were allowed to select the top level group to delete the entire network of the 
    Hud created.
    
    Submission
      The class also responsible for submitting HW2.0 exrs, Draft movs and publishing 
    it to shotgrid"""
  

    def __init__(self):
        
        """ pyqt Widget Related operations """
        
        super(PlayBlastManager,self).__init__()
        self.loader = QUiLoader()
        self.ui_file = QFile(__UI_FILE__)
        self.window = self.loader.load(self.ui_file)

        # Grab images directory of the maya workspace 
        self.images = cmds.workspace( q=True, rootDirectory=True ) + "images/"
        if not os.path.exists(self.images): os.makedirs(self.images)

        # Collects all the HUD text related widgets. 
        # User changes camera in drop down. if the selected camera dont 
        # have any hud then this make sure all initial state of check box
        # go off state. if selected cammera has any hud text then the 
        # only the specifics check box go for on state
        self.all_hud_combobox_widgets =[]

        # Collects all the lineedit widgets and used to check while submission
        # whether all the mandotary informations entered or not 
        self.all_hud_lineedit_widgets =[]

        # The GUI make sure nill selected any objects in outliner
        # while opening
        cmds.select( clear=True )
        
        self.hud_folder_path_widget = self.window.findChild(
            QtWidgets.QLineEdit, 'hud_folder_path_txt'
        )
        self.hud_folder_path_widget.setText(self.images)
        self.all_hud_lineedit_widgets.append(self.hud_folder_path_widget)
        
        self.hud_file_path_widget = self.window.findChild(
            QtWidgets.QLineEdit, 'hud_file_path_txt'
        )
        self.hud_file_path_widget.textChanged.connect(self.set_deadline_jobname)
        self.all_hud_lineedit_widgets.append(self.hud_file_path_widget)
        
        self.hud_folderpath_browse_widget = self.window.findChild(
            QtWidgets.QPushButton, 'hud_folderpath_browse_btn'
        )
        self.hud_folderpath_browse_widget.clicked.connect(self.set_user_selected_directory)
        
        self.custom_toggle_child_list = []
        self.hud_custom_toggle_widget = self.window.findChild(
            QtWidgets.QCheckBox, 
            'hud_custom_toggle'
        )

        self.hud_custom_text_treeview = self.window.findChild(
                QtWidgets.QTableView, 
                'hud_custom_text'
        )
        # Create qt item model for user to enter the custom HUD text
        self.hud_custom_txt_treeview_model = QStandardItemModel()
        self.hud_custom_txt_treeview_model.setHorizontalHeaderLabels(['Title Label', 'Text'])
        self.hud_custom_text_treeview.setModel(self.hud_custom_txt_treeview_model)
        
        self.custom_toggle_child_list.append(self.hud_custom_text_treeview)
        
        self.custom_row_add_button = self.window.findChild(
            QtWidgets.QPushButton, 'custom_row_add_button'
        )
        self.custom_toggle_child_list.append(self.custom_row_add_button)
        
        self.custom_row_remove_button = self.window.findChild(
            QtWidgets.QPushButton, 'custom_row_remove_button'
        )
        self.custom_toggle_child_list.append(self.custom_row_remove_button)
        
        self.hud_custom_text_treeview.setEnabled(False)
        self.custom_row_add_button.setEnabled(False)
        self.custom_row_remove_button.setEnabled(False)
        self.hud_custom_toggle_widget.toggled.connect(
            lambda: self.hide_widgets(self.hud_custom_toggle_widget,
                                      self.custom_toggle_child_list)
        )

        # Push Buttons responsible for add or remove list row
        self.custom_row_add_button.clicked.connect(self.add_treeview_rows)
        self.custom_row_remove_button.clicked.connect(self.remove_treeview_rows)
        
        self.scene_cameras = self.window.findChild(
            QtWidgets.QComboBox, 'load_cameras'
        )
        # Method call to obtain cameras and load in the combobox
        self.load_maya_scene_camera_dropdown_widget()
        
        self.create_or_update_hud = self.window.findChild(
            QtWidgets.QPushButton, 'generat_updat_btn'
        )
        self.create_or_update_hud.clicked.connect(self.create_update_hud)
        
        self.delete_all_hud = self.window.findChild(
            QtWidgets.QPushButton, 'delete_btn'
        )
        self.delete_all_hud.clicked.connect(self.delete_all_hud_in_scene)

        # gather all check boxses
        self.scene_toggle = self.window.findChild(QtWidgets.QCheckBox, 'scene_toggle')
        self.all_hud_combobox_widgets.append(self.scene_toggle)
        
        self.artist_toggle = self.window.findChild(QtWidgets.QCheckBox, 'artist_toggle')
        self.all_hud_combobox_widgets.append(self.artist_toggle)
        
        self.fps_toggle = self.window.findChild(QtWidgets.QCheckBox, 'fps_toggle')
        self.all_hud_combobox_widgets.append(self.fps_toggle)
        
        self.focal_length = self.window.findChild(QtWidgets.QCheckBox, 'focal_length')
        self.all_hud_combobox_widgets.append(self.focal_length)
        
        self.resolution_toggle =self.window.findChild(QtWidgets.QCheckBox, 'resolution_toggle')
        self.all_hud_combobox_widgets.append(self.resolution_toggle)
        
        
        self.sensor_size = self.window.findChild(QtWidgets.QCheckBox, 'sensor_size')
        self.all_hud_combobox_widgets.append(self.sensor_size)
        
        self.pa_ratio_toggle = self.window.findChild(QtWidgets.QCheckBox, 'pa_ratio_toggle')
        self.all_hud_combobox_widgets.append(self.pa_ratio_toggle)
        
        self.frameno_toggle = self.window.findChild(QtWidgets.QCheckBox, 'frameno_toggle')
        self.all_hud_combobox_widgets.append(self.frameno_toggle)
        
        self.hud_deadline_job_name_widget = self.window.findChild(
            QtWidgets.QLineEdit, 'hud_deadline_job_name_txt'
        )
        self.all_hud_lineedit_widgets.append(self.hud_deadline_job_name_widget)
        
        self.hud_deadline_job_comments_widget = self.window.findChild(
            QtWidgets.QLineEdit, 'hud_deadline_job_comments_txt'
        )
        
        self.hud_start_frame_txt = self.window.findChild(
            QtWidgets.QLineEdit, 'hud_start_frame_txt'
        )
        self.hud_start_frame_txt.setText(
            str(int(cmds.playbackOptions(q=True, min=True)))
        )
        self.all_hud_lineedit_widgets.append(self.hud_start_frame_txt)
        
        self.hud_end_frame_txt = self.window.findChild(
            QtWidgets.QLineEdit, 'hud_end_frame_txt'
        )
        self.hud_end_frame_txt.setText(
            str(int(cmds.playbackOptions(q=True, max=True)))
        )
        self.all_hud_lineedit_widgets.append(self.hud_end_frame_txt)

        self.hud_deadline_priority_widget = self.window.findChild(
            QtWidgets.QSlider, 'hud_deadline_priority'
        ) 
        self.hud_priority_counter_qbx_widget = self.window.findChild(
            QtWidgets.QSpinBox, 'hud_priority_counter_qbx'
        )
        self.hud_deadline_priority_widget.valueChanged.connect(
                    self.set_priority_value_to_spinbox
        )
        self.hud_priority_counter_qbx_widget.valueChanged.connect(
                    self.set_priority_value_to_slider
        )
        
        self.hud_deadline_framepertask_widget = self.window.findChild(
            QtWidgets.QSlider, 'hud_deadline_framepertask'
        ) 
        self.hud_priority_fpt_qbx_widget = self.window.findChild(
            QtWidgets.QSpinBox, 'hud_priority_fpt_qbx'
        )
        self.hud_deadline_framepertask_widget.valueChanged.connect(
                    self.framepertask_value_to_spinbox
        )
        self.hud_priority_fpt_qbx_widget.valueChanged.connect(
                    self.framepertask_value_to_slider
        )
        
        self.hud_deadline_pool = self.window.findChild(
            QtWidgets.QComboBox, 'hud_deadline_pool'
        ) 

        # Execute mel deadline command to get the pool list and update in combo box
        self.deadline_pools = mel.eval('CallDeadlineCommand("-Pools", false);').split('\n')
        self.load_deadline_available_pools()
        
        self.hud_local_hw_toggle = self.window.findChild(
                    QtWidgets.QCheckBox, 
                    'hud_local_hw_toggle'
        )
        self.hud_local_hw_toggle.setChecked(True)
        
        self.hud_publish_mov_toggle = self.window.findChild(
                    QtWidgets.QCheckBox, 
                    'hud_publish_mov_toggle'
        )
        
        self.submit_to_deadline_btn = self.window.findChild(
                    QtWidgets.QPushButton, 
                    'submit_to_deadline_btn'
        )
        self.submit_to_deadline_btn.setEnabled(False)
        self.submit_to_deadline_btn.clicked.connect(self.submit_to_deadline)
      
        # Load the widgets as it is in the state of while creating process.
        # Based on the HUD created , during the loading time the GUI made 
        # the check boxes were on and custom text HUD automatically loaded
        # for the given camera.
        try:
            self.load_hud()
        except TypeError:
            pass
        
        self.rv_folder_path_txt_widget = self.window.findChild(
            QtWidgets.QLineEdit, 'rv_folder_path_txt'
        )
        self.rv_exr_folder_names_listview_widget = self.window.findChild(
            QtWidgets.QListView, 'rv_exr_folder_names'
        )
        self.rv_exrs_folders_model = QStandardItemModel()
        self.rv_exr_folder_names_listview_widget.setModel(self.rv_exrs_folders_model)
        self.rv_folder_path_txt_widget.textChanged.connect(self.set_playblast_folder_names)
        
        self.rv_folderpath_browse_btn_widget = self.window.findChild(
            QtWidgets.QPushButton, 'rv_folderpath_browse_btn'
        )
        self.rv_folderpath_browse_btn_widget.clicked.connect(
            self.set_user_selected_exr_directory
        )

        self.rv_play_selected_folders_widget = self.window.findChild(
            QtWidgets.QPushButton, 'rv_play_selected_folders'
        )
        self.rv_play_selected_folders_widget.clicked.connect(
            self.play_in_rv
        )
        
        self.load_cameras = self.window.findChild(
            QtWidgets.QComboBox, 'load_cameras'
        )
        self.load_cameras.currentIndexChanged.connect(self.clear_check_status_hud)
        
    def set_deadline_jobname(self):

        """ Set the deadline job name argument"""
      
        self.hud_deadline_job_name_widget.setText(
                    self.hud_file_path_widget.text()
        )
        
    def add_treeview_rows(self):

        """Add additional rows in the bottom of the custom treeview"""
      
        rows = self.hud_custom_text_treeview.model().rowCount()-1
        cols = self.hud_custom_text_treeview.model().columnCount()-1
        index = self.hud_custom_txt_treeview_model.index(rows,cols)
        self.hud_custom_txt_treeview_model.insertRow(index.row()+1)
    
    def remove_treeview_rows(self):

        """ Remove rows from bottom of the custom treeview"""
      
        rows = self.hud_custom_text_treeview.model().rowCount()-1
        index = self.hud_custom_txt_treeview_model.index(rows,0)
        self.hud_custom_txt_treeview_model.removeRow(index.row())
        
    def hide_widgets(self, 
                     hud_toggle_widget,
                     hud_input_widgets
                     ):

        """ Toggle visibility of the widget on and off"""
                       
        def toggle_visibility(lineedit_widget):
            if  hud_toggle_widget.isChecked():
                lineedit_widget.setEnabled(True)
            else:
                lineedit_widget.setEnabled(False)
            
        # Iterate through all the widgets and toggle
        # on or off 
        if isinstance(hud_input_widgets, list):
            for hud_input_widget in hud_input_widgets:
                toggle_visibility(hud_input_widget)
        else:
            toggle_visibility(hud_input_widgets)
    
    def clear_check_status_hud(self):

        """ Set the check status to false. Load hud called for 
        preserve the last creation operation state"""
      
        for hud_widget in self.all_hud_combobox_widgets:
             hud_widget.setChecked(False)  
        try:
            self.load_hud()
        except TypeError:
            pass
    
    def get_Qfiledialog_selected_file_path(self):

        """ Open the File Dialog for the folder selection""" 
      
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        if dialog.exec_():
            folder_path = dialog.selectedFiles()[0]
            return folder_path
    
    def set_user_selected_directory(self):

        """ User selected folder path setted into the folder path widgets"""
      
        folder_path = self.get_Qfiledialog_selected_file_path()
        self.hud_folder_path_widget.setText(folder_path)
        
    def set_user_selected_exr_directory(self):

        """ User selected folder path setted into the rv folder path widgets"""
      
        folder_path = self.get_Qfiledialog_selected_file_path()
        self.rv_folder_path_txt_widget.setText(folder_path)
        
    def get_user_selected_camera(self):

        """ Return the artist selected camera text from the combo box"""
      
        return self.scene_cameras.currentText()
    
    def get_scene_cameras(self):

        """ Return Scence cameras"""
      
        return [camera for camera in cmds.ls(cameras=True) \
            if not cmds.camera(camera, q=True, startupCamera=True)
        ]
    
    def set_playblast_folder_names(self):

        """ Update List view with the items of folder names od exrs"""
      
        self.rv_exrs_folders_model.clear()
        folders = set()
        for root, dirs, files in os.walk(self.images):
                for file in files:
                    if file.endswith(".exr"):
                        folder_name = os.path.basename(
                            os.path.dirname(
                                os.path.join(root,file)
                            )
                        )
                        folders.add(folder_name)
        for folder in folders:
            self.rv_exrs_folders_model.appendRow(
                        QStandardItem(folder)
            )
        
    @staticmethod
    def create_custom_addtribute(maya_node,
                                attr_name,
                                attr_type,
                                value):

        """ Create custom attributes for the given node based upon the type passed

        Args:
            maya_node: maya node object
            attr_name: name of the attribute string
            attr_type: name of the attribute type string
            value: attribute value 
        """
                                  
        if attr_type == 'string':
             cmds.addAttr( maya_node, longName=attr_name, dataType= attr_type )
             cmds.setAttr( '%s.%s' %(maya_node, attr_name), value, type="string", lock=True )
        else:
            cmds.addAttr( maya_node, longName=attr_name, attributeType= attr_type )
            cmds.setAttr( '%s.%s' %(maya_node, attr_name), value, lock=True )
        
    def show_messagebox(self, message):

        """ Qt Messge box to sow message information """
      
        QtWidgets.QMessageBox.information(self, "Fae Message", message)
        
    def get_camera_transform_nodes(self):

        """ Get all the cameras"""
      
        cameras = []
        scene_cameras = self.get_scene_cameras()
        for scene_camera in scene_cameras:
            parent_camera = cmds.listRelatives(scene_camera, 
                                               parent=True, 
                                               fullPath=True)
            if not cmds.attributeQuery('playblast_camera', node=parent_camera[0],
                                       ex=True ):
                cameras.append(parent_camera[0])
        return cameras
        
    def load_maya_scene_camera_dropdown_widget(self):

        """ Add the collected camera nodes into the camera dropdown widget"""
      
        for cameras in self.get_camera_transform_nodes():
            self.scene_cameras.addItem(cameras)
                   
    def load_deadline_available_pools(self):

       """ Load deadline pool to the combobox drpdown"""
      
        for pools in self.deadline_pools:
            self.hud_deadline_pool.addItem(pools)
            
    def duplicate_camera(self):

        """ Create duplicate camera and set the custom atttributes
        Returns the cameras 
        """
      
        self.user_selected_camera = self.get_user_selected_camera()
        hud_camera = cmds.duplicate( self.user_selected_camera, 
                                    name='hud_%s' %self.user_selected_camera)
        min_frame = cmds.playbackOptions(q=True, min=True)
        max_frame = cmds.playbackOptions(q=True, max=True)
        attributes= [ 'translateX',
                    'translateY',
                    'translateZ',
                    'rotateX',
                    'rotateY',
                    'rotateZ',
                    'scaleX',
                    'scaleY',
                    'scaleZ',
                    'visibility']
        
        # Delete all locks, animation and tranform to zero
        for attr in attributes:
            cmds.setAttr(hud_camera[0]+'.'+attr, lock=0)
            cmds.cutKey(hud_camera[0], time=(min_frame,max_frame), attribute=attr, option="keys" )
            if not attr.startswith('scale'):
                cmds.setAttr(hud_camera[0]+'.'+attr, 0)

        self.create_custom_addtribute(hud_camera[0], 'playblast_camera', 'bool', 1)
        return hud_camera        
    
    @property         
    def get_current_maya_file_name(self):

        """ Extract the filename for the file path and return 
        widget name """
      
        if self.scene_toggle.isChecked():
            
            filepath = cmds.file(q=True, sn=True)
            filename = os.path.basename(filepath)
            raw_name, extension = os.path.splitext(filename)
            return raw_name, 'scene_toggle'
        else:
            return
        
    @property
    def get_username(self):

        """ Returns the user name """
      
        if self.artist_toggle.isChecked():
            return os.environ.get( "USERNAME"), 'artist_toggle'
        else:
            return
    
    @property
    def get_scene_fps(self):

        """ Returns the fps of the scene"""
      
        if self.fps_toggle.isChecked():
        
            label = 'Fps: '
            currentUnit = cmds.currentUnit(query=True, time=True)
            if currentUnit == 'film':
                return label + str(24), 'fps_toggle'
            if currentUnit == 'show':
                return label +str(48), 'fps_toggle'
            if currentUnit == 'pal':
                return label +str(25), 'fps_toggle'
            if currentUnit == 'ntsc':
                return label +str(30), 'fps_toggle'
            if currentUnit == 'palf':
                return label +str(50), 'fps_toggle'
            if currentUnit == 'ntscf':
                return label +str(60), 'fps_toggle'
            if 'fps' in currentUnit:
                return label + str(currentUnit.substitute('fps','')), 'fps_toggle'
        else:
            return
    
    @property
    def get_current_frame_no(self):

        """ Returns the Frame No string"""
      
        if self.frameno_toggle.isChecked():
            return "Frame No", 'frameno_toggle'
        else:
            return
            
            
    @property
    def get_camera_focal_length(self):

        """ Returns camera focal length"""
      
        if self.focal_length.isChecked():
            return "{} {}".format('Focal Length: ',
                                cmds.getAttr(self.user_selected_camera +".focalLength")
            ), 'focal_length'
        else:
            return               
    
    @property
    def get_scene_resolution(self):

        """ Return width and hight of the resolution"""
      
        if self.resolution_toggle.isChecked():
        
            resx = cmds.getAttr("defaultResolution.width")
            resy = cmds.getAttr("defaultResolution.height")
            return "{} {},{}".format("Resolution: ", resx, resy), 'resolution_toggle'
        else:
            return
        
    @property
    def get_camera_sensor_size(self):
        
        if self.sensor_size.isChecked():
            sensorsize_x = cmds.getAttr(self.user_selected_camera +".horizontalFilmAperture") * 25.4
            sensorsize_y = cmds.getAttr(self.user_selected_camera +".verticalFilmAperture") * 25.4
            return "{} {},{}".format("Sensor Size: ", sensorsize_x,sensorsize_y), 'sensor_size'
        else:
            return
    
    @property
    def get_scene_pixel_aspect_ratio(self):
        
        if self.pa_ratio_toggle.isChecked():
        
            return "{} {}".format("Pixel Aspect Ratio: ",
                                cmds.getAttr("defaultResolution.pixelAspect")
            ), 'pa_ratio_toggle'
        else:
            return
    
    @property
    def get_user_custom_hud_text(self):
        
        custom_text = []
        if self.hud_custom_toggle_widget.isChecked():
            for row in range(self.hud_custom_text_treeview.model().rowCount()):
                items = []
                for column in range(self.hud_custom_text_treeview.model().columnCount()):
                    if hasattr(
                        self.hud_custom_text_treeview.model().item(row,column), 'text'
                        ):
                            items.append(
                                str(self.hud_custom_text_treeview.model().item(row,column).text())
                            )
                            if items not in custom_text:
                                custom_text.append(items)
        if custom_text: 
            return custom_text
        else:
            return 
    
    @property
    def is_checked(self):
        
        return True if any(
                    hud.isChecked() 
                    for hud in self.all_hud_combobox_widgets
        ) else False
    
    @property
    def is_filled(self):
        
        return True if all(
                    hud.text() 
                    for hud in self.all_hud_lineedit_widgets
        ) else False 
    
    def set_priority_value_to_spinbox(self):

        self.hud_priority_counter_qbx_widget.setValue(
            self.hud_deadline_priority_widget.value()
        )
    
    def set_priority_value_to_slider(self):
        
        self.hud_deadline_priority_widget.setValue(
            self.hud_priority_counter_qbx_widget.value()
        )
    
    def framepertask_value_to_spinbox(self):
        
         self.hud_priority_fpt_qbx_widget.setValue(
            self.hud_deadline_framepertask_widget.value()
        )
    
    def framepertask_value_to_slider(self):
        
        self.hud_deadline_framepertask_widget.setValue(
            self.hud_priority_fpt_qbx_widget.value()
        )
        
    def get_transform_nodes(self):
        
        # Get all the transform Nodes
        transform_set = set(cmds.listRelatives(cmds.ls(transforms=True), ap=True, ni=True))   
        # Get all the mesh nodes
        mesh_set = set(cmds.listRelatives(cmds.ls(typ='mesh'), parent=True))
        # Do the set different operations to get only groups
        groups = list(transform_set.difference(mesh_set))
        return groups
            
            
    def delete_all_hud_in_scene(self):
        
        """Delete all the Hud related camera, groups and 
        Materials created behalf of the HUD creation Process"""
        
        try:
            
            # Iterate all the groups if the playplst_camera 
            # attribute found then delete it 
            hud_groups = []
            for hud_group in self.get_transform_nodes():
                if cmds.attributeQuery("playblast_camera", node=hud_group, exists=True):
                    hud_groups.append(hud_group)
            
            for hud_grp in hud_groups:
                cmds.delete(hud_grp)
            
            # Any Shader assigned with part of the HUD creation deleted
            for mat in cmds.ls(mat=True):
                if cmds.attributeQuery("playblast_camera", node=mat, exists=True):
                    cmds.delete(mat)
                    
            self.window.close()
            
        except TypeError:
            self.show_messagebox("No HUD Text to Delete")
            
    def load_hud(self):
        
        get_user_camera = self.get_user_selected_camera()
        
        transformation_nodes =[]
        for hud_group in sorted(self.get_transform_nodes()):
            if cmds.attributeQuery("playblast_camera", node=hud_group, exists=True):
                self.submit_to_deadline_btn.setEnabled(True)
                transformation_nodes.append(hud_group)

        point_constrained_master_camera = []
        parentconstrained_hud_cameragrp =[] 
        custom_string_huds_cameragrp = []
        custom_hud_grp = []
        for transformation_node in transformation_nodes:
            if  cmds.pointConstraint(transformation_node, q=True, tl=True):
                point_constrained_master_camera.append(
                    cmds.pointConstraint(transformation_node, q=True, tl=True)[0]
                )
            if cmds.parentConstraint(transformation_node, q=True):
                parentconstrained_hud_cameragrp.append(
                    cmds.listAttr(transformation_node, userDefined=True, scalar=True)
                )
                str_huds =(
                    set(
                        cmds.listAttr(transformation_node, userDefined=True)
                    )-set(
                        cmds.listAttr(transformation_node, userDefined=True, scalar=True)
                    )
                )
                custom_string_huds_cameragrp.append(list(str_huds))
                custom_hud_grp.append(transformation_node)
                
        custom_hud_txts = {}
        camera_string_attributes = {}

        for master_camera, hud_camera, custom_hud_txt in \
                    zip(point_constrained_master_camera, custom_hud_grp, custom_string_huds_cameragrp):
            custom_hud_txts.setdefault(master_camera,{})[hud_camera] = custom_hud_txt

        for camera,hud_cam_key_val in custom_hud_txts.items():
            custom_hud_key_values =[]
            for hud_cam,hud_txt_key_vals in hud_cam_key_val.items():
                for hud_txt_key_val in hud_txt_key_vals:
                    custom_hud_key_values.append(
                        {hud_txt_key_val : cmds.getAttr( hud_cam +'.'+ hud_txt_key_val)}
                    )
                    camera_string_attributes[camera] = custom_hud_key_values
                    
                    
        camera_scalar_attributes =  dict(
            zip(point_constrained_master_camera, 
                parentconstrained_hud_cameragrp)
        )
        
        for cam, attributes in camera_scalar_attributes.items():
            if cam in get_user_camera:
                for attribute in attributes:
                    for widget in self.all_hud_combobox_widgets:
                        if widget.objectName()==attribute:
                            widget.setChecked(True)
        
        self.hud_custom_text_treeview.model().removeRows(
                    0, 
                    self.hud_custom_text_treeview.model().rowCount() 
        )
        for camera, custom_texts in camera_string_attributes.items():
            if camera in get_user_camera:
                self.hud_custom_toggle_widget.setChecked(True)
                for custom_text in custom_texts:
                    for attr_name, attr_value in custom_text.items(): 
                        self.hud_custom_text_treeview.model().appendRow(
                            [QStandardItem(attr_name),
                             QStandardItem(attr_value)
                            ]
                        ) 
            else:              
                self.hud_custom_toggle_widget.setChecked(False)  
                        
    def create_update_hud(self):   
        
        def create_hud():
                  
            self.hud_camera = self.duplicate_camera()
            self.camera_properties = [
                self.get_current_frame_no,
                self.get_current_maya_file_name,
                self.get_username,
                self.get_scene_fps,
                self.get_camera_focal_length,
                self.get_scene_resolution,
                self.get_camera_sensor_size,
                self.get_scene_pixel_aspect_ratio
            ]

            text_hud_name = self.hud_camera[0]+ "_Text_HUD"
            text_hud_transform_grp = self.hud_camera[0]+ "_user_transform"
            cmds.group( empty=True, name=text_hud_name )
            cmds.group( empty=True, name=text_hud_transform_grp, parent=text_hud_name )
            
            
            self.create_custom_addtribute(text_hud_name, 'playblast_camera', 'bool', 1)
            self.create_custom_addtribute(text_hud_name, 'created', 'bool', 1)
            # cmds.parent(text_hud_transform_grp, text_hud_name )
            
            def create_text(cam_properties, y_pos):
                
                generate_hud_txt = GenerateHudText(cam_properties)
                font_obj = generate_hud_txt.generate_text(y_pos)
                cmds.parent(font_obj, text_hud_transform_grp )
                if ':' in  cam_properties:
                    new_name = cam_properties.split(':')[0]
                else:
                    new_name = cam_properties
                cmds.rename(font_obj, new_name)
                
            y_pos = 0   
            # Create text for all the inbuilt property
            for cam_properties in self.camera_properties:
                if cam_properties:
                    create_text(cam_properties[0], y_pos)
                    self.create_custom_addtribute(text_hud_name, cam_properties[-1], 'bool', 1)
                    y_pos = y_pos +-0.006
                    
            # Create HUD for all the custom text         
            if self.get_user_custom_hud_text:     
                for custom_hud in self.get_user_custom_hud_text:
                    custom_hud_txt = ":".join(custom_hud)  
                    create_text(custom_hud_txt, y_pos)
                    y_pos = y_pos +-0.006
                    self.create_custom_addtribute(text_hud_name, custom_hud[0], 'string', custom_hud[-1])
            
            cmds.xform(text_hud_name, centerPivots = True)
            cmds.xform(text_hud_transform_grp, centerPivots = True)
            
            # Reapply the xform again back to the group object
            if hasattr(self, 'hud_trans'):
                cmds.xform(text_hud_transform_grp, 
                           translation=self.hud_trans[0])
            if hasattr(self, 'hud_rotate'):
                cmds.xform(text_hud_transform_grp, 
                           rotation=self.hud_rotate[0])
            if hasattr(self, 'hud_scale'):
                cmds.xform(text_hud_transform_grp, 
                           scale=self.hud_scale[0])
            
            # Screen calculation to place the text
            device_aspect_ratio = round(
                                            float(cmds.getAttr("defaultResolution.deviceAspectRatio")), 2
            )
    
            if device_aspect_ratio == 1.33:
                screen_left_x = -0.2
                screen_left_y = 0.145
                cmds.move(screen_left_x, screen_left_y, 0, text_hud_name)
            elif device_aspect_ratio == 1:

                screen_left_x =-0.152
                screen_left_y = 0.145
                cmds.move(screen_left_x, screen_left_y, 0, text_hud_name)
            else:
                screen_left_x = -0.268
                screen_left_y = 0.142
                cmds.move(screen_left_x, screen_left_y, 0, text_hud_name)
            
            # Constraint the Hud camera with the group and maintain 
            # transform offset for the text to move withe camera
            grp_to_camera_constraint = cmds.parentConstraint( 
                                                                self.hud_camera[0], 
                                                                text_hud_name, 
                                                                maintainOffset=True 
                                                            )
            self.create_custom_addtribute(grp_to_camera_constraint[0], 'constraint', 'bool', 1)
            
            hud_camera_to_mastercam_orientconstraint = cmds.orientConstraint(
                            self.user_selected_camera, 
                            self.hud_camera[0] 
            )
            self.create_custom_addtribute(hud_camera_to_mastercam_orientconstraint[0], 
                                            'constraint', 'bool', 1)
            hud_camera_to_mastercam_pontconstraint = cmds.pointConstraint(
                        self.user_selected_camera, 
                        self.hud_camera[0]
            )
            self.create_custom_addtribute(hud_camera_to_mastercam_pontconstraint[0], 
                                            'constraint', 'bool', 1)
            
            # Create surface shader anc connected it into the group aka all the meshes
            shd = cmds.shadingNode("surfaceShader", name="%s_shaders" %text_hud_name, asShader=True)
            self.create_custom_addtribute(shd, 'playblast_camera', 'bool', 1) 
            shdSG = cmds.sets(name='%sSG' % shd, empty=True, renderable=True, noSurfaceShader=True)
            
            # While Recreating the shader we check if any color was changed the we reaply it
            if hasattr(self,'shader_color'):
                cmds.setAttr('%s.outColor' %shd, 
                             self.shader_color[0],
                             self.shader_color[1],
                             self.shader_color[2], 
                             type="double3"
                )
            else:
                cmds.setAttr('%s.outColor' %shd, 1, 1, 1, type="double3"),
            cmds.connectAttr('%s.outColor' % shd, '%s.surfaceShader' % shdSG)
            cmds.sets(text_hud_name, e=True, forceElement=shdSG)
            cmds.select( clear=True )
            self.window.close()
        
        # Check if user selected hud__group1_camera_Text_HUD group object
        # if selected then update mode will activated. 
        # It apply the preserved transform to recreated hud text objects 
        # Delete all the Hud based objects and recreated with the preserved 
        # settings 
        
        get_user_selected = cmds.ls(sl=True)
        if get_user_selected:
        
            if len(get_user_selected) != 1 or not cmds.attributeQuery("playblast_camera", 
                                                                node=get_user_selected[0], 
                                                                exists=True):
                msg = "Select Only Hud Group Created.\n"
                msg += "Hud Example Name in Scene \n\n"
                msg += "\'hud__group1_camera1_Text_HUD\'"
                self.show_messagebox(msg)
            else:
                
                # Get the surface shader from the selected group
                # It list all the nodes inside the hud__group1_camera1_Text_HUD
                # likely [u'Frame_NoShape', u'Focal_LengthShape', u'ResolutionShape']
                theNodes = cmds.ls(get_user_selected, dag = True, s = True)
                
                # Get the shading engine and the material of the respective 
                shadeEng = cmds.listConnections(theNodes , type = 'shadingEngine')
                self.surface_shader = list(set(cmds.ls(cmds.listConnections(shadeEng ), materials = True)))
                self.shader_color = cmds.getAttr(self.surface_shader[0] +".outColor")[0]
                
                if cmds.attributeQuery("created", 
                                        node=get_user_selected[0], 
                                        exists=True):
                    
                    for children in cmds.listRelatives(get_user_selected[0],  
                                                    children=True):
                        if children.endswith("_user_transform"):
                            self.hud_trans = cmds.getAttr(children +".translate")
                            self.hud_rotate = cmds.getAttr(children +".rotate")
                            self.hud_scale = cmds.getAttr(children +".scale")
                            
                    self.parent_camera = cmds.parentConstraint( get_user_selected[0],
                                                                q=True, 
                                                                targetList=True
                                                                )
                    cmds.delete(self.parent_camera)
                    cmds.delete(get_user_selected[0])
                    cmds.delete(self.surface_shader[0])
                    create_hud()             
        else:
            
            #  if nothing is selected in the outliner then the 
            # it try to find all the list of constraints. 
            # if any hud related constraint have a relationship with
            # a parent camera, user trying to create a a fresh hud
            # for same camera then it omitted with poping up a GUI 
            camera_with_constraints = [] 
            constraint_camera_name = ''
            scene_constraints = cmds.ls( type='constraint')
            if scene_constraints:
                for scene_constraint in scene_constraints:
                    if cmds.attributeQuery("constraint", node=scene_constraint, exists=True):
                        if cmds.objectType(scene_constraint) == 'pointConstraint':
                            constraint_camera_name =  cmds.pointConstraint(scene_constraint, query=True,targetList=True)
                            constraint_camera_shape_path = cmds.listRelatives(
                                            constraint_camera_name, 
                                            shapes=True,
                            )
                            constraint_camera_fullpath = cmds.listRelatives(
                                        constraint_camera_shape_path, 
                                        parent=True,
                                        fullPath=True,
                            )
                            if constraint_camera_fullpath[0] not in camera_with_constraints:  
                                camera_with_constraints.append(constraint_camera_fullpath[0])
                                 
                if any (camera_with_constraint==camera_transform_node and 
                        camera_with_constraint==self.get_user_selected_camera() 
                        for camera_with_constraint in camera_with_constraints 
                        for camera_transform_node in self.get_camera_transform_nodes()
                    ):
                    msg = "A text HUD is already Created from selected Camera!!\n"
                    msg += "Please Select Hud Group to update\n"
                    msg += "Hud Example Name in Scene \n\n"
                    msg += "\'hud__group1_camera1_Text_HUD\'"
                    self.show_messagebox(msg)
                else:
                    create_hud()          
            # If all case fails user not selected anything, For given
            # camera no constraints exist then a fresh HUD text created       
            else:
                if self.is_checked:
                    create_hud()
                else:
                    msg  = 'No HUD check box were selected'
                    self.show_messagebox(msg)
    
    def validation_check(self):
        
        msgs = []
        if not self.is_filled:
            msg = 'Fill and Check all the required fields to proceed'
            msgs.append(msg)
        
        if not isinstance(int(self.hud_start_frame_txt.text()), int) or \
                    not isinstance(int(self.hud_end_frame_txt.text()), int):
            msg = "Frame Ranges Were Not Valid"
            msgs.append(msg)
        
        if not self.get_user_selected_camera():
            msg = "Scene Does Not have any cameras"
            msgs.append(msg)
        
        if not cmds.file(query=True, sceneName=True):
             msg = "Please save the Scene File using Shotgrid"
             msgs.append(msg)
        
        if int(self.hud_start_frame_txt.text()) > int(self.hud_end_frame_txt.text()):
            msg = "Please Check the Frame range. Start frame have higher value than end frame"
            msgs.append(msg)
            
        if msgs:
            self.show_messagebox('\n'.join(msgs))
            return False
            
        return True
    
    def submit_to_deadline(self):
        
        if self.validation_check():
            start_frame = int(self.hud_start_frame_txt.text())
            end_frame = int(self.hud_end_frame_txt.text())
            folder_path =  self.hud_folder_path_widget.text()
            file_name = self.hud_file_path_widget.text()
            job_name = self.hud_deadline_job_name_widget.text()
            comments = self.hud_deadline_job_comments_widget.text()
            pool = self.hud_deadline_pool.currentText()
            priority = self.hud_deadline_priority_widget.value()
            chunksize = self.hud_deadline_framepertask_widget.value()
            batch_name = cmds.file(query=True, sceneName=True, shortName=True)
            steps = 1
            scene_file_full_path = cmds.file(query=True, sceneName=True)
            publish_mov = True if self.hud_publish_mov_toggle.isChecked() else False
            submit_farm = False if self.hud_local_hw_toggle.isChecked() else True
                
            submit_hardware_render = HardwareRenderOperations(batch_name,
                                                              job_name,
                                                              comments,
                                                              pool,
                                                              priority,
                                                              chunksize,
                                                              steps,
                                                              self.get_user_selected_camera(),
                                                              start_frame,
                                                              end_frame,
                                                              scene_file_full_path,
                                                              folder_path=folder_path,
                                                              file_name=file_name,
                                                              publish_mov=publish_mov,
                                                              submit_farm=submit_farm
                                                              )
            submit_hardware_render.do_render()
            self.window.close()
        
        pass
    
    def play_in_rv(self):
        
        import shutil 
        
        rv = r"C:\Program Files\ShotGrid\RV-2022.2.0\bin\rv.exe"        
        rv_exists = lambda: shutil.which(rv) is not None
        selected_items = set()
        all_items = set()
        
        if not rv_exists:
            self.show_messagebox("RV Not configured or NOt installed Contact Production")
        else:
            folderpath = self.rv_folder_path_txt_widget.text()
            if not os.path.exists(folderpath):
                self.show_messagebox("The given path not exsist")
            else:
                for index in self.rv_exr_folder_names_listview_widget.selectedIndexes():
                    item = self.rv_exr_folder_names_listview_widget.model().itemFromIndex(index)
                    folder_fullpath= os.path.join(folderpath, item.text() )
                    selected_items.add(folder_fullpath)
                    
                if not selected_items:  
                    model = self.rv_exr_folder_names_listview_widget.model()
                    for index in range(model.rowCount()):
                        item = model.item(index)
                        folder_fullpath= os.path.join(folderpath, item.text() )
                        all_items.add(folder_fullpath)
            
            if selected_items:
                rv_string = "%s -sRGB %s" %(rv,
                                    " ".join(selected_items))
            if all_items:
                rv_string = "%s -sRGB %s" %(rv,
                                    " ".join(all_items))
            subprocess.Popen(rv_string)
        


class GenerateHudText:
    
    def __init__(self, text):
        
        self.text = text    
        final = list()
        for char in str(self.text):
            final.append(format(ord(char), "x"))
        self.ord_text =  ' '.join(final)
    
    def generate_text(self, y_pos=0):
        
        cmds.CreatePolygonType()
        
        #Delete all the default materials created during the type
        #node creation
        for type_materials in cmds.ls(mat=True):
            if type_materials.startswith('type'):
                cmds.delete(type_materials)
                
        self.font_object_name = cmds.ls(sl=True)[0]
        self.font_type_node = cmds.listConnections("%s.message" %self.font_object_name)[0]

        for type_node in  cmds.listConnections(self.font_type_node):
            if 'Extrude' in type_node:
                type_extrude = type_node
        cmds.setAttr('%s.fontSize' %self.font_type_node, 0.008)
        cmds.setAttr('%s.enableExtrusion'  %type_extrude, 0)
        if not self.text.startswith('Frame No'):
            cmds.setAttr('%s.textInput'  %self.font_type_node, self.ord_text, type='string')
            cmds.move(0, y_pos, -0.45, self.font_object_name)

        else:
            cmds.setAttr('%s.generator' %self.font_type_node, 1)
            cmds.move(0.35, y_pos, -0.45, self.font_object_name)
         
       
        return self.font_object_name
 
 
     
class HardwareRenderOperations:
    
    def __init__(self,
                batch_name,
                job_name,
                comments,
                pool,
                priority,
                chunksize,
                steps, 
                camera_name,
                start_frame,
                end_frame,
                scene_file_full_path,
                folder_path = '',
                file_name = '',
                publish_mov=False,
                submit_farm=False):
        
        self.batch_name = batch_name
        self.job_name=job_name
        self.comments=comments
        self.pool=pool
        self.priority=priority
        self.chunksize=chunksize
        self.steps=steps
        self.camera_name = camera_name
        self.start_frame = start_frame
        self.end_frame = end_frame
        self.scene_file_full_path = scene_file_full_path
        self.folder_path = folder_path
        self.file_name = file_name
        self.publish_mov = publish_mov
        self.submit_farm = submit_farm
        self.__set_hardware_settings()
        
        
    def __set_hardware_settings(self):
        
        cmds.setAttr('defaultRenderGlobals.ren', 'mayaHardware2', type='string')
        cmds.setAttr('defaultRenderGlobals.imageFormat', 40)
        cmds.setAttr('defaultRenderGlobals.deadlineStrictErrorChecking', 1)
        
        # cmds.setAttr('defaultRenderGlobals.outFormatControl', 0)
        cmds.setAttr('defaultRenderGlobals.animation', 1)
        cmds.setAttr('defaultRenderGlobals.putFrameBeforeExt', 1)
        cmds.setAttr('defaultRenderGlobals.extensionPadding', 4)
        cmds.setAttr('defaultRenderGlobals.byFrame', 1)
        # cmds.setAttr('defaultRenderGlobals.byFrameStep', 1)
        cmds.setAttr('defaultRenderGlobals.startFrame', self.start_frame)
        cmds.setAttr('defaultRenderGlobals.endFrame', self.end_frame)
        output_folder = self.__create_output_directory()
        cmds.setAttr('defaultRenderGlobals.imageFilePrefix', 
                     os.path.join(self.folder_path, self.file_name, self.file_name),  
                     type='string')
        object_filter_enable_array = [1] * 22
        cmds.setAttr( "hardwareRenderingGlobals.objectTypeFilterValueArray",
                            object_filter_enable_array,
                            type='Int32Array'
        )
        if cmds.window("unifiedRenderGlobalsWindow", exists=True):
            cmds.deleteUI("unifiedRenderGlobalsWindow")
        mel.eval('unifiedRenderGlobalsWindow;')
        
        
    def __create_output_directory(self):
        
        self.output_folder = os.path.join(self.folder_path, self.file_name)
        
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        return self.output_folder
      
    def do_render(self):
        
        cmds.file(save=True)
        if not self.submit_farm: 
            self.do_batch_render() 
        else:
            self.__submit_to_deadline()
    
    def do_batch_render(self):

        args = 'batch_name=\'%s\',' %self.batch_name
        args += 'job_name=\'%s\',' %self.job_name
        args += 'comment=\'%s\',' %self.comments
        args += 'pool=\'%s\',' %self.pool
        args += 'priority=%s,' %self.priority
        args += 'chunksize=%s,' %self.chunksize
        args += 'steps=%s,' %self.steps
        args += 'camera_name=\'%s\',' %self.camera_name
        args += 'start_frame=%s,'%self.start_frame
        args += 'end_frame=%s,' %self.end_frame
        args += 'scene_file_full_path=\'%s\',' %self.scene_file_full_path
        args += 'folder_path=\'%s\',' %self.folder_path
        args += 'file_name=\'%s\',' %self.file_name
        args += 'renderer=\'mayaHardware2\','
        args += 'maya_version=\'2020\','
        args += 'publish_mov=%s,' %self.publish_mov
        args += 'farm_hardware_render=%s,' %self.submit_farm
        
        # Add shot grid entities if publish mov is on
        if self.publish_mov:
            engine = sgtk.platform.current_engine()
            shot = engine.context.entity
            shot_id = shot['id']
            seq = engine.shotgun.find("Shot", 
                                    [['id', 'is', shot_id ]],
                                    ['sg_sequence'])[0]['sg_sequence']['name']
            task = engine.context.task
            project = engine.context.project
            user = engine.context.user
            args += 'project=%s,' %project
            args += 'seq=\'%s\',' %seq
            args += 'shot=%s,' %shot
            args += 'task=%s,' %task
            args += 'user=%s,' %user
                    
        cmds.setAttr('defaultRenderGlobals.postMel', 
                     'python("from playblast_manager import submit_to_deadline as sd;reload(sd);sub=sd.SubmitToDeadline(%s);sub.submit()")' %args,
                                type='string')
        cmds.file(save=True)
        
        cmd = r'"C:\Program Files\Autodesk\Maya2020\bin\Render.exe"'
        cmd += " -r hw2"
        cmd += " -s %s" %self.start_frame
        cmd += " -e %s" %self.end_frame
        cmd += " -b %s" %self.steps
        cmd += " -cam %s" %cmds.ls(self.camera_name)[0]
        cmd += " -pad 4"
        cmd += " -of exr"
        cmd += " -rd '%s'" %os.path.join(self.folder_path, self.file_name)
        cmd += " %s" %self.scene_file_full_path
        os.system("start /wait cmd /k %s" %cmd)

    def __submit_to_deadline(self):
        
        cmds.setAttr('defaultRenderGlobals.postMel', ' ', type='string')
        from . import submit_to_deadline
        reload(submit_to_deadline)
        submit_to_deadline = submit_to_deadline.SubmitToDeadline(
                    batch_name=self.batch_name,
                    job_name=self.job_name,
                    comment=self.comments,
                    pool=self.pool,
                    priority=self.priority,
                    chunksize=self.chunksize,
                    steps=self.steps,
                    camera_name=self.camera_name,
                    start_frame=self.start_frame,
                    end_frame=self.end_frame,
                    scene_file_full_path=self.scene_file_full_path,
                    folder_path=self.folder_path,
                    file_name=self.file_name,
                    renderer='mayaHardware2',
                    maya_version="2020",
                    publish_mov=self.publish_mov,
                    farm_hardware_render=self.submit_farm,
        )
        submit_to_deadline.submit()
        
        
        pass
           
a = PlayBlastManager()
a.window.show()
