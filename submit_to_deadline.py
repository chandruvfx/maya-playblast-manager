import maya.cmds as cmds
import os
import subprocess
import sgtk

class SubmitToDeadline:
    
    def __init__(self,
                 batch_name = '',
                 job_name = '',
                 comment = '',
                 pool = '',
                 priority = 50,
                 chunksize = 10,
                 steps = 1,
                 camera_name = '',
                 start_frame = 1,
                 end_frame = 1,
                 scene_file_full_path = '',
                 folder_path = '',
                 file_name = '',
                 renderer = "mayaHardware2",
                 maya_version = 2020,
                 publish_mov = False,
                 farm_hardware_render = False,
                 project='',
                 seq='',
                 shot='',
                 task='',
                 user='',
                ):
        
        self.batch_name = batch_name
        self.job_name = job_name
        self.comment = comment
        self.pool = pool
        self.priority = priority
        self.chunksize = chunksize
        self.start_frame =  start_frame
        self.end_frame = end_frame
        self.steps = steps
        self.camera_name = camera_name
        self.scene_file_full_path = scene_file_full_path
        self.folder_path = folder_path
        self.file_name = file_name
        self.renderer = renderer
        self.maya_version = maya_version
        self.publish_mov = publish_mov
        self.farm_hardware_render = farm_hardware_render
        self.project = project
        self.seq = seq
        self.shot = shot
        self.task = task
        self.user = user
        
        self.deadline_files = []   
        self.msgs = ''
        self.maya_playblast_version_py_files=[] 
        self.maya_tmp_dir = "Y:/pipeline/studio/temp/" + \
                      os.environ.get( 'USERNAME' ) + "/" +\
                      "maya_" + os.environ.get('maya_version') + "/"

    @staticmethod
    def __crete_directory(folder_path):
            
            dir_exist = os.path.exists(folder_path)
            if not dir_exist:
                os.makedirs(folder_path)
    
    def __write_job_file(self, filename, data, job_type=''):
        
        dl_job_dir =  self.maya_tmp_dir + \
                          "/%s/deadline_job_files" %job_type
        self.__crete_directory(dl_job_dir)

        job_file = os.path.join(dl_job_dir, filename)
            
        with open(job_file, "w") as write_file:
            for key, value in data.items():
                write_file.write(key +"=" + value + "\n") 
        self.deadline_files.append(job_file)
        return job_file
   
    def __file_job_info(self, job_type='', dep_job_id=''):
        
        if job_type == 'maya':
            plugin = 'MayaBatch'
        elif job_type == 'draft':
            plugin = 'DraftPlugin'
        elif job_type == 'version_publish':
            plugin = 'Python'
                
        dl_job_info = {
            "BatchName": self.job_name,
            "Name": self.job_name,
            "Comment" : self.comment,
            "ChunkSize" : str(self.chunksize),
            "Plugin" : plugin,
            "Pool": self.pool
            }
        
        if job_type == 'maya':
            dl_job_info['Frames'] = "%s-%severy%s" %(str(self.start_frame), 
                                                     str(self.end_frame),
                                                     str(self.steps))
            dl_job_info["OutputDirectory0"] = os.path.join(self.folder_path ,
                                                           self.file_name )
            dl_job_info["OutputFilename0"] = self.file_name 
            
        elif job_type == 'draft' or \
                    job_type == 'version_publish':
                if dep_job_id:
                    dl_job_info['JobDependency0'] = dep_job_id

        job_info_file = self.__write_job_file("job_info_%s_%s.job" 
                                        %(self.file_name, self.camera_name.replace("|", "_")), 
                                        dl_job_info,
                                        job_type)
        return job_info_file
        
        
    def __plugin_job_info(self, job_type='', 
                        exr_path='',
                        mov_path=''):
    
        if job_type == 'maya':
                dl_plugin_job_info = {
                    "OutputFilePath": os.path.join(self.folder_path ,
                                                self.file_name ),
                    "Camera" : self.camera_name,
                    "Renderer": self.renderer,
                    "StrictErrorChecking":'0',
                    "SceneFile" : self.scene_file_full_path,
                    "Version" : self.maya_version,
                    "OutputFilePrefix" : os.path.join(self.folder_path ,
                                                self.file_name,  self.file_name)
                }
        elif job_type == 'draft':
            
            dl_plugin_job_info = {
                'scriptFile': os.path.dirname(os.path.abspath(__file__)) +"/convert.py",
                'ScriptArg0=mov': mov_path,
                'ScriptArg1=exr': exr_path,
                'ScriptArg2=start_frame': str(self.start_frame),
                'ScriptArg3=end_frame':str(self.end_frame)   
            }
            
            
        elif job_type == 'version_publish':
            dl_plugin_job_info = {
                'Arguments' : ' ',
                'SingleFramesOnly': 'False',
                'Version': '3.7'
            }
            
        plugin_info_file = self.__write_job_file("plugin_info_%s_%s.job" 
                                            %(self.file_name, 
                                                self.camera_name.replace("|", "_")),
                                                dl_plugin_job_info,
                                                job_type)
        return plugin_info_file
    

    def send_to_farm(self, auxiliary_files = None):
        
        dl_path = os.environ['DEADLINE_PATH'] 
        dl_path = dl_path.replace(r"/", "//") + "//deadlinecommand.exe"
        dl_path = '"%s"' %dl_path
        if not auxiliary_files:
            dl_command = '%s %s' %(dl_path, " ".join(self.deadline_files))
        else:
            dl_command = '%s %s %s' %(dl_path, 
                                    " ".join(self.deadline_files),
                                    " ".join(auxiliary_files))
        result = subprocess.Popen(dl_command, 
                                stdout=subprocess.PIPE, 
                                shell=True)
        job_id = [id for id in result.communicate()[0].split() if 'JobID' in id]
        return job_id[0]
    
    def submit(self):

        if self.farm_hardware_render:
            self.__file_job_info(job_type='maya')
            self.__plugin_job_info(job_type='maya')
            
            job_id = self.send_to_farm()
            self.msgs += "Deadline Maya Job ID=%s\n" %str(job_id).split("=")[-1]
        
            self.deadline_files[:] = []
            self.__file_job_info(job_type='draft', dep_job_id=job_id.split('=')[-1])
        else:
            
            self.__file_job_info(job_type='draft')
            
        if self.publish_mov: 
            
            img_folder_path = os.path.join(self.folder_path ,
                                    self.file_name )
            full_path = img_folder_path + '/' + self.file_name + ".$F4.exr"
            mov_path =  img_folder_path + '/' + self.file_name + ".mov"
            self.__plugin_job_info(job_type='draft', 
                            exr_path=full_path, 
                            mov_path=mov_path)
            draft_job_id = self.send_to_farm()
            
            engine = sgtk.platform.current_engine()
            shot = self.shot if self.shot else engine.context.entity
            shot_id = shot['id']
            seq = self.seq if self.seq else engine.shotgun.find("Shot", 
                                                    [['id', 'is', shot_id ]],
                                                    ['sg_sequence'])[0]['sg_sequence']['name']
            task = self.task if self.task else engine.context.task
            project = self.project if self.project else engine.context.project
            user = self.user if self.user else engine.context.user
            exr_path = full_path.split("$F4")
            exr_path = exr_path[0] + '####.exr'
            publish_script = """ 
import shotgun_api3
shotgun_api3.shotgun.NO_SSL_VALIDATION= True
sg = shotgun_api3.Shotgun("https://future-associate.shotgunstudio.com",
                        script_name="deadline_integration5",
                        api_key="wjtuuZdl4gqivbndwiqecow$f",
                        http_proxy="proxy01.future.associate:3128")
data = { 'project': %s,
        'code': '%s',
        'description': r'%s',
        'sg_path_to_frames': r'%s',
        'sg_path_to_movie': r'%s',
        'sg_status_list': 'rev',
        'entity': %s,
        'sg_task': %s,
        'user': %s }
version_id = sg.create("Version", data) 
sg.upload("Version", version_id['id'], r'%s', field_name="sg_uploaded_movie")                        
                """%(project, 
                    self.file_name, 
                    self.comment, 
                    exr_path.replace("/", "\\"), 
                    mov_path.replace("/", "\\"),
                    shot, 
                    task,
                    user,
                    mov_path.replace("/", "\\"),
                    )

            maya_playblast_version_py_dir =   self.maya_tmp_dir + \
                                        "playblast/" + project['name'] + "/" + \
                                        seq + "/" + shot['name'] 
            self.__crete_directory(maya_playblast_version_py_dir) 
            maya_playblast_version_py_file =  os.path.join(maya_playblast_version_py_dir, self.file_name + ".py")
            with open(maya_playblast_version_py_file, "w") as flipbook_file:
                flipbook_file.write(publish_script)

            self.deadline_files[:] = []
            
            self.__file_job_info(job_type='version_publish', dep_job_id=draft_job_id.split('=')[-1])
            self.__plugin_job_info(job_type='version_publish', 
                            exr_path=full_path, 
                            mov_path=mov_path)
            
            self.maya_playblast_version_py_files.append(maya_playblast_version_py_file)
            version_publish_job_id = self.send_to_farm(
                auxiliary_files=self.maya_playblast_version_py_files
            )
            self.msgs+= "Deadline Draft Job Id=%s\n" %str(draft_job_id).split("=")[-1]
            self.msgs+= "Deadline Mov Publish Job Id=%s\n" %str(version_publish_job_id).split("=")[-1]
        
        print self.msgs
        myWin = cmds.window(title="FAE Message ", widthHeight=(300, 80))
        cmds.columnLayout()
        cmds.text(label=self.msgs)
        cmds.showWindow(myWin)
